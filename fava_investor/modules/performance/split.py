import copy
import re
from collections import namedtuple

from beancount.core import convert
from beancount.core.amount import Amount
from beancount.core.data import Transaction, Price
from beancount.core.inventory import Inventory
from beancount.core.prices import build_price_map

Split = namedtuple("Split", "transactions values parts")
SplitEntries = namedtuple(
    "Balance",
    "contributions withdrawals dividends costs gains_realized gains_unrealized",
)
Change = namedtuple("Change", "transaction change")


def get_balance_split_history(
        accapi,
        pattern_value,
        income_pattern="^Income:",
        expenses_pattern="^Expenses:",
        pattern_internalized="^Income:Dividend",
):
    accounts = accapi.accounts
    accounts_value = set([acc for acc in accounts if re.match(pattern_value, acc)])
    accounts_internalized = set(
        [acc for acc in accounts if re.match(pattern_internalized, acc)]
    )
    accounts_expenses = set(
        [acc for acc in accounts if re.match(expenses_pattern, acc)]
    )
    accounts_income = set([acc for acc in accounts if re.match(income_pattern, acc)])
    accounts_internal = accounts_income | accounts_expenses

    if needs_dummy_transaction(accapi.ledger.entries):
        date = copy.copy(accapi.ledger.entries[-1].date)
        accapi.ledger.entries.append(
            Transaction(
                None, date, None, None, "UNREALIZED GAINS NEW BALANCE", [], [], []
            )
        )

    price_map = build_price_map_with_fallback_to_cost(accapi.ledger.entries)

    balance = Inventory()
    split_entries = SplitEntries([], [], [], [], [], [])
    split = Split([], [], split_entries)
    last_unrealized_gain = Inventory()

    is_external = (
        lambda acc: acc not in accounts_value
                    and acc not in accounts_internal
                    and acc not in accounts_internalized
    )
    for entry in accapi.ledger.entries:
        if not isinstance(entry, Transaction):
            continue

        dividends = Inventory()
        costs = Inventory()
        contributions = Inventory()
        withdrawals = Inventory()
        gains_realized = Inventory()

        value = any([p.account in accounts_value for p in entry.postings])
        internal = any([p.account in accounts_internal for p in entry.postings])
        income = any([p.account in accounts_income for p in entry.postings])
        expense = any([p.account in accounts_expenses for p in entry.postings])
        external = any([is_external(p.account) for p in entry.postings])

        balance += include_postings(entry, accounts_value)

        if value and external:
            value_change = include_postings_prefer_cost(entry, include_accounts=accounts_value | accounts_internal)
            for position in value_change.get_positions():
                if position.units.number > 0:
                    contributions.add_position(position)
                else:
                    withdrawals.add_position(position)

        if (value and internal and not is_commodity_sale(entry, accounts_value)) or (
                not value and income and external
        ):
            dividends += include_postings(
                entry,
                accounts_income,
                lambda_filter=lambda posting: posting.units.number < 0,
            )

        if value and expense:
            costs += include_postings(entry, accounts_expenses)

        if value and income and is_commodity_sale(entry, accounts_value):
            gains_realized += include_postings(entry, accounts_income)

        # unrealized gain
        current_value = balance.reduce(convert.get_value, price_map, entry.date)
        current_cost = balance.reduce(convert.get_cost)
        unrealized_gain = current_value + -current_cost
        unrealized_gain_change = unrealized_gain + -last_unrealized_gain
        last_unrealized_gain = unrealized_gain

        split_entries.contributions.append(contributions)
        split_entries.withdrawals.append(withdrawals)
        split_entries.dividends.append(-dividends)
        split_entries.costs.append(-costs)
        split_entries.gains_realized.append(-gains_realized)
        split_entries.gains_unrealized.append(unrealized_gain_change)

        current_value = balance.reduce(convert.get_value, price_map, entry.date)
        split.values.append(current_value)
        split.transactions.append(entry)

    return split


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
        sum += inv
    return sum


def get_matching_accounts(accounts, pattern):
    return set([acc for acc in accounts if re.match(pattern, acc)])


def include_postings_prefer_cost(
        transaction, include_accounts=None, exclude_accounts=None, lambda_filter=None
):
    exclude_accounts = exclude_accounts if exclude_accounts else []
    lambda_filter = lambda_filter if lambda_filter is not None else lambda x: True
    inventory = Inventory()

    for posting in transaction.postings:
        if (
                (include_accounts is None or posting.account in include_accounts)
                and posting.account not in exclude_accounts
                and lambda_filter(posting)
        ):
            if posting.cost is not None:
                number = posting.cost.number * posting.units.number
                inventory.add_amount(Amount(number, posting.cost.currency))
            else:
                inventory.add_position(posting)

    return inventory


def include_postings(
        transaction, include_accounts=None, exclude_accounts=None, lambda_filter=None
):
    exclude_accounts = exclude_accounts if exclude_accounts else []
    lambda_filter = lambda_filter if lambda_filter is not None else lambda x: True
    inventory = Inventory()

    for posting in transaction.postings:
        if (
                (include_accounts is None or posting.account in include_accounts)
                and posting.account not in exclude_accounts
                and lambda_filter(posting)
        ):
            inventory.add_position(posting)

    return inventory


def calculate_balances(inventories):
    if len(inventories) == 0:
        return []
    result = []
    balance = Inventory()
    for inv in inventories:
        balance += inv
        result.append(copy.copy(balance))
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
            if (
                    p.cost is not None
                    and p.units is not None
                    and (p.units.currency, p.cost.currency) not in prices
            ):
                key = (entry.date, p.units.currency, p.cost.currency)
                buying_prices[key] = Price(
                    {},
                    entry.date,
                    p.units.currency,
                    Amount(p.units.number / p.cost.number, p.cost.currency),
                )

    prices_to_add = []
    for key, price in buying_prices.items():
        if key not in prices_by_date:
            prices_to_add.append(price)

    return build_price_map(entries + prices_to_add)


def needs_dummy_transaction(entries):
    has_prices_after_last_transaction = False
    for entry in reversed(entries):
        if isinstance(entry, Price):
            has_prices_after_last_transaction = True
        if isinstance(entry, Transaction):
            return has_prices_after_last_transaction
