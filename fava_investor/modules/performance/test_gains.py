from beancount.core.inventory import Inventory
from beancount.utils import test_utils

from .common import get_accounts_from_config
from .gains import GainsCalculator
from .test_balances import get_ledger

CONFIG = {"accounts_patterns": ["^Assets:Account"], "accounts_internal_patterns": ["^Income:Gains$"]}


def get_sut(filename, config) -> GainsCalculator:
    accapi = get_ledger(filename)
    return GainsCalculator(accapi, get_accounts_from_config(accapi, config))


class TestGains(test_utils.TestCase):
    @test_utils.docfile
    def test_get_unrealized_gains(self, filename: str):
        """
        2020-01-01 open Assets:Bank
        2020-01-01 open Assets:Account

        2020-02-22 * "Buy stock"
          Assets:Account  1 AA {1 USD}
          Assets:Bank

        2020-02-22 price AA  2 USD
        """
        sut = get_sut(filename, CONFIG)
        result = sut.get_unrealized_gains_total()

        self.assertEquals({"USD": 1}, result)

    @test_utils.docfile
    def test_get_unrealized_gains_entries(self, filename: str):
        """
        2020-01-01 open Assets:Bank
        2020-01-01 open Assets:Account:A
        2020-01-01 open Assets:Account:B

        2020-02-22 * "Buy stock"
          Assets:Account:A  1 AA {1 USD}
          Assets:Bank

        2020-02-23 * "Buy stock"
          Assets:Account:B  2 AA {1 USD}
          Assets:Bank

        2020-02-22 price AA  2 USD
        """
        sut = get_sut(filename, CONFIG)
        result = sut.get_unrealized_gains_per_account()

        expected = {
            "Assets:Account:A": {"USD": 1},
            "Assets:Account:B": {"USD": 2},
        }
        self.assertEqual(expected, result)

    @test_utils.docfile
    def test_unrealized_ignoreNonValueAccounts(self, filename: str):
        """
        2020-01-01 open Assets:Bank
        2020-01-01 open Assets:Ignored

        2020-02-22 * "Buy stock"
          Assets:Ignored  1 AA {1 USD}
          Assets:Bank

        2020-02-22 price AA  2 USD
        """
        sut = get_sut(filename, CONFIG)
        result = sut.get_unrealized_gains_total()

        self.assertEquals(Inventory(), result)

    @test_utils.docfile
    def test_ignoring_realized_gains(self, filename: str):
        """
        2020-01-01 open Assets:Bank
        2020-01-01 open Assets:Account
        2020-01-01 open Income:Gains

        2020-02-22 * "realized gain"
          Assets:Account  1 AA {1 USD}
          Assets:Bank

        2020-02-23 * "realized gain"
          Assets:Account  -1 AA {1 USD}
          Assets:Bank  2 USD
          Income:Gains  -1 USD

        2020-02-24 * "unrealized gain"
          Assets:Account  1 AA {2 USD}
          Assets:Bank

        2020-02-24 price AA  4 USD
        """
        sut = get_sut(filename, CONFIG)
        result = sut.get_unrealized_gains_total()

        self.assertEquals({"USD": 2}, result)

    @test_utils.docfile
    def test_get_unrealized_gains(self, filename: str):
        """
        2020-01-01 open Assets:Bank
        2020-01-01 open Assets:Account

        2020-02-22 * "Buy stock"
          Assets:Account  1 AA {1 USD}
          Assets:Bank

        2020-02-22 price AA  2 USD
        """
        sut = get_sut(filename, CONFIG)
        result = sut.get_unrealized_gains_total()

        self.assertEquals({"USD": 1}, result)

    @test_utils.docfile
    def test_realized_gains(self, filename: str):
        """
        2020-01-01 open Assets:Bank
        2020-01-01 open Assets:Account
        2020-01-01 open Income:Gains

        2020-02-22 * "buy"
          Assets:Account  1 AA {1 USD}
          Assets:Bank

        2020-02-23 * "sell with gain"
          Assets:Account  -1 AA {1 USD}
          Assets:Bank  2 USD
          Income:Gains
        """
        sut = get_sut(filename, CONFIG)
        result = sut.get_realized_gains_total()

        self.assertEquals(Inventory.from_string("1 USD"), result)

    @test_utils.docfile
    def test_realized_gains_multiple_transactions(self, filename: str):
        """
        2020-01-01 open Assets:Bank
        2020-01-01 open Assets:Account
        2020-01-01 open Income:Gains

        2020-02-22 * "buy"
          Assets:Account  1 AA {1 USD}
          Assets:Account  1 AA {2 USD}
          Assets:Bank

        2020-02-23 * "sell with gain"
          Assets:Account  -1 AA {2 USD}
          Assets:Bank  3 USD
          Income:Gains

        2020-02-24 * "sell with gain again"
          Assets:Account  -1 AA {1 USD}
          Assets:Bank  3 USD
          Income:Gains
        """
        sut = get_sut(filename, CONFIG)
        result = sut.get_realized_gains_total()

        self.assertEquals(Inventory.from_string("3 USD"), result)

    @test_utils.docfile
    def test_realized_lose(self, filename: str):
        """
        2020-01-01 open Assets:Bank
        2020-01-01 open Assets:Account
        2020-01-01 open Income:Gains

        2020-02-22 * "buy"
          Assets:Account  1 AA {2 USD}
          Assets:Bank

        2020-02-23 * "sell with gain"
          Assets:Account  -1 AA {2 USD}
          Assets:Bank  1 USD
          Income:Gains
        """
        sut = get_sut(filename, CONFIG)
        result = sut.get_realized_gains_total()

        self.assertEquals(Inventory.from_string("-1 USD"), result)
