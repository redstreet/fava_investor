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
from beancount.core import amount
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

def compute_percent(asset_buckets, asset, total_assets):
    return (asset_buckets[asset]/total_assets)*100

def compute_percent_subtotal(asset_buckets, asset, total_assets):
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

def tabulate_asset_buckets(asset_buckets):
    ''' Convert asset allocation into a hierarchical tabulation '''
    # print(balance.reduce(convert.get_units))

    table = []
    total_assets = sum(asset_buckets[k] for k in asset_buckets)
    table.append(["total",
        '{:.1f}%'.format(100),
        '{:,.0f}'.format(total_assets) ])

    max_width = max(len(k) for k in asset_buckets)
    buckets = list(asset_buckets.keys())

    # add all parents in the asset allocation hierarchy
    parents = set()
    for b in buckets:
        for i in range(1, b.count('_')+1):
            parents.add( b.rsplit('_', i)[0] )
    buckets = list(set(list(parents) + buckets))

    buckets.sort()
    for a in buckets:
        table.append([tree_indent(a),
            '{:.1f}%'.format(compute_percent_subtotal(asset_buckets, a, total_assets)),
            '{:,.0f}'.format(compute_balance_subtotal(asset_buckets, a)) ])
            
    return tabulate.tabulate(table, 
        headers=['Asset Type', 'Percentage', 'Amount'], 
        colalign=('left', 'decimal', 'right'),
        tablefmt='simple')

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

def scale_inventory(balance, tax_adj):
    '''Scale inventory by tax adjustment'''
    scaled_balance = inventory.Inventory()
    for pos in balance.get_positions():
        scaled_pos = amount.Amount(pos.units.number * (Decimal(tax_adj/100)), pos.units.currency)
        scaled_balance.add_amount(scaled_pos)
    return scaled_balance


def tax_adjust(realacc):
    account_open_close = getters.get_account_open_close(entries)
    for acc in realization.iter_children(realacc):
        if acc.account in account_open_close:
            tax_adj = account_open_close[acc.account][0].meta.get('asset_allocation_tax_adjustment', 100)
            acc.balance = scale_inventory(acc.balance, tax_adj)
    return realacc

@argh.arg('--accounts', nargs='+')
def asset_allocation(filename,
    accounts: 'Regex patterns of accounts to include in asset allocation.' = '',
    base_currency='USD',
    dump_balances_tree=False,
    skip_tax_adjustment=False,
    debug=False):

    if not accounts:
        accounts = ['.*']
    global argsmap
    argsmap = locals()
    init_entries(filename, argsmap)

    realacc = build_interesting_realacc(entries, accounts)
    if not skip_tax_adjustment:
        tax_adjust(realacc)
    balance = realization.compute_balance(realacc)
    vbalance = balance.reduce(convert.get_units)
    asset_buckets = bucketize(vbalance, base_currency, entries)

    # print output
    print(tabulate_asset_buckets(asset_buckets))
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
