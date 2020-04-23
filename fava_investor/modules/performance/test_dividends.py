from beancount.core.inventory import Inventory
from beancount.utils import test_utils

from .common import get_accounts_from_config
from .dividends import DividendsCalculator
from .test_balances import get_ledger

CONFIG = {
    "accounts_patterns": ["^Assets:Account"],
    "accounts_internal_patterns": ["^Income:Dividends"],
}


def get_sut(filename, config) -> DividendsCalculator:
    accapi = get_ledger(filename)
    return DividendsCalculator(accapi, get_accounts_from_config(accapi, config))


class TestDividends(test_utils.TestCase):
    @test_utils.docfile
    def test_dividend(self, filename: str):
        """
        2020-01-01 open Assets:Account
        2020-01-01 open Income:Dividends

        2020-01-01 * "dividend"
            Assets:Account  5 GBP
            Income:Dividends
        """
        sut = get_sut(filename, CONFIG)
        contributions = sut.get_dividends_total()
        self.assertEqual(Inventory.from_string("5 GBP"), contributions)

    @test_utils.docfile
    def test_dividend_to_external_is_counted_if_from_internalized_account(self, filename: str):
        """
        2020-01-01 open Assets:Bank
        2020-01-01 open Income:Dividends

        2020-01-01 * "dividend"
            Assets:Bank  5 GBP
            Income:Dividends
        """
        config = {
            "accounts_patterns": ["^Assets:Account"],
            "accounts_internal_patterns": ["^Income:Dividends"],
            "accounts_internalized_patterns": ["^Income:Dividends"]
        }
        sut = get_sut(filename, config)
        self.assertEquals(Inventory.from_string("5 GBP"), sut.get_dividends_total())

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
            "accounts_patterns": ["^Assets:Account"],
            "accounts_internal_patterns": ["^Income:Dividends"],
            "accounts_internalized_patterns": []
        }
        sut = get_sut(filename, config)
        self.assertEquals(Inventory(), sut.get_dividends_total())
