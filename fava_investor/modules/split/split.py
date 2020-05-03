#!/usr/bin/env python3
# PYTHON_ARGCOMPLETE_OK
# Description: Beancount Tax Loss Harvester

import libsplit
import beancountinvestorapi as api
import argh
import argcomplete
from fava_investor.common.clicommon import *
from beancount.core.inventory import Inventory


def split(beancount_file,
          accounts_pattern='Assets:US',
          dividends_pattern='Income.*Dividends$',
          capgains_pattern='Income.*Gains$',
          ):
    """Splits investment accounts into contribs/withdrawals, dividends, realized, and unrealized gains"""
    accapi = api.AccAPI(beancount_file, locals())
    totals = libsplit.get_tables(accapi)

    for t in totals.keys():
        if totals[t] == Inventory():
            print(t, totals[t], sep=',')
        else:
            print(f"{t},{totals[t].get_only_position().units.number}")

# -----------------------------------------------------------------------------


def main():
    parser = argh.ArghParser(description="Beancount Tax Loss Harvester")
    argh.set_default_command(parser, split)
    argh.completion.autocomplete(parser)
    parser.dispatch()


if __name__ == '__main__':
    main()
