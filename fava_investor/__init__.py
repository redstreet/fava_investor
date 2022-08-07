"""Fava Investor: Investing related reports and tools for Beancount/Fava"""

from fava.ext import FavaExtensionBase
from fava import __version__ as fava_version

from .modules.tlh import libtlh
from .modules.assetalloc_class import libassetalloc
from .modules.assetalloc_account import libaaacc
from .modules.cashdrag import libcashdrag
from .modules.summarizer import libsummarizer
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

    def recently_sold_at_loss(self):
        accapi = FavaInvestorAPI()
        return libtlh.recently_sold_at_loss(accapi, self.config.get('tlh', {}))

    def use_new_querytable(self):
        """
        fava added the ledger as a first required argument to
        querytable.querytable after version 1.18, so in order to support both,
        we have to detect the version and adjust how we call it from inside our
        template
        """
        split_version = fava_version.split('.')
        if len(split_version) != 2:
            split_version = split_version[:2]
        major, minor = split_version
        return int(major) > 1 or (int(major) == 1 and int(minor) > 18)
