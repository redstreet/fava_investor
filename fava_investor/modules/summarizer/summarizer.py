#!/usr/bin/env python3
"""CLI for Metadata Summarizer for Beancount."""

import click
import fava_investor.common.beancountinvestorapi as api
import fava_investor.modules.summarizer.libsummarizer as libsummarizer
from fava_investor.common.clicommon import pretty_print_table


@click.command()
@click.argument('beancount-file', type=click.Path(exists=True), envvar='BEANCOUNT_FILE')
def summarizer(beancount_file):
    """Displays metadata summaries from a config, as tables.

       The BEANCOUNT_FILE environment variable can optionally be set instead of specifying the file on the
       command line.

       The configuration for this module is expected to be supplied as a custom directive like so in your
       beancount file:

       \b
        2010-01-01 custom "fava-extension" "fava_investor" "{
          'summarizer': [
            { 'title' : 'Customer Service Phone Number',
              'directive_type'  : 'accounts',
              'acc_pattern' : '^Assets:(Investments|Banks)',
              'col_labels': [ 'Account', 'Phone_number'],
              'columns' : [ 'account', 'customer_service_phone'],
              'sort_by' : 0,
            }]}"

    """
    accapi = api.AccAPI(beancount_file, {})
    configs = accapi.get_custom_config('summarizer')
    tables = libsummarizer.build_tables(accapi, configs)

    def _gen_output():
        for title, (rtypes, rrows, _, _) in tables:
            yield pretty_print_table(title, rtypes, rrows, floatfmt=",.0f")

    click.echo_via_pager(_gen_output())


if __name__ == '__main__':
    summarizer()
