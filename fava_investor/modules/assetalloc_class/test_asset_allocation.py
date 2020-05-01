#!/usr/bin/env python3

from beancount.utils import test_utils
import asset_allocation


class TestScriptCheck(test_utils.TestCase):

    @test_utils.docfile
    def test_basic_unspecified(self, filename):
        """
        2010-01-01 open Assets:Investments:Brokerage
        2010-01-01 open Assets:Bank

        2011-03-02 * "Buy stock"
         Assets:Investments:Brokerage 1 BNCT {200 USD}
         Assets:Bank

        2011-03-02 price BNCT 200 USD
        """
        with test_utils.capture('stdout', 'stderr') as (stdout, _):
            result = test_utils.run_with_args(asset_allocation.main, [filename])
        self.assertEqual(0, result)
        self.assertRegex(stdout.getvalue(), "unknown *200 *100.0%")
        # self.assertLines("", stdout.getvalue())

    @test_utils.docfile
    def test_basic_specified(self, filename):
        """
        2010-01-01 open Assets:Investments:Brokerage
        2010-01-01 open Assets:Bank
        2010-01-01 commodity BNCT
         asset_allocation_equity: 60
         asset_allocation_bond: 40

        2011-03-02 * "Buy stock"
         Assets:Investments:Brokerage 1 BNCT {200 USD}
         Assets:Bank

        2011-03-02 price BNCT 200 USD
        """
        with test_utils.capture('stdout', 'stderr') as (stdout, _):
            result = test_utils.run_with_args(asset_allocation.main, [filename])
        self.assertEqual(0, result)
        self.assertRegex(stdout.getvalue(), "equity *120 *60.0% *")
        self.assertRegex(stdout.getvalue(), "bond *80 *40.0% *")

    @test_utils.docfile
    def test_basic_account_filter(self, filename):
        """
        2010-01-01 open Assets:Investments:Brokerage
        2010-01-01 open Assets:Investments:XTrade
        2010-01-01 open Assets:Bank
        2010-01-01 commodity BNCT
         asset_allocation_equity: 60
         asset_allocation_bond: 40

        2011-03-02 * "Buy stock"
         Assets:Investments:Brokerage 1 BNCT {200 USD}
         Assets:Bank

        2011-01-02 * "Buy stock"
         Assets:Investments:XTrade 2 BNCT {200 USD}
         Assets:Bank

        2011-03-02 price BNCT 200 USD
        """
        with test_utils.capture('stdout', 'stderr') as (stdout, _):
            result = test_utils.run_with_args(asset_allocation.main, [filename,
                                                                      '--accounts_patterns', 'Assets:Investments:Brokerage'])
        self.assertEqual(0, result)
        self.assertRegex(stdout.getvalue(), "equity *120 *60.0% *")
        self.assertRegex(stdout.getvalue(), "bond *80 *40.0% *")

    @test_utils.docfile
    def test_basic_filter_exclude_parent(self, filename):
        """
        2010-01-01 open Assets:Investments:Brokerage
        2010-01-01 open Assets:Investments:XTrade
        2010-01-01 open Assets:Bank
        2010-01-01 commodity BNCT
         asset_allocation_equity: 60
         asset_allocation_bond: 40

        2011-03-02 * "Buy stock"
         Assets:Investments:Brokerage 1 BNCT {200 USD}
         Assets:Bank

        2011-01-02 * "Buy stock"
         Assets:Investments:XTrade 2 BNCT {200 USD}
         Assets:Bank

        2011-01-02 * "Buy stock"
         Assets:Investments 7 BNCT {200 USD}
         Assets:Bank

        2011-03-02 price BNCT 200 USD
        """
        with test_utils.capture('stdout', 'stderr') as (stdout, _):
            result = test_utils.run_with_args(asset_allocation.main, [filename,
                                                                      '--accounts_patterns', 'Assets:Investments:Brokerage'])
        self.assertEqual(0, result)
        self.assertRegex(stdout.getvalue(), "equity *120 *60.0% *")
        self.assertRegex(stdout.getvalue(), "bond *80 *40.0% *")

    @test_utils.docfile
    def test_tree_empty_parent(self, filename):
        """
        2010-01-01 open Assets:Investments:XTrade
        2010-01-01 open Assets:Bank

        2010-01-01 commodity BNCT
          asset_allocation_equity_international: 100


        2011-01-02 * "Buy stock"
          Assets:Investments:XTrade 700 BNCT {200 USD}
          Assets:Bank

        2011-03-02 price BNCT 200 USD
        """
        with test_utils.capture('stdout', 'stderr') as (stdout, _):
            result = test_utils.run_with_args(asset_allocation.main, [filename,
                                                                      '--accounts_patterns', 'Assets:Investments'])
        self.assertEqual(0, result)
        self.assertRegex(stdout.getvalue(), "equity.*100.0%")
        self.assertRegex(stdout.getvalue(), " international.*100.0%")

    @test_utils.docfile
    def test_parent_with_assets(self, filename):
        """
        2010-01-01 open Assets:Investments:Brokerage
        2010-01-01 open Assets:Bank

        2010-01-01 commodity BNDLOCAL
         asset_allocation_bond_local: 100

        2010-01-01 commodity BONDS
         asset_allocation_bond: 100

        2011-03-02 * "Buy stock"
         Assets:Investments:Brokerage 2 BNDLOCAL {200 USD}
         Assets:Bank

        2011-01-02 * "Buy stock"
         Assets:Investments:Brokerage 2 BONDS {200 USD}
         Assets:Bank

        2011-03-02 price BNDLOCAL 200 USD
        2011-03-02 price BONDS 200 USD
        """
        with test_utils.capture('stdout', 'stderr') as (stdout, _):
            result = test_utils.run_with_args(asset_allocation.main, [filename,
                                                                      '--accounts_patterns', 'Assets:Investments'])
        self.assertEqual(0, result)
        self.assertRegex(stdout.getvalue(), " bond *800 *100.0% *")
        self.assertRegex(stdout.getvalue(), "  local *400 *50.0% *")
