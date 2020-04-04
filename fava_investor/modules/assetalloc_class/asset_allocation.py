#!/usr/bin/env python3
# Description: Beancount script for asset allocation reporting

from beancount import loader
import argparse,argcomplete,argh
import libassetalloc

entries = None
options_map = None
argsmap = {}
def init_entries(beancount_file, args):
    global entries
    global options_map
    global argsmap
    entries, _, options_map = loader.load_file(beancount_file)

@argh.arg('--accounts_pattern', nargs='+')
def asset_allocation(beancount_file,
    accounts_pattern: 'Regex patterns of accounts to include in asset allocation.' = '',
    base_currency='USD',
    dump_balances_tree=False,
    skip_tax_adjustment=False,
    debug=False):

    global argsmap
    argsmap = locals()
    init_entries(beancount_file, argsmap)


    def query_func(sql):
        rtypes, rrows = query.run_query(entries, options_map, sql)
        return rtypes, rrows

    if not accounts_pattern:
        del argsmap['accounts_pattern']
    libassetalloc.assetalloc(entries, options_map, query_func, argsmap)



#-----------------------------------------------------------------------------
def main():
    parser = argh.ArghParser(description="Beancount Asset Allocation Analyzer")
    argh.set_default_command(parser, asset_allocation)
    argh.completion.autocomplete(parser)
    parser.dispatch()
    return 0

if __name__ == '__main__':
    main()
