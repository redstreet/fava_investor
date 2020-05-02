#!/usr/bin/env python3
# Description: CLI for asset allocation

import libassetalloc
import clicommon
import beancountinvestorapi as api
from beancount.core import realization
from beancount.core import display_context
import argh
import argcomplete
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
        rows.append((' '*level+n.name, '{:,.0f}'.format(n.balance_children),
                     '{:.1f}%'.format(n.percentage_children)))

    print(tabulate.tabulate(rows,
                            headers=['asset_type', 'amount', 'percentage'],
                            colalign=('left', 'decimal', 'right'),
                            tablefmt='simple'))


@argh.arg('--accounts_patterns', nargs='+')
def asset_allocation(beancount_file,
                     accounts_patterns: 'Regex patterns of accounts to include in asset allocation.' = '',
                     dump_balances_tree=False,
                     skip_tax_adjustment=False,
                     debug=False):

    argsmap = locals()
    accapi = api.AccAPI(beancount_file, argsmap)
    if not accounts_patterns:
        del argsmap['accounts_patterns']
    asset_buckets_tree, realacc = libassetalloc.assetalloc(accapi, argsmap)

    ftree = formatted_tree(asset_buckets_tree)
    clicommon.pretty_print_table_bare(ftree)

    if dump_balances_tree:
        print_balances_tree(realacc, accapi)

# -----------------------------------------------------------------------------


def main():
    parser = argh.ArghParser(description="Beancount Asset Allocation Analyzer")
    argh.set_default_command(parser, asset_allocation)
    argh.completion.autocomplete(parser)
    parser.dispatch()
    return 0


if __name__ == '__main__':
    main()
