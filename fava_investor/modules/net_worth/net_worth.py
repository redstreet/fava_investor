from typing import List

from beancount.core.inventory import Inventory
from fava.core import FavaLedger


def subtract_inventory(first: Inventory, second: Inventory):
    second_inverted = Inventory(positions=[p.get_negative() for p in second.get_positions()])
    return first.add_inventory(second_inverted)


def query_get_one(ledger, query) -> Inventory:
    result = ledger.query_shell.execute_query(query)
    rows = result[2]
    if len(rows) == 0:
        return Inventory()
    if len(rows) > 1:
        raise ValueError('oops?')
    return rows[0][0]


def calculate_unrealised_gains(ledger):
    costs = query_get_one(ledger, "select sum(cost(position)) where account ~ 'investments'")
    values = query_get_one(ledger, "select sum(value(position)) where account ~ 'investments'")
    return subtract_inventory(values, costs)


def inventory_to_dict(inventory: Inventory):
    result = {}
    for p in inventory.get_positions():
        result[p.units.currency] = p.units.number
    return result


def get_net_worth(ledger: FavaLedger):
    contr = query_get_one(ledger, "select sum(cost(position)) where account ~ 'investments'")

    dividends_all = query_get_one(ledger, "select sum(cost(position)) where account ~ 'dividends'")
    dividends_re = query_get_one(
        ledger, "select sum(cost(position)) where account ~ 'investments' and joinstr(other_accounts) ~ 'dividends'")

    return {
        'contributions': inventory_to_dict(contr),
        'dividends_total': inventory_to_dict(dividends_all),
        'dividends_reinvested': inventory_to_dict(dividends_re),
        'dividends_other': inventory_to_dict(subtract_inventory(dividends_all, dividends_re)),
        'gains_unrealized': inventory_to_dict(calculate_unrealised_gains(ledger)),
        'gains_realized': {}
    }

