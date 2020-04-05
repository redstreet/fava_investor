from decimal import Decimal
from typing import Dict

from beancount.utils import test_utils

from fava_investor.modules.net_worth import net_worth as nw
from fava_investor.modules.net_worth.net_worth import InventoryTools
from fava_investor.modules.net_worth.test_common import get_ledger, ACCOUNTS_CONFIG


class TestNetWorth(test_utils.TestCase):
    def get_contributions(self, filename) -> Dict[str, Decimal]:
        _, result = nw.contributions(get_ledger(filename), ACCOUNTS_CONFIG)
        return InventoryTools.to_dict(result)

    @test_utils.docfile
    def test_buying_from_external_account(self, filename: str):
        """
        2010-01-01 open Assets:Bank
        2010-01-01 open Assets:Investments

        2010-02-01 * "Buy stock"
          Assets:Investments  1 BNCT {20 USD}
          Assets:Bank

        2010-02-01 * "Buy stock"
          Assets:Investments  1 BNCT {18 GBP}
          Assets:Bank
        """

        result = self.get_contributions(filename)
        assert result == {"USD": 20, "GBP": 18}

    @test_utils.docfile
    def test_moving_cash_from_external_account(self, filename: str):
        """
        2010-01-01 open Assets:Bank
        2010-01-01 open Assets:Investments

        2010-02-01 * "Buy stock"
          Assets:Investments  1000 USD
          Assets:Bank
        """

        result = self.get_contributions(filename)
        assert result == {"USD": 1000}
