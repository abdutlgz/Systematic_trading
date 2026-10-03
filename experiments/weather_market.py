import argparse, datetime, json, time, urllib.parse
import numpy as np
import pandas as pd
from probe import ROOT,fetch

def load():
    markets=json.loads((ROOT/'results'/'weather_markets.json').read_text())
    groups={}
    for m in markets:
        date=datetime.datetime.strptime(m['event_ticker'].split('-')[-1],'%y%b%d').strftime('%Y-%m-%d')
        if '2026-09-02'<=date<='2026-09-30': groups.setdefault(date,[]).append(m)
    return markets,groups

def collect():
    _,groups=load(); records=[]
    for date,ms in sorted(groups.items()):
        # Sep dates are EDT: midnight UTC is 20:00 Eastern on the previous day.
        ts=int(pd.Timestamp(date,tz='UTC').timestamp())
        params={'market_tickers':','.join(m['ticker'] for m in ms),'start_ts':ts-3600,'end_ts':ts,'period_interval':60,'include_latest_before_start':'false'}
        name='quotes_'+date
        if not (ROOT/'raw'/f'{name}.raw').exists():
            r=fetch(name,'https://api.elections.kalshi.com/trade-api/v2/markets/candlesticks?'+urllib.parse.urlencode(params))
            records.append(r); print(date,r.get('status',r.get('error')),flush=True); time.sleep(.15)
    (ROOT/'results'/'weather_quote_manifest.json').write_text(json.dumps(records,indent=2))

def evaluate():
    markets,groups=load()
    h=pd.DataFrame(json.loads((ROOT/'raw'/'weather_2026.raw').read_text())['hourly'])
    h['date']=h.time.str[:10]
    daily=h.groupby('date').temperature_2m_previous_day2.max()
    truth={datetime.datetime.strptime(m['event_ticker'].split('-')[-1],'%y%b%d').strftime('%Y-%m-%d'):float(m['expiration_value']) for m in markets if m.get('expiration_value')}
    train_dates=[d for d in sorted(daily.index) if '2026-07-08'<=d<='2026-09-01' and d in truth]
    residual=np.array([truth[d]-daily[d] for d in train_dates])
    rows=[]; missing=[]
    for date,ms in sorted(groups.items()):
        p=ROOT/'raw'/f'quotes_{date}.raw'
        if not p.exists(): missing.append({'date':date,'reason':'download missing'});continue
        raw=json.loads(p.read_text())
        quotes={m['market_ticker']:m['candlesticks'] for m in raw['markets']}
        ts=int(pd.Timestamp(date,tz='UTC').timestamp())
        predicted=daily[date]+residual
        weights=[]
        for m in ms:
            typ=m['strike_type']
            if typ=='greater': mask=predicted>=m['floor_strike']+.5
            elif typ=='less': mask=predicted<m['cap_strike']-.5
            elif typ=='between': mask=(predicted>=m['floor_strike']-.5)&(predicted<m['cap_strike']+.5)
            else: raise ValueError(typ)
            weights.append(float(mask.sum()+.5))
            actual=float(m['expiration_value'])
            actual_yes=(actual>m['floor_strike'] if typ=='greater' else actual<m['cap_strike'] if typ=='less' else m['floor_strike']<=actual<=m['cap_strike'])
            assert actual_yes==(m['result']=='yes'),m['ticker']
        assert sum(m['result']=='yes' for m in ms)==1
        assert abs(sum(weights)-len(residual)-.5*len(ms))<1e-8, 'bins do not partition distribution'
        probs=np.array(weights)/sum(weights)
        for m,prob in zip(ms,probs):
            assert pd.Timestamp(m['open_time']).timestamp()<ts
            candles=[c for c in quotes.get(m['ticker'],[]) if c['end_period_ts']==ts]
            if len(candles)!=1:
                missing.append({'ticker':m['ticker'],'reason':'exact comparison candle missing'});continue
            c=candles[0]
            bid=c['yes_bid'].get('close_dollars');ask=c['yes_ask'].get('close_dollars')
            if bid is None or ask is None:
                missing.append({'ticker':m['ticker'],'reason':'missing bid/ask'});continue
            bid=float(bid);ask=float(ask)
            if not 0<=bid<=ask<=1:
                missing.append({'ticker':m['ticker'],'reason':'invalid bid/ask'});continue
            y=int(m['result']=='yes');mid=(bid+ask)/2
            rows.append({'date':date,'ticker':m['ticker'],'quote_timestamp_utc':pd.Timestamp(ts,unit='s',tz='UTC').isoformat(),
                         'model_probability':float(prob),'market_midpoint':mid,'yes_bid':bid,'yes_ask':ask,
                         'outcome':y,'model_brier':float((prob-y)**2),'market_brier':float((mid-y)**2)})
    df=pd.DataFrame(rows)
    assert not df.empty,'No usable historical quotes'
    daily_scores=df.groupby('date')[['model_brier','market_brier']].mean()
    rng=np.random.default_rng(20261002)
    ix=rng.integers(0,len(daily_scores),(2000,len(daily_scores)))
    sampled=daily_scores.to_numpy()[ix].mean(axis=1)
    diff=sampled[:,0]-sampled[:,1]
    out={'status':'completed_exploratory_probability_comparison_no_execution_backtest',
         'training_days':len(residual),'test_days':len(daily_scores),'contracts':len(df),
         'model_brier':float(df.model_brier.mean()),'market_midpoint_brier':float(df.market_brier.mean()),
         'model_minus_market_brier_95pct_day_bootstrap':np.quantile(diff,[.025,.975]).tolist(),
         'days_model_better':int((daily_scores.model_brier<daily_scores.market_brier).sum()),
         'median_spread':float((df.yes_ask-df.yes_bid).median()),'missing':missing,
         'limitation':'Composite forecast availability assumed conservatively; midpoint is a probability baseline, not a fill price. No P&L. Only 29 dependent daily outcomes; settlement source changed.'}
    (ROOT/'results'/'weather_market_summary.json').write_text(json.dumps(out,indent=2))
    df.to_json(ROOT/'results'/'weather_market_predictions.jsonl',orient='records',lines=True)
    print(json.dumps(out,indent=2))

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--collect',action='store_true');args=parser.parse_args()
    if args.collect:collect()
    else:evaluate()
