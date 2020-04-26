import copy
import re
from collections import namedtuple

from beancount.core import convert
from beancount.core.amount import Amount
from beancount.core.data import Transaction, Price
from beancount.core.inventory import Inventory
from beancount.core.prices import build_price_map

from fava_investor.modules.performance.returns import returns

SplitEntries = namedtuple("Balance",
                          "transactions balances values contributions withdrawals dividends costs gains_realized gains_unrealized")
Change = namedtuple("Change", "transaction change")


def needs_dummy_transaction(entries):
    has_prices_after_last_transaction = False
    for entry in reversed(entries):
        if isinstance(entry, Price):
            has_prices_after_last_transaction = True
        if isinstance(entry, Transaction):
            return has_prices_after_last_transaction


def split_journal(accapi, pattern_value, pattern_internal, pattern_internalized="^Income:Dividend", limit=None):
    accounts = accapi.accounts
    accounts_value = set([acc for acc in accounts if re.match(pattern_value, acc)])
    accounts_internal = set([acc for acc in accounts if re.match(pattern_internal, acc)])
    accounts_internalized = set([acc for acc in accounts if re.match(pattern_internalized, acc)])

    if needs_dummy_transaction(accapi.ledger.entries):
        accapi.ledger.entries.append(Transaction(None, None, None, None, "UNREALIZED GAINS NEW BALANCE", [], [], []))

    _, _, original_and_internalized = returns.internalize(accapi.ledger.entries, "Equity:Internalized", accounts_value,
                                                          accounts_internal, accounts_internalized)
    price_map = build_price_map_with_fallback_to_cost(accapi.ledger.entries)

    balance = Inventory()
    result = SplitEntries([], [], [], [], [], [], [], [], [])
    last_unrealized_gain = Inventory()

    is_external = lambda acc: acc not in accounts_value \
                              and acc not in accounts_internal \
                              and acc not in accounts_internalized
    i = 0
    for original_entry, internalized_entries in original_and_internalized:
        i += 1
        dividends = Inventory()
        costs = Inventory()
        contributions = Inventory()
        withdrawals = Inventory()
        gains_realized = Inventory()
        if limit is not None and i > limit:
            break
        for entry in internalized_entries:
            if not isinstance(entry, Transaction):
                continue

            value = any([p.account in accounts_value for p in entry.postings])
            internal = any([p.account in accounts_internal for p in entry.postings])
            internalized = any([p.account in accounts_internalized for p in entry.postings])
            external = any([is_external(p.account) for p in entry.postings])

            include_postings(balance, entry, accounts_value)

            if (value and internal and not is_commodity_sale(entry, accounts_value)) \
                    or (not value and internalized and external):
                include_postings(dividends, entry, accounts_internal, filter=lambda posting: posting.units.number < 0)

            if value and internal:
                include_postings(costs, entry, accounts_internal, filter=lambda posting: posting.units.number > 0)

            if value and internal and is_commodity_sale(entry, accounts_value):
                include_postings(gains_realized, entry, accounts_internal, filter=lambda posting: posting.units.number < 0)

            if value and external:
                include_postings(contributions, entry, exclude_accounts=accounts_value | accounts_internal,
                                 filter=lambda posting: posting.units.number < 0)
                include_postings(withdrawals, entry, exclude_accounts=accounts_value | accounts_internal,
                                 filter=lambda posting: posting.units.number > 0)

        # unrealized gain
        current_value = balance.reduce(convert.get_value, price_map, original_entry.date)
        current_cost = balance.reduce(convert.get_cost)
        unrealized_gain = Inventory()
        unrealized_gain.add_inventory(current_value).add_inventory(-current_cost)
        unrealized_gain_change = Inventory()
        unrealized_gain_change.add_inventory(unrealized_gain).add_inventory(-last_unrealized_gain)
        last_unrealized_gain = unrealized_gain

        if unrealized_gain_change != {}:
            a= 1
        result.contributions.append(-contributions)
        result.withdrawals.append(-withdrawals)
        result.dividends.append(-dividends)
        result.costs.append(-costs)
        result.gains_realized.append(-gains_realized)
        result.gains_unrealized.append(unrealized_gain_change)

        current_value = balance.reduce(convert.get_value, price_map, original_entry.date)
        result.balances.append(copy.copy(balance))
        result.values.append(current_value)
        result.transactions.append(original_entry)

    try:
        slice = [
            sum_inventories(result.contributions),
            sum_inventories(result.withdrawals),
            sum_inventories(result.dividends),
            sum_inventories(result.costs),
            sum_inventories(result.gains_unrealized),
            sum_inventories(result.gains_realized),
        ]
        checksum = sum_inventories(slice)
        # assert checksum == balance, f"Sum of splits have to match regular balance. Total balance and checksum: \n{balance}\n{checksum}\n"
    except AssertionError as e:
        raise e  # breakpoint here :D
    except Exception as e:
        raise e
    return result


def is_commodity_sale(entry: Transaction, value_accounts):
    for posting in entry.postings:
        if posting.account not in value_accounts:
            continue
        if posting.units.number < 0 and posting.cost is not None:
            return True
    return False


def sum_inventories(inv_list):
    sum = Inventory()
    for inv in inv_list:
        sum.add_inventory(inv)
    return sum


def get_matching_accounts(accounts, pattern):
    return set([acc for acc in accounts if re.match(pattern, acc)])


def include_postings(inventory, transaction, include_accounts=None, exclude_accounts=None, filter=None):
    exclude_accounts = exclude_accounts if exclude_accounts else []
    filter = filter if filter is not None else lambda x: True

    for posting in transaction.postings:
        if (include_accounts is None or posting.account in include_accounts) \
                and posting.account not in exclude_accounts \
                and filter(posting):
            inventory.add_position(posting)


def calculate_balances(inventories):
    if len(inventories) == 0:
        return []
    result = []
    balance = Inventory()
    last_balance = Inventory()
    for inv in inventories:
        if inv != {}:
            balance.add_inventory(inv)
            result.append(copy.copy(balance))
            last_balance = balance
        else:
            result.append(Inventory())

    if result[-1] == {}:
        result[-1] = last_balance
    return result


def build_price_map_with_fallback_to_cost(entries):
    """
    Default price map does not contain purchase price from buying transaction. Beancount fails to calculate value
     unless there is price entry with same or earlier date. This function adds price entries from transaction
     if there isn't one for purchased commodity on purchase date or earlier.
    """
    buying_prices = {}
    prices_by_date = set()
    prices = set()

    for entry in entries:
        if isinstance(entry, Price):
            prices_by_date.add((entry.date, entry.currency, entry.amount.currency))
            prices.add((entry.currency, entry.amount.currency))

        if not isinstance(entry, Transaction):
            continue

        for p in entry.postings:
            if p.cost is not None and p.units is not None \
                    and (p.units.currency, p.cost.currency) not in prices:
                key = (entry.date, p.units.currency, p.cost.currency)
                buying_prices[key] = Price({}, entry.date, p.units.currency,
                                           Amount(p.units.number / p.cost.number, p.cost.currency))

    prices_to_add = []
    for key, price in buying_prices.items():
        if key not in prices_by_date:
            prices_to_add.append(price)

    return build_price_map(entries + prices_to_add)
