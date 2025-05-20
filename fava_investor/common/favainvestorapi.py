from beancount.core import getters
from collections import namedtuple
from fava.core.conversion import cost_or_value as cost_or_value_without_context
from fava import __version__ as fava_version
from packaging import version
from fava.context import g
from fava.core.conversion import convert_position
from beancount.core import realization
from beancount.core import prices
from beanquery import query


class FavaInvestorAPI:
    def __init__(self):
        self.convert_position = convert_position

    def build_price_map(self):
        return g.ledger.prices

    def build_beancount_price_map(self):
        return prices.build_price_map(g.ledger.all_entries)

    def build_filtered_price_map(self, pcur, base_currency):
        """pcur and base_currency are currency strings"""
        return {(pcur, base_currency): g.filtered.prices(pcur, base_currency)}

    def end_date(self):
        return g.filtered.end_date

    def get_commodity_directives(self):
        return {entry.currency: entry for entry in g.filtered.ledger.all_entries_by_type.Commodity}

    def realize(self):
        return realization.realize(g.filtered.entries)

    def root_tree(self):
        return g.filtered.root_tree

    def query_func(self, sql):
        # Based on the fava version, determine if we need to add a new
        # positional argument to fava's execute_query()
        if version.parse(fava_version) >= version.parse("1.30"):
            rtypes, rrows = query.run_query(g.filtered.entries, g.ledger.options, sql)

            # Convert this into Beancount v2 format, so the rows are namedtuples
            field_names = [t.name for t in rtypes]
            Row = namedtuple("Row", field_names)
            rtypes = [(t.name, t.datatype) for t in rtypes]
            rrows = [Row(*row) for row in rrows]

        elif version.parse(fava_version) >= version.parse("1.22"):
            _, rtypes, rrows = g.ledger.query_shell.execute_query(g.filtered.entries, sql)
        else:
            _, rtypes, rrows = g.ledger.query_shell.execute_query(sql)
        return rtypes, rrows

    def get_operating_currencies(self):
        return g.ledger.options["operating_currency"]  # TODO: error check

    def get_operating_currencies_regex(self):
        currencies = self.get_operating_currencies()
        return '(' + '|'.join(currencies) + ')'

    def get_account_open_close(self):
        return getters.get_account_open_close(g.filtered.entries)

    def get_account_open(self):
        # TODO: below is probably fava only, and needs to be made beancount friendly
        return g.ledger.all_entries_by_type.Open

    def cost_or_value(self, node, date, include_children, *, operating_currency=None):
        nodes = node.balance
        if include_children:
            nodes = node.balance_children
        conversion = operating_currency or g.conversion
        return cost_or_value_without_context(nodes, conversion, g.ledger.prices, date)
