from beancount.utils import test_utils

from fava_investor.modules.performance.test.testutils import SplitTestCase, get_interval_balances, \
    get_interval_balances_with_meta


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
        split = get_interval_balances(filename)
        self.assertInventoriesSum("1 USD", split.gains_unrealized)

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
        split = get_interval_balances(filename)
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
        split = get_interval_balances(filename)
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
        split = get_interval_balances(filename)
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
        split = get_interval_balances(filename)
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
        split = get_interval_balances(filename)
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
          Assets:Account  1 USD
          Income:Gains

        2020-02-24 balance Assets:Account  1 USD
        """
        self.assertSumOfSplitsEqual(filename, "1 USD")

    @test_utils.docfile
    def test_dummy_transaction_has_date_to_work_in_templates_with_filters(self, filename):
        """
        2020-01-01 open Assets:Account
        2020-01-01 open Assets:Bank

        2020-01-02 * "contribution"
            Assets:Account  1 AA {1 USD}
            Assets:Bank

        2020-01-04 price AA 2 USD
        """
        split = get_interval_balances_with_meta(filename)
        last_entry = split.transactions[-1]
        self.assertEqual("UNREALIZED GAINS NEW BALANCE", last_entry.narration)
        self.assertIsNotNone(last_entry.date)
