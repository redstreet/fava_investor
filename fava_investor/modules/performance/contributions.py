import copy
from collections import namedtuple
from typing import List

from beancount.core.inventory import Inventory

from .balances import filter_matching
from .returns import returns

Accounts = namedtuple("Accounts", "value internal external")
Contribution = namedtuple("Withdrawal", "transaction change balance")


class ContributionsCalculator:
    def __init__(self, accapi, accounts: Accounts):
        self.accapi = accapi
        self.accounts = accounts

    def get_contributions_total(self) -> Inventory:
        entries = self.get_contributions_entries()
        if not entries:
            return Inventory()
        return entries[len(entries)-1].balance

    def get_contributions_entries(self) -> List[Contribution]:
        tx_tuples = self._get_external_x_value_postings()
        return self._filter_postings(tx_tuples, lambda posting: posting.units.number > 0)

    def get_withdrawals_total(self) -> Inventory:
        entries = self.get_withdrawals_entries()
        if not entries:
            return Inventory()
        return entries[len(entries)-1].balance

    def get_withdrawals_entries(self) -> List[Contribution]:
        tx_tuples = self._get_external_x_value_postings()
        return self._filter_postings(tx_tuples, lambda posting: posting.units.number < 0)

    @staticmethod
    def _filter_postings(tx_tuples, match_lambda) -> List[Contribution]:
        result = []
        balance = Inventory()
        for entry, value, ext in tx_tuples:
            inventory = Inventory()
            for posting in value:
                if match_lambda(posting):
                    inventory.add_position(posting)
                    balance.add_inventory(inventory)

            if inventory != {}:
                result.append(Contribution(entry, inventory, copy.copy(balance)))
        return result

    def _get_external_x_value_postings(self):
        entries, _ = returns.internalize(self.accapi.ledger.entries, "Equity:Internalized", self.accounts.value, [])

        for entry in entries:
            if not returns.is_value_account_entry(entry, self.accounts.value) \
                   or not returns.is_external_flow_entry(entry, self.accounts.value | self.accounts.internal):
                continue
            ext = []
            value = []
            for posting in entry.postings:
                if posting.account in self.accounts.value:
                    value.append(posting)
                else:
                    ext.append(posting)
            yield entry, value, ext


def get_accounts_from_config(accapi, config) -> Accounts:
    value = filter_matching(accapi.ledger.accounts, config.get('accounts_patterns', ['.*']))
    internal = filter_matching(accapi.ledger.accounts, config.get('accounts_internal_patterns', ['.*']))
    external = set(accapi.ledger.accounts).difference(value | internal)
    return Accounts(value, internal, external)