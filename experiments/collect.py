"""Small bounded public-data collection; imports the provenance-preserving downloader."""
import datetime, json, time
from pathlib import Path
from probe import fetch, ROOT

CIKS = {'AAPL':320193,'MSFT':789019,'NVDA':1045810,'AMZN':1018724,'META':1326801,
        'GOOGL':1652044,'TSLA':1318605,'WMT':104169,'JPM':19617,'XOM':34088}

def main():
    records = []
    for symbol in list(CIKS) + ['SPY']:
        name='yahoo_'+symbol.lower()
        if not (ROOT/'raw'/f'{name}.raw').exists():
            records.append(fetch(name,f'https://query1.finance.yahoo.com/v8/finance/chart/{symbol}?range=2y&interval=1d'))
            print(symbol,records[-1].get('status',records[-1].get('error')),flush=True)
            time.sleep(.3)
        if symbol in CIKS:
            name='sec_'+symbol.lower()
            if not (ROOT/'raw'/f'{name}.raw').exists():
                records.append(fetch(name,f'https://data.sec.gov/submissions/CIK{CIKS[symbol]:010d}.json'))
                time.sleep(.3)
    extra={
      'iem_observations_fixed':'https://mesonet.agron.iastate.edu/cgi-bin/request/daily.py?network=NY_ASOS&stations=NYC&sts=2025-06-01&ets=2025-08-31&var=max_temp_f&na=NA&format=csv',
      'kalshi_weather_summer':'https://api.elections.kalshi.com/trade-api/v2/historical/markets?series_ticker=KXHIGHNY&limit=100',
      'kalshi_weather_series':'https://api.elections.kalshi.com/trade-api/v2/series/KXHIGHNY',
    }
    for name,url in extra.items():
        records.append(fetch(name,url))
        print(name,records[-1].get('status',records[-1].get('error')),flush=True)
    (ROOT/'results'/'collection_manifest.json').write_text(json.dumps(records,indent=2))

if __name__=='__main__': main()
