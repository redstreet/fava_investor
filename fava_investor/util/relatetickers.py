#!/usr/bin/env python3

import os
import sys
from collections import defaultdict
import itertools

from beancount import loader
from beancount.core import getters


class RelateTickers:
    def __init__(self, cf):
        entries, _, _ = self.load_file(cf)

        # basic databases
        self.db = getters.get_commodity_directives(entries)
        self.archived = [c for c in self.db if 'archive' in self.db[c].meta]

        # similars databases
        self.ssims = self.build_commodity_groups(['equivalent', 'substsimilar'])
        ssimscopy = [i.copy() for i in self.ssims]
        self.ssims_preferred = {i.pop(): i for i in ssimscopy}

    def load_file(self, cf):
        if cf is None:
            print("File not specified. See help.", file=sys.stderr)
            sys.exit(1)
        if not os.path.exists(cf):
            print(f"File not found: {cf}", file=sys.stderr)
            sys.exit(1)
        return loader.load_file(cf)

    def non_archived_set(self, s):
        removes = [c for c in s if c in self.archived]
        return [i for i in s if i not in removes]

    def non_archived_los(self, listofsets):
        """Filter out archived commodities from a list of sets."""
        retval = []
        for r in listofsets:
            na = self.non_archived_set(r)
            if na:
                retval.append(na)
        return retval

    def substsimilars(self, ticker):
        """Returns a complete list of commodities substantially similar to the given ticker. The substantially
        similar set is built from an incomplete beancount commodities declaration file.

        If the input is a list or a set, returns a list/set for all tickers in the input.
        """

        if isinstance(ticker, list):
            retval = [self.substsimilars(t) for t in ticker]
            return [j for i in retval for j in i]

        if isinstance(ticker, set):
            retval = [self.substsimilars(t) for t in ticker]
            return set([j for i in retval for j in i])

        for group in self.ssims:
            if ticker in group:
                return self.pretty_sort([g for g in group if g != ticker])
        return []

    def representative(self, ticker):
        """Consistently returns a ticker that represents a group of substantially similar tickers. For
        example, if [AA, BB, CC, DD] are a group of substantially similar tickers, this method returns 'AA'
        when called with any ticker in the group (AA, BB, CC, or DD).

        This method also accepts a list or set, and returns a list of representative tickers for each ticker
        in the list or set."""

        db = self.ssims_preferred
        if isinstance(ticker, list):
            return [self.representative(t) for t in ticker]

        if isinstance(ticker, set):
            return set([self.representative(t) for t in ticker])

        if ticker in db:
            return ticker
        for k in db:
            if ticker in db[k]:
                return k
        return ticker

    def build_commodity_groups(self, metas, only_non_archived=False):
        """Find equivalent sets. Includes equivalents."""

        retval = []

        for c in self.db:
            equis = set()
            for m in metas:
                equis.update(self.db[c].meta.get(m, '').split(','))
            if '' in equis:
                equis.remove('')
            if not equis:
                continue
            equis.add(c)
            added = False
            for e in equis:
                for r in retval:
                    if e in r:
                        r = r.update(equis)
                        added = True
                        break

            if not added:
                retval.append(set(equis))

        if only_non_archived:
            return self.non_archived_los(retval)
        return retval

    def pretty_sort(self, tickers, group=False):
        """Sort, and optionally group substantially similar tickers together.
           Input: list of tickers, or a comma separated string of tickers
        """

        if isinstance(tickers, str):
            tickers = tickers.split(',')
        tickers.sort(key=len, reverse=True)
        tickers.sort(key=lambda x: self.representative(x))

        if group:
            return [tuple(g) for k, g in itertools.groupby(tickers, key=lambda x: self.representative(x))]
        else:
            return tickers

    def compute_tlh_groups(self):
        """Given an incomplete specification of TLH partners, and complete specification of substantially similar
        and equivalent mutual funds/ETFs/tickers, compute the full set of TLH partners."""

        tlh = defaultdict(set)

        # Step 1. Read tlh partners manually specified in commodity declarations. This is the incompletely
        # specification that we want to turn into a complete specification
        for c in self.db:
            if 'tlh_partners' in self.db[c].meta:
                partners = self.db[c].meta.get('tlh_partners', '').split(',')
                tlh[c].update(partners)
        # printd(tlh)

        # Step 2. Remove substantially similar tickers by replacing each ticker with a representative for its
        # substantially similar group

        tlh = {self.representative(k): self.representative(v) for k, v in tlh.items()}
        # printd(tlh)

        # Step 3. Apply the following rule, once (no iteration or convergence needed):
        # if we are given:
        # A -> (B, C)   # Meaning: A's TLH partners are B, C
        # where A, B, C are mutually substantially dissimilar
        #
        # then we infer:
        # B -> (A, C)
        # C -> (A, B)

        newtlh = tlh.copy()
        for k, v in tlh.items():
            for t in v:
                tpartners = [k] + [i for i in v if i != t]
                if t in newtlh:
                    newtlh[t].update(tpartners)
                else:
                    newtlh[t] = set(tpartners)

        # printd(newtlh)
        tlh = newtlh

        # Step 4. Add substantially similar tickers (first to values, then to keys)

        tlh = {k: v.union(self.substsimilars(v)) for k, v in tlh.items()}
        newtlh = tlh.copy()
        # printd(tlh)
        for k, v in tlh.items():
            for s in self.substsimilars(k):
                newtlh[s] = v
        # printd(newtlh)
        tlh = newtlh

        # Step 5: cleanup. Remove archived tickers from both keys and values, and sort into groups
        tlh = {k: self.non_archived_set(v) for k, v in tlh.items() if k not in self.archived}
        tlh = {k: self.pretty_sort(v) for k, v in tlh.items()}

        return tlh
