"""Fava Investor: Investing related reports and tools for Beancount/Fava"""

from fava.ext import FavaExtensionBase

import fava_investor.modules.performance.contributions
import fava_investor.modules.performance.gains
from .modules import performance
from .modules.performance.balances import get_balances_tree
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

    def build_contributions_journal(self):
        accapi = FavaInvestorAPI(self.ledger)
        accounts = performance.get_accounts_from_config(accapi, self.config.get('performance', {}))
        contr = fava_investor.modules.performance.contributions.ContributionsCalculator(accapi, accounts)
        entries = contr.get_contributions_entries()
        return map(lambda entry: (entry.transaction, None, entry.change, entry.balance), entries)

    def build_withdrawals_journal(self):
        accapi = FavaInvestorAPI(self.ledger)
        accounts = performance.get_accounts_from_config(accapi, self.config.get('performance', {}))
        contr = fava_investor.modules.performance.contributions.ContributionsCalculator(accapi, accounts)
        entries = contr.get_withdrawals_entries()
        return map(lambda entry: (entry.transaction, None, entry.change, entry.balance), entries)

    def build_gains_journal(self):
        accapi = FavaInvestorAPI(self.ledger)
        accounts = performance.get_accounts_from_config(accapi, self.config.get('performance', {}))
        contr = fava_investor.modules.performance.gains.GainsCalculator(accapi, accounts)
        entries = contr.get_realized_gains_entries()
        return map(lambda entry: (entry.transaction, None, entry.change, entry.balance), entries)



