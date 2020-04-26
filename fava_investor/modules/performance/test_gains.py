from beancount.utils import test_utils

from .test_split import SplitTestCase, get_split, i


class TestGains(SplitTestCase):

    @test_utils.docfile
    def test_get_unrealized_gain(self, filename: str):
        """
        2020-01-01 open Assets:Bank
        2020-01-01 open Assets:Account

        2020-02-21 * "Buy stock"
          Assets:Account  1 AA {1 USD}
          Assets:Bank

        2020-02-22 price AA  2 USD
        """
        split = get_split(filename)
        self.assertInventoriesSum("1 USD", split.gains_unrealized)

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

        2020-02-24 price AA  2 USD
        """
        self.skipTest("todo ")
        sut = get_sut(filename)
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
        split = get_split(filename)
        self.assertInventoriesSum("", split.gains_unrealized)

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

        2020-02-24 price AA  10 USD
        """
        split = get_split(filename)
        self.assertInventoriesSum("8 USD", split.gains_unrealized)

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
        split = get_split(filename)

        self.assertInventoriesSum("1 USD", split.gains_unrealized)

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
        split = get_split(filename)

        self.assertInventoriesSum("1 USD", split.gains_realized)

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
          Income:Gains  -1 USD

        2020-02-24 * "sell with gain again"
          Assets:Account  -1 AA {1 USD}
          Assets:Bank  3 USD
          Income:Gains  -2 USD
        """
        split = get_split(filename)

        self.assertInventoriesSum("3 USD", split.gains_realized)

    @test_utils.docfile
    def test_realized_lose(self, filename: str):
        """
        2020-01-01 open Assets:Bank
        2020-01-01 open Assets:Account
        2020-01-01 open Income:Gains

        2020-02-22 * "buy"
          Assets:Account  1 AA {2 USD}
          Assets:Bank

        2020-02-23 * "sell with lose"
          Assets:Account  -1 AA {2 USD}
          Assets:Bank  1 USD
          Income:Gains
        """
        self.skipTest("how do we differentiate lose from cost/commission?")
        split = get_split(filename)

        self.assertInventoriesSum("-1 USD", split.gains_realized)

