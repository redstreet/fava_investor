"""Fava Investor: Investing related reports and tools for Beancount/Fava
"""

from fava.ext import FavaExtensionBase

from .modules.tlh import libtlh
from .modules.assetalloc_class import libassetalloc
from .modules.aa_byaccount import libaaacc
from .common.favainvestorapi import *

class Investor(FavaExtensionBase):  # pragma: no cover
    report_title = "Investor"

    # TaxLossHarvester
    # -----------------------------------------------------------------------------------------------------------
    def query_func(self, sql):
        contents, rtypes, rrows = self.ledger.query_shell.execute_query(sql)
        return rtypes, rrows

    def build_tlh_tables(self, begin=None, end=None):
        return libtlh.get_tables(self.query_func, self.config.get('tlh', {}))

    # AssetAllocClass
    # -----------------------------------------------------------------------------------------------------------
    def build_assetalloc_by_class(self, begin=None, end=None):
        accapi = FavaInvestorAPI(self.ledger)
        retval = libassetalloc.assetalloc(accapi, self.config.get('asset_alloc_by_class', {}))
        return retval

    # AssetAllocAccount
    # -----------------------------------------------------------------------------------------------------------
    def build_aa_by_account(self, begin=None, end=None):
        if begin:
            tree = Tree(iter_entry_dates(self.ledger.entries, begin, end))
        else:
            tree = self.ledger.root_tree

        return libaaacc.portfolio_accounts(tree, self.config.get('asset_alloc_by_account', []), self.ledger, end)
