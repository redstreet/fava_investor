#!/usr/bin/env python3
"""Beancount cash drag tool."""

import click
import fava_investor.modules.cashdrag.libcashdrag as libcashdrag
from fava_investor.common.clicommon import pretty_print_table
import fava_investor.common.beancountinvestorapi as api


@click.command()
@click.argument('beancount-file', type=click.Path(exists=True), envvar='BEANCOUNT_FILE')
def cashdrag(beancount_file):
    """Cashdrag: Identify cash across all accounts.

       The BEANCOUNT_FILE environment variable can optionally be set instead of specifying the file on the
       command line.

       The configuration for this module is expected to be supplied as a custom directive like so in your
       beancount file:

       \b
        2010-01-01 custom "fava-extension" "fava_investor" "{
          'cashdrag': {
              'accounts_pattern':         '^Assets:.*',
              'accounts_exclude_pattern': '^Assets:(Cash-In-Wallet.*|Zero-Sum)',
              'metadata_label_cash'     : 'asset_allocation_Bond_Cash'
        }}"
    """
    accapi = api.AccAPI(beancount_file, {})
    config = accapi.get_custom_config('cashdrag')
    rtypes, rrows, _, footer = libcashdrag.find_loose_cash(accapi, config)
    click.echo_via_pager(pretty_print_table("Cash Balances", rtypes, rrows, footer=footer))


if __name__ == '__main__':
    cashdrag()
