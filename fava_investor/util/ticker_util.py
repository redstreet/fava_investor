#!/usr/bin/env python3
"""Download and cache basic info about current beancount commodities"""
# PYTHON_ARGCOMPLETE_OK

import argh
import argcomplete
import os
import sys
import pickle
import datetime
import pydoc
import yfinance as yf
from beancount.core import getters
from beancount.parser import printer
import asyncio
import fava_investor.util.ticker_relate
from fava_investor.util.common import *

# cusip info: https://www.quantumonline.com/search.cfm
bean_root = os.getenv('BEAN_ROOT', '~/')
yf_cache = os.sep.join([bean_root, '.ticker_info.yahoo.cache'])


def get_commodity_directives(cf=commodities_file):
    entries, _, _ = load_file(cf)
    return getters.get_commodity_directives(entries)

def background(f):
    def wrapped(*args, **kwargs):
        return asyncio.get_event_loop().run_in_executor(None, f, *args, **kwargs)

    return wrapped


class CachedTickerInfo:
    def __init__(self):
        self.cache_file = yf_cache
        if not os.path.exists(self.cache_file):
            with open(self.cache_file, 'wb') as f:
                pickle.dump({}, f)
        with open(self.cache_file, 'rb') as f:
            data = pickle.load(f)
        # print(self.get_cache_last_updated())
        self.data = data

    def get_cache_last_updated(self):
        cache_file_updated = os.path.getmtime(self.cache_file)
        tz = datetime.datetime.now().astimezone().tzinfo
        self.cache_last_updated = datetime.datetime.fromtimestamp(cache_file_updated, tz).isoformat()
        return self.cache_last_updated

    @background
    def lookup_yahoo(self, ticker):
        t_obj = yf.Ticker(ticker)

        print("Downloading info for", ticker)
        self.data[ticker] = t_obj.info
        self.data[ticker]['isin'] = t_obj.isin
        if self.data[ticker]['isin'] == '-':
            self.data[ticker].pop('isin')
        if 'annualReportExpenseRatio' in self.data[ticker]:
            er = self.data[ticker]['annualReportExpenseRatio']
            if er:
                self.data[ticker]['annualReportExpenseRatio'] = round(er*100, 2)

    def write_cache(self):
        with open(self.cache_file, 'wb') as f:
            pickle.dump(self.data, f)

    def remove(self, ticker):
        self.data.pop(ticker, None)
        self.write_cache()

    def batch_lookup(self, tickers):
        tickers_to_lookup = [t for t in tickers if t not in self.data]
        waiting = []
        for ticker in tickers_to_lookup:
            waiting.append(self.lookup_yahoo(ticker))
        if waiting:
            loop = asyncio.get_event_loop()
            loop.run_until_complete(asyncio.wait(waiting))
        self.write_cache()


@argh.aliases('add')
def add_tickers(tickers):
    """Download and add new tickers to database. Accepts a list of comma separated tickers.
    To get a list of tickers from your beancount sources for the
    very first time you run this utility, the following will help generate a list of tickers that are used in
    your beancount source file (named accounts.beacount below):
    bean-price -a -n accounts.beacount | sed 's/ .*//' | sed -z 's/\\n/,/g;s/,$/\\n/'

    """
    tickers = tickers.split(',')
    ctdata = CachedTickerInfo()
    ctdata.batch_lookup(tickers)
    ctdata.write_cache()


@argh.aliases('remove')
def remove_tickers(tickers):
    """Remove tickers from the database. Accepts a list of comma separated tickers."""
    tickers = tickers.split(',')
    ctdata = CachedTickerInfo()
    for t in tickers:
        ctdata.remove(t)


@argh.aliases('list')
def list_tickers(info=False, explore=False):
    """List tickers (and optionally, basic info) from the database."""
    ctdata = CachedTickerInfo()

    if info:
        interesting = [('Ticker',  'symbol',                   '{:<6}',   6),
                       ('Type',    'quoteType',                '{:<11}', 11),
                       ('ISIN',    'isin',                     '{:>12}', 12),
                       ('ER',      'annualReportExpenseRatio', '{:4.2f}', 4),
                       ('Name',    'longName',                 '{}',      0),
                       ]

        lines = []

        # print header line
        header_line = ' '.join([f'{{:<{width}}}' for _, _, _, width in interesting])
        lines.append(header_line.format(*[h for h, _, _, _ in interesting]))
        lines.append(header_line.format(*['_'*(width if width else 40) for _, _, _, width in interesting]))

        for ticker in sorted(ctdata.data):
            info = ctdata.data[ticker]
            line = ''
            for _, k, fmt, width in interesting:
                try:
                    s = fmt.format(info.get(k, ''))
                except (TypeError, ValueError):
                    s = ' ' * width
                line += s + ' '
            lines.append(line)
        pydoc.pager('\n'.join(lines))
    else:
        print(','.join(ctdata.data.keys()))

    if explore:
        import pdb
        pdb.set_trace()


