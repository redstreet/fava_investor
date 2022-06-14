#!/usr/bin/env python3

import decimal
from beancount.core.inventory import Inventory
from beancount.core import convert


class Node(object):
    """Generic tree implementation. Consider replacing this with anytree"""

    def __init__(self, name):
        self.name = name
        self.children = []
        self.parent = None

    def add_child(self, obj):
        self.children.append(obj)
        obj.parent = self

    def find_child(self, name):
        for child in self.children:
            if child.name == name:
                return child
        return None

    def pre_order(self, level=0):
        yield self, level
        for c in self.children:
            yield from c.pre_order(level + 1)


def val(inv):
    if inv is not None:
        pos = inv.get_only_position()
        if pos is not None:
            return pos.units.number
    if inv.is_empty():
        return 0
    return None


def build_table_footer(types, rows, accapi):
    """Build a footer with sums by default. Looks like: [(<type>, <val>), ...]"""

    def sum_inventories(invs):
        """Sum the given list of inventory into a single inventory"""
        retval = Inventory()
        for i in invs:
            retval.add_inventory(i)
        return retval

    ret_types = [t[1] for t in types]
    ret_values = []
    for label, t in types:
        total = ''
        if t == Inventory:
            total = sum_inventories([getattr(r, label) for r in rows])
            total = total.reduce(convert.convert_position, accapi.get_operating_currencies()[0],
                                 accapi.build_price_map())
        elif t == decimal.Decimal:
            total = sum([getattr(r, label) for r in rows])
        ret_values.append(total)
    return list(zip(ret_types, ret_values))
