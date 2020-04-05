from decimal import Decimal
from pprint import pformat
from typing import Dict

from beancount import loader
from beancount.ops import validation
from beancount.utils import test_utils
from fava.core import FavaLedger

from fava_investor.modules.performance import performance as nw
from fava_investor.modules.performance.performance import InventoryTools


ACCOUNTS_CONFIG = {
    "value": ["Assets:Investments"],
    "internal": ["Income", "Expenses"],
}


def get_ledger(filename):
    _, errors, _ = loader.load_file(filename, extra_validations=validation.HARDCORE_VALIDATIONS)
    if errors:
        raise ValueError("Errors in ledger file: \n" + pformat(errors))

    ledger = FavaLedger(filename)
    return ledger


def get_contributions(filename) -> Dict[str, Decimal]:
    _, result = nw.contributions(get_ledger(filename), ACCOUNTS_CONFIG)
    return InventoryTools.to_dict(result)


class TestNetWorth(test_utils.TestCase):

    @test_utils.docfile
    def test_buying_from_external_account(self, filename: str):
        """
        2010-01-01 open Assets:Bank
        2010-01-01 open Assets:Investments

        2010-02-01 * "Buy stock"
          Assets:Investments  2 BNCT {10 USD}
          Assets:Bank

        2010-02-01 * "Buy stock"
          Assets:Investments  2 BNCT {9 GBP}
          Assets:Bank
        """

        result = get_contributions(filename)
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

        result = get_contributions(filename)
        assert result == {"USD": 1000}