@argh.aliases('comm')
def gen_commodities_file(
        cf: "Beancount commodity declarations file" = commodities_file,

        prefix: "Metadata label prefix for generated metadata" = 'a__',

        write_file: "Overwrite the commodities file. WARNING! This does exactly what it states: it \
                overwrites your file, assuming your commodity declarations source is a separate file (from \
                your beancount sources) that you auto-generate with this utility." = False,

        confirm_overwrite: "Specify in conjunction with --write_file to actually overwrite" = False):

    """Generate Beancount commodity declarations with metadata from database, and existing declarations."""

    auto_metadata = ['quoteType', 'longName', 'isin', 'annualReportExpenseRatio']
    metadata_label_map = {'longName': 'name'}  # fava recognizes and displays 'name'

    commodities = get_commodity_directives()
    comms = ticker_relate.Commodities(cf)
    full_tlh_db = comms.compute_tlh_groups()

    # update a_* metadata
    ctdata = CachedTickerInfo()
    for c, metadata in commodities.items():
        if c in ctdata.data:
            if c in full_tlh_db:
                metadata.meta[prefix + 'tlh_partners'] = ','.join(full_tlh_db[c])
            metadata.meta[prefix + 'substsimilars'] = ','.join(comms.substsimilars(c))
            for m in auto_metadata:
                if m in ctdata.data[c] and ctdata.data[c][m]:
                    if m == 'isin':
                        isins = set(metadata.meta.get(prefix + m, '').split(','))
                        isins = set() if isins == set(['']) else isins
                        isins.add(str(ctdata.data[c][m]))
                        metadata.meta[prefix + m] = ','.join(list(isins))
                    else:
                        label = metadata_label_map.get(m, prefix + m)
                        metadata.meta[label] = str(ctdata.data[c][m])
    cv = list(commodities.values())
    cv.sort(key=lambda x: x.currency)

    fout = open(cf, "w") if write_file and confirm_overwrite else sys.stdout
    print(f"; Generated by: {__file__}, at {datetime.datetime.today().isoformat()}", file=fout)
    fout.flush()
    printer.print_entries(cv, file=fout)

    not_in_commodities_file = [c for c in ctdata.data if c not in commodities]
    if not_in_commodities_file:
        print()
        print("Warning: not in ", commodities_file)
        print(not_in_commodities_file)
        print("Simply declare them in your commodities file, and re-rerun this util to fill in their metadata")

    if write_file and not confirm_overwrite:
        print(f"Not overwriting {cf} because --confirm_overwrite was not specified")

# def rewrite_er():
#     ctdata = CachedTickerInfo()
#     for ticker in ctdata.data:
#         if 'annualReportExpenseRatio' in ctdata.data[ticker] and ctdata.data[ticker]['annualReportExpenseRatio']:
#             er = ctdata.data[ticker]['annualReportExpenseRatio']
#             print(ticker, '\t', er)
#             # ctdata.data[ticker]['annualReportExpenseRatio'] = round(er/100, 2)
#     # ctdata.write_cache()


def generate_fund_info(
        cf: "Beancount commodity declarations file" = commodities_file,
        prefix: "Metadata label prefix for generated metadata" = 'a__'):
    """Generate fund info for importers (from commodity directives in the beancount input file)"""
    commodities = get_commodity_directives(cf)

    fund_data = []
    for c in commodities:
        cd = commodities[c]
        isins = cd.meta.get(prefix + 'isin', '').split(',')
        for i in isins:
            fund_data.append((c, i, cd.meta.get(prefix + 'longName', 'Ticker long name unavailable')))

    money_market = [c for c in commodities if commodities[c].meta.get(prefix + 'quoteType', '') == 'MONEYMARKET']
    fund_info = {'fund_data': fund_data, 'money_market': money_market}
    return fund_info


@argh.aliases('show')
def show_fund_info():
    """Show info that is generated for importers (from commodity directives in the beancount input file)"""
    fund_info = generate_fund_info()
    pydoc.pager('\n'.join(str(i) for i in fund_info['fund_data'] + ['\nMoney Market:',
                str(fund_info['money_market'])]))


def main():
    """In all subcommands, the following environment variables are used:
        $BEAN_ROOT: root directory for beancount source(s). Downloaded info is cached in this directory
        $COMMODITIES_FILE: file with beancount commodities declarations. WARNING: the 'comm' subcommand
                           will overwrite this file when requested
    """
    parser = argh.ArghParser(description=main.__doc__)
    argcomplete.autocomplete(parser)
    parser.add_commands([list_tickers, add_tickers, remove_tickers, gen_commodities_file, show_fund_info])
    argh.completion.autocomplete(parser)
    parser.dispatch()


if __name__ == '__main__':
    main()


# TODOs
# - create new commodity entries as needed, when requested
