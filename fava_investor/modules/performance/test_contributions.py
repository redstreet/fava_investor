from beancount.core.data import Transaction
from beancount.core.inventory import Inventory
from beancount.utils import test_utils

from .contributions import ContributionsCalculator
from .common import get_accounts_from_config
from .test_balances import get_ledger

CONFIG = {"accounts_patterns": ["^Assets:Account"], "accounts_internal_patterns": []}


def get_sut(filename, config) -> ContributionsCalculator:
    accapi = get_ledger(filename)
    return ContributionsCalculator(accapi, get_accounts_from_config(accapi, config))


class TestContributions(test_utils.TestCase):
    @test_utils.docfile
    def test_no_contributions(self, filename: str):
        """
        2020-01-01 open Assets:Bank
        2020-01-01 open Assets:Account
        2020-01-01 open Assets:Account:Sub
        """
        sut = get_sut(filename, CONFIG)
        contributions = sut.get_contributions_total()
        self.assertEquals(Inventory(), contributions)

    @test_utils.docfile
    def test_no_withdrawals(self, filename: str):
        """
        2020-01-01 open Assets:Bank
        2020-01-01 open Assets:Account
        2020-01-01 open Assets:Account:Sub
        """
        sut = get_sut(filename, CONFIG)
        withdrawals = sut.get_withdrawals_total()
        self.assertEquals(Inventory(), withdrawals)

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

        2020-01-02 * "withdrawal 1"
            Assets:Account:A  -1 GBP
            Assets:Account:B  -2 GBP
            Assets:Bank

        2020-01-02 * "withdrawal 2"
            Assets:Account:A  -3 GBP
            Assets:Bank
        """
        sut = get_sut(filename, CONFIG)
        result = sut.get_withdrawals_entries()

        self.assertEquals(2, len(result))

        self.assertEquals(Inventory.from_string("-3 GBP"), result[0].change)
        self.assertEquals(Inventory.from_string("-3 GBP"), result[1].change)

        self.assertIsInstance(result[0].transaction, Transaction)
        self.assertEquals("withdrawal 1", result[0].transaction.narration)
        self.assertIsInstance(result[1].transaction, Transaction)
        self.assertEquals("withdrawal 2", result[1].transaction.narration)

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

        self.assertEqual(Inventory.from_string("-5 GBP"), result[0].change)

    @test_utils.docfile
    def test_list_contribution_entries(self, filename: str):
        """
        2020-01-01 open Assets:Bank
        2020-01-01 open Assets:Account:A
        2020-01-01 open Assets:Account:B

        2020-01-01 * "withdrawal"
            Assets:Account:A  -2 GBP
            Assets:Bank

        2020-01-02 * "contribution 1"
            Assets:Account:A  1 GBP
            Assets:Account:B  2 GBP
            Assets:Bank

        2020-01-03 * "contribution 2"
            Assets:Account:A  3 GBP
            Assets:Bank
        """
        sut = get_sut(filename, CONFIG)
        result = sut.get_contributions_entries()

        self.assertEquals(2, len(result))

        self.assertEquals(Inventory.from_string("3 GBP"), result[0].change)
        self.assertEquals(Inventory.from_string("3 GBP"), result[1].change)

        self.assertIsInstance(result[0].transaction, Transaction)
        self.assertEquals("contribution 1", result[0].transaction.narration)
        self.assertIsInstance(result[1].transaction, Transaction)
        self.assertEquals("contribution 2", result[1].transaction.narration)

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

        self.assertEqual(Inventory.from_string("5 GBP"), result[0].change)

    @test_utils.docfile
    def test_filtered_out_value_accounts_are_treated_as_external(self, filename: str):
        """
        2020-01-01 open Assets:Bank
        2020-01-01 open Assets:Account:A
        2020-01-01 open Assets:Account:B

        2020-01-02 * "contribution"
            Assets:Account:B  5 GBP
            Assets:Bank

        2020-01-02 * "value accounts transfer"
            Assets:Account:A  2 GBP
            Assets:Account:B
        """
        self.skipTest(
            "Not implemented. It will be needed to calculate returns for selected account as well."
        )

        sut = get_sut(filename, CONFIG)
        result = sut.get_contributions_total()

        self.assertEqual(Inventory.from_string("2 GBP"), result)
