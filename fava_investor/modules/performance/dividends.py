import copy
from typing import List

from beancount.core.data import Transaction
from beancount.core.inventory import Inventory

from fava_investor.modules.performance.common import Row, Accounts
from fava_investor.modules.performance.returns import returns


class DividendsCalculator:
    def __init__(self, accapi, accounts: Accounts):
        self.accapi = accapi
        self.accounts = accounts

    def get_dividends_total(self) -> Inventory:
        entries = self.get_dividends_entries()
        if not entries:
            return Inventory()
        return -entries[len(entries) - 1].balance

    def get_dividends_entries(self) -> List[Row]:
        tx_tuples = self._get_internal_x_value_postings()
        return self._filter_postings(tx_tuples)

    @staticmethod
    def _filter_postings(tx_tuples) -> List[Row]:
        result = []
        balance = Inventory()
        for entry, value in tx_tuples:
            inventory = Inventory()
            for posting in value:
                inventory.add_position(posting)
                balance.add_inventory(inventory)

            if inventory != {}:
                result.append(Row(entry, inventory, copy.copy(balance)))
        return result

    def _get_internal_x_value_postings(self):
        entries, _ = returns.internalize(
            self.accapi.ledger.entries, "Equity:Internalized", self.accounts.value, []
        )

        for entry in entries:
            if not isinstance(entry, Transaction):
                continue
            pacc = set([p.account for p in entry.postings])
            accounts = self.accounts

            value = pacc & accounts.value
            internal = pacc & accounts.internal
            internalized = pacc & accounts.internalized
            external = pacc & accounts.external
            if (value and internal) or (not value and internalized and external):
                value = []
                for posting in entry.postings:
                    if posting.account in self.accounts.internal:
                        value.append(posting)
                yield entry, value

