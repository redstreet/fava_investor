#!/usr/bin/env python3
# Description: Beancount script for asset allocation reporting

import argparse,argcomplete,argh
import collections
import os
import re
import sys

from beancount.core import convert
from beancount.core import amount
from beancount.core import inventory
from beancount.core import realization
from beancount.core.number import Decimal

sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', 'common'))
from libinvestor import *

def compute_child_balances(node, total):
    node.balance_children = node.balance + sum(compute_child_balances(c, total) for c in node.children)
    node.percentage = (node.balance / total) * 100
    node.percentage_children = (node.balance_children / total) * 100
    return node.balance_children

def compute_parent_balances(node):
    if node.parent:
        node.percentage_parent = (node.balance_children / node.parent.balance_children) * 100
    else:
        node.percentage_parent = 100
    for c in node.children:
        compute_parent_balances(c)

def treeify(asset_buckets):
    root = Node('Total')
    root.balance = 0
    for bucket, balance in asset_buckets.items():
        path = bucket.split('_')
        node = root
        for p in path:
            new_node = node.find_child(p)
            if not new_node:
                new_node = Node(p)
                new_node.balance = 0
                node.add_child(new_node)
            node = new_node
        node.balance = balance

    total = sum(balance for bucket, balance in asset_buckets.items())
    compute_child_balances(root, total)
    compute_parent_balances(root)
    return root


def bucketize(vbalance, accapi):
    price_map = accapi.build_price_map()
    commodity_map = accapi.get_commodity_map()
    base_currency = accapi.get_operating_currencies()[0]

    # Main part: put each commodity's value into asset buckets
    asset_buckets = collections.defaultdict(int)
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


def tax_adjust(realacc, accapi):
    def scale_inventory(balance, tax_adj):
        """Scale inventory by tax adjustment"""
        scaled_balance = inventory.Inventory()
        for pos in balance.get_positions():
            scaled_pos = amount.Amount(pos.units.number * (Decimal(tax_adj/100)), pos.units.currency)
            scaled_balance.add_amount(scaled_pos)
        return scaled_balance

    account_open_close = accapi.get_account_open_close()
    for acc in realization.iter_children(realacc):
        if acc.account in account_open_close:
            tax_adj = account_open_close[acc.account][0].meta.get('asset_allocation_tax_adjustment', 100)
            acc.balance = scale_inventory(acc.balance, tax_adj)
    return realacc

def assetalloc(accapi, config={}):
    realacc = build_interesting_realacc(accapi, config.get('accounts_patterns', ['.*']))

    if config.get('skip_tax_adjustment', False) is True:
        tax_adjust(realacc, accapi)

    balance = realization.compute_balance(realacc)
    vbalance = balance.reduce(convert.get_units)
    asset_buckets = bucketize(vbalance, accapi)

    return treeify(asset_buckets), realacc
