from beancount.utils import test_utils

from fava_investor.modules.net_worth import net_worth as nw
from fava_investor.modules.net_worth.test_common import get_ledger, ACCOUNTS_CONFIG


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

        log, result = nw.contributions(get_ledger(filename), ACCOUNTS_CONFIG)
        assert result == {"USD": 20, "GBP": 18}

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
        log, result = nw.contributions(get_ledger(filename), ACCOUNTS_CONFIG)
        assert result == {"USD": 20}
