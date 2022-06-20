#!/usr/bin/env python3
"""Provide scaled price estimates for mutual funds based on their ETF prices.

WARNING: it may be dangerous to use this tool financially. You bear all liability for all losses stemming from
usage of this tool.

Problem: Mutual fund NAVs are updated only once a day, at the end of the day. When needing to make financial
decisions (eg: when tax loss harvesting), it is sometimes useful to estimate that NAV, especially on days when
there are huge swings in the market.

Idea: NAV estimations can be made based on the ETF share class of the mutual fund, if one exists.

Note that on volatile days, this can be dangerous, since the estimate can be way off. However, there might be
value to using such scaled estimates even that caveat.

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
import statistics
import datetime

from beancount.core import getters
from beancount.core.data import Price
from beancount.core.amount import Amount
from beancount.parser import printer
from fava_investor.util.relatetickers import RelateTickers


cf_option = click.option('--cf', '--commodities-file', help="Beancount commodity declarations file",
                         envvar='BEAN_COMMODITIES_FILE', type=click.Path(exists=True), required=True)
prices_option = click.option('--pf', '--prices-file', help="Beancount prices declarations file",
                             envvar='BEAN_PRICES_FILE', type=click.Path(exists=True), required=True)


class ScaledNAV(RelateTickers):
    def __init__(self, cf, prices_file, date=None):
        self.cf = cf
        self.prices_file = prices_file
        entries, _, _ = self.load_file(cf)

        # basic databases
        self.db = getters.get_commodity_directives(entries)

        # equivalents databases
        self.equivalents = self.build_commodity_groups(['equivalent'])

        # prices database
        entries, _, _ = self.load_file(prices_file)
        self.price_entries = [entry for entry in entries if isinstance(entry, Price)]
        self.price_entries = sorted(self.price_entries, key=lambda x: x.date)
        if not date:
            date = datetime.datetime.today().date()
        self.latest_prices = {p.currency: p.amount for p in self.price_entries if p.date == date}
        self.estimate_mf_navs()
        # for k, v in self.latest_prices.items():
        #     print(k, v)

    def is_etf(self, ticker):
        try:
            return self.db[ticker].meta['a__quoteType'] == 'ETF'
        except KeyError:
            return False

    def is_mf(self, ticker):
        try:
            return self.db[ticker].meta['a__quoteType'] == 'MUTUALFUND'
        except KeyError:
            return False

    def mf_to_etf_map(self):
        """Map MFs to equivalent ETFs. Assume commodity declarations have 'a__quoteType' set to either
        MUTUALFUND or ETF. See ticker-util to do this automatically."""

        mf_to_etfs = {}
        for equis in self.equivalents:
            etfs = [c for c in equis if self.is_etf(c)]
            for etf in etfs:
                mfs = [c for c in equis if self.is_mf(c)]
                for m in mfs:
                    mf_to_etfs[m] = etf
        return mf_to_etfs

    def estimate_mf_navs(self):
        """Estimate what mutual fund NAVs would be based on the current price of the equivalent ETF. Don't use
        this unless you know what you are doing!"""

        mf_to_etfs = self.mf_to_etf_map()
        scaled_mf = {}
        unavailable_etfs = set()
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
            if ratios:
                if etf in self.latest_prices:
                    median_ratio = statistics.median(ratios)
                    scaled_number = round(self.latest_prices[etf].number * median_ratio, 2)
                    scaled_mf[mf] = (etf, median_ratio, Amount(scaled_number, self.latest_prices[etf].currency))
                else:
                    unavailable_etfs.add(etf)

        if unavailable_etfs:
            print("Today's prices for these ETFs were not found:", ", ".join(sorted(unavailable_etfs)))

        self.estimated_price_entries = [Price({}, datetime.datetime.today().date(), mf, amt)
                                        for mf, (_, _, amt) in scaled_mf.items()]

    def show_estimates(self):
        printer.print_entries(self.estimated_price_entries)

    def update_prices_file(self):
        with open(self.prices_file, "a") as fout:
            print("\n; Below are *estimated* mutual fund NAVs, generated by: ", end='', file=fout)
            print(f"{os.path.basename(__file__)}, at {datetime.datetime.today().isoformat()}", file=fout)
            fout.flush()
            printer.print_entries(self.estimated_price_entries, file=fout)
            print(file=fout)


@click.command()
@cf_option
@prices_option
@click.option('--date', help="Date", default=datetime.datetime.today().date())
@click.option('-w', '--write-to-prices-file', is_flag=True, help='Append estimates to prices file.')
def scaled_navs(cf, pf, date, write_to_prices_file):
    """Provide scaled price estimates for mutual funds based on their ETF prices. Experimental.

\nWARNING: it may be dangerous to use this tool financially. You bear all liability for all losses stemming
from usage of this tool.

\nThe following environment variables are used:
\n$BEAN_COMMODITIES_FILE: file with beancount commodities declarations.
\n$BEAN_PRICES_FILE: file with beancount prices declarations.
    """
    s = ScaledNAV(cf, pf)
    s.show_estimates()
    if write_to_prices_file:
        s.update_prices_file()
        print("Above was append to", pf)


if __name__ == '__main__':
    scaled_navs()
