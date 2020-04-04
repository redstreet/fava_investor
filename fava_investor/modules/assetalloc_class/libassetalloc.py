#!/usr/bin/env python3
# Description: Beancount script for asset allocation reporting

import argparse,argcomplete,argh
import re
import sys

from collections import defaultdict

from beancount.core import convert
from beancount.core import amount
from beancount.core import inventory
from beancount.core import realization
from beancount.core.number import Decimal

def bucketize(vbalance, base_currency, accapi):
    price_map = accapi.build_price_map()
    commodity_map = accapi.get_commodity_map()

    # Main part: put each commodity's value into asset buckets
    asset_buckets = defaultdict(int)
    for pos in vbalance.get_positions():
        amount = convert.convert_position(pos, base_currency, price_map)
        if amount.number < 0:
            # print("Warning: skipping negative balance:", pos) #TODO
            continue
        if amount.currency == pos.units.currency and amount.currency != base_currency:
            sys.stderr.write("Error: unable to convert {} to base currency {} (Missing price directive?)\n".format(pos, base_currency))
            sys.exit(1)
        commodity = pos.units.currency
        metas = commodity_map[commodity].meta
        unallocated = Decimal('100')
        for meta in metas:
            if meta.startswith('asset_allocation_'):
                asset_buckets[meta[len('asset_allocation_'):]] += amount.number * (metas[meta] / 100)
                unallocated -= metas[meta]
        if unallocated:
            print("Warning: {} asset_allocation_* metadata does not add up to 100%. Padding with 'unknown'.".format(commodity))
            asset_buckets['unknown'] += amount.number * (unallocated / 100)
    return asset_buckets

def compute_percent(asset_buckets, asset, total_assets):
    return (asset_buckets[asset]/total_assets)*100

def compute_percent_subtotal(asset_buckets, asset, total_assets):
    return (compute_balance_subtotal(asset_buckets, asset) / total_assets) * 100

def compute_balance_subtotal(asset_buckets, asset):
    children = [k for k in asset_buckets.keys() if k.startswith(asset) and k != asset]
    subtotal = asset_buckets[asset]
    for c in children:
        subtotal += compute_balance_subtotal(asset_buckets, c)
    return subtotal


def tabulate_asset_buckets(asset_buckets):
    ''' Convert asset allocation into a hierarchical tabulation '''
    # print(balance.reduce(convert.get_units))

    table = []
    total_assets = sum(asset_buckets[k] for k in asset_buckets)
    buckets = list(asset_buckets.keys())

    # add all parents in the asset allocation hierarchy
    parents = set()
    for b in buckets:
        for i in range(1, b.count('_')+1):
            parents.add( b.rsplit('_', i)[0] )
    buckets = list(set(list(parents) + buckets))

    buckets.sort()
    for bucket in buckets:
        table.append([len(bucket.split('_')),
            bucket,
            compute_percent_subtotal(asset_buckets, bucket, total_assets),
            compute_balance_subtotal(asset_buckets, bucket)
            ])
            
    headers=['Hierarchy', 'Asset Type', 'Percentage', 'Amount']
    return headers, table


def build_interesting_realacc(accapi, accounts):
    def is_included_account(realacc):
        for pattern in accounts:
            if re.match(pattern, realacc.account):
                if realacc.balance == inventory.Inventory():
                    return False # Remove empty accounts to "clean up" the tree
                return True
        return False

    realroot = accapi.realize()

    # first, filter out accounts that are not specified:
    realacc = realization.filter(realroot, is_included_account)

    if not realacc:
        sys.stderr.write("No included accounts found. (Your --accounts <regex> failed to match any account)\n")
        sys.exit(1)

    # However, realacc includes all ancestor accounts of specified accounts, and their balances. For example,
    # if we specified 'Accounts:Investments:Brokerage', balances due to transactions on 'Accounts:Investments'
    # will also be included. We need to filter these out:
    for acc in realization.iter_children(realacc):
        if not is_included_account(acc):
            acc.balance = inventory.Inventory()
    return realacc

def scale_inventory(balance, tax_adj):
    '''Scale inventory by tax adjustment'''
    scaled_balance = inventory.Inventory()
    for pos in balance.get_positions():
        scaled_pos = amount.Amount(pos.units.number * (Decimal(tax_adj/100)), pos.units.currency)
        scaled_balance.add_amount(scaled_pos)
    return scaled_balance


# TODO
# def tax_adjust(realacc, accapi):
#     account_open_close = getters.get_account_open_close(accapi)
#     for acc in realization.iter_children(realacc):
#         if acc.account in account_open_close:
#             tax_adj = account_open_close[acc.account][0].meta.get('asset_allocation_tax_adjustment', 100)
#             acc.balance = scale_inventory(acc.balance, tax_adj)
#     return realacc

def assetalloc(accapi, config={}):
    realacc = build_interesting_realacc(accapi, config.get('accounts_pattern', ['.*']))
    # if not config['skip_tax_adjustment']:
    #     tax_adjust(realacc, accapi)
    balance = realization.compute_balance(realacc)
    vbalance = balance.reduce(convert.get_units)
    asset_buckets = bucketize(vbalance, config['base_currency'], accapi)

    return asset_buckets, tabulate_asset_buckets(asset_buckets), realacc
