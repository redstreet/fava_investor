#!/usr/bin/env python3
# Description: CLI for asset allocation

import argparse,argcomplete,argh
import sys
import tabulate
tabulate.PRESERVE_WHITESPACE = True

from beancount.core import display_context
from beancount.core import realization

import beancountapi
import libassetalloc

def print_balances_tree(realacc, accapi):
    print()
    print('Account balances:')
    dformat = accapi.options_map['dcontext'].build(alignment=display_context.Align.DOT,
                                            reserved=2)
    realization.dump_balances(realacc, dformat, file=sys.stdout)

def print_asset_table(asset_buckets, headers, table):
    def tree_indent(a):
        splits = a.split('_')
        spaces = len(splits)
        return ' '*spaces + splits[-1]

    newtable = []
    total_assets = sum(asset_buckets[k] for k in asset_buckets)
    newtable.append(["total",
        '{:.1f}%'.format(100),
        '{:,.0f}'.format(total_assets) ])

    for row in table:
        newtable.append([' '*row[0] + row[1].split('_')[-1], 
            '{:.1f}%'.format(row[2]),
            '{:,.0f}'.format(row[3]) ])

    print(tabulate.tabulate(newtable, 
        headers=headers[1:],
        colalign=('left', 'decimal', 'right'),
        tablefmt='simple'))

@argh.arg('--accounts_pattern', nargs='+')
def asset_allocation(beancount_file,
    accounts_pattern: 'Regex patterns of accounts to include in asset allocation.' = '',
    base_currency='USD',
    dump_balances_tree=False,
    skip_tax_adjustment=False,
    debug=False):

    accapi = beancountapi.AccAPI(beancount_file)
    argsmap = locals()
    if not accounts_pattern:
        del argsmap['accounts_pattern']
    asset_buckets, tabulated_buckets, realacc = libassetalloc.assetalloc(accapi, argsmap)

    print_asset_table(asset_buckets, *tabulated_buckets)
    if dump_balances_tree:
        print_balances_tree(realacc, accapi)

#-----------------------------------------------------------------------------
def main():
    parser = argh.ArghParser(description="Beancount Asset Allocation Analyzer")
    argh.set_default_command(parser, asset_allocation)
    argh.completion.autocomplete(parser)
    parser.dispatch()
    return 0

if __name__ == '__main__':
    main()