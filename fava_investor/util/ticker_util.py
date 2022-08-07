#!/usr/bin/env python3
"""Download and cache basic info about current beancount commodities"""

import click
from click_aliases import ClickAliasedGroup
import datetime
import os
import sys

from beancount.core import data
from beancount.parser import printer
from fava_investor.util.relatetickers import RelateTickers
from fava_investor.util.cachedtickerinfo import CachedTickerInfo

cf_help = """Beancount commodity declarations file. This can alternatively be specified by setting
the BEAN_COMMODITIES_FILE environment variable."""
cf_option = click.option('--cf', help=cf_help, envvar='BEAN_COMMODITIES_FILE',
                         type=click.Path(exists=True))
bean_root = os.getenv('BEAN_ROOT', '~/')
yf_cache = os.sep.join([bean_root, '.ticker_info.yahoo.cache'])


def printd(d):
    for k in d:
        print(k, d[k])
    print()


@click.group(cls=ClickAliasedGroup)
def cli():

    """In all subcommands, the following environment variables are used:
\n$BEAN_ROOT: root directory for beancount source(s). Downloaded info is cached in this directory
in a file named .ticker_info.yahoo.cache. Default: ~
\n$BEAN_COMMODITIES_FILE: file with beancount commodities declarations. WARNING: the 'comm' subcommand
will overwrite this file when requested
    """

    pass


@cli.group(cls=ClickAliasedGroup)
def relate():
    """Subcommands that find relationships between tickers."""
    pass


@cli.command(aliases=['add'])
@click.option('--tickers', default='', help='Comma-separated list of tickers to add')
@click.option('--from-file', is_flag=True, help="Add tickers declared in beancount commodity declarations "
              "file (specify the file separately)")
@cf_option
def ticker_add(tickers, from_file, cf):
    """Download and add new tickers to database. Accepts a list of comma separated tickers, or alternatively,
    adds all tickers declared in the specified beancount file. The latter is useful for the very first time
    you run this utility."""

    if from_file:
        tickerrel = RelateTickers(cf)
        tickers = tickerrel.db
    elif tickers:
        tickers = tickers.split(',')
    else:
        print("Tickers to add not specified.", file=sys.stderr)
        return

    ctdata = CachedTickerInfo(yf_cache)
    ctdata.batch_lookup(tickers)
    ctdata.write_cache()


@cli.command(aliases=['remove'])
@click.option('--tickers', default='', help='Comma-separated list of tickers to remove')
def ticker_remove(tickers):
    """Remove tickers from the database. Accepts a list of comma separated tickers."""
    tickers = tickers.split(',')
    ctdata = CachedTickerInfo(yf_cache)
    for t in tickers:
        ctdata.remove(t)


@cli.command(aliases=['list'])
@click.option('-i', '--info', is_flag=True, help='Show extended information')
@click.option('--available-keys', is_flag=True, help='Show all available keys')
@click.option('-e', '--explore', is_flag=True, help='Open a Python debugger shell to explore tickers interactively')
def ticker_list(info, available_keys, explore):
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
        header_line = ' '.join(
            [f'{{:<{width}}}' for _, _, _, width in interesting])
        lines.append(header_line.format(*[h for h, _, _, _ in interesting]))
        lines.append(header_line.format(
            *['_' * (width if width else 40) for _, _, _, width in interesting]))

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
        click.echo_via_pager('\n'.join(lines))
    elif available_keys:
        lines = []
        for k, v in ctdata.data.items():
            lines.append(k)
            lines.append('\n '.join([i for i in v]))
        click.echo_via_pager('\n'.join(lines))
    else:
        print(','.join(ctdata.data.keys()))

    if explore:
        print("Hint: use ctdata and ctdata.data to explore")
        import pdb
        pdb.set_trace()


def label_transform(label, prefix):
    # fava recognizes and displays 'name'
    metadata_label_map = {'longName': 'name'}
    if label in metadata_label_map:
        return metadata_label_map[label]
    if 'Position' in label:
        # for ['preferredPosition', 'bondPosition', etc.]
        return prefix + 'asset_allocation_' + label[:-8]
    return prefix + label


def value_transform(val, label):
    if 'Position' in label:
        return str(round(float(val) * 100))
    return str(val)


metadata_includes = """quoteType,longName,isin,annualReportExpenseRatio,\
preferredPosition,bondPosition,convertiblePosition,otherPosition,cashPosition,stockPosition"""


@cli.command(aliases=['comm'], context_settings={'show_default': True})
@cf_option
@click.option('--prefix', help="Metadata label prefix for generated metadata", default='a__')
@click.option('--metadata', help="Metadata to include", default=metadata_includes)
@click.option('--appends', help="Metadata to append to", default="isin")
@click.option('--include-undeclared', is_flag=True, help="Write new commodity entries for tickers in the "
              "cached database, but not in the existing Beancount commodity declarations file")
@click.option('--write-file', is_flag=True, help="Overwrite the commodities file. WARNING! This does exactly "
              "what it states: it overwrites your file, assuming your commodity declarations source is a "
              "separate file (from your beancount sources) that you auto-generate with this utility.")
@click.option('--confirm-overwrite', is_flag=True, help="Specify in conjunction with --write-file to "
              "actually overwrite")
