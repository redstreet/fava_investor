import re
from collections import namedtuple

Accounts = namedtuple("Accounts", "value internal external internalized")
Row = namedtuple("Row", "transaction change")


def filter_matching(accounts, patterns):
    result = set()
    for account in accounts:
        if _is_value_account(account, patterns):
            result.add(account)
    return result


def get_accounts_from_config(accapi, config) -> Accounts:
    accounts = accapi.accounts

    value = get_matching_accounts(accounts, config.get("accounts_pattern", "^Assets:.*"))
    internal = get_matching_accounts(accounts, config.get("accounts_internal_pattern", "^(Income|Expense):.*"))
    external = set(accounts).difference(value | internal)
    internalized = get_matching_accounts(accounts, config.get("accounts_internalized_pattern", "^Income:Dividends"))

    return Accounts(value, internal, external, internalized)


def _is_value_account(account, patterns):
    for pattern in patterns:
        if re.match(pattern, account):
            return True
    return False


def get_matching_accounts(accounts, pattern):
    return set([acc for acc in accounts if re.match(pattern, acc)])
