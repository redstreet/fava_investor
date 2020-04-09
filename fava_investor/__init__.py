"""Fava Investor: Investing related reports and tools for Beancount/Fava"""

from fava.ext import FavaExtensionBase
from fava.util.date import Interval

from .modules.performance.accounts_config import AccountsConfig
from .modules.performance.balances import interval_balances
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
        retval = libassetalloc.assetalloc(accapi, self.config.get('asset_alloc_by_class', {}))
        return retval

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
    def query_func(self, sql):
        contents, rtypes, rrows = self.ledger.query_shell.execute_query(sql)
        return rtypes, rrows

    def build_tlh_tables(self, begin=None, end=None):
        return libtlh.get_tables(self.query_func, self.config.get('tlh', {}))

    # Balances
    # -----------------------------------------------------------------------------------------------------------
    def get_balances(self, interval: Interval):
        interval_count = 3
        accounts = AccountsConfig.from_dict(self.ledger, self.config.get('performance', []))
        return interval_balances(self.ledger, accounts.value, interval,
                                 self.ledger.options['name_assets'], True, interval_count)
