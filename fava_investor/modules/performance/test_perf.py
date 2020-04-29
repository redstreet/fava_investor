from datetime import datetime
from pathlib import Path

from .test_split import SplitTestCase, get_split, get_ledger
from ... import get_balance_split_history


class TestWithdrawals(SplitTestCase):
    def test_asset_sold_loan_returned_and_rest_withdrawn(self):
        self.skipTest("no need to run it every time")
        root_dir = Path(__file__).parent.parent.parent.parent
        file = root_dir / "huge-example.beancount"
        start = datetime.now().timestamp()
        n = 10
        ledger = get_ledger(file)

        for i in range(0, n):
            get_balance_split_history(
                ledger,
                '^Assets:US:(ETrade|Federal|Vanguard)',
                income_pattern='^Income:US:ETrade',
                expenses_pattern='^Expenses:Financial',
            )
        end = datetime.now().timestamp()

        self.assertEqual(1, (end-start)/n)

