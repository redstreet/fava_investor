#!/usr/bin/env python3
# Description: Beancount script for asset allocation reporting

import argparse,argcomplete,argh
import re
import sys

from collections import defaultdict
from dateutil.parser import parse
from tabulate import tabulate
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

    def is_included_account(realacc):
        for pattern in accounts:
            if re.match(pattern, realacc.account):
                return True
        return False

    realroot = realization.realize(entries)

    # first, filter out accounts that are not specified:
    realacc = realization.filter(realroot, is_included_account)

    # However, realacc includes all ancestor accounts of specified accounts, and their balances. For example,
    # if we specified 'Accounts:Investments:Brokerage', balances due to transactions on 'Accounts:Investments'
    # will also be included. We need to filter these out:
    for acc in realization.iter_children(realacc):
        if not is_included_account(acc):
            acc.balance = inventory.Inventory()

    balance = realization.compute_balance(realacc)
    vbalance = balance.reduce(convert.get_units)
    price_map = prices.build_price_map(entries)
    commodity_map = getters.get_commodity_map(entries)

    if show_balance:
        print(tabulate(vbalance.get_positions(), tablefmt='plain'))

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

    # Convert results into a pretty printed table
    # print(balance.reduce(convert.get_units))
    total_assets = sum(asset_buckets[k] for k in asset_buckets)
    max_width = max(len(k) for k in asset_buckets)
    table = []
    for a in asset_buckets:
        table.append([a,
            '{:.1f}%'.format((asset_buckets[a]/total_assets)*100),
            '{:,.0f}'.format(asset_buckets[a]) ])
            
    table.sort()
    table.append(['---', '---', '---'])
    table.append(["Total",
        '{:.1f}%'.format(100),
        '{:,.0f}'.format(total_assets) ])

    print(tabulate(table, 
        headers=['Asset Type', 'Percentage', 'Amount'], 
        colalign=('left', 'decimal', 'right'),
        tablefmt='simple'
        ))

    if dump_balances_tree:
        print()
        print('Account balances:')
        dformat = options_map['dcontext'].build(alignment=display_context.Align.DOT,
                                                reserved=2)
        realization.dump_balances(realacc, dformat, file=sys.stdout)

#-----------------------------------------------------------------------------
def main():
    parser = argh.ArghParser(description="Beancount Asset Allocation Analyzer")
    argh.set_default_command(parser, asset_allocation)
    argh.completion.autocomplete(parser)
    parser.dispatch()
    return 0

if __name__ == '__main__':
    main()
