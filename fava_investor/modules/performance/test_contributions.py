import datetime
from collections import namedtuple

from beancount.core.amount import A
from beancount.core.data import Transaction
from beancount.core.inventory import Inventory
from beancount.utils import test_utils

from .balances import filter_matching
from .report.returns import internalize, is_value_account_entry, is_external_flow_entry
from .test_balances import get_ledger
from ... import FavaInvestorAPI

CONFIG = {
    "accounts_patterns": ["^Assets:Account"],
    "accounts_internal_patterns": []
}
Accounts = namedtuple("Accounts", "value internal external")
Withdrawal = namedtuple("Withdrawal", "transaction postings inventory")


def _get_accounts(accapi, config) -> Accounts:
    value = filter_matching(accapi.ledger.accounts, config.get('accounts_patterns', ['.*']))
    internal = filter_matching(accapi.ledger.accounts, config.get('accounts_internal_patterns', ['.*']))
    external = set(accapi.ledger.accounts).difference(value | internal)
    return Accounts(value, internal, external)


def _get_external_x_value_postings(accapi: FavaInvestorAPI, accounts: Accounts):
    entries, _ = internalize(accapi.ledger.entries, "Equity:Internalized", accounts.value, [])

    entries = [entry for entry in entries
               if is_value_account_entry(entry, accounts.value)
               and is_external_flow_entry(entry, accounts.value | accounts.internal)]

    for entry in entries:
        ext = []
        value = []
        for posting in entry.postings:
            if posting.account in accounts.value:
                value.append(posting)
            else:
                ext.append(posting)
        yield entry, value, ext


def get_contributions_total(accapi, config):
    result = Inventory()
    for tx, postings, inventory in get_contributions_entries(accapi, config):
        result.add_inventory(inventory)
    return result


def get_withdrawals_total(accapi, config):
    result = Inventory()
    for tx, postings, inventory in get_withdrawals_entries(accapi, config):
        result.add_inventory(inventory)
    return result


def get_withdrawals_entries(accapi, config):
    accounts = _get_accounts(accapi, config)
    tx_tuples = _get_external_x_value_postings(accapi, accounts)
    return _filter_postings(tx_tuples, lambda posting: posting.units.number < 0)


def _filter_postings(tx_tuples, match_lambda):
    result = []
    for entry, value, ext in tx_tuples:
        matched_postings = []
        for posting in value:
            if match_lambda(posting):
                matched_postings.append(posting)

        if matched_postings:
            result.append(Withdrawal(entry, matched_postings, Inventory(matched_postings)))
    return result


def get_contributions_entries(accapi, config):
    accounts = _get_accounts(accapi, config)
    tx_tuples = _get_external_x_value_postings(accapi, accounts)
    return _filter_postings(tx_tuples, lambda posting: posting.units.number > 0)


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
        contributions = get_contributions_total(ledger, CONFIG)

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
        contributions = get_contributions_total(ledger, CONFIG)

        self.assertEquals(Inventory.from_string(""), contributions)

    @test_utils.docfile
    def test_withdrawals_and_contriutions_are_separate(self, filename: str):
        """
        2020-01-01 open Assets:Bank
        2020-01-01 open Assets:Account

        2020-01-01 * "contrib"
            Assets:Account  1 GBP
            Assets:Bank

        2020-01-01 * "withdrawal"
            Assets:Account  -1 GBP
            Assets:Bank

        2020-01-01 * "both"
            Assets:Account  -2 GBP
            Assets:Account  3 GBP
            Assets:Bank
        """
        ledger = get_ledger(filename)
        contributions = get_contributions_total(ledger, CONFIG)
        withdrawals = get_withdrawals_total(ledger, CONFIG)

        self.assertEquals(Inventory.from_string("4 GBP"), contributions)
        self.assertEquals(Inventory.from_string("-3 GBP"), withdrawals)

    @test_utils.docfile
    def test_list_withdrawals_entries(self, filename: str):
        """
        2020-01-01 open Assets:Bank
        2020-01-01 open Assets:Account:A
        2020-01-01 open Assets:Account:B

        2020-01-01 * "contrib"
            Assets:Account:A  2 GBP
            Assets:Bank

        2020-01-02 * "withdrawal"
            Assets:Account:A  -1 GBP
            Assets:Account:B  -2 GBP
            Assets:Bank
        """
        ledger = get_ledger(filename)
        result = get_withdrawals_entries(ledger, CONFIG)

        self.assertEquals(1, len(result))

        withdrawal = result[0]
        self.assertEquals(2, len(withdrawal.postings))

        self.assertEquals(A("-1 GBP"), withdrawal.postings[0].units)
        self.assertEquals(A("-2 GBP"), withdrawal.postings[1].units)
        self.assertEquals('Assets:Account:A', withdrawal.postings[0].account)
        self.assertEquals('Assets:Account:B', withdrawal.postings[1].account)

        self.assertIsInstance(withdrawal.transaction, Transaction)
        self.assertEquals("withdrawal", withdrawal.transaction.narration)

    @test_utils.docfile
    def test_only_negative_postings_are_considered_withdrawals(self, filename: str):
        """
        2020-01-01 open Assets:Bank
        2020-01-01 open Assets:Account:A
        2020-01-01 open Assets:Account:B

        2020-01-02 * "withdrawal"
            Assets:Account:A  -1 GBP
            Assets:Account:A  2 GBP
            Assets:Account:B  -4 GBP
            Assets:Bank
        """
        ledger = get_ledger(filename)
        result = get_withdrawals_entries(ledger, CONFIG)

        self.assertEqual(Inventory.from_string("-5 GBP"), result[0].inventory)

    @test_utils.docfile
    def test_list_contribution_entries(self, filename: str):
        """
        2020-01-01 open Assets:Bank
        2020-01-01 open Assets:Account:A
        2020-01-01 open Assets:Account:B

        2020-01-01 * "withdrawal"
            Assets:Account:A  -2 GBP
            Assets:Bank

        2020-01-02 * "contribution"
            Assets:Account:A  1 GBP
            Assets:Account:B  2 GBP
            Assets:Bank
        """
        ledger = get_ledger(filename)
        result = get_contributions_entries(ledger, CONFIG)

        self.assertEquals(1, len(result))

        withdrawal = result[0]
        self.assertEquals(2, len(withdrawal.postings))

        self.assertEquals(A("1 GBP"), withdrawal.postings[0].units)
        self.assertEquals(A("2 GBP"), withdrawal.postings[1].units)
        self.assertEquals('Assets:Account:A', withdrawal.postings[0].account)
        self.assertEquals('Assets:Account:B', withdrawal.postings[1].account)

        self.assertIsInstance(withdrawal.transaction, Transaction)
        self.assertEquals("contribution", withdrawal.transaction.narration)

    @test_utils.docfile
    def test_only_positive_postings_are_considered_contributions(self, filename: str):
        """
        2020-01-01 open Assets:Bank
        2020-01-01 open Assets:Account:A
        2020-01-01 open Assets:Account:B

        2020-01-02 * "contribution"
            Assets:Account:A  1 GBP
            Assets:Account:A  -2 GBP
            Assets:Account:B  4 GBP
            Assets:Bank
        """
        ledger = get_ledger(filename)
        result = get_contributions_entries(ledger, CONFIG)

        self.assertEqual(Inventory.from_string("5 GBP"), result[0].inventory)
