#!/usr/bin/env python3
# PYTHON_ARGCOMPLETE_OK
# Description: Beancount Tax Loss Harvester

import libtlh
import beancountinvestorapi as api
import argh
# import argcomplete
import tabulate
from datetime import datetime

def tlh(beancount_file,
        accounts_pattern='',
        loss_threshold=0,
        wash_pattern='',
        end_date=None,
        brief=False
        ):
    '''Finds opportunities for tax loss harvesting in a beancount file'''

    if end_date:
        end_date = datetime.fromisoformat(end_date).date()

    argsmap = locals()
    accapi = api.AccAPI(beancount_file, argsmap)

    config = {'accounts_pattern': accounts_pattern, 'loss_threshold': loss_threshold,
            'wash_pattern': wash_pattern}
    harvestable_table, summary, recents, by_commodity = libtlh.get_tables(accapi, config)
    dontbuy = libtlh.recently_sold_at_loss(accapi, config)
    to_sell_types, to_sell = harvestable_table

    def pretty_print(title, types, rows):
        if title:
            print(title)
        headers = [ts[0] for ts in types]
        if rows:
            print(tabulate.tabulate(rows, headers=headers))
        else:
            print('(empty table)')
        print()

    for k, v in summary.items():
        print("{:30}: {:>}".format(k, v))
    print()
    pretty_print("By commodity", *by_commodity)

    if not brief:
        pretty_print("Lot detail", *harvestable_table)
        pretty_print("Wash sale purchases:", *recents)
        print()
        pretty_print("What not to buy", dontbuy[0], dontbuy[1])

        warning = '''Note: Turn OFF dividend reinvestment for all these tickers across ALL accounts'''
        print(warning)
        print("See fava plugin for better formatted and sortable output.")

# -----------------------------------------------------------------------------


def main():
    parser = argh.ArghParser(description="Beancount Tax Loss Harvester")
    argh.set_default_command(parser, tlh)
    argh.completion.autocomplete(parser)
    parser.dispatch()


if __name__ == '__main__':
    main()
