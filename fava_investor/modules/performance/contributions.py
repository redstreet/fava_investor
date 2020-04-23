import copy
from typing import List

from beancount.core.inventory import Inventory

from fava_investor.modules.performance.common import Row, Accounts
from fava_investor.modules.performance.returns import returns


class ContributionsCalculator:
    def __init__(self, accapi, accounts: Accounts):
        self.accapi = accapi
        self.accounts = accounts

    def get_contributions_total(self) -> Inventory:
        entries = self.get_contributions_entries()
        if not entries:
            return Inventory()
        return entries[len(entries) - 1].balance

    def get_contributions_entries(self) -> List[Row]:
        tx_tuples = self._get_external_x_value_postings()
        return self._filter_postings(
            tx_tuples, lambda posting: posting.units.number > 0
        )

    def get_withdrawals_total(self) -> Inventory:
        entries = self.get_withdrawals_entries()
        if not entries:
            return Inventory()
        return entries[len(entries) - 1].balance

    def get_withdrawals_entries(self) -> List[Row]:
        tx_tuples = self._get_external_x_value_postings()
        return self._filter_postings(
            tx_tuples, lambda posting: posting.units.number < 0
        )

    @staticmethod
    def _filter_postings(tx_tuples, match_lambda) -> List[Row]:
        result = []
        balance = Inventory()
        for entry, value, ext in tx_tuples:
            inventory = Inventory()
            for posting in value:
                if match_lambda(posting):
                    inventory.add_position(posting)
                    balance.add_inventory(inventory)

            if inventory != {}:
                result.append(Row(entry, inventory, copy.copy(balance)))
        return result

    def _get_external_x_value_postings(self):
        entries, _ = returns.internalize(
            self.accapi.ledger.entries, "Equity:Internalized", self.accounts.value, []
        )

        for entry in entries:
            if not returns.is_value_account_entry(
                    entry, self.accounts.value
            ) or not returns.is_external_flow_entry(
                entry, self.accounts.value | self.accounts.internal
            ):
                continue
            ext = []
            value = []
            for posting in entry.postings:
                if posting.account in self.accounts.value:
                    value.append(posting)
                else:
                    ext.append(posting)
            yield entry, value, ext