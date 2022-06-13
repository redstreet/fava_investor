#!/usr/bin/env python3
"""CLI for Metadata Summarizer for Beancount. See libsummarizer for more info."""

import click
import fava_investor.common.beancountinvestorapi as api
import libsummarizer
import tabulate
tabulate.PRESERVE_WHITESPACE = True


def pretty_print_table(rtypes, rrows):
    # TODO: Use the one in common
    headers = [i[0] for i in rtypes]
    print(tabulate.tabulate(rrows,
                            headers=headers[1:],
                            tablefmt='simple',
                            floatfmt=",.0f"))


@click.command()
@click.argument('beancount_file', type=click.Path(exists=True))
def summarizer(beancount_file):
    accapi = api.AccAPI(beancount_file, {})
    configs = accapi.get_custom_config('summarizer')
    tables = libsummarizer.build_tables(accapi, configs)
    for title, (rtypes, rrows, _, _) in tables:
        print("# " + title)
        pretty_print_table(rtypes, rrows)
        print()
        print()


if __name__ == '__main__':
    summarizer()
