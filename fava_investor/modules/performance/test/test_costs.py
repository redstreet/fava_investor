from beancount.utils import test_utils

from fava_investor.modules.performance.test.testutils import SplitTestCase, get_interval_balances


class TestCosts(SplitTestCase):
    @test_utils.docfile
    def test_cost(self, filename: str):
        """
        2020-01-01 open Assets:Account
        2020-01-01 open Expenses:ServiceFee

        2020-01-01 * "dividend"
            Assets:Account  -5 GBP
            Expenses:ServiceFee
        """
        split = get_interval_balances(filename)
        self.assertInventoriesSum("-5 GBP", split.costs)

    @test_utils.docfile
    def test_sell_for_commission_with_some_rounding(self, filename: str):
        """
        2020-01-01 open Assets:Bank
        2020-01-01 open Assets:Account
        2020-01-01 open Income:Gains
        2020-01-01 open Expenses:Commission

        2020-01-01 * "sell for fees"
          Assets:Account   -0.19 AA {1.3425 GBP}
          Expenses:Commission  0.3 GBP
        """
        self.skipTest("broken")
        self.assertSumOfSplitsEqualValue(filename)
