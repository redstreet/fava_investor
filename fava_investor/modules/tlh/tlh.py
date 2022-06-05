#!/usr/bin/env python3
"""Beancount Tax Loss Harvester"""

import fava_investor.modules.tlh.libtlh as libtlh
import beancountinvestorapi as api
import click
import tabulate


@click.command()
@click.argument('beancount-file', type=click.Path(exists=True), envvar='BEANCOUNT_FILE')
@click.option('--accounts-pattern', help='Regex pattern of accounts to consider', default='')
@click.option('--loss-threshold', help='Loss threshold', default=0)
@click.option('--wash-pattern', help='Regex patterns of accounts to consider for wash sales. '
              'Include retirement accounts', default='')
@click.option('--brief', help='Summary output', is_flag=True)
def tlh(beancount_file, accounts_pattern, loss_threshold, wash_pattern, brief):
    """Finds opportunities for tax loss harvesting in a beancount file.
       The BEANCOUNT_FILE environment variable can optionally be set instead of specifying the file on the
       command line.
    """
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


if __name__ == '__main__':
    tlh()
