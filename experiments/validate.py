"""Validate real saved artifacts and provenance; no generated observations."""
import hashlib,json
from pathlib import Path
import pandas as pd
from probe import ROOT

count=0
for name in ['source_probe.json','collection_manifest.json','additional_manifest.json','weather_quote_manifest.json']:
    records=json.loads((ROOT/'results'/name).read_text())
    for r in records:
        if 'sha256' not in r:continue
        raw=(ROOT/'raw'/(r['name']+'.raw')).read_bytes()
        assert hashlib.sha256(raw).hexdigest()==r['sha256'],r['name']
        assert len(raw)==r['bytes']
        count+=1
stock=pd.read_json(ROOT/'results'/'stock_predictions.jsonl',lines=True,convert_dates=False)
assert len(stock)==1870 and stock.symbol.nunique()==10
assert stock.date.min()>='2026-01-01' and stock.date.max()<='2026-09-30'
assert not stock[['date','symbol']].duplicated().any()
assert stock.filter(regex='^pred_').notna().all().all()
weather=pd.read_json(ROOT/'results'/'weather_market_predictions.jsonl',lines=True,convert_dates=False)
assert weather.date.nunique()==29
assert ((weather.model_probability>=0)&(weather.model_probability<=1)).all()
assert ((weather.yes_bid<=weather.yes_ask)&(weather.yes_bid>=0)&(weather.yes_ask<=1)).all()
for _,r in weather.iterrows():
    assert pd.Timestamp(r.quote_timestamp_utc).tz_convert('America/New_York').strftime('%Y-%m-%d')<r.date
    assert abs(r.model_brier-(r.model_probability-r.outcome)**2)<1e-8
print(f'PASS: {count} raw-response hashes; chronological stock test; pre-outcome weather quotes; probability and outcome calculations.')
