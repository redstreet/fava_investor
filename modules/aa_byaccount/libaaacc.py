#!/bin/env python3

import re

from beancount.core.data import iter_entry_dates, Open
from beancount.core.number import ZERO, Decimal

from fava.template_filters import cost_or_value
from fava.core.tree import Tree
from fava.core.helpers import FavaAPIException

def portfolio_accounts(tree, configs, ledger, end):
    """An account tree based on matching regex patterns."""

    portfolios = []
    for config in configs:
        pattern_type = config['pattern_type']
        func = globals()['by_' + pattern_type]
        portfolio = func(tree, end, config, ledger)
        portfolios.append(portfolio)

    return portfolios

def by_account_name(tree, date, config, ledger):
    """Returns portfolio info based on matching account name."""

    pattern = config['pattern']
    include_children = config.get('include_children', False)
    title = config.get('title', "Account names matching: '" + pattern + "'")

    selected_accounts = []
    regexer = re.compile(pattern)
    for acct in tree.keys():
        if regexer.match(acct) is not None and acct not in selected_accounts:
            selected_accounts.append(acct)

    selected_nodes = [tree[x] for x in selected_accounts]
    portfolio_data = _portfolio_data(selected_nodes, date, ledger, include_children)
    return title, portfolio_data

def by_account_open_metadata(tree, date, config, ledger):
    """ Returns portfolio info based on matching account open metadata. """

    metadata_key = config['metadata_key']
    pattern = config['pattern']
    title = config.get('title', 'Accounts with {} metadata matching {}'.format(metadata_key, pattern))

    selected_accounts = []
    regexer = re.compile(pattern)
    for entry in ledger.all_entries_by_type[Open]:
        if metadata_key in entry.meta and regexer.match(entry.meta[metadata_key]) is not None:
            selected_accounts.append(entry.account)

    selected_nodes = [tree[x] for x in selected_accounts]
    portfolio_data = _portfolio_data(selected_nodes, date, ledger, include_children)
    return title, portfolio_data

def _portfolio_data(nodes, date, ledger, include_children):
    """
    Turn a portfolio of tree nodes into querytable-style data.

    Args:
        nodes: Account tree nodes.
        date: Date.
    Return:
        types: Tuples of column names and types as strings.
        rows: Dictionaries of row data by column names.
    """
    operating_currency = ledger.options["operating_currency"][0]
    acct_type = ("account", str(str))
    bal_type = ("balance", str(Decimal))
    alloc_type = ("allocation %", str(Decimal))
    types = [acct_type, bal_type, alloc_type]

    rows = []
    for node in nodes:
        row = {}
        row["account"] = node.name
        balance = cost_or_value(node.balance_children, date) if include_children else cost_or_value(node.balance, date)
        if operating_currency in balance:
            row["balance"] = balance[operating_currency]
            rows.append(row)

    portfolio_total = sum(row['balance'] for row in rows)
    for row in rows:
        if "balance" in row:
            row["allocation %"] = round( (row["balance"] / portfolio_total) * 100, 1)

    return types, rows
