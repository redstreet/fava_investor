#!/bin/env python3

import re
import fava_investor.common.libinvestor as libinvestor
from beancount.core.inventory import Inventory
from beancount.core.data import Close


# TODO:
# - for each commodity_leaf account, ensure there is a parent, else print
# - get market_value, not balance

p_leaf = re.compile('^[A-Z0-9]*$')

def is_commodity_leaf(acc):
    leaf = acc.rsplit(':')[-1]
    is_leaf = p_leaf.match(leaf)
    if is_leaf:
        return True
    return False

def find_active_accounts(accapi, options):
    """Build list of investment and bank accounts that are open"""

    balances = get_balances(accapi)

    active_accounts = []
    ocs = accapi.get_account_open_close()
    for acc in ocs.keys():
        if acc.startswith('Assets:Investments') or acc.startswith('Assets:Banks'):
            if not is_commodity_leaf(acc):
                closes = [e for e in ocs[acc] if isinstance(e, Close)]
                if not closes:
                    active_accounts.append((acc, balances.get(acc, Inventory())))
    active_accounts.sort(key=lambda x: x[1])
    return active_accounts


def get_balances(accapi):
    """Find all balances"""

    sql = f"balances"
    rtypes, rrows = accapi.query_func(sql)

    if not rtypes:
        return [], {}, [[]]
    # print(rtypes)
    # print(rrows)

    balances = {acc: bal for acc, bal in rrows}
    # import pdb; pdb.set_trace()
    # return rtypes, rrows, balances
    return balances

    # footer = libinvestor.build_table_footer(rtypes, rrows, accapi)
    # return rtypes, rrows, None, footer
