#!/usr/bin/env python3
"""Download and cache basic info about current beancount commodities"""
# PYTHON_ARGCOMPLETE_OK

import argcomplete
import argh
import datetime
import os
import pydoc
import sys

from beancount.core import data
from beancount.parser import printer
from fava_investor.util.relatetickers import RelateTickers
from fava_investor.util.cachedtickerinfo import CachedTickerInfo

commodities_file = os.getenv('COMMODITIES_FILE')
bean_root = os.getenv('BEAN_ROOT', '~/')
yf_cache = os.sep.join([bean_root, '.ticker_info.yahoo.cache'])


@argh.aliases('add')
def add_tickers(tickers):
    """Download and add new tickers to database. Accepts a list of comma separated tickers.
    To get a list of tickers from your beancount sources for the
    very first time you run this utility, the following will help generate a list of tickers that are used in
    your beancount source file (named accounts.beacount below):
    bean-price -a -n accounts.beacount | sed 's/ .*//' | sed -z 's/\\n/,/g;s/,$/\\n/'

    """
    tickers = tickers.split(',')
    ctdata = CachedTickerInfo(yf_cache)
    ctdata.batch_lookup(tickers)
    ctdata.write_cache()


@argh.aliases('remove')
def remove_tickers(tickers):
    """Remove tickers from the database. Accepts a list of comma separated tickers."""
    tickers = tickers.split(',')
    ctdata = CachedTickerInfo(yf_cache)
    for t in tickers:
        ctdata.remove(t)


@argh.aliases('list')
def list_tickers(info=False, explore=False):
    """List tickers (and optionally, basic info) from the database."""
    ctdata = CachedTickerInfo(yf_cache)

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

        include_undeclared: "Write new commodity entries for tickers the cached database, but not in the \
                             existing Beancount commodity declarations file" = False,

        write_file: "Overwrite the commodities file. WARNING! This does exactly what it states: it \
                overwrites your file, assuming your commodity declarations source is a separate file (from \
                your beancount sources) that you auto-generate with this utility." = False,

        confirm_overwrite: "Specify in conjunction with --write_file to actually overwrite" = False):

    """Generate Beancount commodity declarations with metadata from database, and existing declarations."""

    auto_metadata = ['quoteType', 'longName', 'isin', 'annualReportExpenseRatio']
    metadata_label_map = {'longName': 'name'}  # fava recognizes and displays 'name'

    tickerrel = RelateTickers(cf)
    commodities = tickerrel.db
    full_tlh_db = tickerrel.compute_tlh_groups()
    ctdata = CachedTickerInfo(yf_cache)

    not_in_commodities_file = [c for c in ctdata.data if c not in commodities]
    if not_in_commodities_file:
        if include_undeclared:
            for c in not_in_commodities_file:
                commodities[c] = data.Commodity({}, datetime.datetime.today().date(), c)
        else:
            print("Warning: not in ", commodities_file, file=sys.stderr)
            print(not_in_commodities_file, file=sys.stderr)
            print("Simply declare them in your commodities file, and re-rerun this util to fill in their metadata",
                  file=sys.stderr)

    # update a_* metadata
    for c, metadata in commodities.items():
        if c in ctdata.data:
            if c in full_tlh_db:
                metadata.meta[prefix + 'tlh_partners'] = ','.join(full_tlh_db[c])
            metadata.meta[prefix + 'substsimilars'] = ','.join(tickerrel.substsimilars(c))
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

    if write_file and not confirm_overwrite:
        print(f"Not overwriting {cf} because --confirm_overwrite was not specified")

# def rewrite_er():
#     ctdata = CachedTickerInfo(yf_cache)
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
    tickerrel = RelateTickers(cf)
    commodities = tickerrel.db

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


@argh.aliases('eq')
def find_equivalents(cf: "Beancount commodity declarations file" = commodities_file):
    """Determine equivalent groups of commodities, from an incomplete specification."""

    tickerrel = RelateTickers(cf)
    retval = tickerrel.build_commodity_groups(['equivalent'])
    for r in retval:
        print(r)


@argh.aliases('sim')
def find_similars(cf: "Beancount commodity declarations file" = commodities_file):
    """Determine substantially similar groups of commodities from an incomplete specification. Includes
    equivalents."""

    tickerrel = RelateTickers(cf)
    retval = tickerrel.build_commodity_groups(['equivalent', 'substsimilar'])
    for r in retval:
        print(r)


def archived(cf: "Beancount commodity declarations file" = commodities_file):
    """List archived commodities."""

    tickerrel = RelateTickers(cf)
    archived = tickerrel.archived
    for r in archived:
        print(r)


def printd(d):
    for k in d:
        print(k, d[k])
    print()


@argh.aliases('tlh')
def find_tlh_groups(cf: "Beancount commodity declarations file" = commodities_file):
    tickerrel = RelateTickers(cf)
    full_tlh_db = tickerrel.compute_tlh_groups()
    for t, partners in sorted(full_tlh_db.items()):
        print("{:<5}".format(t), partners)


def main():
    """In all subcommands, the following environment variables are used:
        $BEAN_ROOT: root directory for beancount source(s). Downloaded info is cached in this directory
        $COMMODITIES_FILE: file with beancount commodities declarations. WARNING: the 'comm' subcommand
                           will overwrite this file when requested
    """
    parser = argh.ArghParser(description=main.__doc__)
    argcomplete.autocomplete(parser)
    parser.add_commands([list_tickers, add_tickers, remove_tickers, gen_commodities_file, show_fund_info])
    parser.add_commands([find_equivalents, find_similars, find_tlh_groups, archived], namespace='relate',
                        title='Discover relationships between tickers')
    argh.completion.autocomplete(parser)
    parser.dispatch()


if __name__ == '__main__':
    main()


# TODOs
# - create new commodity entries as needed, when requested
# - cusip info: https://www.quantumonline.com/search.cfm
