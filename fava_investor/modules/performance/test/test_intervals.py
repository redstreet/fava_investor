from beancount.utils import test_utils
from fava.util.date import Interval

from fava_investor.modules.performance.test.testutils import SplitTestCase, get_interval_balances, \
    get_interval_balances_with_meta


class TestIntervals(SplitTestCase):
    @test_utils.docfile
    def test_contributions_in_intervals(self, filename):
        """
        2020-01-01 open Assets:Account
        2020-01-01 open Assets:Bank

        2020-01-02 * "contribution"
            Assets:Account  1 AA {1 USD}
            Assets:Bank

        2020-02-02 * "contribution"
            Assets:Account  1 AA {3 USD}
            Assets:Bank
        """
        split = get_interval_balances(filename, interval=Interval.MONTH)
        self.assertEqual(2, len(split.contributions))
        self.assertInventory("1 USD", split.contributions[0])
        self.assertInventory("3 USD", split.contributions[1])

    @test_utils.docfile
    def test_various_splits_in_intervals(self, filename):
        """
        2020-01-01 open Assets:Account
        2020-01-01 open Assets:Bank
        2020-01-01 open Income:Dividend
        2020-01-01 open Income:Gains
        2020-01-01 open Expenses:Costs

        2020-01-02 * "contribution"
            Assets:Account  1 AA {1 USD}
            Assets:Bank

        2020-01-02 * "dividend"
            Assets:Account
            Income:Dividend  -4 USD

        2020-01-02 price AA 3 USD

        2020-02-02 * "withdrawal"
            Assets:Account
            Assets:Bank  1 USD

        2020-02-02 * "cost"
            Assets:Account
            Expenses:Costs  2 USD

        2020-02-02 * "realized gain"
            Assets:Account  -1 AA {1 USD}
            Assets:Account
            Income:Gains -4 USD
        """
        split = get_interval_balances_with_meta(filename, interval=Interval.MONTH)
        parts = split.parts
        self.assertInventory("1 USD", parts.contributions[0])
        self.assertInventory("0 USD", parts.withdrawals[0])
        self.assertInventory("4 USD", parts.dividends[0])
        self.assertInventory("0 USD", parts.costs[0])
        self.assertInventory("0 USD", parts.gains_realized[0])
        self.assertInventory("2 USD", parts.gains_unrealized[0])

        self.assertInventory("0 USD", parts.contributions[1])
        self.assertInventory("-1 USD", parts.withdrawals[1])
        self.assertInventory("0 USD", parts.dividends[1])
        self.assertInventory("-2 USD", parts.costs[1])
        self.assertInventory("4 USD", parts.gains_realized[1])
        self.assertInventory("-2 USD", parts.gains_unrealized[1])

    @test_utils.docfile
    def test_various_splits_in_total(self, filename):
        """
        2020-01-01 open Assets:Account
        2020-01-01 open Assets:Bank
        2020-01-01 open Income:Dividend
        2020-01-01 open Income:Gains
        2020-01-01 open Expenses:Costs

        2020-01-02 * "contribution"
            Assets:Account  1 AA {1 USD}
            Assets:Bank

        2020-01-02 * "dividend"
            Assets:Account
            Income:Dividend  -4 USD

        2020-01-02 price AA 3 USD

        2020-02-02 * "withdrawal"
            Assets:Account
            Assets:Bank  1 USD

        2020-02-02 * "cost"
            Assets:Account
            Expenses:Costs  2 USD

        2020-02-02 * "realized gain"
            Assets:Account  -1 AA {1 USD}
            Assets:Account
            Income:Gains -4 USD
        """

        split = get_interval_balances_with_meta(filename, interval=None)
        parts = split.parts
        self.assertEqual(1, len(parts.contributions))
        self.assertInventory("1 USD", parts.contributions[0])
        self.assertInventory("-1 USD", parts.withdrawals[0])
        self.assertInventory("4 USD", parts.dividends[0])
        self.assertInventory("-2 USD", parts.costs[0])
        self.assertInventory("4 USD", parts.gains_realized[0])
        self.assertInventory("0 USD", parts.gains_unrealized[0])
