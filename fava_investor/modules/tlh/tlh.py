#!/usr/bin/env python3
# Description: Beancount Tax Loss Harvester

from beancount import loader
from beancount.query import query

import argparse,argcomplete,argh
import pickle
from types import SimpleNamespace
import tabulate

import libtlh

entries = None
options_map = None
argsmap = {}
def init_entries(beancount_file, args):
    global entries
    global options_map
    global argsmap
    entries, _, options_map = loader.load_file(beancount_file)
    argsmap = SimpleNamespace(**args)

def tlh(beancount_file,
        accounts_pattern='',
        loss_threshold=10,
        wash_pattern = '',
        brief=False
        ):
    '''Finds opportunities for tax loss harvesting in a beancount file'''
    global argsmap
    argsmap = locals()
    init_entries(beancount_file, argsmap)

    def query_func(sql):
        rtypes, rrows = query.run_query(entries, options_map, sql)
        return rtypes, rrows

    config = {'accounts_pattern': accounts_pattern, 'loss_threshold': loss_threshold,
            'wash_pattern':wash_pattern}
    harvestable_table, summary, recents, by_commodity = libtlh.get_tables(query_func, config)
    to_sell_types, to_sell = harvestable_table

    def pretty_print(title, types, rows):
        if title:
            print(title)
        headers = [l[0] for l in types]
        print(tabulate.tabulate(rows, headers=headers))
        print()

    for k, v in summary.items():
        print("{:30}: {:>}".format(k, v))
    print()
    pretty_print("By commodity", *by_commodity)

    if not brief:
        pretty_print("Lot detail", *harvestable_table)
        pretty_print("Wash sale purchases:", *recents)
        print("See fava plugin for better formatted and sortable output.")
        warning = '''Note:
        1) Do NOT repurchase tickers within 30 days to avoid a wash sale.
        2) Turn OFF dividend reinvestment for all these tickers across ALL accounts
        '''
        print()
        print(warning)

#-----------------------------------------------------------------------------
def main():
    parser = argh.ArghParser(description="Beancount Tax Loss Harvester")
    argh.set_default_command(parser, tlh)
    argh.completion.autocomplete(parser)
    parser.dispatch()

if __name__ == '__main__':
    main()
