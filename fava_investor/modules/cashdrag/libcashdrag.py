#!/bin/env python3

from beancount.core.number import ZERO, Decimal, D
import collections
import locale

def val(inv):
    return inv.get_only_position().units.number

def find_cash_commodities(accapi, options):
    """Build list of commodities that are considered cash"""

    meta_label = options.get('metadata_label_cash', 'asset_allocation_Bond_Cash')
    cash_commodities = []
    for commodity, declaration in accapi.get_commodity_map().items():
        if declaration.meta.get(meta_label, 0) == 100:
            cash_commodities.append(commodity)

    operating_currencies = accapi.get_operating_currencies()
    cash_commodities += operating_currencies
    cash_commodities = set(cash_commodities)
    commodities_pattern = '(' + '|'.join(cash_commodities) + ')'
    return commodities_pattern, operating_currencies[0]

def find_loose_cash(accapi, options):
    """Find uninvested cash in specified accounts"""

    currencies_pattern, base_currency = find_cash_commodities(accapi, options)
    sql = """
    SELECT account AS account,
           sum(position) AS position,
           sum(convert(position, '{base_currency}')) as value
      WHERE account ~ '{accounts_pattern}'
      AND not account ~ '{accounts_exclude_pattern}'
      AND currency ~ '{currencies_pattern}'
    GROUP BY account
    ORDER BY sum(position) DESC
    """.format(accounts_pattern=options.get('accounts_pattern', '^Assets'),
            accounts_exclude_pattern=options.get('accounts_exclude_pattern', '^XXX'), #TODO
            base_currency=base_currency,
            currencies_pattern=currencies_pattern,
            )
    rtypes, rrows = accapi.query_func(sql)
    if not rtypes:
        return [], {}, [[]]

    total_cash = 0
    rrows_new = []
    RetRow = collections.namedtuple('RetRow', [i[0] for i in rtypes[:-1]])
    for r in rrows:
        if not r.position.is_empty():
            rrows_new.append(RetRow(r.account, r.position))
            total_cash += val(r.value)

    return rtypes[:-1], rrows_new, total_cash
