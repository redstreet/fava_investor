#!/bin/env python3

import fava_investor.common.libinvestor as libinvestor
from beancount.core.inventory import Inventory


def find_cash_commodities(accapi, options):
    """Build list of commodities that are considered cash"""

    meta_label = options.get('metadata_label_cash', 'asset_allocation_Bond_Cash')
    cash_commodities = []
    for commodity, declaration in accapi.get_commodity_directives().items():
        if declaration.meta.get(meta_label, 0) == 100:
            cash_commodities.append(f'^{commodity}$')

    operating_currencies = accapi.get_operating_currencies()
    cash_commodities += map(lambda cur: f'^{cur}$', operating_currencies)
    cash_commodities = set(cash_commodities)
    commodities_pattern = '(' + '|'.join(cash_commodities) + ')'
    return commodities_pattern, operating_currencies[0]


def find_loose_cash(accapi, options):
    """Find uninvested cash in specified accounts"""

    currencies_pattern, main_currency = find_cash_commodities(accapi, options)
    sql = """
    SELECT account AS account,
           CONVERT(sum(position), '{main_currency}') AS position
      WHERE account ~ '{accounts_pattern}'
      AND not account ~ '{accounts_exclude_pattern}'
      AND currency ~ '{currencies_pattern}'
    GROUP BY account
    ORDER BY position DESC
    """.format(main_currency=main_currency,
               accounts_pattern=options.get('accounts_pattern', '^Assets'),
               accounts_exclude_pattern=options.get('accounts_exclude_pattern', '^   $'),  # TODO
               currencies_pattern=currencies_pattern,
               )
    rtypes, rrows = accapi.query_func(sql)
    if not rtypes:
        return [], {}, [[]]

    rrows = [r for r in rrows if r.position != Inventory()]
    threshold = options.get('min_threshold', 0)
    if threshold:
        rrows = [r for r in rrows if r.position.get_only_position().units.number >= threshold]

    footer = libinvestor.build_table_footer(rtypes, rrows, accapi)
    return [('Cash Drag Analysis', (rtypes, rrows, None, footer))]
