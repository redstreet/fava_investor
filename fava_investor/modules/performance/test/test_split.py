from beancount.utils import test_utils

from fava_investor.modules.performance.test.testutils import SplitTestCase


class TestSplit(SplitTestCase):
    @test_utils.docfile
    def test_no_dividends_counted_when_realizing_gain(self, filename):
        """
        2020-01-01 open Assets:Account
        2020-01-01 open Income:Gains

        2020-01-05 * "realized gain"
            Assets:Account  1 SHARE {1 USD}
            Assets:Account

        2020-01-06 * "realized gain"
            Assets:Account  -1 SHARE {1 USD}
            Assets:Account
            Income:Gains  -1 USD
        """
        self.assertSumOfSplitsEqualValue(filename)

    @test_utils.docfile
    def test_splits_of_unrealized_gain(self, filename):
        """
        2020-01-01 open Assets:Account
        2020-01-01 open Assets:Bank
        2020-01-01 open Expenses:ServiceFee
        2020-01-01 open Income:Dividends
        2020-01-01 open Income:Gains

        2020-01-02 * "unrealized gain"
            Assets:Account  1 SHARE {1 USD}
            Assets:Account

        2020-01-03 price SHARE 2 USD

        2020-01-04 * "irrelevant"
            Assets:Account  1 GBP
            Assets:Account
        """

        self.assertSumOfSplitsEqualValue(filename)

    @test_utils.docfile
    def test_unrealized_gains_in_discounted_purchase(self, filename: str):
        """
        2020-01-01 open Assets:Bank
        2020-01-01 open Assets:Account
        2020-01-01 open Income:Gains

        2020-01-01 price AA 2 USD

        2020-01-02 * "buy discounted"
          Assets:Account  1 AA {1 USD}
          Assets:Account
        """
        self.assertSumOfSplitsEqualValue(filename)

    @test_utils.docfile
    def test_selling_with_commission(self, filename: str):
        """
        2020-01-01 open Assets:Bank
        2020-01-01 open Assets:Account
        2020-01-01 open Income:Gains
        2020-01-01 open Expenses:Commission

        2020-01-01 * "contrib and buy"
          Assets:Account       1 VLS {2 GBP}
          Assets:Bank         -2 GBP

        2020-01-01 * "sell with cost"
          Assets:Account      -1 VLS {2 GBP}
          Assets:Account       1 GBP
          Expenses:Commission  1 GBP

        """
        self.assertSumOfSplitsEqualValue(filename)

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


