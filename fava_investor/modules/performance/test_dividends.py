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
    def test_dividend_to_external_is_counted_if_from_internalized_account(self, filename: str):
        """
        2020-01-01 open Assets:Bank
        2020-01-01 open Income:Dividends

        2020-01-01 * "dividend"
            Assets:Bank
            Income:Dividends  -5 GBP
        """
        config = {
            "accounts_pattern": "^Assets:Account",
            "accounts_internal_pattern": "^Income:",
            "accounts_internalized_pattern": "^Income:Dividends"
        }
        split = get_split(filename, config)
        self.assertEqual(Inventory.from_string("5 GBP"), sum_inventories(split.dividends))

    @test_utils.docfile
    def test_dividend_to_external_is_ignored_if_its_not_from_internalized_account(self, filename: str):
        """
        2020-01-01 open Assets:Bank
        2020-01-01 open Income:Dividends

        2020-01-01 * "dividend"
            Assets:Bank  5 GBP
            Income:Dividends
        """
        config = {
            "accounts_pattern": "^Assets:Account",
            "accounts_internal_pattern": "^Income:Dividends",
            "accounts_internalized_pattern": "^DoesNotMatch$"
        }
        split = get_split(filename, config)
        self.assertEqual(Inventory(), sum_inventories(split.dividends))

    @test_utils.docfile
    def test_cost(self, filename: str):
        """
        2020-01-01 open Assets:Account
        2020-01-01 open Expenses:ServiceFee

        2020-01-01 * "dividend"
            Assets:Account  -5 GBP
            Expenses:ServiceFee
        """
        split = get_split(filename)
        inventories = sum_inventories(split.costs)
        self.assertEqual(Inventory.from_string("-5 GBP"), inventories)

    @test_utils.docfile
    def test_sum_of_each_split_should_match_balance(self, filename):
        """
        2020-01-01 open Assets:Account
        2020-01-01 open Expenses:ServiceFee
        2020-01-02 * "cost"
            Assets:Account  1 USD
            Expenses:ServiceFee
        """

        self.assertSumOfSplitsEqualValue(filename)
