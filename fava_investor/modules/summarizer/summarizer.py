#!/usr/bin/env python3
# Description: CLI for summarizer

import libsummarizer
# from fava_investor.common.clicommon import *
import fava_investor.common.beancountinvestorapi as api
import argcomplete
import argh
import tabulate
tabulate.PRESERVE_WHITESPACE = True

def pretty_print_table(rtypes, rrows):
    headers = [i[0] for i in rtypes]
    print(tabulate.tabulate(rrows,
                            headers=headers[1:],
                            tablefmt='simple',
                            floatfmt=",.0f"))


def summarizer(beancount_file,
              acc_pattern = '^Assets:(Investments|Banks)',
              meta_prefix = 'beneficiary_',
              meta_skip = 'beneficiary_skip',
              col_order = [
                'account',
                'balance',
                'last_verified',
                'todo',
                'notes',
                'legal_points',
                'primary',
                'contingent'
              ],
             debug=False):

    argsmap = locals()
    accapi = api.AccAPI(beancount_file, argsmap)

    rtypes, rrows, _, _ = libsummarizer.build_table(accapi, argsmap)

    # print('# vim:tw=0 number')
    pretty_print_table(rtypes, rrows)

# -----------------------------------------------------------------------------
def main():
    parser = argh.ArghParser(description="Beancount Metadata Summarizer")
    argh.set_default_command(parser, summarizer)
    argh.completion.autocomplete(parser)
    parser.dispatch()
    return 0


if __name__ == '__main__':
    main()
