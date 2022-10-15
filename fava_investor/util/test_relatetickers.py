#!/usr/bin/env python3

# 2005-01-01 commodity VTI
#   a__quoteType: "ETF"
#   a__substidenticals: "VTSMX,VTSAX"
#   equivalent: "VTSAX"
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
          equivalent: "VTSAX"

        2005-01-01 commodity VTSAX
          equivalent: "VTSMX"

        2005-01-01 commodity VTSMX
        """
        tickerrel = RelateTickers(f)
        retval = tickerrel.build_commodity_groups(['equivalent'])

        self.assertEqual(1, len(retval))
        self.assertSetEqual(retval[0], set(['VTI', 'VTSAX', 'VTSMX']))

    @test_utils.docfile
    def test_none(self, f):
        """
        2005-01-01 commodity VOO
          substidenticals: "IVV"

        2005-01-01 commodity IVV
          substidenticals: "SPY"
        """
        tickerrel = RelateTickers(f)
        retval = tickerrel.build_commodity_groups(['equivalent'])

        self.assertEqual(0, len(retval))

    @test_utils.docfile
    def test_identicals_only(self, f):
        """
        2005-01-01 commodity VOO
          substidenticals: "IVV"

        2005-01-01 commodity IVV
          substidenticals: "SPY"
        """
        tickerrel = RelateTickers(f)
        retval = tickerrel.build_commodity_groups(['substidenticals'])

        self.assertEqual(1, len(retval))
        self.assertSetEqual(retval[0], set(['IVV', 'SPY', 'VOO']))

    @test_utils.docfile
    def test_identicals(self, f):
        """
        2005-01-01 commodity VOO
          substidenticals: "IVV"
          equivalent: "VFIAX"

        2005-01-01 commodity IVV
          substidenticals: "SPY"
        """
        tickerrel = RelateTickers(f)
        retval = tickerrel.ssims

        self.assertEqual(1, len(retval))
        self.assertSetEqual(retval[0], set(['IVV', 'SPY', 'VOO', 'VFIAX']))

    @test_utils.docfile
    def test_tlh_groups(self, f):
        """
        2005-01-01 commodity VOO
          substidenticals: "IVV"
          equivalent: "VFIAX"

        2005-01-01 commodity IVV
          substidenticals: "SPY"

        2005-01-01 commodity VTI
          equivalent: "VTSAX"

        2005-01-01 commodity VTSAX
          equivalent: "VTSMX"

        2005-01-01 commodity VLCAX
          equivalent: "VV"
          tlh_partners: "VTSAX,FXAIX"

        2005-01-01 commodity FXAIX
          substidenticals: "VFIAX"

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

        expected_value = {k: v.sort() for k, v in expected_value.items()}
        retval = {k: v.sort() for k, v in retval.items()}
        self.assertDictEqual(retval, expected_value)
