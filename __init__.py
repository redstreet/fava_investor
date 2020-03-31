"""Fava Investor: Investing related reports and tools for Beancount/Fava
"""

from fava.ext import FavaExtensionBase

from .modules.tlh import libtlh
from .modules.aa_byaccount import libaaacc

# -----------------------------------------------------------------------------------------------------------
class TaxLossHarvester(FavaExtensionBase):  # pragma: no cover
    '''Tax Loss Harvester Fava (Beancount) Plugin
    '''
    report_title = "Investor: Tax Loss Harvester"

    def query_func(self, sql):
        contents, rtypes, rrows = self.ledger.query_shell.execute_query(sql)
        return rtypes, rrows

    def build_tlh_tables(self, begin=None, end=None):
        """Build fava TLH tables using TLH library
        """
        return libtlh.get_tables(self.query_func, self.config.get('tlh', {}))

# -----------------------------------------------------------------------------------------------------------

class AssetAllocAccount(FavaExtensionBase):  # pragma: no cover
    """Sample Extension Report that just prints out an Portfolio List.
    """
    report_title = "Investor: AA by Account"

    def build_aa_by_account(self, begin=None, end=None):
        """An account tree based on matching regex patterns."""
        if begin:
            tree = Tree(iter_entry_dates(self.ledger.entries, begin, end))
        else:
            tree = self.ledger.root_tree

        return libaaacc.portfolio_accounts(tree, self.config.get('asset_alloc_class', []), self.ledger, end)
