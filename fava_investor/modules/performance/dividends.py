from collections import namedtuple

from beancount.core import prices, convert
from beancount.core.data import Transaction
from beancount.core.inventory import Inventory

from fava_investor.modules.performance.common import Accounts
from fava_investor.modules.performance.returns import returns

Row = namedtuple("Row", "transaction contr div")


class DividendsCalculator:
    def __init__(self, accapi, accounts: Accounts):
        self.accapi = accapi
        self.accounts = accounts

    def get_dividends_total(self):
        rows = get_balance_split(self.accounts, self.accapi)
        return rows[-1][3]


def add_only_postings_from(inventory, transaction, accounts, filter=None):
    for posting in transaction.postings:
        if posting.account in accounts and (filter is None or filter(posting)):
            inventory.add_position(posting)


def get_balance_split(accounts, accapi):
    is_external = lambda account: account not in accounts.value \
                                  and account not in accounts.internal \
                                  and account not in accounts.internalized

    _, _, old_new = returns.internalize(
        accapi.ledger.entries, "Equity:Internalized", accounts.value, accounts.internal, accounts.internalized
    )
    price_map = prices.build_price_map(accapi.ledger.entries)

    rows = []
    balance = Inventory()
    for original_entry, internalized_entries in old_new:
        dividends = Inventory()
        contributions = Inventory()
        withdrawals = Inventory()
        gains_realized = Inventory()
        unrealized = Inventory()
        unrealized_diff = Inventory()
        for entry in internalized_entries:
            if not isinstance(entry, Transaction):
                continue

            value = any([p.account in accounts.value for p in entry.postings])
            internal = any([p.account in accounts.internal for p in entry.postings])
            internalized = any([p.account in accounts.internalized for p in entry.postings])
            external = any([is_external(p.account) for p in entry.postings])

            add_only_postings_from(balance, entry, accounts.value)

            if (value and internal) or (not value and internalized and external):
                add_only_postings_from(dividends, entry, accounts.internal, None)

            if value and external:
                add_only_postings_from(contributions, entry, accounts.value, lambda posting: posting.units.number > 0)
                add_only_postings_from(withdrawals, entry, accounts.value, lambda posting: posting.units.number < 0)

            if value and internal and is_commodity_sale(entry, accounts.value):
                add_only_postings_from(gains_realized, entry, accounts.internal)

            # gains
            current_value = balance.reduce(convert.get_value, price_map, entry.date)
            current_cost = balance.reduce(convert.get_cost)
            new_unrealized = current_value.add_inventory(-current_cost)
            if new_unrealized != unrealized:
                unrealized_diff = unrealized_diff.add_inventory(
                    Inventory({**new_unrealized.add_inventory(-unrealized)})
                )

        rows.append((original_entry, contributions, withdrawals, -dividends, -gains_realized, unrealized_diff))
    return rows


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
