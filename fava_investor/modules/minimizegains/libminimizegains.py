#!/bin/env python3
"""Determine what assets to sell to minimize gains."""

import collections
from datetime import datetime
from fava_investor.common.libinvestor import val
from beancount.core.number import Decimal, D
from fava_investor.modules.tlh import libtlh


def find_minimized_gains(accapi, options):
    account_field = libtlh.get_account_field(options)
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

    # our output table is slightly different from our query table:
    retrow_types = rtypes[:-1] + [('gain', Decimal), ('marginal_percent', Decimal), ('term', str)]

    # rtypes:
    # [('account', <class 'str'>),
    #  ('units', <class 'beancount.core.inventory.Inventory'>),
    #  ('acquisition_date', <class 'datetime.date'>),
    #  ('market_value', <class 'beancount.core.inventory.Inventory'>),
    #  ('basis', <class 'beancount.core.inventory.Inventory'>)]

    RetRow = collections.namedtuple('RetRow', [i[0] for i in retrow_types])

    to_sell = []
    for row in rrows:
        if row.market_value.get_only_position():
            gain = D(val(row.market_value) - val(row.basis))
            term = libtlh.gain_term(row.acquisition_date, datetime.today().date())

            to_sell.append(RetRow(row.account, row.units, row.acquisition_date,
                                  row.market_value, gain, (gain/val(row.market_value))*100, term))

    to_sell.sort(key=lambda x: x.marginal_percent)

    # add cumulative column
    retrow_types = retrow_types + [('cumu_proceeds', Decimal), ('cumu_gains', Decimal),
            ('percent', Decimal)]
    RetRow = collections.namedtuple('RetRow', [i[0] for i in retrow_types])
    retval = []
    cumu_proceeds = cumu_gains = 0
    for row in to_sell:
        cumu_gains += row.gain
        cumu_proceeds += val(row.market_value)
        retval.append(RetRow(*row, cumu_proceeds, cumu_gains, (cumu_gains/cumu_proceeds)*100))

    return retrow_types, retval
