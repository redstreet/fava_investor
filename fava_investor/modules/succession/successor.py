#!/usr/bin/env python3
# Description: CLI for succession

import libsuccession
from fava_investor.common.clicommon import *
import fava_investor.common.beancountinvestorapi as api
import argcomplete
import argh

col_order = [
  'account',
  'last_verified',
  'todo',
  'notes',
  'legal_points',
  'primary',
  'contingent'
]

meta_prefx = 'beneficiary'

def partial_order(header):
    """Order the header according to our preference, but don't lose unspecified keys"""
    # take advantage of python 3.7+'s insertion order preservation

    retval = {}
    for c in col_order:
        if c in header:
            retval[c] = header[c]

    for h in header:
        if h not in retval:
            retval[h] = header[h]

    return retval 

def successor(beancount_file,
             debug=False):

    argsmap = locals()
    accapi = api.AccAPI(beancount_file, argsmap)
    rows = libsuccession.find_active_accounts(accapi, argsmap)
    all_keys = {j: j for i in rows for j in list(i)}
    header = partial_order(all_keys)
    print('# vim:tw=0 number')
    # Need to add a dummy row with all keys so tabulate prints them in order
    print(tabulate.tabulate([{k:'' for k in header}] + rows,
                            headers=all_keys,
                            tablefmt='simple'))


# -----------------------------------------------------------------------------
def main():
    parser = argh.ArghParser(description="Beancount Asset Cash Drag")
    argh.set_default_command(parser, successor)
    argh.completion.autocomplete(parser)
    parser.dispatch()
    return 0


if __name__ == '__main__':
    main()
