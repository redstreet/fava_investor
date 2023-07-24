#!/bin/env python3
"""
# Gains Minimizer
_Determine lots to sell to minimize capital gains taxes._

See accompanying README.txt
"""

import collections
from datetime import datetime
from fava_investor.common.libinvestor import val, build_config_table
from beancount.core.number import Decimal, D
from fava_investor.modules.tlh import libtlh


def find_minimized_gains(accapi, options):
    account_field = libtlh.get_account_field(options)
    accounts_pattern = options.get('accounts_pattern', '')
    tax_rate = {'Short': Decimal(options.get('st_tax_rate', 1)),
                'Long':  Decimal(options.get('lt_tax_rate', 1))}

    currency = accapi.get_operating_currencies()[0]

    sql = f"""
    SELECT
        {account_field} as account,
        units(sum(position)) as units,
        CONVERT(value(sum(position)), '{currency}') as market_value,
        cost_date as acq_date,
        CONVERT(cost(sum(position)), '{currency}') as basis
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
    retrow_types = rtypes[:-1] + [('term', str), ('gain', Decimal),
                                  ('est_tax', Decimal), ('est_tax_percent', Decimal)]

    # rtypes:
    # [('account', <class 'str'>),
    #  ('units', <class 'beancount.core.inventory.Inventory'>),
    #  ('acq_date', <class 'datetime.date'>),
    #  ('market_value', <class 'beancount.core.inventory.Inventory'>),
    #  ('basis', <class 'beancount.core.inventory.Inventory'>)]

    RetRow = collections.namedtuple('RetRow', [i[0] for i in retrow_types])

    to_sell = []
    for row in rrows:
        if row.market_value.get_only_position():
            gain = D(val(row.market_value) - val(row.basis))
            term = libtlh.gain_term(row.acq_date, datetime.today().date())
            est_tax = gain * tax_rate[term]

            to_sell.append(RetRow(row.account, row.units, row.market_value, row.acq_date,
                           term, gain, est_tax, (est_tax / val(row.market_value)) * 100))

    to_sell.sort(key=lambda x: x.est_tax_percent)

    # add cumulative column ([:-2] to remove est_tax and est_tax_percent)
    retrow_types = [('cu_proceeds', Decimal), ('cu_taxes', Decimal),
                    ('tax_avg', Decimal), ('tax_marg', Decimal)] + \
                    retrow_types[:-2] + [('cu_gains', Decimal)]  # noqa: E127

    RetRow = collections.namedtuple('RetRow', [i[0] for i in retrow_types])
    rrows = []
    cumu_proceeds = cumu_gains = cumu_taxes = 0
    prev_cumu_proceeds = prev_cumu_taxes = 0
    for row in to_sell:
        cumu_gains += row.gain
        cumu_proceeds += val(row.market_value)
        cumu_taxes += row.est_tax
        tax_rate_avg = (cumu_taxes / cumu_proceeds) * 100
        tax_rate_marginal = ((cumu_taxes - prev_cumu_taxes) / (cumu_proceeds - prev_cumu_proceeds)) * 100
        rrows.append(RetRow(round(cumu_proceeds, 0),
                            round(cumu_taxes, 0),
                            round(tax_rate_avg, 1),
                            round(tax_rate_marginal, 2),
                            *row[:-2],  # Remove est_tax and est_tax_percent
                            round(cumu_gains, 0)))

        prev_cumu_proceeds = cumu_proceeds
        prev_cumu_taxes = cumu_taxes

    retrow_types = [r for r in retrow_types if r[0] not in ['est_tax', 'est_tax_percent']]
    # rrows, retrow_types = remove_column('gain', rrows, retrow_types)
    tables = [build_config_table(options)]
    tables.append(('Proceeds, Gains, Taxes', (retrow_types, rrows, None, None)))
    return tables
