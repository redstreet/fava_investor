import datetime
from pprint import pformat

from beancount import loader
from beancount.core import convert
from beancount.core.amount import Amount
from beancount.core.inventory import Inventory
from beancount.ops import validation
from beancount.utils import test_utils
from fava.core import FavaLedger

from fava_investor import sum_inventories, FavaInvestorAPI, calculate_interval_balances
from fava_investor.modules.performance.split import build_price_map_with_fallback_to_cost


def get_readable_split_parts(split_parts):
    return (
            f"\ncontrib    {split_parts.contributions}"
            + f"\nwithdrawal {split_parts.withdrawals}"
            + f"\ndividends  {split_parts.dividends}"
            + f"\ncosts      {split_parts.costs}"
            + f"\ngains r.   {split_parts.gains_realized}"
            + f"\ngains u.   {split_parts.gains_unrealized}"
    )


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
        split_parts = get_interval_balances(filename)
        final_value = get_value(
            ledger,
            build_price_map_with_fallback_to_cost(ledger.ledger.entries),
            account,
            ledger.ledger.entries[-1].date,
        )
        self.assertEqual(
            final_value,
            sum_inteval_balances(split_parts),
            f"Value of account {account} doesnt equal sum of splits. Splits: {get_readable_split_parts(split_parts)}",
        )

    def assertSumOfSplitsEqual(self, filename, value):
        interval_balances = get_interval_balances(filename)
        self.assertEqual(
            sum_inteval_balances(interval_balances),
            i(value),
            f"Sum of splits doesnt equal given inventory. Splits: {get_readable_split_parts(interval_balances)}",
        )


def get_ledger(filename):
    _, errors, _ = loader.load_file(
        filename, extra_validations=validation.HARDCORE_VALIDATIONS
    )
    if errors:
        raise ValueError("Errors in ledger file: \n" + pformat(errors))

    return FavaInvestorAPI(FavaLedger(filename))


def get_interval_balances(filename, config_override=None, interval=None):
    split = get_interval_balances_with_meta(filename, config_override, interval=interval)
    return split.parts


def get_interval_balances_with_meta(filename, config_override=None, interval=None):
    defaults = {
        "accounts_pattern": "^Assets:Account",
        "accounts_income_pattern": "^Income:",
        "accounts_expenses_pattern": "^Expenses:",
    }
    if not config_override:
        config_override = {}
    config = {**defaults, **config_override}
    ledger = get_ledger(filename)
    balances = calculate_interval_balances(
        ledger,
        ['contributions', 'withdrawals', 'costs', 'dividends', 'gains_realized', 'gains_unrealized'],
        config["accounts_pattern"],
        config["accounts_income_pattern"],
        config["accounts_expenses_pattern"],
        interval=interval
    )
    return balances


def sum_inteval_balances(balances):
    sum = Inventory()
    sum += sum_inventories(balances.contributions)
    sum += sum_inventories(balances.withdrawals)
    sum += sum_inventories(balances.costs)
    sum += sum_inventories(balances.dividends)
    sum += sum_inventories(balances.gains_realized)
    sum += sum_inventories(balances.gains_unrealized)
    return sum


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
