#!/usr/bin/env python3
# Description: CLI for succession

import libsuccession
from fava_investor.common.clicommon import *
import fava_investor.common.beancountinvestorapi as api
import argcomplete
import argh


def successor(beancount_file,
             debug=False):

    argsmap = locals()
    accapi = api.AccAPI(beancount_file, argsmap)
    accounts = libsuccession.find_active_accounts(accapi, argsmap)
    pretty_print_table_bare(accounts)


# -----------------------------------------------------------------------------
def main():
    parser = argh.ArghParser(description="Beancount Asset Cash Drag")
    argh.set_default_command(parser, successor)
    argh.completion.autocomplete(parser)
    parser.dispatch()
    return 0


if __name__ == '__main__':
    main()
