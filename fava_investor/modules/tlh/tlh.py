#!/usr/bin/env python3
"""Beancount Tax Loss Harvester"""

import fava_investor.modules.tlh.libtlh as libtlh
import beancountinvestorapi as api
import click
import tabulate


@click.command()
@click.argument('beancount-file', type=click.Path(exists=True), envvar='BEANCOUNT_FILE')
@click.option('--brief', help='Summary output', is_flag=True)
def tlh(beancount_file, brief):
    """Finds opportunities for tax loss harvesting in a beancount file.

       The BEANCOUNT_FILE environment variable can optionally be set instead of specifying the file on the
       command line.

       The configuration for this module is expected to be supplied as a custom directive like so in your
       beancount file:
        2010-01-01 custom "fava-extension" "fava_investor" "{
          'tlh' : { 'accounts_pattern': 'Assets:Investments:Taxable',
                    'loss_threshold': 0,
                    'wash_pattern': 'Assets:Investments',
                    'account_field': 2,
                    'tlh_partners_meta_label': 'a__tlh_partners',
                    'substantially_similars_meta_label': 'a__substsimilars',
           }}"

    """
    accapi = api.AccAPI(beancount_file, {})
    config = accapi.get_custom_config('tlh')
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


if __name__ == '__main__':
    tlh()
