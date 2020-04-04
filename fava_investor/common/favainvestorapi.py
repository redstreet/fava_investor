from beancount.core import getters
class FavaInvestorAPI:
    def __init__(self, ledger):
        self.ledger = ledger

    def build_price_map(self):
        return self.ledger.price_map

    def get_commodity_map(self):
        return getters.get_commodity_map(self.ledger.entries)

    def realize(self):
        return self.ledger.root_account

    def query_func(self, sql):
        contents, rtypes, rrows = self.ledger.query_shell.execute_query(sql)
        return rtypes, rrows

    def get_operating_currency(self):
        return self.ledger.options["operating_currency"][0] #TBD: error check

    def get_account_open_close(self):
        return getters.get_account_open_close(self.ledger.entries)

