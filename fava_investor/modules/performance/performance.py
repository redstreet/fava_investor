#!/usr/bin/env python3
"""Beancount Tool to find lots to sell with lowest gains, to minimize the tax burden."""

import fava_investor.modules.performance.libperformance as libpf
import fava_investor.common.beancountinvestorapi as api
from fava_investor.common.clicommon import pretty_print_table, write_table_csv
import click


@click.command()
@click.argument('beancount-file', type=click.Path(exists=True), envvar='BEANCOUNT_FILE')
@click.option('--csv-output', help='In addition to summary, output to performance.csv', is_flag=True)
def performance(beancount_file, csv_output):
    """Generate XIRR for each investment.

       The BEANCOUNT_FILE environment variable can optionally be set instead of specifying the file on the
       command line.

       The configuration for this module is expected to be supplied as a custom directive like so in your
       beancount file:

       \b
        2010-01-01 custom "fava-extension" "fava_investor" "{
              'performance' : {
                 'account_field': 'account',
                 'accounts_pattern': 'Assets:Investments',
                 'accuracy': 2,
              },
           }}"

    """
    accapi = api.AccAPI(beancount_file, {})
    config = accapi.get_custom_config('performance')
    tables = libpf.find_xirrs(accapi, config)

    # TODO:
    # - use same return return API for all of fava_investor
    #   - ordered dictionary of title: [retrow_types, table]
    # - make output printing and csv a common function

    if csv_output:
        write_table_csv('performance.csv', tables[1])
    else:
        def _gen_output():
            for title, (rtypes, rrows, _, _) in tables:
                yield pretty_print_table(title, rtypes, rrows)

        click.echo_via_pager(_gen_output())


if __name__ == '__main__':
    performance()
