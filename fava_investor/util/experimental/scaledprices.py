#!/usr/bin/env python3
"""Provide scaled price estimates for mutual funds based on their ETF prices.

WARNING: it may be dangerous to use this tool financially. You bear all liability for all losses stemming from
usage of this tool.

Problem: Mutual fund NAVs are updated only once a day, at the end of the day. When needing to make financial
decisions (eg: tax loss harvesting), it is sometimes useful to estimate that NAV, especially on days when
there are huge swings in the market.

Idea: NAV estimations can be made based on the ETF share class of the mutual fund, if one exists.

Note that on volatile days, this can be dangerous, since the estimate can
be way off. However, there is some value to using such scaled estimates even with those caveats.


Solution: Scan a beancount price database, and build a list of mf:etf equivalents. Then, determine the typical
price ratio between these. This is done by building a list of mf:etf price pairs on the same days across time,
and using the median value for the ratio (so extreme and incorrect values are discarded).

Finally, this ratio is used to estimate today's MF NAV price, based on today's ETF price as supplied in the
price database.


Misc notes:
-----------

- When multiple Price directives do exist for the same day, the last one to appear in the file will be
  selected for inclusion in the Price database.
  https://beancount.github.io/docs/beancount_language_syntax.html#prices-on-the-same-day

"""

import click
import os
import sys
import statistics
import datetime

from beancount import loader
from beancount.core import getters
from beancount.parser import printer
from fava_investor.util.relatetickers import RelateTickers


from beancount.core.amount import Amount
from beancount.core.data import Price

cf_option = click.option('--cf', help="Beancount commodity declarations file", envvar='BEAN_COMMODITIES_FILE',
                         type=click.Path(exists=True))
bean_root = os.getenv('BEAN_ROOT', '~/')
prices_file = os.sep.join([bean_root, 'prices', 'prices.bc'])


class ScaledNAV(RelateTickers):
    def __init__(self, cf, prices_file):
        commodity_entries, _, _ = self.load_file(cf)

        # basic databases
        self.db = getters.get_commodity_directives(commodity_entries)

        # equivalents databases
        self.equivalents = self.build_commodity_groups(['equivalent'])

        # prices database
        self.price_entries, _, _ = self.load_file(prices_file)
        self.price_entries = sorted(self.price_entries, key=lambda x: x.date)
        today = datetime.datetime.today().date()
        self.latest_prices = {p.currency: p.amount for p in self.price_entries if p.date == today}
        # for k, v in self.latest_prices.items():
        #     print(k, v)

    def load_file(self, f):
        if f is None:
            print("File not specified. See help.", file=sys.stderr)
            sys.exit(1)
        if not os.path.exists(f):
            print(f"File not found: {f}", file=sys.stderr)
            sys.exit(1)
        return loader.load_file(f)

    def estimate_mf_navs(self):
        """Estimate what mutual fund NAVs would be at the end of the day *if* the current prices of the
        equivalent ETF held through the end of the day. Don't use this unless you know what you are doing!"""

        # map MFs to ETFs
        mf_to_etfs = {}
        for equis in self.equivalents:
            etfs = [c for c in equis if len(c) == 3]
            for etf in etfs:
                mfs = [c for c in equis if len(c) == 5]
                for m in mfs:
                    mf_to_etfs[m] = etf

        scaled_mf = {}
        for mf, etf in mf_to_etfs.items():
            ratios = []
            for p in self.price_entries:
                if p.currency == mf:
                    etf_prices = [x for x in self.price_entries if (x.currency == etf and x.date == p.date)]
                    if etf_prices:
                        mf_price = p.amount.number
                        etf_price = etf_prices[0].amount.number
                        ratio = mf_price / etf_price
                        # print("  ", p.date, mf_price, etf_price, ratio)
                        ratios.append(ratio)
            ratios.sort()
            if ratios:
                median = statistics.median(ratios)
                # print(f"{mf}: {etf} * {median}, {ratios}")
                scaled_mf[mf] = (etf, median)

        self.scaled_prices = {}
        for mf, (etf, ratio) in scaled_mf.items():
            # rratio = round(ratio, 2)
            # print(f"{mf}: {etf} * {rratio}")
            self.scaled_prices[mf] = Amount(self.latest_prices[etf].number * ratio,
                                            self.latest_prices[etf].currency)

        for mf, amt in self.scaled_prices.items():
            price = Price({}, datetime.datetime.today().date(), mf, amt)
            printer.print_entries([price])


@click.command()
@cf_option
def scaled_navs(cf):
    """The following environment variables are used:
\n$BEAN_ROOT: root directory for beancount source(s). $BEAN_ROOT/prices/prices.bc is the price file used. Default: ~
\n$BEAN_COMMODITIES_FILE: file with beancount commodities declarations. WARNING: the 'comm' subcommand
will overwrite this file when requested
    """
    s = ScaledNAV(cf, prices_file)
    s.estimate_mf_navs()


if __name__ == '__main__':
    scaled_navs()
