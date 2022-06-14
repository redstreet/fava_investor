#!/bin/env python3
"""Metadata summarizer library for Beancount. See accompanying README.md for documentation."""

import collections
import re
import fava_investor.common.libinvestor as libinvestor
from beancount.core.data import Close
from beancount.core import realization
from beancount.core import convert
from fava_investor.common.libinvestor import build_table_footer


# TODO:
# - print balances nicely, sort by them, show what percent is complete
#   - for each commodity_leaf account, ensure there is a parent, else print

p_leaf = re.compile('^[A-Z0-9]*$')


def get_active_commodities(accapi):
    sql = """
    SELECT
    units(sum(position)) as units,
    value(sum(position)) as market_value
    WHERE account_sortkey(account) ~ "^[01]"
    GROUP BY currency, cost_currency
    ORDER BY currency, cost_currency
    """
    rtypes, rrows = accapi.query_func(sql)
    retval = {r.units.get_only_position().units.currency: r.market_value for r in rrows if not r.units.is_empty()}
    return retval


def order_and_rename(header, options):
    """Order the header according to the config, and replace col names with col labels"""
    # take advantage of python 3.7+'s insertion order preservation

    def get_col_label(c):
        if 'col_labels' in options:
            index = options['columns'].index(c)
            return options['col_labels'][index]
        return c

    retval = {}
    for c in options['columns']:
        if c in header:
            retval[get_col_label(c)] = header[c]

    return retval


def is_commodity_leaf(acc, ocs):
    splits = acc.rsplit(':', maxsplit=1)
    parent = splits[0]
    leaf = splits[-1]
    is_commodity = p_leaf.match(leaf)
    if is_commodity:
        return parent in ocs
    return False


def build_tables(accapi, configs):
    tables = []
    for config in configs:
        table = build_table(accapi, config)
        tables.append(table)
    return tables


def build_table(accapi, options):
    if options['directive_type'] == 'accounts':
        rows = active_accounts_metadata(accapi, options)
    elif options['directive_type'] == 'commodities':
        rows = commodities_metadata(accapi, options)

    all_keys_and_types = {j: type(i[j]) for i in rows for j in list(i)}
    header = order_and_rename(all_keys_and_types, options)

    # rename each row's keys to col_labels
    if 'col_labels' in options:
        for i in range(len(rows)):
            rows[i] = order_and_rename(rows[i], options)

    # add all keys to all rows
    for i in rows:
        for j in header:
            if j not in i:
                i[j] = ''  # TODO: type could be incorrect

    RowTuple = collections.namedtuple('RowTuple', header)
    rows = [RowTuple(**i) for i in rows]
    rtypes = list(header.items())

    # sort by the requested. Default to first column
    sort_col = options.get('sort_by', 0)
    reverse = options.get('sort_reverse', False)
    rows.sort(key=lambda x: x[sort_col], reverse=reverse)

    footer = None if 'no_footer' in options else build_table_footer(rtypes, rows, accapi)
    return options['title'], (rtypes, rows, None, footer)
    # last one is footer


def commodities_metadata(accapi, options):
    """Build list of commodities"""

    commodities = accapi.get_commodity_directives()
    if 'active_only' in options and options['active_only']:
        active_commodities = get_active_commodities(accapi)
        commodities = {k: v for k, v in commodities.items() if k in active_commodities}

    retval = []
    for co in commodities:
        row = {k: v for k, v in commodities[co].meta.items() if k in options['columns']}
        if 'ticker' in options['columns']:
            row['ticker'] = co
        if 'market_value' in options['columns']:
            row['market_value'] = active_commodities[co]
        retval.append(row)

    return retval


def get_metadata(meta, meta_prefix, specified_cols):
    ml = len(meta_prefix)
    if not specified_cols:  # get all metadata that matches meta_prefix
        row = {k[ml:]: v for (k, v) in meta.items() if meta_prefix in k}
    else:  # get metadata that begins with meta_prefix and is in specified_cols
        cols_to_get = [meta_prefix + col for col in specified_cols]
        row = {k[ml:]: v for (k, v) in meta.items() if k in cols_to_get}
    return row


def active_accounts_metadata(accapi, options):
    """Build metadata table for accounts that are open"""

    # balances = get_balances(accapi)
    realacc = accapi.realize()
    pm = accapi.build_price_map()
    currency = accapi.get_operating_currencies()[0]

    p_acc_pattern = re.compile(options['acc_pattern'])
    meta_prefix = options.get('meta_prefix', '')
    specified_cols = options.get('columns', [])
    meta_skip = options.get('meta_skip', '')
    retval = []

    # special metadata
    add_account = 'account' in options.get('columns', ['account'])
    add_balance = 'balance' in options.get('columns', ['balance'])
    ocs = accapi.get_account_open_close()
    for acc in ocs.keys():
        if p_acc_pattern.match(acc) and not is_commodity_leaf(acc, ocs):
            closes = [e for e in ocs[acc] if isinstance(e, Close)]
            if not closes:
                if meta_skip not in ocs[acc][0].meta:
                    row = get_metadata(ocs[acc][0].meta, meta_prefix, specified_cols)
                    if add_account:
                        row['account'] = acc
                    if add_balance:
                        row['balance'] = get_balance(realacc, acc, pm, currency)
                    retval.append(row)
    return retval


def get_balance(realacc, account, pm, currency):
    subtree = realization.get(realacc, account)
    balance = realization.compute_balance(subtree)
    vbalance = balance.reduce(convert.get_units)
    market_value = vbalance.reduce(convert.convert_position, currency, pm)
    val = libinvestor.val(market_value)
    return val
    # return int(val)


def get_balances(accapi):
    """Find all balances"""

    currency = accapi.get_operating_currencies()[0]
    sql = f"SELECT account, SUM(CONVERT(position, '{currency}'))"
    rtypes, rrows = accapi.query_func(sql)

    if not rtypes:
        return [], {}, [[]]
    # print(rtypes)
    # print(rrows)

    balances = {acc: bal for acc, bal in rrows}
    # import pdb; pdb.set_trace()
    # return rtypes, rrows, balances
    return balances

    # footer = libinvestor.build_table_footer(rtypes, rrows, accapi)
    # return rtypes, rrows, None, footer
