from beancount.utils import test_utils

from fava_investor.modules.performance.test.testutils import SplitTestCase, get_interval_balances


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
        split = get_interval_balances(filename)
        self.assertInventoriesSum("5 GBP", split.dividends)

    @test_utils.docfile
    def test_dividend_paid_out_to_external_account(self, filename: str):
        """
        2020-01-01 open Assets:Bank
        2020-01-01 open Income:Dividends

        2020-01-01 * "dividend"
            Assets:Bank
            Income:Dividends  -5 GBP
        """
        split = get_interval_balances(filename)
        self.assertInventoriesSum("5 GBP", split.dividends)
