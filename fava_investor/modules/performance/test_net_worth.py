from pprint import pformat

from beancount import loader
from beancount.ops import validation
from beancount.utils import test_utils
from fava.core import FavaLedger

from fava_investor.modules.performance import performance as nw
from fava_investor.modules.performance.performance import AccountsConfig


def get_ledger(filename):
    _, errors, _ = loader.load_file(filename, extra_validations=validation.HARDCORE_VALIDATIONS)
    if errors:
        raise ValueError("Errors in ledger file: \n" + pformat(errors))

    ledger = FavaLedger(filename)
    return ledger


ACCOUNTS_CONFIG = {
    "inv": ["Assets:Investments"],
    "internal": ["Income", "Expenses"],
}


class TestNetWorth(test_utils.TestCase):
    @test_utils.docfile
    def test_dividends(self, filename: str):
        """
        2010-01-01 open Assets:Investments
        2010-01-01 open Assets:Bank
        2010-01-01 open Income:Dividends

        2010-02-01 * "reinvested dividends"
          Income:Dividends  -1 USD
          Income:Dividends  -2 GBP
          Assets:Investments

        2010-02-01 * "withdrawn dividends"
          Income:Dividends  -2 USD
          Income:Dividends  -3 GBP
          Assets:Bank
        """

        result = nw.report(get_ledger(filename), ACCOUNTS_CONFIG)
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

        result = nw.report(get_ledger(filename), ACCOUNTS_CONFIG)
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

        result = nw.report(get_ledger(filename), ACCOUNTS_CONFIG)
        assert result['gains_realized'] == {"USD": 2, "GBP": -1}


class TestAccountSelector(test_utils.TestCase):
    @test_utils.docfile
    def test_single_accounts(self, filename: str):
        """
        2010-01-01 open Assets:Bank
        2010-01-01 open Assets:Investments
        2010-01-01 open Income:Gains
        """
        config = {
            "inv": 'Assets:Investments',
            "internal": 'Income'
        }
        result = AccountsConfig.from_dict(get_ledger(filename), config)

        assert isinstance(result, AccountsConfig)
        assert ["Assets:Investments"] == result.value
        assert ["Income:Gains"] == result.internal
        assert ["Assets:Bank"] == result.external

    @test_utils.docfile
    def test_multiple_accounts(self, filename: str):
        """
        2010-01-01 open Assets:Taxable
        2010-01-01 open Assets:Pension
        2010-01-01 open Income:Gains
        2010-01-01 open Expenses:Fees
        2010-01-01 open Assets:RealEstate
        2010-01-01 open Assets:Bank
        """
        config = {
            "inv": ["Assets:Taxable", "Assets:Pension"],
            "internal": ["Income", "Expenses"],
        }
        result = AccountsConfig.from_dict(get_ledger(filename), config)

        assert isinstance(result, AccountsConfig)
        assert ["Assets:Taxable", "Assets:Pension"] == result.value
        assert ["Income:Gains", "Expenses:Fees"] == result.internal
        assert ["Assets:RealEstate", "Assets:Bank"] == result.external
