from fava_investor.modules.performance.common import Accounts
from fava_investor.modules.performance.dividends import get_balance_split, sum_inventories


class GainsCalculator:
    def __init__(self, accapi, accounts: Accounts):
        self.accapi = accapi
        self.accounts = accounts

    def get_unrealized_gains_per_account(self):
        raise NotImplementedError('nooo')

    def get_unrealized_gains_total(self):
        rows = get_balance_split(self.accounts, self.accapi)
        return rows[-1][5]

    def get_realized_gains_total(self):
        rows = get_balance_split(self.accounts, self.accapi)
        return sum_inventories(row[4] for row in rows)
