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
        option "operating_currency" "USD"
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
        ret = libmg.find_minimized_gains(accapi, self.options)
        title, (retrow_types, to_sell, _, _) = ret[1]

        self.assertEqual(2, len(to_sell))
        self.assertEqual(20100, to_sell[0].cu_proceeds)
        self.assertEqual(5100, to_sell[1].cu_taxes)
