#!/bin/env python3

import collections
import re
import fava_investor.common.libinvestor as libinvestor
from beancount.core.inventory import Inventory
from beancount.core.data import Close
from beancount.core import realization
from beancount.core import convert


# TODO:
# - print balances nicely, sort by them, show what percent is complete
#   - for each commodity_leaf account, ensure there is a parent, else print


p_leaf = re.compile('^[A-Z0-9]*$')

def partial_order(header, options):
    """Order the header according to our preference, but don't lose unspecified keys"""
    # take advantage of python 3.7+'s insertion order preservation

    retval = {}
    for c in options['col_order']:
        if c in header:
            retval[c] = header[c]

    for h in header:
        if h not in retval:
            retval[h] = header[h]

    return retval 


def is_commodity_leaf(acc, ocs):
    splits = acc.rsplit(':', maxsplit=1)
    parent = splits[0]
    leaf = splits[-1]
    is_commodity = p_leaf.match(leaf)
    if is_commodity:
        return parent in ocs
    return False

def build_table(accapi, options):
    rows = find_active_accounts(accapi, options)
    all_keys = {j: type(i[j]) for i in rows for j in list(i)}
    header = partial_order(all_keys, options)

    # add all keys to all rows
    for i in rows:
        for j in header:
            if j not in i:
                i[j] = ''  # TODO: type could be incorrect

    # so that tabulate builds the column in order
    rows[0] = partial_order(rows[0], options)

    RowTuple = collections.namedtuple('RowTuple', header)
    rows = [RowTuple(**i) for i in rows]
    rtypes = [(k, v) for k,v in header.items()]

    return rtypes, rows, None, None
    # last one is footer. Could summarize # of TBDs, oldest date, etc.


def find_active_accounts(accapi, options):
    """Build list of investment and bank accounts that are open"""

    # balances = get_balances(accapi)
    realacc = accapi.realize()
    pm = accapi.build_price_map()
    currency = accapi.get_operating_currencies()[0]

    p_acc_pattern = re.compile(options['acc_pattern'])
    ml = len(options['meta_prefix'])
    active_accounts = []
    ocs = accapi.get_account_open_close()
    for acc in ocs.keys():
        if p_acc_pattern.match(acc):
            if not is_commodity_leaf(acc, ocs):
                closes = [e for e in ocs[acc] if isinstance(e, Close)]
                if not closes:
                    # active_accounts.append((acc, balances.get(acc, Inventory())))
                    # balance = realization.get(realroot, acc).balance
                    # active_accounts.append((acc, balances.get(acc, balance)))

                    # active_accounts.append((acc, balances.get(acc, Inventory())))
                    
                    if options['meta_skip'] not in ocs[acc][0].meta:
                        row = {k[ml:]:v for (k,v) in ocs[acc][0].meta.items() if options['meta_prefix'] in k}
                        row['account'] = acc
                        row['balance'] = get_balance(realacc, acc, pm, currency)
                        active_accounts.append(row)
    # active_accounts.sort(key=lambda x: x[1])
    active_accounts.sort(key=lambda x: x['account'])
    return active_accounts


def get_balance(realacc, account, pm, currency):
    subtree = realization.get(realacc, account)
    balance = realization.compute_balance(subtree)
    vbalance = balance.reduce(convert.get_units)
    market_value = vbalance.reduce(convert.convert_position, currency, pm)
    val = libinvestor.val(market_value)
    return val
    # return int(val)

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
