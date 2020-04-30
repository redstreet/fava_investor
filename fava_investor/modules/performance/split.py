import copy
import re
from collections import namedtuple

from beancount.core.amount import Amount
from beancount.core.data import Transaction, Price
from beancount.core.inventory import Inventory
from beancount.core.prices import build_price_map
from fava.util.date import Interval, interval_ends

from fava_investor.modules.performance.accumulators import UnrealizedGainProcessor, CostProcessor, ValueProcessor, \
    RealizedGainProcessor, DividendsProcessor, ContributionProcessor, Accounts

Split = namedtuple("Split", "transactions values parts")
SplitEntries = namedtuple(
    "SplitEntries",
    "contributions withdrawals dividends costs gains_realized gains_unrealized",
)
Change = namedtuple("Change", "transaction change")


def get_balance_split_history(
        accapi,
        pattern_value,
        income_pattern="^Income:",
        expenses_pattern="^Expenses:",
        interval=Interval.MONTH
):
    accounts = accapi.accounts
    accounts_value = set([acc for acc in accounts if re.match(pattern_value, acc)])
    accounts_expenses = set(
        [acc for acc in accounts if re.match(expenses_pattern, acc)]
    )
    accounts_income = set([acc for acc in accounts if re.match(income_pattern, acc)])

    entries = accapi.ledger.entries
    if needs_dummy_transaction(entries):
        date = copy.copy(entries[-1].date)
        entries.append(
            Transaction(
                None, date, None, None, "UNREALIZED GAINS NEW BALANCE", [], [], []
            )
        )

    next_interval_start = None
    if interval is not None:
        dates = list(interval_ends(entries[0].date, entries[-1].date, interval))
        if len(dates) == 1:
            dates.append(dates[0])
        next_interval_start = dates[1]
        dates = dates[2:]

    split_entries = SplitEntries([], [], [], [], [], [])
    split = Split([], [], split_entries)

    price_map = build_price_map_with_fallback_to_cost(entries)

    accounts = Accounts(accounts_value, accounts_income, accounts_expenses)
    contribution_processor = ContributionProcessor(accounts)
    dividends_processor = DividendsProcessor(accounts)
    gains_processor = RealizedGainProcessor(accounts)
    costs_processor = CostProcessor(accounts)

    ug_processor = UnrealizedGainProcessor(accounts, price_map)
    value_processor = ValueProcessor(accounts, price_map)

    first = True
    for entry in entries:
        if not isinstance(entry, Transaction):
            continue
        split.transactions.append(entry)

        if first is False and (interval is None or entry.date > next_interval_start):
            if interval is not None:
                next_interval_start = dates[0]
                dates = dates[1:]
            contributions, withdrawals = contribution_processor.get_result_and_reset()
            dividends = dividends_processor.get_result_and_reset()
            costs = costs_processor.get_result_and_reset()
            unrealized_gain_change = ug_processor.get_result_and_reset()
            gains_realized = gains_processor.get_result_and_reset()
            value = value_processor.get_result_and_reset()
            split_entries.contributions.append(contributions)
            split_entries.withdrawals.append(withdrawals)
            split_entries.dividends.append(dividends)
            split_entries.costs.append(costs)
            split_entries.gains_realized.append(gains_realized)
            split_entries.gains_unrealized.append(unrealized_gain_change)
            split.values.append(value)

        contribution_processor.process(entry)
        dividends_processor.process(entry)
        gains_processor.process(entry)
        costs_processor.process(entry)
        ug_processor.process(entry)
        value_processor.process(entry)

        first = False

    contributions, withdrawals = contribution_processor.get_result_and_reset()
    dividends = dividends_processor.get_result_and_reset()
    costs = costs_processor.get_result_and_reset()
    gains_realized = gains_processor.get_result_and_reset()
    ug = ug_processor.get_result_and_reset()
    value = value_processor.get_result_and_reset()

    split_entries.contributions.append(contributions)
    split_entries.withdrawals.append(withdrawals)
    split_entries.dividends.append(dividends)
    split_entries.costs.append(costs)
    split_entries.gains_realized.append(gains_realized)
    split_entries.gains_unrealized.append(ug)
    split.values.append(value)

    return split


def sum_inventories(inv_list):
    sum = Inventory()
    for inv in inv_list:
        sum += inv
    return sum


def calculate_balances(inventories):
    if len(inventories) == 0:
        return []
    result = []
    balance = Inventory()
    for inv in inventories:
        balance += inv
        result.append(copy.copy(balance))
    return result


def build_price_map_with_fallback_to_cost(entries):
    """
    Default price map does not contain purchase price from buying transaction. Beancount fails to calculate value
     unless there is price entry with same or earlier date. This function adds price entries from transaction
     if there isn't one for purchased commodity on purchase date or earlier.
    """
    buying_prices = {}
    first_price_date = {}
    prices = set()

    for entry in entries:
        if isinstance(entry, Price):
            first_price_date[(entry.currency, entry.amount.currency)] = entry.date
            prices.add((entry.currency, entry.amount.currency))

        if not isinstance(entry, Transaction):
            continue

        for p in entry.postings:
            if (
                    p.cost is not None
                    and p.units is not None
                    and (p.units.currency, p.cost.currency) not in prices
            ):
                key = (p.units.currency, p.cost.currency)
                if key in buying_prices:
                    continue
                buying_prices[key] = Price(
                    {},
                    entry.date,
                    p.units.currency,
                    Amount(p.units.number / p.cost.number, p.cost.currency),
                )

    prices_to_add = []
    for key, price in buying_prices.items():
        if key not in first_price_date or first_price_date[key] > price.date:
            first_price_date[key] = price.date
            prices_to_add.append(price)

    return build_price_map(entries + prices_to_add)


def needs_dummy_transaction(entries):
    has_prices_after_last_transaction = False
    for entry in reversed(entries):
        if isinstance(entry, Price):
            has_prices_after_last_transaction = True
        if isinstance(entry, Transaction):
            return has_prices_after_last_transaction
