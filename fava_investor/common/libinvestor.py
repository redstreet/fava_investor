#!/usr/bin/env python3

import collections
import decimal
from beancount.core.inventory import Inventory
from beancount.core import convert  # noqa: F401
from beancount.core.convert import convert_position


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

    def __lt__(self, other):
        return self.name < other.name

    def pre_order(self, level=0):
        yield self, level
        for c in sorted(self.children):
            yield from c.pre_order(level + 1)


def val(inv):
    if inv is not None:
        pos = inv.get_only_position()
        if pos is not None:
            return pos.units.number
    if inv.is_empty():
        return 0
    return None


def remove_column(col_name, rows, types):
    """Remove a column by name from a beancount query return pair of rows and types"""
    try:
        col = [i for i in types if i[0] == col_name][0]
    except IndexError:  # Col not found
        return rows, types
    idx = types.index(col)

    del types[idx]
    RetRow = collections.namedtuple('RetRow', [i[0] for i in types])
    rrows = []
    for r in rows:
        tmp = list(r)
        del tmp[idx]
        rrows.append(RetRow(*tmp))
    return rrows, types


def insert_column(cols, col_name, col_type, new_col_name, new_col_type=str):
    """Inserts a column right after col_name. in a list of data types returned by a beancount query
    If col_type is specified (is not None), changes the type of col_name to col_type."""

    retval = []
    for col, ctype in cols:
        if col == col_name:
            if col_type is None:
                col_type = ctype
            retval.append((col_name, col_type))
            retval.append((new_col_name, new_col_type))
        else:
            retval.append((col, ctype))
    return retval


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
            total = total.reduce(convert_position, accapi.get_operating_currencies()[0],
                                 accapi.build_beancount_price_map())
        elif t == decimal.Decimal:
            total = sum([getattr(r, label) for r in rows])
        ret_values.append(total)
    return list(zip(ret_types, ret_values))


def build_config_table(options):
    """Build a table listing the config options."""

    retrow_types = [('Key', str), ('Value', str)]
    RetRow = collections.namedtuple('RetRow', [i[0] for i in retrow_types])
    rrows = [RetRow(k, str(v)) for k, v in options.items()]
    return 'Config Summary', (retrow_types, rrows, None, None)


def split_currency(value):
    units = value.get_only_position().units
    return units.number, units.currency
