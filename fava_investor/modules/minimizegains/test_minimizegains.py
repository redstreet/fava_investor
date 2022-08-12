#!/usr/bin/env python3

import beancountinvestorapi as api
import sys
import os
from beancount.utils import test_utils
sys.path.append(os.path.join(os.path.dirname(__file__), '.'))
import libminimizegains as libmg
# To run: pytest


class TestScriptCheck(test_utils.TestCase):
    def setUp(self):
        self.options = {'accounts_pattern': "Assets:Investments:Taxable"}

    @test_utils.docfile
    def test_minimizegains_basic(self, f):
        """
        2010-01-01 open Assets:Investments:Taxable:Brokerage
        2010-01-01 open Assets:Bank

        2010-01-01 commodity BNCT
        2010-01-01 commodity COFE

        2015-01-01 * "Buy stock"
         Assets:Investments:Taxable:Brokerage 100 BNCT {100 USD}
         Assets:Bank

        2016-01-01 * "Buy stock"
         Assets:Investments:Taxable:Brokerage 100 COFE {200 USD}
         Assets:Bank

        2018-01-01 price BNCT 150 USD
        2018-01-01 price COFE 201 USD
        """
        accapi = api.AccAPI(f, {})
        retrow_types, to_sell = libmg.find_minimized_gains(accapi, self.options)

        self.assertEqual(2, len(to_sell))
        self.assertEqual(100, to_sell[0].gain)
        self.assertEqual(5000, to_sell[1].gain)
