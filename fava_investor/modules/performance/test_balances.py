from pprint import pformat

from beancount import loader
from beancount.ops import validation
from beancount.utils import test_utils
from fava.core import FavaLedger
from freezegun import freeze_time

from fava_investor import FavaInvestorAPI, get_closed_tree_with_value_accounts_only


def get_ledger(filename):
    _, errors, _ = loader.load_file(filename, extra_validations=validation.HARDCORE_VALIDATIONS)
    if errors:
        raise ValueError("Errors in ledger file: \n" + pformat(errors))

    return FavaInvestorAPI(FavaLedger(filename))


CONFIG = {
    "value": ["^Assets:Account"],
    "internal": []
}


class TestBalances(test_utils.TestCase):
    @test_utils.docfile
    @freeze_time("2020-03-10")
    def test_sums(self, filename: str):
        """
        2010-01-01 open Assets:Bank
        2010-01-01 open Assets:Account

        2020-01-01 * "transfer"
            Assets:Account  10 GBP
            Assets:Bank

        2020-03-01 * "transfer"
            Assets:Account  10 GBP
            Assets:Bank
        """
        tree = get_closed_tree_with_value_accounts_only(get_ledger(filename), CONFIG)
        assert {('GBP', None): 20} == tree["Assets:Account"].balance
        assert {('GBP', None): 20} == tree["Assets"].balance_children
        assert {} == tree["Assets"].balance

    @test_utils.docfile
    @freeze_time("2020-03-10")
    def test_it_has_value_accounts_and_ancestors(self, filename: str):
        """
        2010-01-01 open Assets:Bank
        2010-01-01 open Assets:Account

        2020-03-01 * "buy"
            Assets:Account  1 GBP
            Assets:Bank
        """

        tree = get_closed_tree_with_value_accounts_only(get_ledger(filename), CONFIG)
        assert "Assets" in tree
        assert "Assets:Account" in tree
        assert len(tree['Assets'].children) == 1

        assert "Assets:Bank" not in tree
