#!/usr/bin/env python3

import beancountinvestorapi as api
import sys
import os
from beancount.utils import test_utils
sys.path.append(os.path.join(os.path.dirname(__file__), '.'))
import libperformance as libpf

class TestScriptCheck(test_utils.TestCase):
    def setUp(self):
        self.options = {
            'account_field': 'account',
            'accounts_pattern': 'Assets:Investments',
            'accuracy': 2,
        }

    @test_utils.docfile
    def test_performance_basic(self, f):
        """
2010-01-01 commodity BNCT
2010-01-01 commodity COFE

2020-01-01 * "Buy stock"
   Assets:Investments:BNCT                   1000 BNCT {100 USD}
   Assets:Investments:COFE                   1000 COFE {10 USD}
   Assets:Bank

2021-03-12 * "Buy stock"
   Assets:Investments:BNCT                   1000 BNCT {100 USD}
   Assets:Investments:COFE                   1000 COFE {10 USD}
   Assets:Bank

2022-01-01 * "Sell stock"
   Assets:Investments:BNCT                  -1500 BNCT {} @ 100 USD
   Assets:Investments:COFE                  -1500 COFE {} @ 10 USD
   Assets:Bank                               165000 USD
   Income:Gains

2022-06-01 * "Sell stock"
   Assets:Investments:BNCT                  -500 BNCT {} @ 160 USD
   Assets:Bank                               88000 USD
   Income:Gains

2024-07-14 * "Sell stock"
   Assets:Investments:COFE                  -500 COFE {} @ 25 USD
   Assets:Bank                               12500 USD
   Income:Gains

2020-01-01 price BNCT 100 USD
2021-03-12 price BNCT 100 USD
2022-01-01 price BNCT 100 USD
2022-06-01 price BNCT 160 USD

2020-01-01 price COFE 10 USD
2021-03-12 price COFE 10 USD
2022-01-01 price COFE 10 USD
2022-06-01 price COFE 16 USD
2023-01-01 price COFE 20 USD
2024-01-01 price COFE 25 USD

        """
        accapi = api.AccAPI(f, {})
        ret = libpf.find_xirrs(accapi, self.options)
        title, (retrow_types, xirrs, _, _) = ret[1]

        self.assertEqual(2, len(xirrs))
        self.assertEqual("Assets:Investments:BNCT", xirrs[0].account)
        self.assertEqual(9.35, xirrs[0].XIRR)
        self.assertEqual("Assets:Investments:COFE", xirrs[1].account)
        self.assertEqual(13.70, xirrs[1].XIRR)
