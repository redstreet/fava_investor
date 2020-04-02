from pprint import pformat

from beancount import loader
from beancount.ops import validation
from beancount.utils import test_utils
from fava.core import FavaLedger

from fava_investor.modules.net_worth import net_worth as nw


def get_ledger(filename):
    _, errors, _ = loader.load_file(filename, extra_validations=validation.HARDCORE_VALIDATIONS)
    if errors:
        raise ValueError("Errors in ledger file: \n" + pformat(errors))
    ledger = FavaLedger(filename)
    return ledger


class TestNetWorth(test_utils.TestCase):
    @test_utils.docfile
    def test_contributions_with_multiple_currencies(self, filename: str):
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

        result = nw.get_net_worth(get_ledger(filename))
        assert result['contributions'] == {"USD": 20, "GBP": 18}

    @test_utils.docfile
    def test_transactions_with_various_splits(self, filename: str):
        """
        2010-01-01 open Assets:Bank
        2010-01-01 open Assets:Cash
        2010-01-01 open Assets:Investments

        2010-02-01 * "Buy stock"
          Assets:Investments  -1 BNCT {15 USD}
          Assets:Investments  1 BNCT {15 USD}
          Assets:Investments  1 BNCT {20 USD}
          Assets:Bank  -15 USD
          Assets:Cash  -10 USD
          Assets:Bank  5 USD
        """
        result = nw.get_net_worth(get_ledger(filename))
        assert result['contributions'] == {"USD": 20}

    @test_utils.docfile
    def test_income(self, filename: str):
        """
        2010-01-01 open Assets:Investments
        2010-01-01 open Income:Dividends
        2010-01-01 open Income:Rent

        2010-02-01 * "dividend"
          Income:Dividends  -20 USD
          Assets:Investments

        2010-02-01 * "irrelevant income"
          Income:Rent  -500 USD
          Assets:Investments
        """

        result = nw.get_net_worth(get_ledger(filename))
        assert result['dividends_reinvested'] == {"USD": 20}

    @test_utils.docfile
    def test_appreciation(self, filename: str):
        """
        2010-01-01 open Assets:Investments
        2010-01-01 open Assets:Bank

        2010-02-01 * "buy"
          Assets:Investments  1 STK {12 USD}
          Assets:Bank

        2010-02-02 price  STK  13 USD
        """

        result = nw.get_net_worth(get_ledger(filename))
        assert result['gains_unrealized'] == {"USD": 1}

    @test_utils.docfile
    def test_appreciation_multiple_currencies(self, filename: str):
        """
        2010-01-01 open Assets:Investments
        2010-01-01 open Assets:Bank

        2010-02-01 * "buy"
          Assets:Investments  1 STK {12 USD}
          Assets:Investments  1 ZXC {2 GBP}
          Assets:Bank

        2010-02-02 price  STK  13 USD
        2010-02-02 price  ZXC  1 GBP
        """

        result = nw.get_net_worth(get_ledger(filename))
        assert result['gains_unrealized'] == {"USD": 1, "GBP": -1}
