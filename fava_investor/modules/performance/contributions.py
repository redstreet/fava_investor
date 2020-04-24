import copy
from typing import List

from beancount.core.inventory import Inventory

from fava_investor.modules.performance import dividends
from fava_investor.modules.performance.common import Row, Accounts
from fava_investor.modules.performance.dividends import sum_inventories
from fava_investor.modules.performance.returns import returns


class ContributionsCalculator:
    def __init__(self, accapi, accounts: Accounts):
        self.accapi = accapi
        self.accounts = accounts

    def get_contributions_total(self) -> Inventory:
        rows = dividends.get_balance_split(self.accounts, self.accapi)
        return sum_inventories([row[1] for row in rows])

    def get_contributions_entries(self) -> List[Row]:
        return [Row(row[0], row[1]) for row in dividends.get_balance_split(self.accounts, self.accapi)]

    def get_withdrawals_total(self) -> Inventory:
        rows = dividends.get_balance_split(self.accounts, self.accapi)
        return sum_inventories([row[2] for row in rows])

    def get_withdrawals_entries(self) -> List[Row]:
        return [Row(row[0], row[2]) for row in dividends.get_balance_split(self.accounts, self.accapi)]


    def _get_external_x_value_postings(self):
        entries, _, old_new = returns.internalize(
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
