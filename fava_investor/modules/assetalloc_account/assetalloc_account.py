#!/usr/bin/env python3
"""Beancount Asset Allocation by Account"""

# import fava_investor.modules.assetalloc_account.libassetalloc_account as libassetalloc_account
import libassetalloc_account
import fava_investor.common.beancountinvestorapi as api
from fava_investor.common.clicommon import pretty_print_table
import click


@click.command()
@click.argument('beancount-file', type=click.Path(exists=True), envvar='BEANCOUNT_FILE')
def assetalloc_account(beancount_file):
    """Beancount asset allocation by account.

       The BEANCOUNT_FILE environment variable can optionally be set instead of specifying the file on the
       command line.

       The configuration for this module is expected to be supplied as a custom directive like so in your
       beancount file:

       \b
        2010-01-01 custom "fava-extension" "fava_investor" "{
           'asset_alloc_by_account': [
             { 'title':            'Allocation by Taxability',
               'pattern_type':     'account_name',
               'pattern':          'Assets:Investments:[^:]*$',
               'include_children': True,
             },
             { 'title':            'Allocation by Account',
               'pattern_type':     'account_name',
               'pattern':          'Assets:Investments:.*',
             },
           ]}"
    """
    accapi = api.AccAPI(beancount_file, {})
    config = accapi.get_custom_config('asset_alloc_by_account')
    tables = libassetalloc_account.get_tables(accapi, config)

    def _gen_output():
        for title, table in tables:
            yield pretty_print_table(title, *table)

    click.echo_via_pager(_gen_output())


if __name__ == '__main__':
    assetalloc_account()
