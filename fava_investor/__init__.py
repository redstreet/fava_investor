"""Fava Investor: Investing related reports and tools for Beancount/Fava
"""

from fava.ext import FavaExtensionBase

from .modules.tlh import libtlh
from .modules.assetalloc_class import libassetalloc
from .modules.aa_byaccount import libaaacc

from beancount.core import getters
class FavaInvestorAPI:
    def __init__(self, ledger):
        self.ledger = ledger

    def build_price_map(self):
        return self.ledger.price_map

    def get_commodity_map(self):
        return getters.get_commodity_map(self.ledger.entries)

    def realize(self):
        return self.ledger.root_account

    def query_func(self, sql):
        contents, rtypes, rrows = self.ledger.query_shell.execute_query(sql)
        return rtypes, rrows

    def get_operating_currency(self):
        return self.ledger.options["operating_currency"][0] #TBD: error check

    def get_account_open_close(self):
        return getters.get_account_open_close(self.ledger.entries)

# -----------------------------------------------------------------------------------------------------------
class TaxLossHarvester(FavaExtensionBase):  # pragma: no cover
    report_title = "Investor: Tax Loss Harvester"

    def query_func(self, sql):
        contents, rtypes, rrows = self.ledger.query_shell.execute_query(sql)
        return rtypes, rrows

    def build_tlh_tables(self, begin=None, end=None):
        return libtlh.get_tables(self.query_func, self.config.get('tlh', {}))

# -----------------------------------------------------------------------------------------------------------
class AssetAllocClass(FavaExtensionBase):  # pragma: no cover
    report_title = "Investor: Asset Allocation by Class"


    def build_assetalloc_by_class(self, begin=None, end=None):
        accapi = FavaInvestorAPI(self.ledger)
        retval = libassetalloc.assetalloc(accapi, self.config.get('asset_alloc_by_class', {}))
        return retval

# -----------------------------------------------------------------------------------------------------------
class NetWorth(FavaExtensionBase):  # pragma: no cover
    report_title = "Investor: NetWorth"

    def get_net_worth(self, begin=None, end=None):
        """An account tree based on matching regex patterns."""
        from fava_investor.modules.net_worth import net_worth as nw

        return nw.get_net_worth(self.ledger)

# -----------------------------------------------------------------------------------------------------------

class AssetAllocAccount(FavaExtensionBase):  # pragma: no cover
    report_title = "Investor: AA by Account"

    def build_aa_by_account(self, begin=None, end=None):
        if begin:
            tree = Tree(iter_entry_dates(self.ledger.entries, begin, end))
        else:
            tree = self.ledger.root_tree

        return libaaacc.portfolio_accounts(tree, self.config.get('asset_alloc_by_account', []), self.ledger, end)
