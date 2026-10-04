"""Rebuild acquisition inputs from raw licensed responses in an isolated workspace.

No grid_events.csv, grid_prices.csv, parent disclosure cache, or saved NAV is read
during construction. Parent files are read ONLY for the final comparison report.
--workspace must be new/empty on first collection. --offline replays own receipts.
"""
import argparse
from concurrent.futures import ThreadPoolExecutor
import hashlib
import io
import json
from pathlib import Path
import subprocess
import sys
import zipfile

import numpy as np
import pandas as pd

from vendor import HERE,Vendor,sha,utc


def public(url,dest,offline=False):
    receipt=dest.with_suffix(dest.suffix+'.receipt.json')
    if dest.exists():
        meta=json.loads(receipt.read_text())
        if sha(dest)!=meta['sha256']:raise RuntimeError('Public source cache integrity failure')
        return meta
    if offline:raise RuntimeError('Public raw response missing: '+dest.name)
    subprocess.run(['/usr/bin/curl','--silent','--show-error','--fail','--location','--max-time','60',
                    url,'--output',str(dest)],check=True)
    meta={'url':url,'retrieved_utc':utc(),'sha256':sha(dest),'response_file':dest.name}
    receipt.write_text(json.dumps(meta,indent=2));return meta


def event_table(raw):
    d=pd.DataFrame(raw)
    d['ticker']=d.tickers.map(lambda t:str(t[0]).upper().replace('/','.') if isinstance(t,list) and t else None)
    d['cik']=d.cik.astype(str).str.lstrip('0');d['filing_date']=pd.to_datetime(d.filing_date)
    d=d.dropna(subset=['ticker']).sort_values(['cik','filing_date'])
    keep=[];last={}
    for r in d.itertuples():
        ok=r.cik not in last or (r.filing_date-last[r.cik]).days>30
        keep.append(ok)
        if ok:last[r.cik]=r.filing_date
    return d.loc[keep].query("filing_date >= '2022-01-01'").copy()


def panel(rows,field='c'):
    if not rows:return pd.Series(dtype=float)
    idx=pd.to_datetime([r['t'] for r in rows],unit='ms',utc=True).tz_convert('America/New_York').normalize().tz_localize(None)
    values=[r['c']*r.get('v',0) if field=='dollars' else r[field] for r in rows]
    s=pd.Series(values,index=idx,dtype=float);return s[~s.index.duplicated()]


