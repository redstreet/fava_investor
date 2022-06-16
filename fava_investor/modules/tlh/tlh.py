#!/usr/bin/env python3
"""Beancount Tax Loss Harvester"""

import fava_investor.modules.tlh.libtlh as libtlh
import fava_investor.common.beancountinvestorapi as api
from fava_investor.common.clicommon import pretty_print_table
import click


@click.command()
@click.argument('beancount-file', type=click.Path(exists=True), envvar='BEANCOUNT_FILE')
@click.option('--brief', help='Summary output', is_flag=True)
def tlh(beancount_file, brief):
    """Finds opportunities for tax loss harvesting in a beancount file.

       The BEANCOUNT_FILE environment variable can optionally be set instead of specifying the file on the
       command line.

       The configuration for this module is expected to be supplied as a custom directive like so in your
       beancount file:

       \b
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

    def _gen_output():
        yield click.style("Summary" + '\n', bg='green', fg='white')
        for k, v in summary.items():
            yield "{:30}: {:>}\n".format(k, v)
        yield '\n'
        yield pretty_print_table("Losses by commodity", *by_commodity)

        if not brief:
            yield pretty_print_table("Candidates for tax loss harvesting", *harvestable_table)
            yield pretty_print_table("What not to sell: recent purchases that would cause wash sales", *recents)
            yield pretty_print_table("What not to buy (sales within the last 30 days with losses)", dontbuy[0], dontbuy[1])

            yield "Note: Turn OFF dividend reinvestment for all these tickers across ALL accounts.\n"
            yield "See fava plugin for better formatted and sortable output.\n"
    click.echo_via_pager(_gen_output())


if __name__ == '__main__':
    tlh()
