from collections import namedtuple

from beancount.core.inventory import Inventory

from fava_investor.modules.performance.balances import filter_matching
from fava_investor.modules.performance.report.returns import internalize, is_value_account_entry, is_external_flow_entry

Accounts = namedtuple("Accounts", "value internal external")
Contribution = namedtuple("Withdrawal", "transaction postings inventory")


class ContributionsCalculator:
    def __init__(self, accapi, accounts: Accounts):
        self.accapi = accapi
        self.accounts = accounts

    def get_contributions_total(self):
        result = Inventory()
        for tx, postings, inventory in self.get_contributions_entries():
            result.add_inventory(inventory)
        return result

    def get_contributions_entries(self):
        tx_tuples = self._get_external_x_value_postings()
        return self._filter_postings(tx_tuples, lambda posting: posting.units.number > 0)

    def get_withdrawals_total(self):
        result = Inventory()
        for tx, postings, inventory in self.get_withdrawals_entries():
            result.add_inventory(inventory)
        return result

    def get_withdrawals_entries(self):
        tx_tuples = self._get_external_x_value_postings()
        return self._filter_postings(tx_tuples, lambda posting: posting.units.number < 0)

    @staticmethod
    def _filter_postings(tx_tuples, match_lambda):
        result = []
        for entry, value, ext in tx_tuples:
            matched_postings = []
            for posting in value:
                if match_lambda(posting):
                    matched_postings.append(posting)

            if matched_postings:
                result.append(Contribution(entry, matched_postings, Inventory(matched_postings)))
        return result

    def _get_external_x_value_postings(self):
        entries, _ = internalize(self.accapi.ledger.entries, "Equity:Internalized", self.accounts.value, [])

        for entry in entries:
            if not is_value_account_entry(entry, self.accounts.value) \
                   or not is_external_flow_entry(entry, self.accounts.value | self.accounts.internal):
                continue
            ext = []
            value = []
            for posting in entry.postings:
                if posting.account in self.accounts.value:
                    value.append(posting)
                else:
                    ext.append(posting)
            yield entry, value, ext


def _get_accounts(accapi, config) -> Accounts:
    value = filter_matching(accapi.ledger.accounts, config.get('accounts_patterns', ['.*']))
    internal = filter_matching(accapi.ledger.accounts, config.get('accounts_internal_patterns', ['.*']))
    external = set(accapi.ledger.accounts).difference(value | internal)
    return Accounts(value, internal, external)