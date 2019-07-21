#!/usr/bin/env python3
# Description: Beancount script for asset allocation reporting

import argparse,argcomplete,argh
import re
import sys

from collections import defaultdict
from dateutil.parser import parse
import tabulate
tabulate.PRESERVE_WHITESPACE = True
from types import SimpleNamespace

from beancount import loader
from beancount.core import convert
from beancount.core import display_context
from beancount.core import getters
from beancount.core import inventory
from beancount.core import prices
from beancount.core import realization
from beancount.core.number import Decimal

entries = None
options_map = None
argsmap = {}
def init_entries(filename, args):
    global entries
    global options_map
    global argsmap
    entries, _, options_map = loader.load_file(filename)
    argsmap = SimpleNamespace(**args)

def bucketize(vbalance, base_currency, entries):
    price_map = prices.build_price_map(entries)
    commodity_map = getters.get_commodity_map(entries)

    # Main part: put each commodity's value into asset buckets
    asset_buckets = defaultdict(int)
    for pos in vbalance.get_positions():
        amount = convert.convert_position(pos, base_currency, price_map)
        if amount.number < 0:
            # print("Warning: skipping negative balance:", pos) #TODO
            continue
        if amount.currency == pos.units.currency and amount.currency != base_currency:
            sys.stderr.write("Error: unable to convert {} to base currency {} (Missing price directive?)\n".format(pos, base_currency))
            sys.exit(1)
        commodity = pos.units.currency
        metas = commodity_map[commodity].meta
        unallocated = Decimal('100')
        for meta in metas:
            if meta.startswith('asset_allocation_'):
                asset_buckets[meta[len('asset_allocation_'):]] += amount.number * (metas[meta] / 100)
                unallocated -= metas[meta]
        if unallocated:
            print("Warning: {} asset_allocation_* metadata does not add up to 100%. Padding with 'unknown'.".format(commodity))
            asset_buckets['unknown'] += amount.number * (unallocated / 100)
    return asset_buckets

def compute_percent(asset_buckets, asset):
    total_assets = sum(asset_buckets[k] for k in asset_buckets)
    return (asset_buckets[asset]/total_assets)*100

def compute_percent_subtotal(asset_buckets, asset):
    total_assets = sum(asset_buckets[k] for k in asset_buckets)
    return (compute_balance_subtotal(asset_buckets, asset) / total_assets) * 100

def compute_balance_subtotal(asset_buckets, asset):
    children = [k for k in asset_buckets.keys() if k.startswith(asset) and k != asset]
    subtotal = asset_buckets[asset]
    for c in children:
        subtotal += compute_balance_subtotal(asset_buckets, c)
    return subtotal

def tree_indent(a):
    splits = a.split('_')
    spaces = len(splits)
    return ' '*spaces + splits[-1]

def pretty_print_buckets(asset_buckets):
    # Convert results into a pretty printed table
    # print(balance.reduce(convert.get_units))

    table = []
    total_assets = sum(asset_buckets[k] for k in asset_buckets)
    table.append(["total",
        '{:.1f}%'.format(100),
        '{:,.0f}'.format(total_assets) ])

    max_width = max(len(k) for k in asset_buckets)
    buckets = list(asset_buckets.keys())
    buckets.sort()
    for a in buckets:
        table.append([tree_indent(a),
            '{:.1f}%'.format(compute_percent_subtotal(asset_buckets, a)),
            '{:,.0f}'.format(compute_balance_subtotal(asset_buckets, a)) ])
            
    print(tabulate.tabulate(table, 
        headers=['Asset Type', 'Percentage', 'Amount'], 
        colalign=('left', 'decimal', 'right'),
        tablefmt='simple'
        ))

def build_interesting_realacc(entries, accounts):
    def is_included_account(realacc):
        for pattern in accounts:
            if re.match(pattern, realacc.account):
                return True
        return False

    realroot = realization.realize(entries)

    # first, filter out accounts that are not specified:
    realacc = realization.filter(realroot, is_included_account)

    if not realacc:
        sys.stderr.write("No included accounts found. (Your --accounts <regex> failed to match any account)\n")
        sys.exit(1)

    # However, realacc includes all ancestor accounts of specified accounts, and their balances. For example,
    # if we specified 'Accounts:Investments:Brokerage', balances due to transactions on 'Accounts:Investments'
    # will also be included. We need to filter these out:
    for acc in realization.iter_children(realacc):
        if not is_included_account(acc):
            acc.balance = inventory.Inventory()
    return realacc


def print_balances_tree(realacc):
    print()
    print('Account balances:')
    dformat = options_map['dcontext'].build(alignment=display_context.Align.DOT,
                                            reserved=2)
    realization.dump_balances(realacc, dformat, file=sys.stdout)

@argh.arg('--accounts', nargs='+')
def asset_allocation(filename,
    accounts: 'Regex patterns of accounts to include in asset allocation.' = '',
    base_currency='USD',
    show_balance=False,
    dump_balances_tree=False,
    debug=False):

    if not accounts:
        accounts = ['.*']
    global argsmap
    argsmap = locals()
    init_entries(filename, argsmap)

    realacc = build_interesting_realacc(entries, accounts)
    balance = realization.compute_balance(realacc)
    vbalance = balance.reduce(convert.get_units)

    if show_balance:
        print(tabulate.tabulate(vbalance.get_positions(), tablefmt='plain'))

    asset_buckets = bucketize(vbalance, base_currency, entries)

    # print output
    pretty_print_buckets(asset_buckets)
    if dump_balances_tree:
        print_balances_tree(realacc)

#-----------------------------------------------------------------------------
def main():
    parser = argh.ArghParser(description="Beancount Asset Allocation Analyzer")
    argh.set_default_command(parser, asset_allocation)
    argh.completion.autocomplete(parser)
    parser.dispatch()
    return 0

if __name__ == '__main__':
    main()
