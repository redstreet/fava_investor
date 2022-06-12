#!/usr/bin/env python3
import asyncio
import os
import pickle
import datetime
import yfinance as yf


class CachedTickerInfo:
    def __init__(self, cache_file):
        self.cache_file = cache_file
        if not os.path.exists(self.cache_file):
            with open(self.cache_file, 'wb') as f:
                pickle.dump({}, f)
        with open(self.cache_file, 'rb') as f:
            data = pickle.load(f)
        # print(self.get_cache_last_updated())
        self.data = data

    def get_cache_last_updated(self):
        cache_file_updated = os.path.getmtime(self.cache_file)
        tz = datetime.datetime.now().astimezone().tzinfo
        self.cache_last_updated = datetime.datetime.fromtimestamp(cache_file_updated, tz).isoformat()
        return self.cache_last_updated

    def lookup_yahoo(self, ticker):
        t_obj = yf.Ticker(ticker)

        print("Downloading info for", ticker)
        self.data[ticker] = t_obj.info
        self.data[ticker]['isin'] = t_obj.isin
        if self.data[ticker]['isin'] == '-':
            self.data[ticker].pop('isin')
        if 'annualReportExpenseRatio' in self.data[ticker]:
            er = self.data[ticker]['annualReportExpenseRatio']
            if er:
                self.data[ticker]['annualReportExpenseRatio'] = round(er * 100, 2)

    def write_cache(self):
        with open(self.cache_file, 'wb') as f:
            pickle.dump(self.data, f)

    def remove(self, ticker):
        self.data.pop(ticker, None)
        self.write_cache()

    def batch_lookup(self, tickers):
        async def download():
            loop = asyncio.get_running_loop()
            tickers_to_lookup = [t for t in tickers if t not in self.data]
            tasks = [loop.run_in_executor(None, self.lookup_yahoo, ticker) for ticker in tickers_to_lookup]
            await asyncio.gather(*tasks)

        asyncio.run(download())
        self.write_cache()
