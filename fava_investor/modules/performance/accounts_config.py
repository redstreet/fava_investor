import re
from typing import List

from core import FavaLedger

from fava_investor.modules.performance.balances import ConfigDict


class AccountsConfig:
    def __init__(self, value: List[str], internal: List[str], external: List[str]):
        """
        Full lists of all accounts considered value/internal/external. useful when building queries
        for matching account or these with joinstr(other_accounts)
        """
        self.value = value
        self.internal = internal
        self.external = external

    @classmethod
    def from_dict(cls, ledger: FavaLedger, config: ConfigDict) -> 'AccountsConfig':
        re_inv = cls._prepare_regexp(config['value'])
        re_int = cls._prepare_regexp(config['internal'])
        inv = []
        internal = []
        external = []
        for account, _ in ledger.accounts.items():
            if re_inv.match(account):
                inv.append(account)
            elif re_int.match(account):
                internal.append(account)
            else:
                external.append(account)

        return AccountsConfig(inv, internal, external)

    @staticmethod
    def _prepare_regexp(inv_):
        if isinstance(inv_, str):
            inv_ = [inv_]
        re_inv = re.compile(r"\b({})".format("|".join(inv_)))
        return re_inv