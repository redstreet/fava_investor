#!/usr/bin/env python3

import beancountinvestorapi as api
import functools
import datetime
from beancount.utils import test_utils
import libtlh
# python3 -m unittest discover . to run


@functools.lru_cache(maxsize=1)
def dates():
    def minusdays(today, d):
        return (today - datetime.timedelta(days=d)).isoformat()
    today = datetime.datetime.now().date()
    retval = {'today': today,
              'm1': minusdays(today, 1),
              'm5': minusdays(today, 5),
              'm9': minusdays(today, 9),
              'm10': minusdays(today, 10),
              'm15': minusdays(today, 15),
              'm20': minusdays(today, 20),
              'm100': minusdays(today, 100),
              }
    return retval


def insert_dates(function, **kwargs):
    """A decorator that rewrites the function's docstring with dates. Needed here because TLH looks back at
    the past 30 days, which means all test cases need to be aware of this period."""

    @functools.wraps(function)
    def new_function(self, filename):
        return function(self, filename)
    new_function.__doc__ = function.__doc__.format(**(dates()))
    return new_function


class TestScriptCheck(test_utils.TestCase):
    def setUp(self):
        self.options = {'accounts_pattern': "Assets:Investments:Taxable", 'wash_pattern': "Assets:Investments"}

    @test_utils.docfile
    @insert_dates
    def test_no_relevant_accounts(self, f):
        """
        2010-01-01 open Assets:Investments:Brokerage
        2010-01-01 open Assets:Bank

        {m10} * "Buy stock"
         Assets:Investments:Brokerage 1 BNCT {{200 USD}}
         Assets:Bank

        {m1} price BNCT 100 USD
        """
        accapi = api.AccAPI(f, {})

        retrow_types, to_sell, recent_purchases = libtlh.find_harvestable_lots(accapi, self.options)

        self.assertEqual(0, len(to_sell))
        self.assertEqual(0, len(recent_purchases))

    @test_utils.docfile
    @insert_dates
    def test_harvestable_basic(self, f):
        """
        2010-01-01 open Assets:Investments:Taxable:Brokerage
        2010-01-01 open Assets:Bank

        {m10} * "Buy stock"
         Assets:Investments:Taxable:Brokerage 1 BNCT {{200 USD}}
         Assets:Bank

        {m1} price BNCT 100 USD
        """
        accapi = api.AccAPI(f, {})

        retrow_types, to_sell, recent_purchases = libtlh.find_harvestable_lots(accapi, self.options)

        self.assertEqual(1, len(to_sell))
        self.assertEqual(1, len(recent_purchases))

    @test_utils.docfile
    @insert_dates
    def test_dontbuy(self, f):
        """
        option "operating_currency" "USD"
        2010-01-01 open Assets:Investments:Taxable:Brokerage
        2010-01-01 open Assets:Bank

        {m100} * "Buy stock"
         Assets:Investments:Taxable:Brokerage 1 BNCT {{200 USD}}
         Assets:Bank

        {m10} * "Sell stock"
         Assets:Investments:Taxable:Brokerage -1 BNCT {{200 USD}} @ 100 USD
         Assets:Bank

        {m1} price BNCT 100 USD
        """
        accapi = api.AccAPI(f, {})

        rtypes, rrows = libtlh.recently_sold_at_loss(accapi, self.options)

        self.assertEqual(1, len(rrows))
