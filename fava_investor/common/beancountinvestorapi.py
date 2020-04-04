#!/usr/bin/env python3

from beancount import loader
from beancount.core import getters
from beancount.core import prices
from beancount.core import realization

class AccAPI:
    def __init__(self, beancount_file, options):
        self.entries, _, self.options_map = loader.load_file(beancount_file)
        self.options = options

    def build_price_map(self):
        return prices.build_price_map(self.entries)

    def get_commodity_map(self):
        return getters.get_commodity_map(self.entries)

    def realize(self):
        return realization.realize(self.entries)

    def query_func(self, sql):
        rtypes, rrows = query.run_query(self.entries, self.options_map, sql)
        return rtypes, rrows

    def get_operating_currency(self):
        return self.options['base_currency']

    def get_account_open_close(self):
        return getters.get_account_open_close(self.entries)
