from beancount.core.data import Transaction
from beancount.core.inventory import Inventory
from beancount.utils import test_utils

from .split import sum_inventories
from .test_split import SplitTestCase, i, get_split, get_split_with_meta


class TestWithdrawals(SplitTestCase):
    @test_utils.docfile
    def test_asset_sold_loan_returned_and_rest_withdrawn(self, filename: str):
        """
        2020-01-01 open Assets:Bank
        2020-01-01 open Assets:Account:Loan
        2020-01-01 open Assets:Account:Asset

        2020-01-02 * "transfer"
            Assets:Account:Loan  6 GBP
            Assets:Account:Asset  -1 AA {11 GBP}
            Assets:Bank  5 GBP
        """
        split = get_split(filename)

        self.assertInventoriesSum("-5 GBP", split.withdrawals)

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
        split = get_split_with_meta(filename)

        self.assertEqual({}, split.parts.withdrawals[0])
        self.assertEqual(i("-3 GBP"), split.parts.withdrawals[1])
        self.assertEqual(i("-3 GBP"), split.parts.withdrawals[2])

        self.assertIsInstance(split.transactions[0], Transaction)
        self.assertIsInstance(split.transactions[1], Transaction)
        self.assertIsInstance(split.transactions[2], Transaction)
        self.assertEqual("contrib", split.transactions[0].narration)
        self.assertEqual("withdrawal 1", split.transactions[1].narration)
        self.assertEqual("withdrawal 2", split.transactions[2].narration)

    @test_utils.docfile
    def test_no_withdrawals(self, filename: str):
        """
        2020-01-01 open Assets:Bank
        2020-01-01 open Assets:Account
        2020-01-01 open Assets:Account:Sub
        """
        split = get_split(filename)
        self.assertInventoriesSum("0", split.withdrawals)
