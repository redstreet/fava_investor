from beancount.utils import test_utils
from fava.util.date import Interval

from fava_investor import sum_inventories
from fava_investor.modules.performance.test.testutils import SplitTestCase, get_split, get_split_with_meta


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
        split = get_split(filename, interval=Interval.MONTH)
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

        2020-01-02 * "contribution"
            Assets:Account  1 AA {1 USD}
            Assets:Bank

        2020-02-02 * "dividend"
            Assets:Account
            Income:Dividend  -4 GBP

        2020-03-02 * "gain"
            Assets:Account  -1 AA {1 USD}
            Assets:Account
            Income:Gains  -5 USD
        """
        split = get_split_with_meta(filename, interval=Interval.MONTH)
        self.assertEqual(3, len(split.values))
        sum_week1 = sum_inventories([s[0] for s in split.parts])
        self.assertEqual(split.values[0], sum_week1)

        sum_week2 = sum_inventories([s[1] for s in split.parts])
        self.assertEqual(split.values[1], sum_week2)

        sum_week3 = sum_inventories([s[2] for s in split.parts])
        self.assertEqual(split.values[2], sum_week3)
