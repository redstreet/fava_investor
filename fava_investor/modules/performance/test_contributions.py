from collections import namedtuple

from beancount.core.amount import A
from beancount.core.data import Transaction
from beancount.core.inventory import Inventory
from beancount.utils import test_utils

from .contributions import ContributionsCalculator, _get_accounts
from .test_balances import get_ledger

CONFIG = {
    "accounts_patterns": ["^Assets:Account"],
    "accounts_internal_patterns": []
}


def get_sut(filename, config) -> ContributionsCalculator:
    accapi = get_ledger(filename)
    return ContributionsCalculator(accapi, _get_accounts(accapi, config))


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
        sut = get_sut(filename, CONFIG)
        contributions = sut.get_contributions_total()

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
        sut = get_sut(filename, CONFIG)
        contributions = sut.get_contributions_total()

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
        sut = get_sut(filename, CONFIG)
        contributions = sut.get_contributions_total()
        withdrawals = sut.get_withdrawals_total()

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
        sut = get_sut(filename, CONFIG)
        ledger = get_ledger(filename)
        result = sut.get_withdrawals_entries()

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
        sut = get_sut(filename, CONFIG)
        result = sut.get_withdrawals_entries()

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
        sut = get_sut(filename, CONFIG)
        result = sut.get_contributions_entries()

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
        sut = get_sut(filename, CONFIG)
        result = sut.get_contributions_entries()

        self.assertEqual(Inventory.from_string("5 GBP"), result[0].inventory)
