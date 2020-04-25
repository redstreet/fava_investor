from pprint import pformat

from beancount import loader
from beancount.core.data import Transaction
from beancount.core.inventory import Inventory
from beancount.ops import validation
from beancount.utils import test_utils
from fava.core import FavaLedger

from .split import split_journal, sum_inventories
from favainvestorapi import FavaInvestorAPI


def get_ledger(filename):
    _, errors, _ = loader.load_file(
        filename, extra_validations=validation.HARDCORE_VALIDATIONS
    )
    if errors:
        raise ValueError("Errors in ledger file: \n" + pformat(errors))

    return FavaInvestorAPI(FavaLedger(filename))


def i(string=None):
    return Inventory.from_string(string if string else "")


def get_split(filename, config_override=None):
    defaults = {
        "accounts_pattern": "^Assets:Account",
        "accounts_internal_pattern": "^(Income|Expenses):",
        "accounts_internalized_pattern": "^Income:Dividends",
    }
    if not config_override:
        config_override = {}

    config = {**defaults, **config_override}
    ledger = get_ledger(filename)
    return split_journal(ledger, config["accounts_pattern"], config["accounts_internal_pattern"], config["accounts_internalized_pattern"])


class TestContributions(test_utils.TestCase):
    @test_utils.docfile
    def test_no_contributions(self, filename: str):
        """
        2020-01-01 open Assets:Bank
        2020-01-01 open Assets:Account
        2020-01-01 open Assets:Account:Sub
        """
        result = sum_inventories(get_split(filename).contributions)
        self.assertEqual({}, result)

    @test_utils.docfile
    def test_no_withdrawals(self, filename: str):
        """
        2020-01-01 open Assets:Bank
        2020-01-01 open Assets:Account
        2020-01-01 open Assets:Account:Sub
        """
        result = sum_inventories(get_split(filename).withdrawals)
        self.assertEqual({}, result)

    @test_utils.docfile
    def test_contributions_to_subaccounts(self, filename: str):
        """
        2020-01-01 open Assets:Bank
        2020-01-01 open Assets:Account
        2020-01-01 open Assets:Account:Sub

        2020-01-01 * "contrib 1"
            Assets:Account  10 GBP
            Assets:Bank

        2020-01-01 * "contrib 2"
            Assets:Account:Sub  10 GBP
            Assets:Bank
        """
        result = sum_inventories(get_split(filename).contributions)
        self.assertEqual(i("20 GBP"), result)

    @test_utils.docfile
    def test_other_transfers_are_ignored(self, filename: str):
        """
        2020-01-01 open Assets:Bank
        2020-01-01 open Assets:Bank2
        2020-01-01 open Assets:Account
        2020-01-01 open Assets:Account:Sub

        2020-01-01 * "irrelevant"
            Assets:Account  10 GBP
            Assets:Account:Sub

        2020-01-01 * "irrelevant"
            Assets:Bank  20 GBP
            Assets:Bank2
        """
        result = sum_inventories(get_split(filename).contributions)
        self.assertEqual({}, result)

    @test_utils.docfile
    def test_list_withdrawals_entries(self, filename: str):
        """
        2020-01-01 open Assets:Bank
        2020-01-01 open Assets:Account:A
        2020-01-01 open Assets:Account:B

        2020-01-01 * "contrib"
            Assets:Account:A  2 GBP
            Assets:Bank

        2020-01-02 * "withdrawal 1"
            Assets:Account:A  -1 GBP
            Assets:Account:B  -2 GBP
            Assets:Bank

        2020-01-02 * "withdrawal 2"
            Assets:Account:A  -3 GBP
            Assets:Bank
        """
        split = get_split(filename)

        self.assertEqual({}, split.withdrawals[0])
        self.assertEqual(i("-3 GBP"), split.withdrawals[1])
        self.assertEqual(i("-3 GBP"), split.withdrawals[2])

        self.assertIsInstance(split.transactions[0], Transaction)
        self.assertIsInstance(split.transactions[1], Transaction)
        self.assertIsInstance(split.transactions[2], Transaction)
        self.assertEqual("contrib", split.transactions[0].narration)
        self.assertEqual("withdrawal 1", split.transactions[1].narration)
        self.assertEqual("withdrawal 2", split.transactions[2].narration)

    @test_utils.docfile
    def test_list_contribution_entries(self, filename: str):
        """
        2020-01-01 open Assets:Bank
        2020-01-01 open Assets:Account:A
        2020-01-01 open Assets:Account:B

        2020-01-01 * "withdrawal"
            Assets:Account:A  -2 GBP
            Assets:Bank

        2020-01-02 * "contribution 1"
            Assets:Account:A  1 GBP
            Assets:Account:B  2 GBP
            Assets:Bank

        2020-01-03 * "contribution 2"
            Assets:Account:A  3 GBP
            Assets:Bank
        """
        split = get_split(filename)
        self.assertEqual(Inventory.from_string("3 GBP"), split.contributions[1])
        self.assertEqual(Inventory.from_string("3 GBP"), split.contributions[2])

        self.assertIsInstance(split.transactions[1], Transaction)
        self.assertEqual("contribution 1", split.transactions[1].narration)
        self.assertIsInstance(split.transactions[2], Transaction)
        self.assertEqual("contribution 2", split.transactions[2].narration)

    @test_utils.docfile
    def test_filtered_out_value_accounts_are_treated_as_external(self, filename: str):
        """
        2020-01-01 open Assets:Bank
        2020-01-01 open Assets:Account:A
        2020-01-01 open Assets:Account:B

        2020-01-02 * "contribution"
            Assets:Account:B  5 GBP
            Assets:Bank

        2020-01-02 * "value accounts transfer"
            Assets:Account:A  2 GBP
            Assets:Account:B
        """
        self.skipTest(
            "Not implemented. It will be needed to calculate returns for selected account as well."
        )

        split = get_split(filename)

        self.assertEqual(Inventory.from_string("2 GBP"), sum_inventories(split.contributions))

    @test_utils.docfile
    def test_asset_on_loan_with_contributed_part(self, filename: str):
        """
        2020-01-01 open Assets:Bank
        2020-01-01 open Assets:Account:Loan
        2020-01-01 open Assets:Account:Asset

        2020-01-02 price AA 15 GBP

        2020-01-02 * "transfer"
            Assets:Account:Loan  -6 GBP
            Assets:Account:Asset  1 AA {11 GBP}
            Assets:Bank  -5 GBP

        """
        split = get_split(filename)

        self.assertEqual(Inventory.from_string("5 GBP"), sum_inventories(split.contributions))

    @test_utils.docfile
    def test_asset_sold_loan_returned_and_rest_withdrawn(self, filename: str):
        """
        2020-01-01 open Assets:Bank
        2020-01-01 open Assets:Account:Loan
        2020-01-01 open Assets:Account:Asset

        2020-01-02 price AA 15 GBP

        2020-01-02 * "transfer"
            Assets:Account:Loan  6 GBP
            Assets:Account:Asset  -1 AA {11 GBP}
            Assets:Bank  5 GBP
        """
        split = get_split(filename)

        self.assertEqual(Inventory.from_string("-5 GBP"), sum_inventories(split.withdrawals))
