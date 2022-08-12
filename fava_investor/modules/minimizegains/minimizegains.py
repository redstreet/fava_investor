#!/usr/bin/env python3
"""Beancount Tool to find lots to sell with lowest gains"""

import fava_investor.modules.minimizegains.libminimizegains as libmg
import fava_investor.common.beancountinvestorapi as api
from fava_investor.common.clicommon import pretty_print_table
import click


@click.command()
@click.argument('beancount-file', type=click.Path(exists=True), envvar='BEANCOUNT_FILE')
@click.option('--brief', help='Summary output', is_flag=True)
def minimizegains(beancount_file, brief):
    """Finds lots to sell with the lowest gains.

       The BEANCOUNT_FILE environment variable can optionally be set instead of specifying the file on the
       command line.

       The configuration for this module is expected to be supplied as a custom directive like so in your
       beancount file:

       \b
        2010-01-01 custom "fava-extension" "fava_investor" "{
          'minimizegains' : { 'accounts_pattern': 'Assets:Investments:Taxable',
           }}"

    """
    accapi = api.AccAPI(beancount_file, {})
    config = accapi.get_custom_config('minimizegains')
    retrow_types, to_sell = libmg.find_minimized_gains(accapi, config)

    def _gen_output():
        yield pretty_print_table("Minimized Gains Table", retrow_types, to_sell)

    click.echo_via_pager(_gen_output())


if __name__ == '__main__':
    minimizegains()
