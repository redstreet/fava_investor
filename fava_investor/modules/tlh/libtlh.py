#!/bin/env python3
"""Tax loss harvesting library for Beancount. Determines tax loss harvestable commodities, and potential wash
sales, after account for substantially similar funds."""

import collections
import locale
import itertools
from datetime import datetime
from dateutil import relativedelta
from fava_investor.common.libinvestor import val, build_table_footer
from beancount.core.number import Decimal, D
from beancount.core.inventory import Inventory


def get_tables(accapi, options):
    retrow_types, to_sell, recent_purchases = find_harvestable_lots(accapi, options)
    harvestable_table = retrow_types, to_sell
    by_commodity = harvestable_by_commodity(accapi, options, *harvestable_table)
    summary = summarize_tlh(harvestable_table, by_commodity)
    recents = build_recents(recent_purchases)

    harvestable_table = sort_harvestable_table(harvestable_table, by_commodity)
    return harvestable_table, summary, recents, by_commodity


def sort_harvestable_table(harvestable_table, by_commodity):
    """Sort the main table (harvestable_table) in the order of highest to lowest losses."""
    sort_order = [i.currency for i in by_commodity[1]]

    def order(elem):
        return sort_order.index(elem.ticker)

    harvestable_table[1].sort(key=order)
    return harvestable_table


def insert_column(cols, col_name, col_type, new_col_name, new_col_type=str):
    """Inserts a column right after col_name. If col_type is specified (is not None), changes the type fo
    col_name to col_type"""
    retval = []
    for col, ctype in cols:
        if col == col_name:
            if col_type is None:
                col_type = ctype
            retval.append((col_name, col_type))
            retval.append((new_col_name, new_col_type))
        else:
            retval.append((col, ctype))
    return retval


def split_currency(value):
    units = value.get_only_position().units
    return units.number, units.currency


def gain_term(bought, sold):
    diff = relativedelta.relativedelta(sold, bought)
    # relativedelta is used to account for leap years, since IRS defines 'long/short' as "> 1 year"
    if diff.years > 1 or (diff.years == 1 and (diff.months >= 1 or diff.days >= 1)):
        return 'Long'
    return 'Short'


def get_metavalue(ticker, directives, mlabel):
    metadata = {} if directives.get(ticker) is None else directives[ticker].meta
    return metadata.get(mlabel, '')  # Why a string?
    # for multiple values
    # values = [metadata[mlabel] for mlabel in mlabels if mlabel in metadata]
    # return ','.join(values)


def get_account_field(options):
    account_field = options.get('account_field', 'LEAF(account)')
    try:
        if isinstance(account_field, int):
            account_field = ['account',
                             'LEAF(account)',
                             'GREPN("(.*):([^:]*):", account, 2)'  # get one-but-leaf account
                             ][account_field]
    except ValueError:
        pass
    return account_field


def find_harvestable_lots(accapi, options):
    """Find tax loss harvestable lots.
    - This is intended for the US, but may be adaptable to other countries.
    - This assumes SpecID (Specific Identification of Shares) is the method used for these accounts
    """

    account_field = get_account_field(options)
    accounts_pattern = options.get('accounts_pattern', '')

    sql = f"""
    SELECT {account_field} as account,
        units(sum(position)) as units,
        cost_date as acquisition_date,
        value(sum(position)) as market_value,
        cost(sum(position)) as basis
      WHERE account_sortkey(account) ~ "^[01]" AND
        account ~ '{accounts_pattern}'
      GROUP BY {account_field}, cost_date, currency, cost_currency, cost_number, account_sortkey(account)
      ORDER BY account_sortkey(account), currency, cost_date
    """
    rtypes, rrows = accapi.query_func(sql)
    if not rtypes:
        return [], {}, [[]]

    # Since we GROUP BY cost_date, currency, cost_currency, cost_number, we never expect any of the
    # inventories we get to have more than a single position. Thus, we can and should use
    # get_only_position() below. We do this grouping because we are interested in seeing every lot (price,
    # date) seperately, that can be sold to generate a TLH

    loss_threshold = options.get('loss_threshold', 1)

    # our output table is slightly different from our query table:
    retrow_types = rtypes[:-1] + [('loss', Decimal), ('term', str), ('wash', str)]
    retrow_types = insert_column(retrow_types, 'units', Decimal, 'ticker', str)
    retrow_types = insert_column(retrow_types, 'market_value', Decimal, 'currency', str)

    # rtypes:
    # [('account', <class 'str'>),
    #  ('units', <class 'beancount.core.inventory.Inventory'>),
    #  ('acquisition_date', <class 'datetime.date'>),
    #  ('market_value', <class 'beancount.core.inventory.Inventory'>),
    #  ('basis', <class 'beancount.core.inventory.Inventory'>)]

    RetRow = collections.namedtuple('RetRow', [i[0] for i in retrow_types])

    # build our output table: calculate losses, find wash sales
    to_sell = []
    recent_purchases = {}
    commodities = accapi.get_commodity_directives()
    wash_buy_counter = itertools.count()
    mlabel = options.get('substantially_similars_meta_label', 'substantially_similars')

    for row in rrows:
        if row.market_value.get_only_position() and \
                (val(row.market_value) - val(row.basis) < -loss_threshold):
            loss = D(val(row.basis) - val(row.market_value))

            term = gain_term(row.acquisition_date, datetime.today().date())

            # find wash sales
            units, ticker = split_currency(row.units)
            recent, wash_id = recent_purchases.get(ticker, (None, None))
            if not recent:
                similars = get_metavalue(ticker, commodities, mlabel)
                ticksims = [ticker] + similars.split(',') if similars else [ticker]
                recent = query_recently_bought(ticksims, accapi, options)
                wash_id = ''
                if len(recent[1]):
                    wash_id = next(wash_buy_counter)
                for t in ticksims:
                    recent_purchases[t] = (recent, wash_id)
            wash = wash_id if len(recent[1]) else ''

            to_sell.append(RetRow(row.account, units, ticker, row.acquisition_date,
                                  *split_currency(row.market_value), loss, term, wash))

    return retrow_types, to_sell, recent_purchases


