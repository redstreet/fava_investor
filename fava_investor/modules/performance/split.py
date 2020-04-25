import copy
import re
from collections import namedtuple

from beancount.core import prices, convert
from beancount.core.data import Transaction
from beancount.core.inventory import Inventory

from fava_investor.modules.performance.returns import returns

SplitEntries = namedtuple("Balance",
                          "transactions contributions withdrawals dividends gains_realized gains_unrealized ")
Change = namedtuple("Change", "transaction change")


def split_journal(accapi, pattern_value, pattern_internal, pattern_internalized="$^"):
    accounts = accapi.accounts
    accounts_value = set([acc for acc in accounts if re.match(pattern_value, acc)])
    accounts_internal = set([acc for acc in accounts if re.match(pattern_internal, acc)])
    accounts_internalized = set([acc for acc in accounts if re.match(pattern_internalized, acc)])

    _, _, original_and_internalized = returns.internalize(accapi.ledger.entries, "Equity:Internalized", accounts_value, accounts_internal,
                                        accounts_internalized)
    price_map = prices.build_price_map(accapi.ledger.entries)

    balance = Inventory()
    result = SplitEntries([], [], [], [], [], [])

    is_external = lambda acc: acc not in accounts_value \
                                  and acc not in accounts_internal \
                                  and acc not in accounts_internalized
    previous_unrealized_gain = Inventory()
    for original_entry, internalized_entries in original_and_internalized:
        dividends = Inventory()
        contributions = Inventory()
        withdrawals = Inventory()
        gains_realized = Inventory()
        unrealized = Inventory()
        unrealized_diff = Inventory()
        for entry in internalized_entries:
            if not isinstance(entry, Transaction):
                continue

            value = any([p.account in accounts_value for p in entry.postings])
            internal = any([p.account in accounts_internal for p in entry.postings])
            internalized = any([p.account in accounts_internalized for p in entry.postings])
            external = any([is_external(p.account) for p in entry.postings])

            add_only_postings_from(balance, entry, accounts_value)

            if (value and internal) or (not value and internalized and external):
                add_only_postings_from(dividends, entry, accounts_internal)

            if value and external:
                add_only_postings_from(contributions, entry, accounts_value, lambda posting: posting.units.number > 0)
                add_only_postings_from(withdrawals, entry, accounts_value, lambda posting: posting.units.number < 0)

            if value and internal and is_commodity_sale(entry, accounts_value):
                add_only_postings_from(gains_realized, entry, accounts_internal)

        # gains
        current_value = balance.reduce(convert.get_value, price_map, original_entry.date)
        current_cost = balance.reduce(convert.get_cost)
        unrealized_gain = Inventory()
        unrealized_gain.add_inventory(current_value).add_inventory(-current_cost)
        gain_diff=Inventory()
        gain_diff.add_inventory(unrealized_gain).add_inventory(-previous_unrealized_gain)
        previous_unrealized_gain = unrealized_gain
        # rows.append((original_entry, contributions, withdrawals, -dividends, -gains_realized, unrealized_diff))
        result.transactions.append(original_entry)
        result.contributions.append(contributions)
        result.withdrawals.append(withdrawals)
        result.dividends.append(-dividends)
        result.gains_realized.append(-gains_realized)
        result.gains_unrealized.append(gain_diff)
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


def add_only_postings_from(inventory, transaction, accounts, lambda_filter=None):
    lambda_filter = lambda_filter if lambda_filter is not None else lambda x: True

    for posting in transaction.postings:
        if posting.account in accounts and lambda_filter(posting):
            inventory.add_position(posting)
