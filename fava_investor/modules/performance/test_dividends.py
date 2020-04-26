from beancount.core.inventory import Inventory
from beancount.utils import test_utils

from .split import sum_inventories
from .test_split import SplitTestCase, get_split


class TestDividends(SplitTestCase):
    @test_utils.docfile
    def test_dividend(self, filename: str):
        """
        2020-01-01 open Assets:Account
        2020-01-01 open Income:Dividends

        2020-01-01 * "dividend"
            Assets:Account  5 GBP
            Income:Dividends
        """
        split = get_split(filename)
        self.assertEqual(Inventory.from_string("5 GBP"), sum_inventories(split.dividends))

    @test_utils.docfile
    def test_dividend_paid_out_to_external_account(self, filename: str):
        """
        2020-01-01 open Assets:Bank
        2020-01-01 open Income:Dividends

        2020-01-01 * "dividend"
            Assets:Bank
            Income:Dividends  -5 GBP
        """
        split = get_split(filename)
        self.assertEqual(Inventory.from_string("5 GBP"), sum_inventories(split.dividends))
