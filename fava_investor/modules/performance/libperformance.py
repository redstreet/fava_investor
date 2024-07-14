#!/bin/env python3
"""
# Gains Minimizer
_Determine lots to sell to minimize capital gains taxes._

See accompanying README.txt
"""

import collections
from datetime import date, timedelta
from fava_investor.common.libinvestor import build_config_table
from beancount.core.number import Decimal
from fava_investor.modules.tlh import libtlh

def calculate_error_grad(investments: list[date, Decimal], guess: Decimal) -> tuple[Decimal, Decimal]:
    sum: Decimal = 0
    grad: Decimal = 0
    init_date: date = investments[0][0]
    for item in investments:
        investment_date = item[0]
        value = item[1]
        time_step = Decimal(((investment_date - init_date)/timedelta(days=1))/365)
        sum += value / (1 + guess)**time_step
        grad += -time_step * value / (1 + guess)**(time_step + 1)

    return sum, grad

def calculate_xirr(investments: list[date, Decimal], accuracy) -> Decimal:
    guess = Decimal(0.1)

    for _ in range(10):
        value, grad = calculate_error_grad(investments, guess)
        correction: Decimal = value / grad
        guess -= correction
        if abs(value) < 1 and correction < 10**(-accuracy-2):
            break

    return round(guess*100, accuracy)

def find_xirrs(accapi, options):
    account_field = libtlh.get_account_field(options)
    accounts_pattern = options.get('accounts_pattern', '')
    accuracy = int(options.get('accuracy', 2))

    currency = accapi.get_operating_currencies()[0]

    sql = f"""
    SELECT
        {account_field} as account,
        CONVERT(value(position, date), '{currency}') as market_value,
        date as date
      WHERE account_sortkey(account) ~ "^[01]" AND
        account ~ '{accounts_pattern}'
    """
    rtypes, rrows = accapi.query_func(sql)
    if not rtypes:
        return [], {}, [[]]

    sql = f"""
    SELECT
        {account_field} as account,
        ONLY('{currency}', NEG(CONVERT(sum(position), '{currency}'))) as market_value,
        cost_date as date
      WHERE account_sortkey(account) ~ "^[01]" AND
        account ~ '{accounts_pattern}'
      GROUP BY {account_field}, date, account_sortkey(account)
      ORDER BY account_sortkey(account)
    """
    remaintypes, remainrows = accapi.query_func(sql)
    if not remaintypes:
        return [], {}, [[]]

    investments = {}
    for row in rrows:
        if row.account not in investments.keys():
            investments[row.account] = []
        investments[row.account].append([row.date, row.market_value.number])
    for row in remainrows:
        if row.market_value.number != 0:
            investments[row.account].append([date.today(), row.market_value.number])

    xirr = {key: calculate_xirr(investments[key], accuracy) for key in investments}

    retrow_types = [('account', str), ('XIRR', Decimal)]
    RetRow = collections.namedtuple('RetRow', [i[0] for i in retrow_types])
    rrows = [RetRow(key, value) for key, value in xirr.items()]

    tables = [build_config_table(options)]
    tables.append(('XIRR performance', (retrow_types, rrows, None, None)))
    return tables
