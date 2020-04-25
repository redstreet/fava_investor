from beancount.utils import test_utils

from fava_investor.modules.performance.split import calculate_balances
from fava_investor.modules.performance.test_contributions import i


class TestSplit(test_utils.TestCase):
    def test_calculating_balances(self):
        input = [i("10 GBP"), i("15 GBP")]
        balances = calculate_balances(input)

        expected = [i("10 GBP"), i("25 GBP")]
        self.assertEqual(expected, balances)

    def test_empty_if_no_change(self):
        input = [i("10 GBP"), i("10 GBP"), i("15 GBP")]
        balances = calculate_balances(input)

        expected = [i("10 GBP"), i(), i("25 GBP")]
        self.assertEqual(expected, balances)

    def test_last_entry_is_there_even_if_no_change(self):
        input = [i("10 GBP"), i(), i()]
        balances = calculate_balances(input)

        expected = [i("10 GBP"), i(), i("10 GBP")]
        self.assertEqual(expected, balances)
