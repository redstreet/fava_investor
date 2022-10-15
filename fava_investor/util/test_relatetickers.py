#!/usr/bin/env python3

# 2005-01-01 commodity VTI
#   a__quoteType: "ETF"
#   a__substidenticals: "VTSMX,VTSAX"
#   a__equivalents: "VTSAX"
#   tlh_partners: "VOO,VV"

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '.'))
from beancount.utils import test_utils
from relatetickers import RelateTickers


class TestRelateTickers(test_utils.TestCase):
    @test_utils.docfile
    def test_equivalent_transitive(self, f):
        """
        2005-01-01 commodity VTI
          a__equivalents: "VTSAX"

        2005-01-01 commodity VTSAX
          a__equivalents: "VTSMX"

        2005-01-01 commodity VTSMX
        """
        tickerrel = RelateTickers(f)
        retval = tickerrel.build_commodity_groups(['a__equivalents'])

        self.assertEqual(1, len(retval))
        self.assertSetEqual(retval[0], set(['VTI', 'VTSAX', 'VTSMX']))

    @test_utils.docfile
    def test_none(self, f):
        """
        2005-01-01 commodity VOO
          a__substidenticals: "IVV"

        2005-01-01 commodity IVV
          a__substidenticals: "SPY"
        """
        tickerrel = RelateTickers(f)
        retval = tickerrel.build_commodity_groups(['a__equivalents'])

        self.assertEqual(0, len(retval))

    @test_utils.docfile
    def test_identicals_only(self, f):
        """
        2005-01-01 commodity VOO
          a__substidenticals: "IVV"

        2005-01-01 commodity IVV
          a__substidenticals: "SPY"
        """
        tickerrel = RelateTickers(f)
        retval = tickerrel.build_commodity_groups(['a__substidenticals'])

        self.assertEqual(1, len(retval))
        self.assertSetEqual(retval[0], set(['IVV', 'SPY', 'VOO']))

    @test_utils.docfile
    def test_identicals(self, f):
        """
        2005-01-01 commodity VOO
          a__substidenticals: "IVV"
          a__equivalents: "VFIAX"

        2005-01-01 commodity IVV
          a__substidenticals: "SPY"
        """
        tickerrel = RelateTickers(f)
        retval = tickerrel.ssims

        self.assertEqual(1, len(retval))
        self.assertSetEqual(retval[0], set(['IVV', 'SPY', 'VOO', 'VFIAX']))

    @test_utils.docfile
    def test_tlh_groups(self, f):
        """
        2005-01-01 commodity VOO
          a__substidenticals: "IVV"
          a__equivalents: "VFIAX"

        2005-01-01 commodity IVV
          a__substidenticals: "SPY"

        2005-01-01 commodity VTI
          a__equivalents: "VTSAX"

        2005-01-01 commodity VTSAX
          a__equivalents: "VTSMX"

        2005-01-01 commodity VLCAX
          a__equivalents: "VV"
          tlh_partners: "VTSAX,FXAIX"

        2005-01-01 commodity FXAIX
          a__substidenticals: "VFIAX"

        """
        tickerrel = RelateTickers(f)
        retval = tickerrel.compute_tlh_groups()

        expected_value = {'VLCAX': ['FXAIX', 'VFIAX', 'IVV', 'SPY', 'VOO', 'VTSAX', 'VTSMX', 'VTI'],
                          'IVV': ['VLCAX', 'VV', 'VTSAX', 'VTSMX', 'VTI'],
                          'VTI': ['FXAIX', 'VFIAX', 'IVV', 'SPY', 'VOO', 'VLCAX', 'VV'],
                          'VV': ['FXAIX', 'VFIAX', 'IVV', 'SPY', 'VOO', 'VTSAX', 'VTSMX', 'VTI'],
                          'FXAIX': ['VLCAX', 'VV', 'VTSAX', 'VTSMX', 'VTI'],
                          'VFIAX': ['VLCAX', 'VV', 'VTSAX', 'VTSMX', 'VTI'],
                          'SPY': ['VLCAX', 'VV', 'VTSAX', 'VTSMX', 'VTI'],
                          'VOO': ['VLCAX', 'VV', 'VTSAX', 'VTSMX', 'VTI'],
                          'VTSAX': ['FXAIX', 'VFIAX', 'IVV', 'SPY', 'VOO', 'VLCAX', 'VV'],
                          'VTSMX': ['FXAIX', 'VFIAX', 'IVV', 'SPY', 'VOO', 'VLCAX', 'VV']}

        expected_value = {k: sorted(v) for k, v in expected_value.items()}
        retval = {k: sorted(v) for k, v in retval.items()}
        self.assertDictEqual(retval, expected_value)

    @test_utils.docfile
    def test_tlh_sametype(self, f):
        """
        2005-01-01 commodity VOO
          a__substidenticals: "IVV"
          a__equivalents: "VFIAX"
          a__quoteType: "ETF"

        2005-01-01 commodity IVV
          a__substidenticals: "SPY"
          a__quoteType: "ETF"

        2005-01-01 commodity VV
          a__quoteType: "ETF"

        2005-01-01 commodity SPY
          a__quoteType: "ETF"

        2005-01-01 commodity VTI
          a__equivalents: "VTSAX"
          a__quoteType: "ETF"

        2005-01-01 commodity VTSAX
          a__equivalents: "VTSMX"
          a__quoteType: "MUTUALFUND"

        2005-01-01 commodity VTSMX
          a__quoteType: "MUTUALFUND"

        2005-01-01 commodity VLCAX
          a__equivalents: "VV"
          tlh_partners: "VTSAX,FXAIX"
          a__quoteType: "MUTUALFUND"

        2005-01-01 commodity FXAIX
          a__substidenticals: "VFIAX"
          a__quoteType: "MUTUALFUND"

        2005-01-01 commodity VFIAX
          a__quoteType: "MUTUALFUND"

        """
        tickerrel = RelateTickers(f)
        retval = tickerrel.compute_tlh_groups(same_type_funds_only=True)

        expected_value = {'VLCAX': ['FXAIX', 'VFIAX', 'VTSAX', 'VTSMX'],
                          'IVV': ['VV', 'VTI'],
                          'VTI': ['IVV', 'SPY', 'VOO', 'VV'],
                          'VV': ['IVV', 'SPY', 'VOO', 'VTI'],
                          'FXAIX': ['VLCAX', 'VTSAX', 'VTSMX'],
                          'VFIAX': ['VLCAX', 'VTSAX', 'VTSMX'],
                          'SPY': ['VV', 'VTI'],
                          'VOO': ['VV', 'VTI'],
                          'VTSAX': ['FXAIX', 'VFIAX', 'VLCAX'],
                          'VTSMX': ['FXAIX', 'VFIAX', 'VLCAX']}

        expected_value = {k: sorted(v) for k, v in expected_value.items()}
        retval = {k: sorted(v) for k, v in retval.items()}
        self.assertDictEqual(retval, expected_value)
