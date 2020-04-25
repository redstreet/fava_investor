from beancount.core.inventory import Inventory
from beancount.utils import test_utils

from fava_investor.modules.performance.split import calculate_balances


class TestSplit(test_utils.TestCase):
    def test_calculating_balances(self):
        input = [Inventory.from_string("10 GBP"), Inventory.from_string("15 GBP")]
        balances = calculate_balances(input)

        expected = [Inventory.from_string("10 GBP"), Inventory.from_string("25 GBP")]
        self.assertEqual(expected, balances)
