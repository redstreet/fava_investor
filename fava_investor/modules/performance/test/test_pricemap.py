import datetime

from beancount.core.prices import get_latest_price
from beancount.utils import test_utils

from fava_investor.modules.performance.split import build_price_map_with_fallback_to_cost
from fava_investor.modules.performance.test.testutils import SplitTestCase, get_ledger, i, get_value


class TestPriceMap(SplitTestCase):
    def assertHasPrice(self, currency_pair, date_str, price_map):
        self.assertIn(
            currency_pair, price_map, msg=f"currency pair not found in given price map"
        )

        date = datetime.datetime.strptime(date_str, "%Y-%m-%d").date()
        prices_found = len(
            [
                amount
                for price_date, amount in price_map[currency_pair]
                if price_date == date
            ]
        )
        self.assertGreater(
            prices_found,
            0,
            msg=f"price not found for {currency_pair} and date {date_str}",
        )

    @test_utils.docfile
    def test_fallback_to_purchase_price(self, filename):
        """
        2020-01-01 open Assets:Account
        2020-01-01 open Assets:Bank

        2020-01-01 * "contribution"
            Assets:Account  1 AA {1 USD}
            Assets:Bank
        """
        ledger = get_ledger(filename)
        entries = ledger.ledger.entries
        price_map = build_price_map_with_fallback_to_cost(entries)

        self.assertHasPrice(("AA", "USD"), "2020-01-01", price_map)

    @test_utils.docfile
    def test_no_fallback_if_there_is_earlier_price(self, filename):
        """
        2020-01-01 open Assets:Account
        2020-01-01 open Assets:Bank

        2020-01-01 price AA 2 USD
        2020-01-02 * "contribution"
            Assets:Account  1 AA {1 USD}
            Assets:Bank
        """
        ledger = get_ledger(filename)
        price_map = build_price_map_with_fallback_to_cost(ledger.ledger.entries)

        self.assertEqual(
            i("2 USD"), get_value(ledger, price_map, "Assets:Account", "2020-01-02")
        )

    @test_utils.docfile
    def test_prices_from_purchases_after_first_one_are_not_used(self, filename):
        """
        2020-01-01 open Assets:Account
        2020-01-01 open Assets:Bank

        2020-01-01 * "buy"
            Assets:Account  1 AA {1 USD}
            Assets:Bank

        2020-01-02 * "buy"
            Assets:Account  1 AA {2 USD}
            Assets:Bank
        """
        ledger = get_ledger(filename)
        price_map = build_price_map_with_fallback_to_cost(ledger.ledger.entries)

        self.assertEqual(1, get_latest_price(price_map, ("USD", "AA"))[1])

    @test_utils.docfile
    def test_no_fallback_if_there_is_price_in_following_entries_with_same_date(
            self, filename
    ):
        """
        2020-01-01 open Assets:Account
        2020-01-01 open Assets:Bank

        2020-01-02 * "contribution"
            Assets:Account  1 AA {1 USD}
            Assets:Bank

        2020-01-02 price AA 2 USD
        """
        ledger = get_ledger(filename)
        price_map = build_price_map_with_fallback_to_cost(ledger.ledger.entries)

        self.assertEqual(
            i("2 USD"), get_value(ledger, price_map, "Assets:Account", "2020-01-02")
        )
