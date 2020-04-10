#!/usr/bin/env python3
# Description: CLI for cash drag

import argparse,argcomplete,argh
import os
import sys

sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', 'common'))
import beancountinvestorapi as api

from clicommon import *
import libcashdrag

def cashdrag(beancount_file,
    whitelist: 'Regex pattern of accounts to include in hunting cash drag.' = '',
    blacklist: 'Regex pattern of accounts to exclude in hunting cash drag.' = '',
    base_currency='USD',
    debug=False):

    argsmap = locals()
    accapi = api.AccAPI(beancount_file, argsmap)
    if not whitelist:
        del argsmap['whitelist']
    if not blacklist:
        del argsmap['blacklist']
    rtypes, rrows = libcashdrag.find_loose_cash(accapi, argsmap)
    pretty_print_table(rtypes, rrows)


#-----------------------------------------------------------------------------
def main():
    parser = argh.ArghParser(description="Beancount Asset Cash Drag")
    argh.set_default_command(parser, cashdrag)
    argh.completion.autocomplete(parser)
    parser.dispatch()
    return 0

if __name__ == '__main__':
    main()
