"""Fava Investor: Investing related reports and tools for Beancount/Fava"""
from beancount.core.inventory import Inventory
from fava.ext import FavaExtensionBase

from .modules import performance
from .modules.performance.balances import get_balances_tree
from .modules.performance.split import split_journal, sum_inventories, calculate_balances
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
        balances = calculate_balances(split.contributions)
        return map(lambda i: (split.transactions[i], None, split.contributions[i], balances[i]),
                   range(0, len(split.transactions)))

    def build_withdrawals_journal(self):
        split = self.get_split()
        balances = calculate_balances(split.withdrawals)
        return map(lambda i: (split.transactions[i], None, split.withdrawals[i], balances[i]),
                   range(0, len(split.transactions)))

    def build_realized_gains_journal(self):
        split = self.get_split()
        balances = calculate_balances(split.gains_realized)
        return map(lambda i: (split.transactions[i], None, split.gains_realized[i], balances[i]),
                   range(0, len(split.transactions)))

    def build_unrealized_gains_journal(self):
        split = self.get_split()
        balances = calculate_balances(split.gains_unrealized)
        return map(lambda i: (split.transactions[i], None, split.gains_unrealized[i], balances[i]),
                   range(0, len(split.transactions)))

    def build_dividends_journal(self):
        split = self.get_split()
        balances = calculate_balances(split.dividends)
        return map(lambda i: (split.transactions[i], None, split.dividends[i], balances[i]),
                   range(0, len(split.transactions)))

    def build_costs_journal(self):
        split = self.get_split()
        balances = calculate_balances(split.costs)
        return map(lambda i: (split.transactions[i], None, split.costs[i], balances[i]),
                   range(0, len(split.transactions)))
