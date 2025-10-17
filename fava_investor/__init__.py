"""Fava Investor: Investing related reports and tools for Beancount/Fava"""

from fava.ext import FavaExtensionBase

from .modules.tlh import libtlh
from .modules.assetalloc_class import libassetalloc
from .modules.assetalloc_account import libaaacc
from .modules.cashdrag import libcashdrag
from .modules.summarizer import libsummarizer
from .modules.minimizegains import libminimizegains
from .modules.performance import libperformance
from .common.favainvestorapi import FavaInvestorAPI


class Investor(FavaExtensionBase):  # pragma: no cover
    report_title = "Investor"

    # AssetAllocClass
    # -----------------------------------------------------------------------------------------------------------
    def build_assetalloc_by_class(self):
        accapi = FavaInvestorAPI()
        return libassetalloc.assetalloc(accapi, self.config.get('asset_alloc_by_class', {}))

    # AssetAllocAccount
    # -----------------------------------------------------------------------------------------------------------
    def build_aa_by_account(self):
        accapi = FavaInvestorAPI()
        return libaaacc.portfolio_accounts(accapi, self.config.get('asset_alloc_by_account', []))

    # Cash Drag
    # -----------------------------------------------------------------------------------------------------------
    def build_cashdrag(self):
        accapi = FavaInvestorAPI()
        return libcashdrag.find_loose_cash(accapi, self.config.get('cashdrag', {}))

    # Summarizer (metadata info)
    # -----------------------------------------------------------------------------------------------------------
    def build_summarizer(self):
        accapi = FavaInvestorAPI()
        return libsummarizer.build_tables(accapi, self.config.get('summarizer', {}))

    # TaxLossHarvester
    # -----------------------------------------------------------------------------------------------------------
    def build_tlh_tables(self):
        accapi = FavaInvestorAPI()
        return libtlh.get_tables(accapi, self.config.get('tlh', {}))

    # Gains Minimizer
    # -----------------------------------------------------------------------------------------------------------
    def build_minimizegains(self):
        accapi = FavaInvestorAPI()
        return libminimizegains.find_minimized_gains(accapi, self.config.get('minimizegains', {}))

    def build_performance(self):
        accapi = FavaInvestorAPI()
        return libperformance.find_xirrs(accapi, self.config.get('performance', {}))

    def recently_sold_at_loss(self):
        accapi = FavaInvestorAPI()
        return libtlh.recently_sold_at_loss(accapi, self.config.get('tlh', {}))
