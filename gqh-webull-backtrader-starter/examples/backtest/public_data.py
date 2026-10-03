"""Offline feed replay using saved real Yahoo responses; no Webull SDK or credentials.

This is an integration audit, not a strategy or profitability result.
Run from the outer QGHACKS workspace with .venv/bin/python and --symbol AMD.
"""
import argparse,hashlib,json
from pathlib import Path
import backtrader as bt
import pandas as pd

WORKSPACE=Path(__file__).resolve().parents[3]

class AuditStrategy(bt.Strategy):
    def __init__(self):self.rows=0;self.last_time=None
    def next(self):
        now=self.data.datetime.datetime(0)
        assert self.last_time is None or now>self.last_time
        assert self.data.volume[0]>0
        assert self.data.high[0]>=max(self.data.open[0],self.data.close[0],self.data.low[0])
        assert self.data.low[0]<=min(self.data.open[0],self.data.close[0])
        self.last_time=now;self.rows+=1

def main():
    parser=argparse.ArgumentParser();parser.add_argument('--symbol',default='AMD',choices=['AMD','ADBE','CRM','ORCL','NFLX','COST']);args=parser.parse_args()
    path=WORKSPACE/'experiments'/'raw'/('semantic_prices_'+args.symbol+'.raw')
    source=json.loads(path.read_text());assert source['chart']['error'] is None
    raw=source['chart']['result'][0];assert raw['meta']['symbol']==args.symbol
    frame=pd.DataFrame(raw['indicators']['quote'][0])
    frame.index=pd.to_datetime(raw['timestamp'],unit='s',utc=True).tz_convert('America/New_York').normalize().tz_localize(None)
    frame=frame.loc[:'2026-09-30',['open','high','low','close','volume']]
    assert frame.notna().all().all() and not frame.index.duplicated().any()
    engine=bt.Cerebro(stdstats=False)
    engine.adddata(bt.feeds.PandasData(dataname=frame,timeframe=bt.TimeFrame.Days,openinterest=None),name=args.symbol)
    engine.addstrategy(AuditStrategy)
    strategy=engine.run()[0]
    assert strategy.rows==len(frame)
    out={'status':'offline_feed_replay_passed','symbol':args.symbol,'bars':strategy.rows,'start':str(frame.index.min().date()),'end':str(frame.index.max().date()),
         'source_sha256':hashlib.sha256(path.read_bytes()).hexdigest(),'orders_submitted':0,
         'note':'Feed integration audit only. No trading strategy or performance evaluated.'}
    (WORKSPACE/'experiments'/'results'/'offline_feed_audit.json').write_text(json.dumps(out,indent=2));print(json.dumps(out,indent=2))

if __name__=='__main__':main()