def main():
    ap=argparse.ArgumentParser();ap.add_argument('--workspace',type=Path,required=True)
    ap.add_argument('--offline',action='store_true');ap.add_argument('--simulate',action='store_true')
    ap.add_argument('--placebos',type=int,default=100);a=ap.parse_args()
    root=a.workspace.resolve()
    if root==HERE.parent or HERE.parent/'data'==root:raise RuntimeError('Use a separate reconstruction workspace')
    root.mkdir(parents=True,exist_ok=True);data=root/'data';data.mkdir(exist_ok=True)
    out=root/'output';out.mkdir(exist_ok=True);v=Vendor(root,offline=a.offline)
    raw=v.rows('/stocks/filings/8-K/vX/disclosures',{'tertiary_category':'acquisition_agreement',
           'filing_date.gte':'2021-09-01','filing_date.lte':'2026-09-30','limit':1000,'sort':'filing_date.asc'})
    (data/'disclosures.json').write_text(json.dumps(raw,indent=1))
    ev=event_table(raw);print('Raw disclosures:',len(raw),'deduplicated cap checks:',len(ev),flush=True)
    def cap(r):
        p=v.get('/v3/reference/tickers/'+r.ticker,{'date':(r.filing_date-pd.Timedelta(days=1)).strftime('%Y-%m-%d')},allow_not_found=True)
        return p.get('results',{}).get('market_cap')
    caps=[]
    with ThreadPoolExecutor(8) as pool:
        for i,c in enumerate(pool.map(cap,ev.itertuples()),1):
            caps.append(c)
            if i%100==0:print('Cap checks',i,'/',len(ev),flush=True)
    ev['mcap']=caps
    ev[['cik','ticker','filing_date','accession_number','mcap']].to_csv(data/'cap_audit.csv',index=False)
    missing=int(ev.mcap.isna().sum());ev=ev[ev.mcap.fillna(0)>=2e9]
    ev.assign(defn='acquisition_agreement')[['defn','cik','ticker','filing_date','mcap']].to_csv(data/'events.csv',index=False)
    tickers=sorted(set(ev.ticker)|{'SPY'})
    journal=pd.read_csv(HERE.parent/'corporate_actions.csv')
    symbols=sorted(set(tickers)|set(journal.stock_ticker.dropna()))
    prices={};adv={};div=[];completed=[]
    def one(t):
        bars=v.rows('/v2/aggs/ticker/'+t+'/range/1/day/2021-01-01/2026-10-02',{'adjusted':'true','limit':50000})
        dividends=v.rows('/stocks/v1/dividends',{'ticker':t,'ex_dividend_date.gte':'2022-01-01',
                        'ex_dividend_date.lte':'2026-09-30','limit':5000,'sort':'ex_dividend_date.asc'})
        if not bars:raise RuntimeError('No raw bars: '+t)
        return t,bars,dividends
    with ThreadPoolExecutor(8) as pool:
        for i,(t,bars,dividends) in enumerate(pool.map(one,symbols),1):
            prices[t]=panel(bars)
            if t in set(ev.ticker):adv[t]=panel(bars,'dollars')
            div.extend(dividends);completed.append(t)
            if i%100==0:print('Bars/dividends',i,'/',len(symbols),flush=True)
    px=pd.DataFrame(prices).sort_index();px.to_csv(data/'original_prices.csv',index_label='date')
    pd.DataFrame(adv).to_csv(data/'adv.csv',index_label='date')
    columns=['id','ticker','ex_dividend_date','pay_date','currency','cash_amount','split_adjusted_cash_amount']
    dividends=pd.DataFrame(div).drop_duplicates('id').reindex(columns=columns)
    dividends.to_csv(data/'original_dividends.csv',index=False)
    (data/'dividend_coverage.json').write_text(json.dumps({'complete':True,'tickers':completed,'records':len(dividends)},indent=2))
    pd.DataFrame(columns=['ticker','date','split_adjusted_cash_price','source_url']).to_csv(data/'settlements.csv',index=False)
    public_receipts=[]
    for target,archive in [('ff5.csv','F-F_Research_Data_5_Factors_2x3_daily_CSV'),('momentum.csv','F-F_Momentum_Factor_daily_CSV')]:
        dest=v.cache/(archive+'.zip')
        public_receipts.append(public('https://mba.tuck.dartmouth.edu/pages/faculty/ken.french/ftp/'+archive+'.zip',dest,a.offline))
        z=zipfile.ZipFile(dest);names=[n for n in z.namelist() if n.lower().endswith('.csv')]
        if len(names)!=1:raise RuntimeError('Unexpected factor archive')
        (data/target).write_bytes(z.read(names[0]))
    import fx,actions
    for url,filename in [(fx.BOC,'boc_fx.json'),(fx.BOC2022,'boc_2022_fx.json')]:
        public_receipts.append(public(url,v.cache/filename,a.offline))
    # Reuse the publicly supplied, tested accounting transforms on NEW raw inputs.
    old=sys.argv
    try:
        fx.DATA=data;fx.HERE=root;sys.argv=['fx.py'];fx.main()
        actions.DATA=data;actions.HERE=HERE.parent;actions.key=lambda:None
        actions.get=lambda url,params=None,token=None:v.get(url,params)
        actions.main()
    finally:sys.argv=old
    manifest={'created_utc':utc(),'construction':'raw vendor/public responses; no parent derived inputs',
        'files':{p.name:{'sha256':sha(p),'bytes':p.stat().st_size} for p in sorted(data.iterdir()) if p.is_file()},
        'protocol_sha256':sha(HERE.parent/'PROTOCOL.md'),
        'corporate_action_journal_sha256':sha(HERE.parent/'corporate_actions.csv'),
        'licensed_data_not_for_redistribution':True,'parent_inputs_read_during_construction':False,
        'raw_vendor_receipts':sorted(v.receipts,key=lambda d:d['url']),'public_receipts':public_receipts,
        'missing_cap_checks':missing}
    (out/'input_manifest.json').write_text(json.dumps(manifest,indent=2))
    # The original package is consulted for the first time here, solely as a comparator.
    rebuilt=pd.read_csv(data/'events.csv',dtype={'cik':str})
    comparison={'generated_utc':utc(),'rebuilt_events':len(rebuilt),
       'source_response_count':len({r['url'] for r in v.receipts}),'not_independent_software_implementation':True,
       'clean_input_reconstruction':True,'no_historical_reselection':True,
       'parent_raw_comparison_available':(HERE.parent/'data/events.csv').exists() and (HERE.parent/'data/prices.csv').exists()}
    if comparison['parent_raw_comparison_available']:
        original=pd.read_csv(HERE.parent/'data/events.csv',dtype={'cik':str})
        keys=['cik','ticker','filing_date'];left=set(map(tuple,original[keys].values));right=set(map(tuple,rebuilt[keys].values))
        oldpx=pd.read_csv(HERE.parent/'data/prices.csv',index_col=0,parse_dates=True)
        newpx=pd.read_csv(data/'prices.csv',index_col=0,parse_dates=True)
        common=sorted(set(oldpx)&set(newpx));dates=oldpx.index.intersection(newpx.index)
        x=oldpx.loc[dates,common];y=newpx.loc[dates,common];mismatch=((x-y).abs()>1e-8)|(x.isna()!=y.isna())
        comparison.update({'original_events':len(original),'events_only_original':sorted(left-right),'events_only_rebuilt':sorted(right-left),
               'price_columns_compared':len(common),'price_dates_compared':len(dates),'quote_cells_differing':int(mismatch.to_numpy().sum()),
               'max_shared_quote_difference':float((x-y).abs().max().max())})
    (HERE/'output/reconstruction_comparison.json').write_text(json.dumps(comparison,indent=2))
    if a.simulate:
        subprocess.run([sys.executable,str(HERE.parent/'run.py'),'--data-dir',str(data),'--out-dir',str(out),
                        '--placebos',str(a.placebos)],check=True)
        before=json.loads((HERE.parent/'output/results.json').read_text());after=json.loads((out/'results.json').read_text())
        error=0.;daily_error=0.
        for config in before['metrics']:
            for window in before['metrics'][config]:
                for name,value in before['metrics'][config][window].items():
                    if isinstance(value,(int,float)) and isinstance(after['metrics'][config][window].get(name),(int,float)):
                        error=max(error,abs(value-after['metrics'][config][window][name]))
            old=pd.read_csv(HERE.parent/'output'/f'{config}_daily.csv',index_col=0)
            new=pd.read_csv(out/f'{config}_daily.csv',index_col=0)
            assert old.index.equals(new.index),'Daily calendar differs; investigate rather than align away differences'
            daily_error=max(daily_error,float((old['return']-new['return']).abs().max()))
        comparison.update({'maximum_metric_difference':error,'maximum_daily_return_difference':daily_error,
             'daily_return_match_1e_10':daily_error<1e-10,'metrics_match_1e_8':error<1e-8,
             'reconstructed_placebos':a.placebos})
        (HERE/'output/reconstruction_comparison.json').write_text(json.dumps(comparison,indent=2))
    print(json.dumps(comparison,indent=2),flush=True)


if __name__=='__main__':main()
