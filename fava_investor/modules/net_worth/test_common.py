from pprint import pformat

from beancount import loader
from beancount.ops import validation
from fava.core import FavaLedger


def get_ledger(filename):
    _, errors, _ = loader.load_file(filename, extra_validations=validation.HARDCORE_VALIDATIONS)
    if errors:
        raise ValueError("Errors in ledger file: \n" + pformat(errors))

    ledger = FavaLedger(filename)
    return ledger

ACCOUNTS_CONFIG = {
    "inv": ["Assets:Investments"],
    "internal": ["Income", "Expenses"],
}
