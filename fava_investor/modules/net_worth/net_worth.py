from decimal import Decimal
from typing import List, Dict

from beancount.core.inventory import Inventory
from fava.core import FavaLedger


class InventoryTools:
    @staticmethod
    def subtract(first: Inventory, second: Inventory):
        second_inverted = InventoryTools.invert(second)
        return first.add_inventory(second_inverted)

    @staticmethod
    def invert(inventory: Inventory):
        return Inventory(positions=[p.get_negative() for p in inventory.get_positions()])

    @staticmethod
    def to_dict(inventory: Inventory) -> Dict[str, Decimal]:
        result = {}
        assert isinstance(inventory, Inventory)
        for p in inventory.get_positions():
            result[p.units.currency] = p.units.number
        return result


def query_get_one(ledger, query) -> Inventory:
    result = ledger.query_shell.execute_query(query)
    rows = result[2]
    if len(rows) == 0:
        return Inventory()
    if len(rows) > 1:
        raise ValueError('oops?')
    return rows[0][0]


def calculate_unrealised_gains(ledger: FavaLedger):
    costs = query_get_one(ledger, "select sum(cost(position)) where account ~ 'investments'")
    values = query_get_one(ledger, "select sum(value(position)) where account ~ 'investments'")
    return InventoryTools.subtract(values, costs)


def get_net_worth(ledger: FavaLedger) -> Dict[str, Dict[str, Decimal]]:
    contr = query_get_one(ledger, "select sum(cost(position)) where account ~ 'investments'")

    dividends_all = InventoryTools.invert(
        query_get_one(ledger, "select sum(cost(position)) where account ~ 'dividends'")
    )
    dividends_reinvested = query_get_one(
        ledger, "select sum(cost(position)) where account ~ 'investments' and joinstr(other_accounts) ~ 'dividends'")

    inv_dict = {
        'contributions': contr,
        'dividends_total': dividends_all,
        'dividends_reinvested': dividends_reinvested,
        'dividends_withdrawn': InventoryTools.subtract(dividends_all, dividends_reinvested),
        'gains_unrealized': calculate_unrealised_gains(ledger),
        'gains_realized': Inventory()
    }
    return {k: InventoryTools.to_dict(v) for (k, v) in inv_dict.items()}

