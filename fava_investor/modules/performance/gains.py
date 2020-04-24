from beancount.core import prices, convert
from beancount.core.data import Transaction, Posting
from beancount.core.inventory import Inventory
from fava.core.inventory import CounterInventory
from fava.core.tree import TreeNode

from fava_investor.modules.performance.common import Row, Accounts
from fava_investor.modules.performance.dividends import get_balance_split, sum_inventories
from fava_investor.modules.performance.returns import returns


class GainsCalculator:
    def __init__(self, accapi, accounts: Accounts):
        self.accapi = accapi
        self.accounts = accounts

    def get_unrealized_gains_per_account(self):
        tree = self.accapi.root_tree()

        price_map = prices.build_price_map(self.accapi.ledger.entries)

        result = {}
        for acc in self.accounts.value:
            node: TreeNode = tree.get(acc)
            value = node.balance.reduce(convert.get_value, price_map)
            a = CounterInventory()
            a.add_inventory(-node.balance.reduce(convert.get_cost))
            a.add_inventory(value)
            if a != {}:
                result[acc] = a
        return result

    def get_unrealized_gains_total(self):
        total = CounterInventory()
        per_account = self.get_unrealized_gains_per_account()
        for account, gain in per_account.items():
            total.add_inventory(gain)
        return Inventory({**total})

    def get_realized_gains_total(self):
        rows = get_balance_split(self.accounts, self.accapi)
        return sum_inventories(row[4] for row in rows)

    @staticmethod
    def _is_commodity_sale(entry: Transaction, value_accounts):
        for posting in entry.postings:
            posting: Posting
            if posting.account not in value_accounts:
                continue
            if posting.units.number < 0 and posting.cost is not None:
                return True
        return False
