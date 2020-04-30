import datetime
from pprint import pformat

from beancount import loader
from beancount.core import convert
from beancount.core.amount import Amount
from beancount.core.inventory import Inventory
from beancount.ops import validation
from beancount.utils import test_utils
from fava.core import FavaLedger

from fava_investor import sum_inventories, FavaInvestorAPI, get_balance_split_history
from fava_investor.modules.performance.split import build_price_map_with_fallback_to_cost


class SplitTestCase(test_utils.TestCase):
    def assertInventoriesSum(self, inventory_string, inventories: list):
        self.assertEqual(
            Inventory.from_string(inventory_string),
            sum_inventories(inventories),
            "Sum of given inventories does not match expected balance:\n"
            + pformat(inventories),
        )

    def assertInventory(self, expected_inventory_str, inventory):
        self.assertEqual(i(expected_inventory_str), inventory)

    def assertSumOfSplitsEqualValue(self, filename, account="Assets:Account"):
        ledger = get_ledger(filename)
        split = get_split(filename)
        final_value = get_value(
            ledger,
            build_price_map_with_fallback_to_cost(ledger.ledger.entries),
            account,
            ledger.ledger.entries[-1].date,
        )
        self.assertEqual(
            final_value,
            self.get_split_sum(split),
            f"Value of account {account} doesnt equal sum of splits. Splits: {self.get_readable_splits(split)}",
        )

    def assertSumOfSplitsEqual(self, filename, value):
        split = get_split(filename)
        self.assertEqual(
            self.get_split_sum(split),
            i(value),
            f"Sum of splits doesnt equal given inventory. Splits: {self.get_readable_splits(split)}",
        )

    def get_readable_splits(self, split):
        return (
                f"\ncontrib    {split.contributions}"
                + f"\nwithdrawal {split.withdrawals}"
                + f"\ndividends  {split.dividends}"
                + f"\ncosts      {split.costs}"
                + f"\ngains r.   {split.gains_realized}"
                + f"\ngains u.   {split.gains_unrealized}"
        )

    def get_split_sum(self, split):
        split_list = list(split)
        sum = sum_inventories([sum_inventories(s) for s in split_list])
        return sum


def get_ledger(filename):
    _, errors, _ = loader.load_file(
        filename, extra_validations=validation.HARDCORE_VALIDATIONS
    )
    if errors:
        raise ValueError("Errors in ledger file: \n" + pformat(errors))

    return FavaInvestorAPI(FavaLedger(filename))


def get_split(filename, config_override=None, interval=None):
    split = get_split_with_meta(filename, config_override, interval=interval)
    return split.parts


def get_split_with_meta(filename, config_override=None, interval=None):
    defaults = {
        "accounts_pattern": "^Assets:Account",
        "accounts_income_pattern": "^Income:",
        "accounts_expenses_pattern": "^Expenses:",
    }
    if not config_override:
        config_override = {}
    config = {**defaults, **config_override}
    ledger = get_ledger(filename)
    split = get_balance_split_history(
        ledger,
        config["accounts_pattern"],
        config["accounts_income_pattern"],
        config["accounts_expenses_pattern"],
        interval=interval
    )
    return split


def i(string=""):
    return Inventory.from_string(string)


def get_value(ledger, price_map, account, date):
    if isinstance(date, str):
        date = datetime.datetime.strptime(date, "%Y-%m-%d").date()
    balance = ledger.root_tree()[account].balance
    reduce = balance.reduce(convert.get_value, price_map, date)
    inv = Inventory()
    for key, value in reduce.items():
        inv.add_amount(Amount(value, key))

    return inv
