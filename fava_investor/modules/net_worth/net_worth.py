import re
from decimal import Decimal
from typing import Dict, List, Union

from beancount.core.inventory import Inventory
from fava.core import FavaLedger

ConfigDict = Dict[str, Union[str, List[str]]]


class AccountsConfig:
    def __init__(self, value: List[str], internal: List[str], external: List[str]):
        """
        Full lists of all accounts considered value/internal/external. useful when building queries
        for matching account or these with joinstr(other_accounts)
        """
        self.value = value
        self.internal = internal
        self.external = external

    @classmethod
    def from_dict(cls, ledger: FavaLedger, config: ConfigDict) -> 'AccountsConfig':
        re_inv = prepare_regexp(config['inv'])
        re_int = prepare_regexp(config['internal'])
        inv = []
        internal = []
        external = []
        for account, _ in ledger.accounts.items():
            if re_inv.match(account):
                inv.append(account)
            elif re_int.match(account):
                internal.append(account)
            else:
                external.append(account)

        return AccountsConfig(inv, internal, external)

    def sql_match_value(self) -> str:
        return self._sql_match(self.value)

    def sql_match_external(self) -> str:
        return self._sql_match(self.external)

    def sql_match_internal(self) -> str:
        return self._sql_match(self.internal)

    @staticmethod
    def _sql_match(accounts: List[str]) -> str:
        accounts = "|".join(accounts)
        return f"~ '\\b{accounts}\\b'"


def prepare_regexp(inv_):
    if isinstance(inv_, str):
        inv_ = [inv_]
    re_inv = re.compile(r"\b({})".format("|".join(inv_)))
    return re_inv


class InventoryTools:
    @staticmethod
    def clone(first: Inventory):
        return Inventory(positions=first.get_positions())

    @staticmethod
    def subtract(first: Inventory, second: Inventory) -> Inventory:
        second_inverted = InventoryTools.invert(second)
        return InventoryTools.clone(first).add_inventory(second_inverted)

    @staticmethod
    def invert(inventory: Inventory) -> Inventory:
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


def calculate_unrealised_gains(ledger: FavaLedger) -> Inventory:
    costs = query_get_one(ledger, "select sum(cost(position)) where account ~ 'investments'")
    values = query_get_one(ledger, "select sum(value(position)) where account ~ 'investments'")
    return InventoryTools.subtract(values, costs)


def report(ledger: FavaLedger, acc_config: ConfigDict) -> Dict[str, Dict[str, Decimal]]:
    acc = AccountsConfig.from_dict(ledger, acc_config)
    contributions = query_get_one(ledger, f"select sum(cost(position)) where account {acc.sql_match_value()}")

    dividends_all = InventoryTools.invert(
        query_get_one(ledger, f"select sum(cost(position)) where account {acc.sql_match_internal()}")
    )
    dividends_reinvested = query_get_one(
        ledger, f"select sum(cost(position)) \
                    where account {acc.sql_match_value()} \
                    and joinstr(other_accounts) {acc.sql_match_internal()}")

    # TODO query should use list of internal and value accounts.
    #  Is condition ((VALUE + INTERNAL) and SELLING) enough to filter these?
    gains_realized = query_get_one(
        ledger, f"select sum(cost(position)) \
                    where account ~ 'gains' \
                    and joinstr(other_accounts) {acc.sql_match_value()}")

    inv_dict = {
        'contributions': contributions,
        'dividends_total': dividends_all,
        'dividends_reinvested': dividends_reinvested,
        'dividends_withdrawn': InventoryTools.subtract(dividends_all, dividends_reinvested),
        'gains_unrealized': calculate_unrealised_gains(ledger),
        'gains_realized': InventoryTools.invert(gains_realized)
    }
    return {k: InventoryTools.to_dict(v) for (k, v) in inv_dict.items()}
