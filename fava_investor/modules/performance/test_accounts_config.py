from beancount.utils import test_utils

from fava_investor import AccountsConfig
from fava_investor.modules.performance.test_balances import get_ledger


class TestAccountsConfig(test_utils.TestCase):
    @test_utils.docfile
    def test_single_accounts(self, filename: str):
        """
        2010-01-01 open Assets:Bank
        2010-01-01 open Assets:Investments
        2010-01-01 open Income:Gains
        """
        config = {
            "value": 'Assets:Investments',
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
            "value": ["Assets:Taxable", "Assets:Pension"],
            "internal": ["Income", "Expenses"],
        }
        result = AccountsConfig.from_dict(get_ledger(filename), config)

        assert isinstance(result, AccountsConfig)
        assert ["Assets:Taxable", "Assets:Pension"] == result.value
        assert ["Income:Gains", "Expenses:Fees"] == result.internal
        assert ["Assets:RealEstate", "Assets:Bank"] == result.external
