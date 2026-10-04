"""Collect successor-symbol prices/dividends and build identity-continuous inputs.

Cash and conversion terms are a source-linked manual journal, not inferred fills.
"""
from concurrent.futures import ThreadPoolExecutor
import json
from pathlib import Path
import shutil

import pandas as pd
import requests

from prepare import DATA,HERE,ROOT,get,key


def main():
    actions=pd.read_csv(HERE/'corporate_actions.csv',parse_dates=['date'])
    for filename in ('prices.csv','dividends.csv'):
        raw=DATA/('original_'+filename)
        if not raw.exists():shutil.copy2(DATA/filename,raw)
    px=pd.read_csv(DATA/'original_prices.csv',index_col=0,parse_dates=True).sort_index()
    div=pd.read_csv(DATA/'original_dividends.csv',parse_dates=['ex_dividend_date','pay_date'])
    token=key();symbols=sorted(set(actions.stock_ticker.dropna()))
    def one(ticker):
        p=get(f'https://api.massive.com/v2/aggs/ticker/{ticker}/range/1/day/2021-01-01/2026-10-02',
              {'adjusted':'true','limit':50000},token)
        rows=p.get('results',[])
        if not rows:raise RuntimeError(f'No successor quotes for {ticker}')
        idx=pd.to_datetime([r['t'] for r in rows],unit='ms',utc=True).tz_convert('America/New_York').normalize().tz_localize(None)
        s=pd.Series([r['c'] for r in rows],index=idx,dtype=float)
        p=get('https://api.massive.com/stocks/v1/dividends',{'ticker':ticker,'ex_dividend_date.gte':'2022-01-01',
             'ex_dividend_date.lte':'2026-09-30','limit':5000,'sort':'ex_dividend_date.asc'},token)
        dr=list(p.get('results',[]))
        while p.get('next_url'):
            p=get(p['next_url'],token=token);dr.extend(p.get('results',[]))
        return ticker,s,dr
    add=[]
    with ThreadPoolExecutor(6) as pool:
        for ticker,series,rows in pool.map(one,symbols):
            if ticker not in px:px[ticker]=series.reindex(px.index)
            add.extend(rows)
    if add:div=pd.concat([div,pd.DataFrame(add)],ignore_index=True).drop_duplicates('id')
    for field in ('ex_dividend_date','pay_date'):div[field]=pd.to_datetime(div[field],errors='coerce')
    override=DATA/'dividend_overrides.csv'
    if override.exists():
        for o in pd.read_csv(override,parse_dates=['ex_dividend_date','known_at_date']).itertuples():
            if o.known_at_date>o.ex_dividend_date:raise RuntimeError('Future FX must not be used at ex-date')
            matching=(div.ticker==o.ticker)&(div.ex_dividend_date==o.ex_dividend_date)
            if matching.sum()!=1:raise RuntimeError('Dividend override must match exactly one raw dividend')
            div.loc[matching,'currency']='USD'
            div.loc[matching,'split_adjusted_cash_amount']=o.split_adjusted_cash_amount
    for a in actions[actions.type=='rename'].itertuples():
        # Fixed adjusted-share quantities use a common, verified 1:1 share basis.
        if a.stock_ratio!=1:raise RuntimeError('Non-1:1 rename needs explicit share-basis normalization')
        post=px.index>=a.date
        px.loc[post,a.ticker]=px.loc[post,a.stock_ticker]
        # Prefix known predecessor history for the successor's beta lookback.
        before=px.index<a.date
        px.loc[before,a.stock_ticker]=px.loc[before,a.stock_ticker].fillna(px.loc[before,a.ticker])
        mapped=div[(div.ticker==a.stock_ticker)&(div.ex_dividend_date>=a.date)].copy()
        mapped['ticker']=a.ticker;mapped['id']=mapped.id.astype(str)+'_identity_'+a.ticker
        div=pd.concat([div,mapped],ignore_index=True)
    px.to_csv(DATA/'prices.csv',index_label='date')
    div.reindex(columns=['id','ticker','ex_dividend_date','pay_date','currency','cash_amount','split_adjusted_cash_amount']).to_csv(DATA/'dividends.csv',index=False)
    (DATA/'corporate_action_coverage.json').write_text(json.dumps({'journal_rows':len(actions),
          'successor_symbols':symbols,'source_urls_required':True,'not_entry_filters':True},indent=2))
    print('Corporate actions: collected',len(symbols),'successor series; identity-continuous inputs saved.')


if __name__=='__main__':main()
