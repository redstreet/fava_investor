#!/bin/env python3

import re
from beancount.core.data import Open
from beancount.core.number import Decimal


def portfolio_accounts(accapi, configs):
    """An account tree based on matching regex patterns."""

    portfolios = []
    for config in configs:
        pattern_type = config['pattern_type']
        func = globals()['by_' + pattern_type]
        portfolio = func(accapi, config)
        portfolios.append(portfolio)

    return portfolios


def by_account_name(accapi, config):
    """Returns portfolio info based on matching account name."""

    tree = accapi.root_tree()
    pattern = config['pattern']
    include_children = config.get('include_children', False)
    title = config.get('title', "Account names matching: '" + pattern + "'")

    selected_accounts = []
    regexer = re.compile(pattern)
    for acct in tree.keys():
        if regexer.match(acct) is not None and acct not in selected_accounts:
            selected_accounts.append(acct)

    selected_nodes = [tree[x] for x in selected_accounts]
    portfolio_data = asset_allocation(selected_nodes, accapi, include_children)
    return title, portfolio_data


def by_account_open_metadata(accapi, config):
    """ Returns portfolio info based on matching account open metadata. """

    metadata_key = config['metadata_key']
    pattern = config['pattern']
    title = config.get('title', 'Accounts with {} metadata matching {}'.format(metadata_key, pattern))

    selected_accounts = []
    include_children = config.get('include_children', False)
    regexer = re.compile(pattern)
    for entry in accapi.all_entries_by_type[Open]:
        if metadata_key in entry.meta and regexer.match(entry.meta[metadata_key]) is not None:
            selected_accounts.append(entry.account)

    selected_nodes = [accapi.root_tree()[x] for x in selected_accounts]
    portfolio_data = asset_allocation(selected_nodes, accapi, include_children)
    return title, portfolio_data


def asset_allocation(nodes, accapi, include_children):
    """Compute percentage of assets in each of the given nodes."""

    date = accapi.end
    operating_currency = accapi.get_operating_currencies()[0]
    acct_type = ("account", str(str))
    bal_type = ("balance", str(Decimal))
    alloc_type = ("allocation %", str(Decimal))
    types = [acct_type, bal_type, alloc_type]

    rows = []
    for node in nodes:
        row = {'account': node.name}
        balance = accapi.cost_or_value(node, date, include_children)
        if operating_currency in balance:
            row["balance"] = balance[operating_currency]
            rows.append(row)

    portfolio_total = sum(row['balance'] for row in rows)
    for row in rows:
        if "balance" in row:
            row["allocation %"] = round((row["balance"] / portfolio_total) * 100, 1)

    return types, rows