def gen_commodities_file(cf, prefix, metadata, appends, include_undeclared, write_file, confirm_overwrite):
    """Generate Beancount commodity declarations with metadata from database, and existing declarations."""

    auto_metadata = metadata.split(',')
    auto_metadata_appends = appends.split(',')

    tickerrel = RelateTickers(cf)
    commodities = tickerrel.db
    full_tlh_db = tickerrel.compute_tlh_groups()
    ctdata = CachedTickerInfo(yf_cache)

    not_in_commodities_file = [c for c in ctdata.data if c not in commodities]
    if not_in_commodities_file:
        if include_undeclared:
            for c in not_in_commodities_file:
                commodities[c] = data.Commodity(
                    {}, datetime.datetime.today().date(), c)
        else:
            print("Warning: not in ", cf, file=sys.stderr)
            print(not_in_commodities_file, file=sys.stderr)
            print("Simply declare them in your commodities file, and re-rerun this util to fill in their metadata",
                  file=sys.stderr)

    # update a_* metadata
    for c, metadata in commodities.items():
        if c in ctdata.data:
            if tickerrel.substsimilars(c):
                metadata.meta[prefix + 'substsimilars'] = ','.join(tickerrel.substsimilars(c))
            if c in full_tlh_db:
                metadata.meta[prefix + 'tlh_partners'] = ','.join(full_tlh_db[c])
            for m in auto_metadata:
                if m in ctdata.data[c] and ctdata.data[c][m]:
                    if m in auto_metadata_appends:
                        mdval = set(metadata.meta.get(prefix + m, '').split(','))
                        mdval = set() if mdval == set(['']) else mdval
                        mdval.add(str(ctdata.data[c][m]))
                        metadata.meta[prefix + m] = ','.join(sorted(list(mdval)))
                    else:
                        label = label_transform(m, prefix)
                        value = value_transform(ctdata.data[c][m], m)
                        metadata.meta[label] = value
    cv = list(commodities.values())
    cv.sort(key=lambda x: x.currency)

    with open(cf, "w") if write_file and confirm_overwrite else sys.stdout as fout:
        print(f"; Generated by: {os.path.basename(__file__)}, at {datetime.datetime.today().isoformat()}",
              file=fout)
        fout.flush()
        printer.print_entries(cv, file=fout)

    if write_file and not confirm_overwrite:
        print(
            f"Not overwriting {cf} because --confirm-overwrite was not specified")

# def rewrite_er():
#     ctdata = CachedTickerInfo(yf_cache)
#     for ticker in ctdata.data:
#         if 'annualReportExpenseRatio' in ctdata.data[ticker] and ctdata.data[ticker]['annualReportExpenseRatio']:
#             er = ctdata.data[ticker]['annualReportExpenseRatio']
#             print(ticker, '\t', er)
#             # ctdata.data[ticker]['annualReportExpenseRatio'] = round(er/100, 2)
#     # ctdata.write_cache()


def generate_fund_info(cf=os.getenv('BEAN_COMMODITIES_FILE'), prefix='a__'):
    """Generate fund info for importers (from commodity directives in the beancount input file)"""
    tickerrel = RelateTickers(cf)
    commodities = tickerrel.db

    fund_data = []
    for c in commodities:
        cd = commodities[c]
        isins = cd.meta.get(prefix + 'isin', '').split(',')
        for i in isins:
            fund_data.append(
                (c, i, cd.meta.get('name', 'Ticker long name unavailable')))

    money_market = [c for c in commodities if commodities[c].meta.get(
        prefix + 'quoteType', '') == 'MONEYMARKET']
    fund_info = {'fund_data': fund_data, 'money_market': money_market}
    return fund_info


@cli.command(aliases=['show'])
@cf_option
@click.option('--prefix', help="Metadata label prefix for generated metadata", default='a__')
def show_fund_info(cf, prefix):
    """Show info that is generated for importers (from commodity directives in the beancount input file)"""
    fund_info = generate_fund_info(cf, prefix)
    click.echo_via_pager('\n'.join(str(i) for i in fund_info['fund_data'] + ['\nMoney Market:',
                         str(fund_info['money_market'])]))


@relate.command(aliases=['eq'])
@cf_option
def find_equivalents(cf):
    """Determine equivalent groups of commodities, from an incomplete specification."""

    tickerrel = RelateTickers(cf)
    retval = tickerrel.build_commodity_groups(['equivalent'])
    for r in retval:
        print(r)


@relate.command(aliases=['sim'])
@cf_option
def find_similars(cf):
    """Determine substantially similar groups of commodities from an incomplete specification. Includes
    equivalents."""

    tickerrel = RelateTickers(cf)
    retval = tickerrel.build_commodity_groups(['equivalent', 'substsimilar'])
    for r in retval:
        print(r)


@relate.command(aliases=['archives'])
@cf_option
def list_archived(cf):
    """List archived commodities."""

    tickerrel = RelateTickers(cf)
    archived = tickerrel.archived
    for r in archived:
        print(r)


@relate.command(aliases=['tlh'])
@cf_option
def find_tlh_groups(cf):
    """Determine Tax Loss Harvest partner groups."""
    tickerrel = RelateTickers(cf)
    full_tlh_db = tickerrel.compute_tlh_groups()
    for t, partners in sorted(full_tlh_db.items()):
        print("{:<5}".format(t), partners)


if __name__ == '__main__':
    cli()

# TODOs
# - create new commodity entries as needed, when requested
# - cusip info: https://www.quantumonline.com/search.cfm
