#!/bin/env python3

from beancount.core.number import ZERO, Decimal, D
import collections
import locale

def find_loose_cash(accapi, options):
    """Find uninvested cash in specified accounts"""

    sql = """
    SELECT account AS account,
           sum(position) AS position
      WHERE account ~ '{whitelist}'
      AND not account ~ '{blacklist}'
      AND currency ~ '{currency}'
    GROUP BY account
    ORDER BY sum(position) DESC
    """.format(whitelist=options.get('whitelist', '^Assets'),
            blacklist=options.get('blacklist', '^XXX'), #TODO
            currency=accapi.get_operating_currency())
    rtypes, rrows = accapi.query_func(sql)
    if not rtypes:
        return [], {}, [[]]

    rrows = [r for r in rrows if not r.position.is_empty()]
    return rtypes, rrows
