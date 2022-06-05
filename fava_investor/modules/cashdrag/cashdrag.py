#!/usr/bin/env python3
"""Beancount cash drag tool."""

import click
import fava_investor.modules.cashdrag.libcashdrag as libcashdrag
from fava_investor.common.clicommon import pretty_print_table
import fava_investor.common.beancountinvestorapi as api


@click.command()
@click.argument('beancount-file', type=click.Path(exists=True), envvar='BEANCOUNT_FILE')
@click.option('--accounts-pattern', help='Regex pattern of accounts to consider', default='')
@click.option('--accounts-exclude-pattern', help='Regex pattern of accounts to exclude in hunting cash drag.',
              default='')
@click.option('--debug', help='Debug', is_flag=True)
def cashdrag(beancount_file, accounts_pattern, accounts_exclude_pattern, debug):
    """Beancount: Identify cash across all accounts
       The BEANCOUNT_FILE environment variable can optionally be set instead of specifying the file on the
       command line.
    """

    argsmap = locals()
    accapi = api.AccAPI(beancount_file, argsmap)
    if not accounts_pattern:
        del argsmap['accounts_pattern']
    if not accounts_exclude_pattern:
        del argsmap['accounts_exclude_pattern']
    rtypes, rrows, _, total = libcashdrag.find_loose_cash(accapi, argsmap)
    print("Total: {}".format(total))
    pretty_print_table(rtypes, rrows)


if __name__ == '__main__':
    cashdrag()
