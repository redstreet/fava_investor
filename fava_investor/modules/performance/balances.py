import datetime
from typing import Dict, List, Union

from beancount.core import realization
from beancount.core.data import iter_entry_dates
from fava.core import FavaLedger
from util import pairwise
from util.date import Interval

ConfigDict = Dict[str, Union[str, List[str]]]


def filter_nested_accounts_dict(accounts_dict: Dict[str, Dict],
                                accounts_to_keep: List[str], prev:str = "") -> dict:
    """
    filters accounts_dict of following format:
    {
        Assets: {
            Bank: {
                BankA: {...},
                ... },
            Investment: {
                BrokerA: {...},
                ... }
            ... }
        ... }
    """
    for key in list(accounts_dict.keys()):
        str_begin = f"{prev}{key}"
        if str_begin not in [acc[:len(str_begin)] for acc in accounts_to_keep]:
            del accounts_dict[key]
        else:
            accounts_dict[key] = filter_nested_accounts_dict(accounts_dict[key], accounts_to_keep, prev + key + ":")

    return accounts_dict


def interval_balances(ledger: FavaLedger, accounts: List[str], interval: Interval,
                      account_name: str, accumulate=True, interval_count=3):
    """Balances by interval.

    Function copied from FavaLedger to add interval_count and account filtering

    TODO filter out closed accounts instead of displaying empty rows

    Arguments:
        interval: An interval.
        account_name: An account name.
        accumulate: A boolean, ``True`` if the balances for an interval
            should include all entries up to the end of the interval.

    Returns:
        A list of RealAccount instances for all the intervals.
    """

    interval_tuples = list(
        reversed(list(pairwise(ledger.interval_ends(interval))))
    )[:interval_count]

    interval_balances = [
        realization.realize(
            list(
                iter_entry_dates(
                    ledger.entries,
                    datetime.date.min if accumulate else begin_date,
                    end_date,
                )
            ),
            accounts,
        )
        for begin_date, end_date in interval_tuples
    ]

    for i in range(0, len(interval_balances)):
        interval_balances[i] = filter_nested_accounts_dict(interval_balances[i], accounts)

    return interval_balances, interval_tuples
