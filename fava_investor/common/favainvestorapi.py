from beancount.core import getters
from fava.template_filters import cost_or_value
from fava import __version__ as fava_version


class FavaInvestorAPI:
    def __init__(self, ledger, begin=None, end=None):
        # TODO: are begin/end needed?
        self.ledger = ledger
        self.begin = begin
        self.end = end
        self.entries = self.ledger.root_tree

    def build_price_map(self):
        return self.ledger.price_map

    def get_commodity_directives(self):
        return getters.get_commodity_directives(self.ledger.entries)

    def realize(self):
        return self.ledger.root_account

    def root_tree(self):
        return self.ledger.root_tree

    def query_func(self, sql):
        # Based on the fava version, determine if we need to add a new
        # positional argument to fava's execute_query()
        split_version = fava_version.split('.')
        if len(split_version) != 2:
            split_version = split_version[:2]
        major, minor = split_version
        new_execute_query = int(major) > 1 or (int(major) == 1 and int(minor) > 21)

        if new_execute_query:
            _, rtypes, rrows = self.ledger.query_shell.execute_query(self.ledger.all_entries, sql)
        else:
            _, rtypes, rrows = self.ledger.query_shell.execute_query(sql)
        return rtypes, rrows

    def get_operating_currencies(self):
        return self.ledger.options["operating_currency"]  # TODO: error check

    def get_operating_currencies_regex(self):
        currencies = self.get_operating_currencies()
        return '(' + '|'.join(currencies) + ')'

    def get_account_open_close(self):
        return getters.get_account_open_close(self.ledger.entries)

    def get_account_open(self):
        # TODO: below is probably fava only, and needs to be made beancount friendly
        return self.ledger.all_entries_by_type.Open

    def cost_or_value(self, node, date, include_children):
        if include_children:
            return cost_or_value(node.balance_children, date)
        return cost_or_value(node.balance, date)
