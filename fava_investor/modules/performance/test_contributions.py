from beancount.core.data import Transaction
from beancount.core.inventory import Inventory
from beancount.utils import test_utils

from .test_split import SplitTestCase, i, get_split, get_split_with_meta


class TestContributions(SplitTestCase):
    @test_utils.docfile
    def test_no_contributions(self, filename: str):
        """
        2020-01-01 open Assets:Bank
        2020-01-01 open Assets:Account
        2020-01-01 open Assets:Account:Sub
        """
        self.assertSumOfSplitsEqual(filename, "0")

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
        self.assertSumOfSplitsEqual(filename, "20 GBP")

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
        self.assertSumOfSplitsEqual(filename, "0")

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
        split = get_split_with_meta(filename)
        self.assertEqual(Inventory.from_string("3 GBP"), split.parts.contributions[1])
        self.assertEqual(Inventory.from_string("3 GBP"), split.parts.contributions[2])

        self.assertIsInstance(split.transactions[1], Transaction)
        self.assertEqual("contribution 1", split.transactions[1].narration)
        self.assertIsInstance(split.transactions[2], Transaction)
        self.assertEqual("contribution 2", split.transactions[2].narration)

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
        self.skipTest("value account filtering not implemented")

        split = get_split(filename)
        self.assertInventoriesSum("2 GBP", split.contributions)

    @test_utils.docfile
    def test_asset_on_loan_with_contributed_part(self, filename: str):
        """
        2020-01-01 open Assets:Bank
        2020-01-01 open Assets:Account:Loan
        2020-01-01 open Assets:Account:Asset

        2020-01-02 price AA 15 GBP

        2020-01-02 * "transfer"
            Assets:Account:Loan  -6 GBP
            Assets:Account:Asset  1 AA {11 GBP}
            Assets:Bank  -5 GBP

        """
        split = get_split(filename)
        self.assertInventoriesSum("5 GBP", split.contributions)
