#!/usr/bin/env python3

import sys
import os
from beancount.utils import test_utils
import click.testing
sys.path.append(os.path.join(os.path.dirname(__file__), '.'))
import assetalloc_class


class ClickTestCase(test_utils.TestCase):
    """Base class for command-line program test cases."""

    def run_with_args(self, function, *args):
        runner = click.testing.CliRunner()
        result = runner.invoke(function, args, catch_exceptions=False)
        self.assertEqual(result.exit_code, 0)
        return result


class TestScriptCheck(ClickTestCase):

    @test_utils.docfile
    def test_basic_unspecified(self, filename):
        """
        option "operating_currency" "USD"
        2010-01-01 open Assets:Investments:Brokerage
        2010-01-01 open Assets:Bank

        2011-03-02 * "Buy stock"
         Assets:Investments:Brokerage 1 BNCT {200 USD}
         Assets:Bank

        2011-03-02 price BNCT 200 USD
        """
        result = self.run_with_args(assetalloc_class.assetalloc_class, filename)
        expected_output = """
        Warning: BNCT asset_allocation_* metadata does not add up to 100%. Padding with 'unknown'.
        asset_type      amount    percentage
        ------------  --------  ------------
        Total              200        100.0%
         unknown           200        100.0%
        """
        self.assertLines(expected_output, result.stdout)

    @test_utils.docfile
    def test_basic_specified(self, filename):
        """
        option "operating_currency" "USD"
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
        result = self.run_with_args(assetalloc_class.assetalloc_class, filename)
        expected_output = """
        asset_type      amount    percentage
        ------------  --------  ------------
        Total              200        100.0%
         equity            120         60.0%
         bond               80         40.0%
        """
        self.assertLines(expected_output, result.stdout)

    @test_utils.docfile
    def test_basic_account_filter(self, filename):
        """
        option "operating_currency" "USD"
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
        2010-01-01 custom "fava-extension" "fava_investor" "{
          'asset_alloc_by_class' : {
              'accounts_patterns': ['Assets:Investments:Brokerage'],
          }
        }"
        """
        result = self.run_with_args(assetalloc_class.assetalloc_class, filename)
        expected_output = """
        asset_type      amount    percentage
        ------------  --------  ------------
        Total              200        100.0%
         equity            120         60.0%
         bond               80         40.0%
        """
        self.assertLines(expected_output, result.stdout)

    @test_utils.docfile
    def test_basic_filter_exclude_parent(self, filename):
        """
        option "operating_currency" "USD"
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
        2010-01-01 custom "fava-extension" "fava_investor" "{
          'asset_alloc_by_class' : {
              'accounts_patterns': ['Assets:Investments:Brokerage'],
          }
        }"
        """
        result = self.run_with_args(assetalloc_class.assetalloc_class, filename)
        expected_output = """
        asset_type      amount    percentage
        ------------  --------  ------------
        Total              200        100.0%
         equity            120         60.0%
         bond               80         40.0%
        """
        self.assertLines(expected_output, result.stdout)

    @test_utils.docfile
    def test_tree_empty_parent(self, filename):
        """
        option "operating_currency" "USD"
        2010-01-01 open Assets:Investments:XTrade
        2010-01-01 open Assets:Bank

        2010-01-01 commodity BNCT
          asset_allocation_equity_international: 100


        2011-01-02 * "Buy stock"
          Assets:Investments:XTrade 700 BNCT {200 USD}
          Assets:Bank

        2011-03-02 price BNCT 200 USD
        2010-01-01 custom "fava-extension" "fava_investor" "{
          'asset_alloc_by_class' : {
              'accounts_patterns': ['Assets:Investments'],
          }
        }"
        """
        result = self.run_with_args(assetalloc_class.assetalloc_class, filename)
        expected_output = """
        asset_type                amount    percentage
        ----------------------  --------  ------------
        Total                    140,000        100.0%
         equity                  140,000        100.0%
          equity_international   140,000        100.0%
        """
        self.assertLines(expected_output, result.stdout)

    @test_utils.docfile
    def test_parent_with_assets(self, filename):
        """
        option "operating_currency" "USD"
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
        2010-01-01 custom "fava-extension" "fava_investor" "{
          'asset_alloc_by_class' : {
              'accounts_patterns': ['Assets:Investments'],
          }
        }"
        """
        result = self.run_with_args(assetalloc_class.assetalloc_class, filename)
        expected_output = """
        asset_type      amount    percentage
        ------------  --------  ------------
        Total              800        100.0%
         bond              800        100.0%
          bond_local       400         50.0%
        """
        self.assertLines(expected_output, result.stdout)

    @test_utils.docfile
    def test_multicurrency(self, filename):
        """
        option "operating_currency" "USD"
        option "operating_currency" "GBP"

        2010-01-01 open Assets:Investments:Taxable:XTrade
        2010-01-01 open Assets:Bank

        2010-01-01 commodity SPFIVE
         asset_allocation_equity_domestic: 100

        2010-01-01 commodity SPUK
         asset_allocation_equity_international: 100

        2011-01-10 * "Buy stock"
         Assets:Investments:Taxable:XTrade 100 SPFIVE {5 USD}
         Assets:Bank

        2011-01-09 price GBP 1.5 USD
        2011-01-10 * "Buy stock"
         Assets:Investments:Taxable:XTrade 100 SPUK {5 GBP}
         Assets:Bank

        2011-03-02 price SPFIVE 5 USD
        2011-03-02 price SPUK   5 GBP
        2011-03-02 price GBP 1.5 USD
        2010-01-01 custom "fava-extension" "fava_investor" "{
          'asset_alloc_by_class' : {
              'accounts_patterns': ['Assets:Investments'],
          }
        }"
        """
        result = self.run_with_args(assetalloc_class.assetalloc_class, filename)
        expected_output = """
        asset_type                amount    percentage
        ----------------------  --------  ------------
        Total                      1,250        100.0%
         equity                    1,250        100.0%
          equity_domestic            500         40.0%
          equity_international       750         60.0%
        """
        self.assertLines(expected_output, result.stdout)
