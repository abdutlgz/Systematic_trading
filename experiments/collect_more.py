import datetime, json, time, urllib.parse
from probe import ROOT, fetch

records=[]
def get(name,url):
    r=fetch(name,url); records.append(r)
    print(name,r.get('status',r.get('error')),flush=True)
    if 'error' not in r:
        return json.loads((ROOT/'raw'/f'{name}.raw').read_text())

# Fill JPM's actual history gap rather than silently encoding missing filings as zero.
jpm=json.loads((ROOT/'raw'/'sec_jpm.raw').read_text())
for f in jpm['filings']['files']:
    if f['filingTo'] >= '2024-10-01':
        get('sec_jpm_'+f['name'].split('-')[-1].split('.')[0], 'https://data.sec.gov/submissions/'+f['name'])
        time.sleep(.25)

# Fixed 92-day weather window. Paginate both current and archived stores.
allmarkets=[]
for mode,initial in [('markets','kalshi_weather'),('historical/markets','kalshi_weather_summer')]:
    page=json.loads((ROOT/'raw'/f'{initial}.raw').read_text())
    allmarkets.extend(page['markets'])
    for n in range(1,8):
        dates=[m['event_ticker'].split('-')[-1] for m in page['markets']]
        parsed=[datetime.datetime.strptime(d,'%y%b%d').date() for d in dates]
        if not page.get('cursor') or min(parsed)<datetime.date(2026,7,1): break
        url=f'https://api.elections.kalshi.com/trade-api/v2/{mode}?series_ticker=KXHIGHNY&limit=100&cursor='+urllib.parse.quote(page['cursor'])
        if mode=='markets': url+='&status=settled'
        page=get('kalshi_'+mode.replace('/','_')+'_'+str(n),url)
        if page is None: break
        allmarkets.extend(page['markets'])
        time.sleep(.2)
unique={m['ticker']:m for m in allmarkets}
(ROOT/'results'/'weather_markets.json').write_text(json.dumps(list(unique.values()),indent=2))
get('weather_2026','https://previous-runs-api.open-meteo.com/v1/forecast?latitude=40.7789&longitude=-73.9692&start_date=2026-07-01&end_date=2026-09-30&hourly=temperature_2m_previous_day1,temperature_2m_previous_day2&models=gfs_seamless&timezone=America%2FNew_York&temperature_unit=fahrenheit')
# Check real historical quotes on one archived contract before attempting any backtest.
m=next(m for m in allmarkets if m['event_ticker']=='KXHIGHNY-26JUL31')
start=int(datetime.datetime(2026,7,30,tzinfo=datetime.timezone.utc).timestamp())
get('kalshi_candle_probe',f'https://api.elections.kalshi.com/trade-api/v2/historical/markets/{m["ticker"]}/candlesticks?start_ts={start}&end_ts={start+3*86400}&period_interval=60')
(ROOT/'results'/'additional_manifest.json').write_text(json.dumps(records,indent=2))
