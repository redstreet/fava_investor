#!/usr/bin/env python3

from beancount import loader
from beancount.core import getters
from beancount.core import prices
from beancount.core import realization
from beancount.query import query
from beancount.core.data import Open
from datetime import datetime


class AccAPI:
    def __init__(self, beancount_file, options):
        self.entries, _, self.options_map = loader.load_file(beancount_file)
        self.options = options
        self.begin = self.end = None  # Only used in fava

    def get_end_date(self):
        """Note that Fava provides a self.ledger that takes end_date into account (i.e., the ledger ends on
        end_date), while this beancount api does not do so. Be careful when using get_end_date()"""
        return self.options.get('end_date', datetime.today().date())

    def build_price_map(self):
        return prices.build_price_map(self.entries)

    def get_commodity_directives(self):
        return getters.get_commodity_directives(self.entries)

    def realize(self):
        return realization.realize(self.entries)

    def root_tree(self):
        from fava.core import Tree
        return Tree(self.entries)

        # rrr = realization.realize(self.entries)
        # import pdb; pdb.set_trace()
        # return realization.realize(self.entries)

    def query_func(self, sql):
        rtypes, rrows = query.run_query(self.entries, self.options_map, sql)
        return rtypes, rrows

    def get_operating_currencies(self):
        return self.options_map['operating_currency']

    def get_operating_currencies_regex(self):
        currencies = self.get_operating_currencies()
        return '(' + '|'.join(currencies) + ')'

    def get_account_open_close(self):
        return getters.get_account_open_close(self.entries)

    def get_account_open(self):
        oc = getters.get_account_open_close(self.entries)
        opens = [e for e in oc if isinstance(e, Open)]
        return opens

    # def cost_or_value(self, node, date, include_children):
    #     invent inventory.reduce(get_market_value, g.ledger.price_map, date)
    #     if include_children:
    #         return cost_or_value(node.balance_children, date)
    #     return cost_or_value(node.balance, date)
