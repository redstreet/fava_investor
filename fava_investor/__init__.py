"""Fava Investor: Investing related reports and tools for Beancount/Fava"""
import copy

from beancount.core.inventory import Inventory
from fava.ext import FavaExtensionBase

from .modules import performance
from .modules.performance.balances import get_balances_tree
from .modules.performance.split import calculate_interval_balances, sum_inventories, calculate_balances
from .modules.tlh import libtlh
from .modules.assetalloc_class import libassetalloc
from .modules.assetalloc_account import libaaacc
from .modules.cashdrag import libcashdrag
from .common.favainvestorapi import *


class Investor(FavaExtensionBase):  # pragma: no cover
    report_title = "Investor"

    # AssetAllocClass
    # -----------------------------------------------------------------------------------------------------------
    def build_assetalloc_by_class(self, begin=None, end=None):
        accapi = FavaInvestorAPI(self.ledger)
        return libassetalloc.assetalloc(accapi, self.config.get('asset_alloc_by_class', {}))

    # AssetAllocAccount
    # -----------------------------------------------------------------------------------------------------------
    def build_aa_by_account(self, begin=None, end=None):
        accapi = FavaInvestorAPI(self.ledger)
        # if begin:
        #     tree = Tree(iter_entry_dates(self.ledger.entries, begin, end))
        # else:
        #     tree = self.ledger.root_tree

        return libaaacc.portfolio_accounts(accapi, self.config.get('asset_alloc_by_account', []))

    # Cash Drag
    # -----------------------------------------------------------------------------------------------------------
    def build_cashdrag(self, begin=None, end=None):
        accapi = FavaInvestorAPI(self.ledger)
        return libcashdrag.find_loose_cash(accapi, self.config.get('cashdrag', {}))

    # TaxLossHarvester
    # -----------------------------------------------------------------------------------------------------------
    def build_tlh_tables(self, begin=None, end=None):
        accapi = FavaInvestorAPI(self.ledger)
        return libtlh.get_tables(accapi, self.config.get('tlh', {}))

    def recently_sold_at_loss(self, begin=None, end=None):
        accapi = FavaInvestorAPI(self.ledger)
        return libtlh.recently_sold_at_loss(accapi, self.config.get('tlh', {}))

    # Performance
    # -----------------------------------------------------------------------------------------------------------
    def build_balances_tree(self):
        accapi = FavaInvestorAPI(self.ledger)
        return get_balances_tree(accapi, self.config.get('performance', {}))

    def get_split(self, accumulators):
        config = self.config.get("performance", {})
        split = calculate_interval_balances(FavaInvestorAPI(self.ledger),
                                            accumulators,
                                            config.get("accounts_pattern", "^Assets:Investments"),
                                            config.get("accounts_income_pattern", "^Income:"),
                                            config.get("accounts_expenses_pattern", "^Expenses:"),
                                            )
        return split

    def build_split_journal(self, kind):
        split_values_by_kind = {
            'contributions': lambda split: split.parts.accumulated,
            'withdrawals': lambda split: split.parts.gains,
            'dividends': lambda split: split.parts.gains,
            'costs': lambda split: split.parts.costs,
            'gains_realized': lambda split: split.parts.gains_realized,
            'accounts_value': lambda split: split.values,
        }
        split = self.get_split()
        split_values = split_values_by_kind[kind](split)
        to_keep = []
        for index in range(0, len(split.transactions)):
            if split_values[index] != {}:
                to_keep.append(index)

        balances = calculate_balances(split_values)

        return [(split.transactions[i], None, split_values[i], balances[i]) for i in range(0, len(split.transactions))
                if i in to_keep]

    def testing(self):
        split = self.get_split()
        parts = split.parts
        summary = {
            'contributions': sum_inventories(parts.accumulated),
            'withdrawals': sum_inventories(parts.gains),
            'dividends': sum_inventories(parts.gains),
            'costs': sum_inventories(parts.costs),
            'gains_realized': sum_inventories(parts.gains_realized),
            'gains_unrealized': sum_inventories(parts.gains_unrealized),
        }
        checksum = sum_inventories(summary.values())

        accounts_value = sum_inventories(split.values)
        summary['accounts_value'] = accounts_value
        summary["sum_of_splits"] = checksum
        summary["error"] = sum_inventories([checksum, -accounts_value])
        return summary

    def build_errors_journal(self):
        split = self.get_split()
        journal = []
        error_sum = Inventory()
        for i in range(0, len(split.transactions)):
            parts = split.parts
            parts_sum = sum_inventories([split_values[i] for split_values in parts])
            error = -split.values[i] + parts_sum
            error_sum += error
            if error != {}:
                journal.append((split.transactions[i], None, error, copy.copy(error_sum)))
        return journal
