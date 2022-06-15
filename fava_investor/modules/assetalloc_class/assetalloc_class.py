#!/usr/bin/env python3
# Description: CLI for asset allocation

import fava_investor.modules.assetalloc_class.libassetalloc as libassetalloc
import beancountinvestorapi as api
from beancount.core import realization
from beancount.core import display_context
import click
import os
import sys
import tabulate
tabulate.PRESERVE_WHITESPACE = True


sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', 'common'))


def print_balances_tree(realacc, accapi):
    print()
    print('Account balances:')
    dformat = accapi.options_map['dcontext'].build(alignment=display_context.Align.DOT,
                                                   reserved=2)
    realization.dump_balances(realacc, dformat, file=sys.stdout)


def formatted_tree(root):
    rows = []
    for n, level in root.pre_order(0):
        rows.append((' ' * level + n.name, '{:,.0f}'.format(n.balance_children),
                     '{:.1f}%'.format(n.percentage_children)))

    return tabulate.tabulate(rows,
                             headers=['asset_type', 'amount', 'percentage'],
                             colalign=('left', 'decimal', 'right'),
                             tablefmt='simple')


@click.command()
@click.argument('beancount-file', type=click.Path(exists=True), envvar='BEANCOUNT_FILE')
@click.option('-d', '--dump-balances-tree', help='Show tree', is_flag=True)
def assetalloc_class(beancount_file, dump_balances_tree):
    """Beancount Asset Allocation Analyzer.

       The BEANCOUNT_FILE environment variable can optionally be set instead of specifying the file on the
       command line.

       The configuration for this module is expected to be supplied as a custom directive like so in your
       beancount file:

       \b
        2010-01-01 custom "fava-extension" "fava_investor" "{
          'asset_alloc_by_class' : {
              'accounts_patterns': ['Assets:(Investments|Banks)'],
              'skip-tax-adjustment': True,
          }}"
    """
    accapi = api.AccAPI(beancount_file, {})
    config = accapi.get_custom_config('asset_alloc_by_class')
    asset_buckets_tree, realacc = libassetalloc.assetalloc(accapi, config)

    click.echo_via_pager(formatted_tree(asset_buckets_tree))

    if dump_balances_tree:
        print_balances_tree(realacc, accapi)


if __name__ == '__main__':
    assetalloc_class()
