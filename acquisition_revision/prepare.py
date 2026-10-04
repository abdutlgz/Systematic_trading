"""Snapshot existing inputs and optionally collect split-normalized dividends.

python acquisition_revision/prepare.py
python acquisition_revision/prepare.py --dividends
Uses MASSIVE_API_KEY or the existing ignored starter .env; never prints credentials.
"""
import argparse
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import shutil
import time
from urllib.parse import urlparse, parse_qsl, urlencode, urlunparse

import pandas as pd
import requests

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
DATA = HERE / 'data'
CACHE = HERE / 'cache'


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def clean_url(url):
    u = urlparse(url)
    return urlunparse(u._replace(query=urlencode([(k,v) for k,v in parse_qsl(u.query)
                                                  if k.lower() not in ('apikey','api_key')])))


def key():
    if os.environ.get('MASSIVE_API_KEY'):
        return os.environ['MASSIVE_API_KEY']
    env = ROOT / 'gqh-massive-8k-starter/.env'
    if env.exists():
        for line in env.read_text().splitlines():
            if line.startswith('MASSIVE_API_KEY='):
                return line.split('=',1)[1].strip().strip('"\'')
    raise RuntimeError('Set MASSIVE_API_KEY; no credential is stored in this folder.')


def get(url, params=None, token=None, old_cache=False):
    prepared = requests.Request('GET',url,params=params).prepare().url
    url = clean_url(prepared)
    if urlparse(url).hostname != 'api.massive.com':
        raise RuntimeError('Unexpected API host')
    digest = hashlib.sha1(url.encode()).hexdigest()+'.json'
    path = (ROOT/'gqh-massive-8k-starter/.massive_cache' if old_cache else CACHE)/digest
    if old_cache and not path.exists():
        path=ROOT/'gqh-massive-8k-starter/.massive_cache'/(hashlib.sha1(prepared.encode()).hexdigest()+'.json')
    if path.exists():
        return json.loads(path.read_text())
    if old_cache:
        raise RuntimeError('Required historical disclosure cache page missing')
    for attempt in range(4):
        try:
            response=requests.get(url,headers={'Authorization':f'Bearer {token}'},timeout=25)
            if response.status_code in (429,500,502,503,504):
                time.sleep(1+attempt);continue
            response.raise_for_status()
            result=response.json()
            if result.get('status') not in ('OK','DELAYED'):
                raise RuntimeError('API returned non-success status')
            # Do not cache URLs containing credentials.
            if result.get('next_url'):result['next_url']=clean_url(result['next_url'])
            path.write_text(json.dumps(result))
            return result
        except requests.RequestException as exc:
            if attempt==3:
                raise RuntimeError(f'API request failed ({type(exc).__name__})') from None
    raise RuntimeError('API retry limit exceeded')


def disclosures():
    p=get('https://api.massive.com/stocks/filings/8-K/vX/disclosures',
          {'tertiary_category':'acquisition_agreement','filing_date.gte':'2021-09-01',
           'filing_date.lte':'2026-09-30','limit':1000,'sort':'filing_date.asc'},old_cache=True)
    rows=list(p.get('results',[]))
    while p.get('next_url'):
        p=get(p['next_url'],old_cache=True);rows.extend(p.get('results',[]))
    (DATA/'disclosures.json').write_text(json.dumps(rows,indent=1))


def collect_dividends():
    ev=pd.read_csv(DATA/'events.csv')
    tickers=sorted(set(ev.ticker)|{'SPY'})
    token=key()
    def one(ticker):
        p=get('https://api.massive.com/stocks/v1/dividends',
              {'ticker':ticker,'ex_dividend_date.gte':'2022-01-01',
               'ex_dividend_date.lte':'2026-09-30','limit':5000,'sort':'ex_dividend_date.asc'},token)
        rows=list(p.get('results',[]))
        while p.get('next_url'):
            p=get(p['next_url'],token=token);rows.extend(p.get('results',[]))
        return ticker,rows
    rows=[];completed=[]
    with ThreadPoolExecutor(8) as pool:
        for ticker,result in pool.map(one,tickers):
            rows.extend(result);completed.append(ticker)
            if len(completed)%100==0:print(f'Dividends: {len(completed)}/{len(tickers)} tickers',flush=True)
    columns=['id','ticker','ex_dividend_date','pay_date','currency','cash_amount','split_adjusted_cash_amount']
    d=pd.DataFrame(rows).reindex(columns=columns)
    d.to_csv(DATA/'dividends.csv',index=False)
    (DATA/'dividend_coverage.json').write_text(json.dumps({'complete':True,'tickers':completed,
         'endpoint':'/stocks/v1/dividends','records':len(rows),'retrieved_utc':datetime.now(timezone.utc).isoformat()},indent=2))
    print(f'Dividends complete: {len(tickers)} tickers; {len(rows)} records',flush=True)


def main():
    ap=argparse.ArgumentParser();ap.add_argument('--dividends',action='store_true');args=ap.parse_args()
    DATA.mkdir(exist_ok=True);CACHE.mkdir(exist_ok=True)
    source={'prices.csv':'event8k/data/grid_prices.csv','adv.csv':'event8k/data/acq_dollar_volume.csv',
            'ff5.csv':'strategy/data/F-F_Research_Data_5_Factors_2x3_daily.csv',
            'momentum.csv':'strategy/data/F-F_Momentum_Factor_daily.csv'}
    for target,path in source.items():
        if not (DATA/target).exists():shutil.copy2(ROOT/path,DATA/target)
    if not (DATA/'events.csv').exists():
        ev=pd.read_csv(ROOT/'event8k/data/grid_events.csv')
        ev=ev[(ev.defn=='acquisition_agreement')&(ev.mcap>=2e9)]
        ev.to_csv(DATA/'events.csv',index=False)
    if not (DATA/'settlements.csv').exists():
        pd.DataFrame(columns=['ticker','date','split_adjusted_cash_price','source_url']).to_csv(DATA/'settlements.csv',index=False)
    if not (DATA/'disclosures.json').exists():disclosures()
    if args.dividends:collect_dividends()
    manifest={'created_utc':datetime.now(timezone.utc).isoformat(),'source_root':str(ROOT),
              'source_files':source,'files':{p.name:{'sha256':sha(p),'bytes':p.stat().st_size}
                       for p in sorted(DATA.iterdir()) if p.is_file()},
              'protocol_sha256':sha(HERE/'PROTOCOL.md'),'licensed_data_not_for_redistribution':True}
    manifest['corporate_action_journal_sha256']=sha(HERE/'corporate_actions.csv')
    (HERE/'output/input_manifest.json').write_text(json.dumps(manifest,indent=2))
    print('Input manifest saved; original inputs preserved.')


if __name__=='__main__':main()
