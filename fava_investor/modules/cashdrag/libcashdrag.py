#!/bin/env python3

from beancount.core.number import ZERO, Decimal, D
import collections
import locale

def find_cash_commodities(accapi, options):
    """Build list of commodities that are considered cash"""

    meta_label = options.get('metadata_label_cash', 'asset_allocation_Bond_Cash')
    cash_commodities = []
    for commodity, declaration in accapi.get_commodity_map().items():
        if declaration.meta.get(meta_label, 0) == 100:
            cash_commodities.append(commodity)

    cash_commodities.append(accapi.get_operating_currency())
    cash_commodities = set(cash_commodities)
    commodities_pattern = '(' + '|'.join(cash_commodities) + ')'
    return commodities_pattern

def find_loose_cash(accapi, options):
    """Find uninvested cash in specified accounts"""

    sql = """
    SELECT account AS account,
           sum(position) AS position
      WHERE account ~ '{accounts_pattern}'
      AND not account ~ '{accounts_exclude_pattern}'
      AND currency ~ '{currency}'
    GROUP BY account
    ORDER BY sum(position) DESC
    """.format(accounts_pattern=options.get('accounts_pattern', '^Assets'),
            accounts_exclude_pattern=options.get('accounts_exclude_pattern', '^XXX'), #TODO
            currency=find_cash_commodities(accapi, options))
    rtypes, rrows = accapi.query_func(sql)
    if not rtypes:
        return [], {}, [[]]

    rrows = [r for r in rrows if not r.position.is_empty()]
    return rtypes, rrows
