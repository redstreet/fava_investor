from beancount.utils import test_utils

from fava_investor import calculate_balances
from fava_investor.modules.performance.test.testutils import i


class TestCalculateBalances(test_utils.TestCase):
    def test_calculating_balances(self):
        input = [i("10 GBP"), i("15 GBP")]
        balances = calculate_balances(input)

        expected = [i("10 GBP"), i("25 GBP")]
        self.assertEqual(expected, balances)

    def test_empty_list(self):
        balances = calculate_balances([])
        self.assertEqual([], balances)