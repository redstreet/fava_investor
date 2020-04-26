"""Fava Investor: Investing related reports and tools for Beancount/Fava"""
import copy

from beancount.core.inventory import Inventory
from fava.ext import FavaExtensionBase

from .modules import performance
from .modules.performance.balances import get_balances_tree
from .modules.performance.split import split_journal, sum_inventories, calculate_balances, SplitEntries
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

    def get_split(self):
        config = self.config.get("performance", {})
        split = split_journal(FavaInvestorAPI(self.ledger),
                              config.get("accounts_pattern", "^Assets:Investments"),
                              config.get("accounts_internal_pattern", "^(Income|Expense):"),
                              config.get("accounts_internalized_pattern", "^Income:Dividends"))
        return split

    def build_contributions_journal(self):
        split = self.get_split()
        balances = calculate_balances(split.parts.contributions)
        return map(lambda i: (split.transactions[i], None, split.parts.contributions[i], balances[i]),
                   range(0, len(split.transactions)))

    def build_withdrawals_journal(self):
        split = self.get_split()
        balances = calculate_balances(split.parts.withdrawals)
        return map(lambda i: (split.transactions[i], None, split.parts.withdrawals[i], balances[i]),
                   range(0, len(split.transactions)))

    def build_realized_gains_journal(self):
        split = self.get_split()
        balances = calculate_balances(split.parts.gains_realized)
        return map(lambda i: (split.transactions[i], None, split.parts.gains_realized[i], balances[i]),
                   range(0, len(split.transactions)))

    def build_unrealized_gains_journal(self):
        split = self.get_split()
        balances = calculate_balances(split.parts.gains_unrealized)
        return map(lambda i: (split.transactions[i], None, split.parts.gains_unrealized[i], balances[i]),
                   range(0, len(split.transactions)))

    def build_dividends_journal(self):
        split = self.get_split()
        balances = calculate_balances(split.parts.dividends)
        return map(lambda i: (split.transactions[i], None, split.parts.dividends[i], balances[i]),
                   range(0, len(split.transactions)))

    def build_costs_journal(self):
        split = self.get_split()
        balances = calculate_balances(split.parts.costs)
        return map(lambda i: (split.transactions[i], None, split.parts.costs[i], balances[i]),
                   range(0, len(split.transactions)))

    def testing(self):
        split = self.get_split()
        parts = split.parts
        summary = {
            'contributions': sum_inventories(parts.contributions),
            'withdrawals': sum_inventories(parts.withdrawals),
            'dividends': sum_inventories(parts.dividends),
            'costs': sum_inventories(parts.costs),
            'realized': sum_inventories(parts.gains_realized),
            'unrealized': sum_inventories(parts.gains_unrealized),
        }
        checksum = sum_inventories(summary.values())

        summary['date'] = split.transactions[-1].date
        summary['value'] = split.values[-1]
        summary["checksum"] = checksum
        summary["error"] = sum_inventories([checksum, -split.values[-1]])

        journal = []
        error_sum = Inventory()
        for i in range(0, len(split.transactions)):
            parts = split.parts
            parts_sum = parts.contributions[i] + parts.withdrawals[i] + parts.dividends[i] + parts.costs[i] + \
                        parts.gains_realized[i] + parts.gains_unrealized[i]
            if i == 0:
                current_value = Inventory()
            else:
                current_value = split.values[i] + (-split.values[i-1])
            error = -current_value + parts_sum
            error_sum += error
            journal.append((split.transactions[i], None, error, copy.copy(error_sum)))
        return summary, journal