def harvestable_by_commodity(accapi, options, rtype, rrows):
    """Group input by sum(commodity)
    """

    retrow_types = [('currency', str), ('total_loss', Decimal), ('market_value', Decimal), ('alt', str)]
    RetRow = collections.namedtuple('RetRow', [i[0] for i in retrow_types])

    losses = collections.defaultdict(Decimal)
    market_value = collections.defaultdict(Decimal)
    for row in rrows:
        losses[row.ticker] += row.loss
        market_value[row.ticker] += row.market_value

    by_commodity = []
    commodities = accapi.get_commodity_directives()
    mlabel = options.get('tlh_partners_meta_label', 'tlh_alternates')
    for ticker, loss in sorted(losses.items(), key=lambda x: x[1], reverse=True):
        alts = get_metavalue(ticker, commodities, mlabel).replace(',', ', ')
        by_commodity.append(RetRow(ticker, loss, market_value[ticker], alts))

    return retrow_types, by_commodity


def build_recents(recent_purchases):
    recents = []
    types = []
    for _, ((header, rows), wash_id) in recent_purchases.items():
        if len(rows):
            types = header + [('wash', str)]
            RetRow = collections.namedtuple('RetRow', [i[0] for i in types])
            rows = [RetRow(*row, wash_id) for row in rows]
            recents += rows

    # dedupe recents
    recents_dd = []
    [recents_dd.append(r) for r in recents if r not in recents_dd]
    return types, recents_dd


def gen_ticker_expression(tickers):
    """tickers is either a list, or a comma separated string of one or more tickers"""
    if isinstance(tickers, str):
        tickers = tickers.split(',')
    expr = [f'CURRENCY = "{t}" OR' for t in tickers]
    expr = ' '.join(expr)
    expr = expr[:-3]
    return f"({expr})"


def query_recently_bought(tickers, accapi, options):
    """Looking back 30 days for purchases that would cause wash sales"""

    wash_pattern = options.get('wash_pattern', '')
    account_field = get_account_field(options)
    wash_pattern_sql = 'AND account ~ "{}"'.format(wash_pattern) if wash_pattern else ''
    ticker_expr = gen_ticker_expression(tickers)
    sql = '''
    SELECT
        {account_field} as account,
        date as acquisition_date,
        DATE_ADD(date, 31) as earliest_sale,
        units(sum(position)) as units,
        cost(sum(position)) as basis
      WHERE
        number > 0 AND
        date >= DATE_ADD(TODAY(), -30) AND
        {ticker_expr}
        {wash_pattern_sql}
      GROUP BY {account_field},date,earliest_sale
      ORDER BY date DESC
      '''.format(**locals())
    rtypes, rrows = accapi.query_func(sql)
    return rtypes, rrows


def recently_sold_at_loss(accapi, options):
    """Looking back 30 days for sales that caused losses. These were likely to have been TLH (but not
    necessarily so). This tells us what NOT to buy in order to avoid wash sales."""

    operating_currencies = accapi.get_operating_currencies_regex()
    wash_pattern = options.get('wash_pattern', '')
    account_field = get_account_field(options)
    wash_pattern_sql = 'AND account ~ "{}"'.format(wash_pattern) if wash_pattern else ''
    sql = '''
    SELECT
        date as sale_date,
        DATE_ADD(date, 30) as until,
        currency,
        NEG(SUM(COST(position))) as basis,
        NEG(SUM(CONVERT(position, cost_currency, date))) as proceeds
      WHERE
        date >= DATE_ADD(TODAY(), -30)
        AND number < 0
        AND not currency ~ "{operating_currencies}"
      GROUP BY sale_date,until,currency
      '''.format(**locals())
    rtypes, rrows = accapi.query_func(sql)
    if not rtypes:
        return [], []

    # filter out losses
    rtypes = insert_column(rtypes, 'currency', None, 'similars', str)
    rtypes = rtypes + [('loss', Inventory)]
    RetRow = collections.namedtuple('RetRow', [i[0] for i in rtypes])
    return_rows = []

    commodities = accapi.get_commodity_directives()
    mlabel = options.get('substantially_similars_meta_label', 'substantially_similars')
    for row in rrows:
        loss = Inventory(row.proceeds)
        loss.add_inventory(-(row.basis))
        if loss != Inventory() and val(loss) < 0:
            similars = get_metavalue(row.currency, commodities, mlabel).replace(',', ', ')
            return_rows.append(RetRow(row.sale_date, row.until, row.currency, similars, row.basis,
                                      row.proceeds, loss))

    footer = build_table_footer(rtypes, return_rows, accapi)
    return rtypes, return_rows, None, footer


def summarize_tlh(harvestable_table, by_commodity):
    # Summary

    locale.setlocale(locale.LC_ALL, '')

    to_sell = harvestable_table[1]
    summary = {}
    summary["Total harvestable loss"] = sum(i.loss for i in to_sell)
    summary["Total sale value required"] = sum(i.market_value for i in to_sell)
    summary["Commmodities with a loss"] = len(by_commodity[1])
    summary["Number of lots to sell"] = len(to_sell)
    unique_txns = set((r.account, r.ticker) for r in to_sell)
    summary["Total unique transactions"] = len(unique_txns)
    summary = {k: '{:n}'.format(int(v)) for k, v in summary.items()}
    return summary
