#!/usr/bin/env python3

from beancount import loader
from beancount.core import getters
from beancount.core import prices
from beancount.core import realization
from beancount.query import query
from beancount.core.data import Open
from beancount.core.data import Custom
import ast


class AccAPI:
    def __init__(self, beancount_file, options):
        self.entries, _, self.options_map = loader.load_file(beancount_file)
        self.options = options

    def end_date(self):
        return None  # Only used in fava (UI selection context)

    def build_price_map(self):
        return prices.build_price_map(self.entries)

    def build_filtered_price_map(self, pos, base_currency):
        """Ignore filtering since we are not in fava. Return all prices"""
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

    def get_custom_config(self, module_name):
        """Get fava config for the given plugin that can then be used on the command line"""
        _extension_entries = [e for e in self.entries
                              if isinstance(e, Custom) and e.type == 'fava-extension']
        config_meta = {entry.values[0].value:
                       (entry.values[1].value if (len(entry.values) == 2) else None)
                       for entry in _extension_entries}

        all_configs = {k: ast.literal_eval(v) for k, v in config_meta.items() if 'fava_investor' in k}

        # extract conig for just this module:
        module_config = [v[module_name] for k, v in all_configs.items() if module_name in v]
        if module_config:
            return module_config[0]
        return {}
