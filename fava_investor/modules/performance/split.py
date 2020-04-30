import copy
import re
from collections import namedtuple

from beancount.core.amount import Amount
from beancount.core.data import Transaction, Price
from beancount.core.inventory import Inventory
from beancount.core.prices import build_price_map
from fava.util.date import Interval, interval_ends

from fava_investor.modules.performance.accumulators import UnrealizedGainAccumulator, CostAccumulator, \
    ValueChangeAccumulator, \
    RealizedGainAccumulator, DividendsAccumulator, ContributionAccumulator, Accounts, WithdrawalAccumulator

Split = namedtuple("Split", "transactions parts")
IntervalBalances = namedtuple(
    "IntervalBalances",
    "contributions withdrawals dividends costs gains_realized gains_unrealized value_changes errors",
)
Change = namedtuple("Change", "transaction change")


def collect_results(accumulators, split_entries):
    for a in accumulators:
        getattr(split_entries, a.get_id()).append(a.get_result_and_reset())


def calculate_interval_balances(
        accapi,
        accumulators_ids,
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
    if has_prices_after_last_transaction(entries):
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

    split_entries = IntervalBalances([], [], [], [], [], [], [], [])
    split = Split([], split_entries)

    accounts = Accounts(accounts_value, accounts_income, accounts_expenses)
    accumulators = get_accumulators(accounts, entries, accumulators_ids)

    first = True
    for entry in entries:
        if not isinstance(entry, Transaction):
            continue
        split.transactions.append(entry)

        if first is False and (interval is None or entry.date > next_interval_start):
            if interval is not None:
                next_interval_start = dates[0]
                dates = dates[1:]

            collect_results(accumulators, split_entries)

        for accum in accumulators:
            accum.process(entry)

        first = False

    collect_results(accumulators, split_entries)

    return split


def get_accumulators(accounts, entries, ids):
    price_map = build_price_map_with_fallback_to_cost(entries)
    accs = {
        'contributions': lambda: ContributionAccumulator(accounts),
        'withdrawals': lambda: WithdrawalAccumulator(accounts),
        'dividends': lambda: DividendsAccumulator(accounts),
        'gains_realized': lambda: RealizedGainAccumulator(accounts),
        'costs': lambda: CostAccumulator(accounts),
        'gains_unrealized': lambda: UnrealizedGainAccumulator(accounts, price_map),
        'valuations': lambda: ValueChangeAccumulator(accounts, price_map),
    }

    return list([accs[key]() for key in ids])


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


def has_prices_after_last_transaction(entries):
    has_prices_after_last_transaction = False
    for entry in reversed(entries):
        if isinstance(entry, Price):
            has_prices_after_last_transaction = True

        if isinstance(entry, Transaction):
            return has_prices_after_last_transaction
