"""Download public source responses verbatim; never replace failed data with samples."""
from pathlib import Path
import concurrent.futures, datetime, hashlib, json, urllib.request, urllib.error

ROOT = Path(__file__).resolve().parent
SOURCES = {
    'yahoo_aapl': 'https://query1.finance.yahoo.com/v8/finance/chart/AAPL?range=2y&interval=1d',
    'stooq_aapl': 'https://stooq.com/q/d/l/?s=aapl.us&i=d&d1=20240101&d2=20260930',
    'sec_aapl': 'https://data.sec.gov/submissions/CIK0000320193.json',
    'kalshi_weather': 'https://api.elections.kalshi.com/trade-api/v2/markets?series_ticker=KXHIGHNY&status=settled&limit=100',
    'weather_forecasts': 'https://previous-runs-api.open-meteo.com/v1/forecast?latitude=40.7789&longitude=-73.9692&start_date=2025-06-01&end_date=2025-08-31&hourly=temperature_2m_previous_day1,temperature_2m_previous_day2&models=gfs_seamless&timezone=America%2FNew_York&temperature_unit=fahrenheit',
    'iem_observations': 'https://mesonet.agron.iastate.edu/cgi-bin/request/daily.py?network=NY_ASOS&stations=NYC&year1=2025&month1=6&day1=1&year2=2025&month2=8&day2=31&vars=max_temp_f&na=NA&format=csv',
    'house_index': 'https://disclosures-clerk.house.gov/public_disc/financial-pdfs/2025FD.zip',
}

def fetch(name, url):
    record = {'name': name, 'url': url, 'retrieved_at_utc': datetime.datetime.now(datetime.timezone.utc).isoformat()}
    try:
        req = urllib.request.Request(url, headers={'User-Agent': 'QGHacksAcademicResearch/0.1', 'Accept': '*/*'})
        with urllib.request.urlopen(req, timeout=35) as response:
            data = response.read()
            record.update(status=response.status, content_type=response.headers.get('Content-Type'))
        (ROOT / 'raw' / (name + '.raw')).write_bytes(data)
        record.update(bytes=len(data), sha256=hashlib.sha256(data).hexdigest())
    except Exception as exc:
        record['error'] = str(exc)
    return record

if __name__ == '__main__':
    with concurrent.futures.ThreadPoolExecutor(max_workers=3) as pool:
        records = list(pool.map(lambda item: fetch(*item), SOURCES.items()))
    (ROOT / 'results' / 'source_probe.json').write_text(json.dumps(records, indent=2))
    print(json.dumps(records, indent=2))
