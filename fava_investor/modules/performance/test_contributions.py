from collections import namedtuple

from beancount.core.inventory import Inventory
from beancount.utils import test_utils
from freezegun import freeze_time

from .balances import filter_matching
from .report.returns import internalize, is_value_account_entry, is_external_flow_entry
from .test_balances import get_ledger
from ... import FavaInvestorAPI

CONFIG = {
    "accounts_patterns": ["^Assets:Account"],
    "accounts_internal_patterns": []
}
Accounts = namedtuple("Accounts", "value internal external")


def _get_accounts(accapi, config) -> Accounts:
    value = filter_matching(accapi.ledger.accounts, config.get('accounts_patterns', ['.*']))
    internal = filter_matching(accapi.ledger.accounts, config.get('accounts_internal_patterns', ['.*']))
    external = set(accapi.ledger.accounts).difference(value | internal)
    return Accounts(value, internal, external)


def _get_external_to_value_postings(accapi: FavaInvestorAPI, accounts: Accounts):
    entries, _ = internalize(accapi.ledger.entries, "Equity:Internalized", accounts.value, [])

    entries = [entry for entry in entries
               if is_value_account_entry(entry, accounts.value)
               and is_external_flow_entry(entry, accounts.value | accounts.internal)]

    result = []
    for entry in entries:
        for posting in entry.postings:
            if posting.account in accounts.value:
                result.append(posting)

    return result


def get_contributions(accapi, config):
    accounts = _get_accounts(accapi, config)
    result = Inventory()
    [result.add_position(p) for p in (_get_external_to_value_postings(accapi, accounts)) if p.units.number > 0]
    return result


def get_withdrawals(accapi, config):
    accounts = _get_accounts(accapi, config)
    result = Inventory()
    [result.add_position(p) for p in (_get_external_to_value_postings(accapi, accounts)) if p.units.number < 0]
    return -result


class TestContributions(test_utils.TestCase):
    @test_utils.docfile
    def test_contributions_to_subaccounts(self, filename: str):
        """
        2020-01-01 open Assets:Bank
        2020-01-01 open Assets:Account
        2020-01-01 open Assets:Account:Sub

        2020-01-01 * "contrib 1"
            Assets:Account  10 GBP
            Assets:Bank

        2020-01-01 * "contrib 2"
            Assets:Account:Sub  10 GBP
            Assets:Bank
        """
        ledger = get_ledger(filename)
        contributions = get_contributions(ledger, CONFIG)

        self.assertEquals(Inventory.from_string("20 GBP"), contributions)

    @test_utils.docfile
    def test_other_transfers_are_ignored(self, filename: str):
        """
        2020-01-01 open Assets:Bank
        2020-01-01 open Assets:Bank2
        2020-01-01 open Assets:Account
        2020-01-01 open Assets:Account:Sub

        2020-01-01 * "irrelevant"
            Assets:Account  10 GBP
            Assets:Account:Sub

        2020-01-01 * "irrelevant"
            Assets:Bank  20 GBP
            Assets:Bank2
        """
        ledger = get_ledger(filename)
        contributions = get_contributions(ledger, CONFIG)

        self.assertEquals(Inventory.from_string(""), contributions)

    @test_utils.docfile
    def test_withdrawals_are_separate(self, filename: str):
        """
        2020-01-01 open Assets:Bank
        2020-01-01 open Assets:Account

        2020-01-01 * "contrib"
            Assets:Account  2 GBP
            Assets:Bank

        2020-01-01 * "withdrawal"
            Assets:Account  -1 GBP
            Assets:Bank
        """
        ledger = get_ledger(filename)
        contributions = get_contributions(ledger, CONFIG)
        withdrawals = get_withdrawals(ledger, CONFIG)

        self.assertEquals(Inventory.from_string("2 GBP"), contributions)
        self.assertEquals(Inventory.from_string("1 GBP"), withdrawals)
