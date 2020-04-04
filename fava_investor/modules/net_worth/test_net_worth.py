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
    def test_contributions(self, filename: str):
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
    def test_contributions_with_extra_splits(self, filename: str):
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
    def test_dividends(self, filename: str):
        """
        2010-01-01 open Assets:Investments
        2010-01-01 open Assets:Bank
        2010-01-01 open Income:Dividends
        2010-01-01 open Income:Rent

        2010-02-01 * "reinvested dividends"
          Income:Dividends  -1 USD
          Income:Dividends  -2 GBP
          Assets:Investments

        2010-02-01 * "irrelevant income"
          Income:Rent  -500 USD
          Assets:Investments

        2010-02-01 * "withdrawn dividends"
          Income:Dividends  -2 USD
          Income:Dividends  -3 GBP
          Assets:Bank
        """

        result = nw.get_net_worth(get_ledger(filename))
        assert result['dividends_reinvested'] == {"USD": 1, "GBP": 2}
        assert result['dividends_withdrawn'] == {"USD": 2, "GBP": 3}
        assert result['dividends_total'] == {"USD": 3, "GBP": 5}

    @test_utils.docfile
    def test_gains_unrealized(self, filename: str):
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

    @test_utils.docfile
    def test_gains_realized(self, filename: str):
        """
        2010-01-01 open Assets:Investments
        2010-01-01 open Assets:Bank
        2010-01-01 open Income:Gains

        2010-02-01 * "buy"
          Assets:Investments  1 STK {10 USD}
          Assets:Investments  1 ZXC {2 GBP}
          Assets:Bank

        2010-02-01 * "sell"
          Assets:Investments  -1 STK {10 USD}
          Assets:Investments  -1 ZXC {2 GBP}
          Assets:Investments  12 USD
          Assets:Investments  1 GBP
          Income:Gains
        """

        result = nw.get_net_worth(get_ledger(filename))
        assert result['gains_realized'] == {"USD": 2, "GBP": -1}
