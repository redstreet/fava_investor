import copy
from collections import namedtuple

from beancount.core import convert
from beancount.core.amount import Amount
from beancount.core.data import Transaction
from beancount.core.inventory import Inventory

Accounts = namedtuple("Accounts", "value income expenses")


class ContributionAccumulator:
    def __init__(self, accounts: Accounts):
        self.accumulated = Inventory()
        self.accounts = accounts
        self.all_accounts = self.accounts.value | self.accounts.income | self.accounts.expenses

    def get_posting_filter_condition(self):
        return lambda posting: posting.units.number > 0

    def get_id(self):
        return 'contributions'

    def process(self, entry):
        value = any([p.account in self.accounts.value for p in entry.postings])
        external = any([p.account not in self.all_accounts for p in entry.postings])

        if not value or not external:
            return

        included = self.accounts.value | self.accounts.income | self.accounts.expenses
        relevant = get_postings_prefer_cost(entry, include_accounts=included)
        for position in relevant.get_positions():
            if self.get_posting_filter_condition()(position):
                self.accumulated.add_position(position)

    def get_result_and_reset(self):
        result = self.accumulated
        self.accumulated = Inventory()
        return result


class WithdrawalAccumulator(ContributionAccumulator):
    def get_posting_filter_condition(self):
        return lambda posting: posting.units.number < 0

    def get_id(self):
        return 'withdrawals'


class UnrealizedGainAccumulator:
    def __init__(self, accounts: Accounts, price_map):
        self.last_entry_date = None
        self.price_map = price_map
        self.gain = Inventory()
        self.balance = Inventory()
        self.accounts = accounts
        self.last_result = Inventory()

    def get_id(self):
        return 'gains_unrealized'

    def process(self, entry):
        for p in entry.postings:
            if p.account in self.accounts.value:
                self.balance.add_position(p)
        self.last_entry_date = entry.date

    def get_result_and_reset(self):
        current_value = self.balance.reduce(convert.get_value, self.price_map, self.last_entry_date)
        current_cost = self.balance.reduce(convert.get_cost)
        unrealized_gain = current_value + -current_cost
        self.gain += unrealized_gain + -self.last_result
        self.last_result = copy.copy(self.gain)
        result = self.gain
        self.gain = Inventory()
        return result


class CostAccumulator:
    def __init__(self, accounts: Accounts):
        self.costs = Inventory()
        self.accounts = accounts

    def get_id(self):
        return 'costs'

    def process(self, entry):
        value = any([p.account in self.accounts.value for p in entry.postings])
        expense = any([p.account in self.accounts.expenses for p in entry.postings])
        if value and expense:
            self.costs += -include_postings(entry, self.accounts.expenses)

    def get_result_and_reset(self):
        result = self.costs
        self.costs = Inventory()
        return result


class ValueChangeAccumulator:
    last_entry_date = None

    def __init__(self, accounts: Accounts, price_map):
        self.price_map = price_map
        self.balance = Inventory()
        self.accounts = accounts

    def get_id(self):
        return 'value_changes'

    def process(self, entry):
        for p in entry.postings:
            if p.account in self.accounts.value:
                self.balance.add_position(p)
        self.last_entry_date = entry.date

    def get_result_and_reset(self):
        value = self.balance.reduce(convert.get_value, self.price_map, self.last_entry_date)
        self.balance.clear()
        result = Inventory()
        for amount, _ in value:
            result.add_amount(amount)
        return result


class RealizedGainAccumulator:
    def __init__(self, accounts: Accounts):
        self.gains = Inventory()
        self.accounts = accounts

    def get_id(self):
        return 'gains_realized'

    def process(self, entry):
        value = any([p.account in self.accounts.value for p in entry.postings])
        income = any([p.account in self.accounts.income for p in entry.postings])
        if value and income and is_commodity_sale(entry, self.accounts.value):
            postings = include_postings(entry, self.accounts.income)
            self.gains += -postings

    def get_result_and_reset(self):
        result = self.gains
        self.gains = Inventory()
        return result


class DividendsAccumulator:
    def __init__(self, accounts: Accounts):
        self.dividends = Inventory()
        self.accounts = accounts
        self.all_accounts = self.accounts.value | self.accounts.income | self.accounts.expenses

    def get_id(self):
        return 'dividends'

    def process(self, entry):
        value = any([p.account in self.accounts.value for p in entry.postings])
        income = any([p.account in self.accounts.income for p in entry.postings])
        external = any([p.account not in self.all_accounts for p in entry.postings])

        if (value and income and not is_commodity_sale(entry, self.accounts.value)) or (
                not value and income and external
        ):
            self.dividends += -include_postings(
                entry,
                self.accounts.income,
                lambda_filter=lambda posting: posting.units.number < 0,
            )

    def get_result_and_reset(self):
        result = self.dividends
        self.dividends = Inventory()
        return result


def include_postings(
        transaction, include_accounts=None, exclude_accounts=None, lambda_filter=None
):
    exclude_accounts = exclude_accounts if exclude_accounts else []
    lambda_filter = lambda_filter if lambda_filter is not None else lambda x: True
    inventory = Inventory()

    for posting in transaction.postings:
        if (
                (include_accounts is None or posting.account in include_accounts)
                and posting.account not in exclude_accounts
                and lambda_filter(posting)
        ):
            inventory.add_position(posting)

    return inventory


def get_postings_prefer_cost(
        transaction, include_accounts=None, exclude_accounts=None, lambda_filter=None
):
    exclude_accounts = exclude_accounts if exclude_accounts else []
    lambda_filter = lambda_filter if lambda_filter is not None else lambda x: True
    inventory = Inventory()

    for posting in transaction.postings:
        if (
                (include_accounts is None or posting.account in include_accounts)
                and posting.account not in exclude_accounts
                and lambda_filter(posting)
        ):
            if posting.cost is not None:
                number = posting.cost.number * posting.units.number
                inventory.add_amount(Amount(number, posting.cost.currency))
            else:
                inventory.add_position(posting)

    return inventory


def is_commodity_sale(entry: Transaction, value_accounts):
    for posting in entry.postings:
        if posting.account not in value_accounts:
            continue
        if posting.units.number < 0 and posting.cost is not None:
            return True
    return False
