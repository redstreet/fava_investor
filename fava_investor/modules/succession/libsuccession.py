#!/bin/env python3

import re
import fava_investor.common.libinvestor as libinvestor
from beancount.core.inventory import Inventory
from beancount.core.data import Close
from beancount.core import realization


# TODO:
# - print balances nicely, sort by them, show what percent is complete
#   - for each commodity_leaf account, ensure there is a parent, else print

p_leaf = re.compile('^[A-Z0-9]*$')
acc_pattern = re.compile('^Assets:(Investments|Banks)')
meta_prefix = 'beneficiary'

def is_commodity_leaf(acc, ocs):
    splits = acc.rsplit(':', maxsplit=1)
    parent = splits[0]
    leaf = splits[-1]
    is_commodity = p_leaf.match(leaf)
    if is_commodity:
        return parent in ocs
    return False

def find_active_accounts(accapi, options):
    """Build list of investment and bank accounts that are open"""

    balances = get_balances(accapi)
    # realroot = accapi.realize()
    # import pdb; pdb.set_trace()

    active_accounts = []
    ocs = accapi.get_account_open_close()
    for acc in ocs.keys():
        if acc_pattern.match(acc):
            if not is_commodity_leaf(acc, ocs):
                closes = [e for e in ocs[acc] if isinstance(e, Close)]
                if not closes:
                    # active_accounts.append((acc, balances.get(acc, Inventory())))
                    # balance = realization.get(realroot, acc).balance
                    # active_accounts.append((acc, balances.get(acc, balance)))

                    # active_accounts.append((acc, balances.get(acc, Inventory())))

                    metas = {k:v for (k,v) in ocs[acc][0].meta.items() if meta_prefix in k}
                    active_accounts.append((acc, metas))
    # active_accounts.sort(key=lambda x: x[1])
    active_accounts.sort()
    return active_accounts


def get_balances(accapi):
    """Find all balances"""

    currency = accapi.get_operating_currencies()[0]
    sql = f"SELECT account, SUM(CONVERT(position, '{currency}'))"
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
