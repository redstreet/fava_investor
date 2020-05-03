#!/bin/env python3

from fava_investor.common.libinvestor import val, build_table_footer
from beancount.core.number import Decimal, D
from beancount.core.inventory import Inventory
import collections
import locale
from beancount.core import data, inventory, position, convert
import re


def get_tables(accapi):
    buckets = build_buckets(accapi)
    classify_postings(accapi.entries, accapi.options['accounts_pattern'], buckets.values())
    return compute_totals(buckets)


def build_buckets(accapi):
    retval = {}
    patterns = ['accounts', 'dividends', 'capgains']
    for p in patterns:
        retval[p] = Bucket(accapi, p+'_pattern')
    retval['contribs'] = AntiBucket(accapi, [p+'_pattern' for p in patterns])
    # TODO: ensure buckets have mutually exclusive accounts
    return retval


def classify_postings(entries, value_pattern, buckets, start_date=None, end_date=None):
    # start_date, end_date filtering not yet implemented
    for entry in entries:
        if isinstance(entry, data.Transaction):
            if any(re.match(value_pattern, posting.account) for posting in entry.postings):
                for bucket in buckets:
                    bucket.update(entry)


def compute_totals(buckets):
    for b in buckets.values():
        b.compute_totals()
    # buckets['accounts'].compute_value()
    totals = {
        'contribs':     -buckets['contribs'].cost,
        'dividends':    -buckets['dividends'].cost,
        'realized':     -buckets['capgains'].cost,
        'unrealized':   buckets['accounts'].value + -buckets['accounts'].cost,
        'basis':        buckets['accounts'].cost,
        'market_value': buckets['accounts'].value,
    }
    return totals


class Bucket:
    def __init__(self, accapi, config_pattern):
        self.label = config_pattern
        self.accapi = accapi
        self.postings = []
        if not isinstance(config_pattern, list):
            self.pattern = accapi.options[config_pattern]

    def update(self, entry):
        for p in entry.postings:
            if re.match(self.pattern, p.account):
                self.postings.append(data.TxnPosting(entry, p))

    def compute_totals(self):
        self.total = inventory.Inventory()
        for tp in self.postings:
            self.total.add_position(position.get_position(tp.posting))
        price_map = self.accapi.build_price_map()
        currency = self.accapi.get_operating_currencies()[0]

        self.cost = self.total.reduce(convert.get_cost)
        self.cost = self.cost.reduce(convert.convert_position, currency, price_map)

        self.value = self.total.reduce(convert.get_value, price_map)
        self.value = self.value.reduce(convert.convert_position, currency, price_map)


class AntiBucket(Bucket):
    def __init__(self, accapi, config_patterns):
        super(AntiBucket, self).__init__(accapi, config_patterns)
        self.patterns = [accapi.options[p] for p in config_patterns]

    def update(self, entry):
        for p in entry.postings:
            if not any(re.match(pattern, p.account) for pattern in self.patterns):
                self.postings.append(data.TxnPosting(entry, p))
