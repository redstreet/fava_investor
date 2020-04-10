import datetime
from pprint import pformat

from beancount import loader
from beancount.ops import validation
from beancount.utils import test_utils
from core import FavaLedger
from freezegun import freeze_time
from fava.util.date import Interval

from fava_investor import AccountsConfig, interval_balances


def get_ledger(filename):
    _, errors, _ = loader.load_file(filename, extra_validations=validation.HARDCORE_VALIDATIONS)
    if errors:
        raise ValueError("Errors in ledger file: \n" + pformat(errors))

    ledger = FavaLedger(filename)
    return ledger


class TestBalances(test_utils.TestCase):
    @test_utils.docfile
    @freeze_time("2020-03-10")
    def test_cash(self, filename: str):
        """
        2010-01-01 open Assets:Bank
        2010-01-01 open Assets:Account

        2020-01-01 * "transfer"
            Assets:Account  20 GBP
            Assets:Bank

        2020-03-01 * "transfer"
            Assets:Account  20 GBP
            Assets:Bank
        """
        ledger = get_ledger(filename)
        accounts = AccountsConfig.from_dict(ledger, {
            "value": 'Assets:Account',
            "internal": []
        })

        balances, dates = interval_balances(ledger, accounts.value, Interval.MONTH)
        assert dates[0] == (datetime.date(2020, 3, 1), datetime.date(2020, 3, 2))
        assert dates[1] == (datetime.date(2020, 2, 1), datetime.date(2020, 3, 1))
        assert dates[2] == (datetime.date(2020, 1, 1), datetime.date(2020, 2, 1))

        assert balances[0]['Assets']['Account'].balance.to_string() == "(40 GBP)"
        assert balances[1]['Assets']['Account'].balance.to_string() == "(20 GBP)"
        assert balances[2]['Assets']['Account'].balance.to_string() == "(20 GBP)"

    @test_utils.docfile
    @freeze_time("2020-03-10")
    def test_stock(self, filename: str):
        """
        2010-01-01 open Assets:Bank
        2010-01-01 open Assets:Account

        2020-03-01 * "buy"
            Assets:Account  1 STK {10 GBP}
            Assets:Bank
        """
        ledger = get_ledger(filename)
        accounts = AccountsConfig.from_dict(ledger, {
            "value": 'Assets:Account',
            "internal": []
        })

        balances, dates = interval_balances(ledger, accounts.value, Interval.MONTH)
        assert dates[0] == (datetime.date(2020, 3, 1), datetime.date(2020, 3, 2))
        assert balances[0]['Assets']['Account'].balance.to_string() == "(1 STK {10 GBP, 2020-03-01})"
