"""Offline, reproducible pilots from saved real provider responses."""
import csv, datetime, io, json, zipfile
from pathlib import Path
import numpy as np
import pandas as pd
from collect import CIKS
from probe import ROOT

ITEMS=['2.02','5.02','1.01','2.01','7.01','8.01']

def read(name):
    return json.loads((ROOT/'raw'/f'{name}.raw').read_text())

def save(name,value):
    (ROOT/'results'/name).write_text(json.dumps(value,indent=2,allow_nan=False))

def prices(symbol):
    source=read('yahoo_'+symbol.lower())
    assert source['chart']['error'] is None
    raw=source['chart']['result'][0]
    assert raw['meta']['symbol']==symbol
    df=pd.DataFrame(raw['indicators']['quote'][0])
    df['date']=pd.to_datetime(raw['timestamp'],unit='s',utc=True).tz_convert('America/New_York').strftime('%Y-%m-%d')
    assert not df.date.duplicated().any()
    df=df[df.date<='2026-09-30'].copy()
    assert (df.volume.dropna()>0).all()
    assert (df.high>=df.low).all()
    df['symbol']=symbol
    return df

def ridge(train,test,cols,target):
    a=train[cols].to_numpy(dtype=float); b=test[cols].to_numpy(dtype=float)
    mu=a.mean(axis=0); sd=a.std(axis=0); sd[sd<1e-12]=1
    a=np.column_stack([np.ones(len(a)),(a-mu)/sd])
    b=np.column_stack([np.ones(len(b)),(b-mu)/sd])
    penalty=10*np.eye(a.shape[1]); penalty[0,0]=0
    coef=np.linalg.solve(a.T@a+penalty,a.T@train[target].to_numpy())
    return b@coef

def stock_pilot():
    frames=[]; audits=[]
    spy=prices('SPY').set_index('date')
    spyret=spy.close/spy.open-1
    for symbol in CIKS:
        df=prices(symbol)
        sec=read('sec_'+symbol.lower())['filings']['recent']
        filings=pd.DataFrame(sec)
        for p in sorted((ROOT/'raw').glob('sec_'+symbol.lower()+'_*.raw')):
            filings=pd.concat([filings,pd.DataFrame(json.loads(p.read_text()))],ignore_index=True)
        filings=filings.drop_duplicates('accessionNumber')
        earliest=filings.filingDate.min()
        assert earliest<'2024-10-03', (symbol,'incomplete SEC history',earliest)
        filings['accepted']=pd.to_datetime(filings.acceptanceDateTime,utc=True,errors='raise')
        decision=pd.to_datetime(df.date+' 09:25').dt.tz_localize('America/New_York').dt.tz_convert('UTC')
        deadlines=(decision-pd.Timedelta(minutes=30)).astype('int64').to_numpy()
        # The first decision AFTER acceptance + 30m. Intraday filings are assigned to the next session.
        assignments=np.searchsorted(deadlines,filings.accepted.astype('int64').to_numpy(),side='left')
        filings['row']=assignments
        filings=filings[(filings.row>0)&(filings.row<len(df))].copy()
        df['filing_count']=0.; df['k8_count']=0.
        for item in ITEMS: df['item_'+item]=0.
        for row,g in filings.groupby('row'):
            df.loc[row,'filing_count']=len(g)
            k8=g[g.form=='8-K']
            df.loc[row,'k8_count']=len(k8)
            for item in ITEMS:
                df.loc[row,'item_'+item]=int(any(item in str(x).split(',') for x in k8['items']))
            assert (g.accepted<=decision.iloc[row]-pd.Timedelta(minutes=30)).all()
        df['reference_volume']=df.volume.shift(1).rolling(20).median()
        df['target']=np.log(df.volume/df.reference_volume)
        df['lag_rvol']=df.target.shift(1)
        ret=df.close.pct_change(fill_method=None)
        df['lag_abs_return']=ret.abs().shift(1)
        df['volatility']=ret.shift(1).rolling(20).std()
        df['lag_five_rvol']=df.target.shift(1).rolling(5).mean()
        df['price_target']=df.close/df.open-1-df.date.map(spyret)
        for day in range(5): df['weekday_'+str(day)]=(pd.to_datetime(df.date).dt.dayofweek==day).astype(int)
        for s in CIKS: df['ticker_'+s]=int(symbol==s)
        audits.append({'symbol':symbol,'price_rows':len(df),'price_start':df.date.min(),'price_end':df.date.max(),
                       'sec_earliest_date':earliest,'filings_assigned':len(filings),'8k_assigned':int((filings.form=='8-K').sum())})
        frames.append(df)
    allrows=pd.concat(frames,ignore_index=True).dropna().sort_values(['date','symbol']).reset_index(drop=True)
    train=allrows[allrows.date<'2026-01-01'].copy()
    test=allrows[allrows.date>='2026-01-01'].copy()
    baseline=['lag_rvol','lag_abs_return','volatility','lag_five_rvol']+[f'weekday_{i}' for i in range(5)]+['ticker_'+s for s in CIKS]
    attention=baseline+['filing_count','k8_count']
    categories=attention+['item_'+i for i in ITEMS]
    metrics={}; price_metrics={}
    for name,cols in [('market',baseline),('attention',attention),('earnings_only',attention+['item_2.02']),('categories',categories)]:
        test['pred_'+name]=ridge(train,test,cols,'target')
        test['err_'+name]=abs(test.target-test['pred_'+name])
        metrics[name]={'mae_log_relative_volume':float(test['err_'+name].mean()),
                       'rmse_log_relative_volume':float(np.sqrt(np.mean((test.target-test['pred_'+name])**2)))}
        pred=ridge(train,test,cols,'price_target')
        price_metrics[name]={'mae_return':float(np.mean(abs(test.price_target-pred))),
                             'direction_accuracy':float(np.mean((pred>0)==(test.price_target>0)))}
    dates=sorted(test.date.unique()); mid=dates[len(dates)//2]
    def comparison(g):
        a=float(g.err_attention.mean()); c=float(g.err_categories.mean())
        return {'n':len(g),'attention_mae':a,'category_mae':c,'improvement_pct':100*(a-c)/a}
    daily=test.groupby('date')[['err_attention','err_categories']].mean()
    rng=np.random.default_rng(20261002)
    samples=rng.integers(0,len(daily),(2000,len(daily)))
    errors=daily.to_numpy()[samples].mean(axis=1)
    gains=100*(errors[:,0]-errors[:,1])/errors[:,0]
    summary={'status':'completed_daily_structured_filing_pilot_not_LLM_news',
             'train_rows':len(train),'test_rows':len(test),'train_dates':[train.date.min(),train.date.max()],
             'test_dates':[test.date.min(),test.date.max()],'test_days':len(dates),'metrics':metrics,
             'category_vs_attention':comparison(test),'bootstrap_day_95pct_improvement_interval':np.quantile(gains,[.025,.975]).tolist(),
             'time_halves':{'first':comparison(test[test.date<mid]),'second':comparison(test[test.date>=mid])},
             'by_ticker':{s:comparison(g) for s,g in test.groupby('symbol')},
             'event_days':comparison(test[test.k8_count>0]),'no_event_days':comparison(test[test.k8_count==0]),
             'exploratory_price_metrics':price_metrics,'price_zero_return_mae':float(abs(test.price_target).mean()),
             'audit':audits,'seed':20261002}
    summary['passes_initial_gate']=bool(summary['category_vs_attention']['improvement_pct']>=5 and all(v['improvement_pct']>0 for v in summary['time_halves'].values()))
    summary['exploratory_earnings_ablation']={
        'note':'Added after primary results to check whether earnings alone explain category gains; not a new holdout.',
        'all_categories_vs_earnings_only_improvement_pct':100*(test.err_earnings_only.mean()-test.err_categories.mean())/test.err_earnings_only.mean()}
    test['observed_relative_volume']=np.exp(test.target)
    summary['descriptive_test_volume']={name:{'n':len(g),'median_relative_volume':float(g.observed_relative_volume.median())} for name,g in [
        ('earnings_8k',test[test['item_2.02']>0]),('other_8k',test[(test.k8_count>0)&(test['item_2.02']==0)]),('no_8k',test[test.k8_count==0]) ]}
    allrows.to_json(ROOT/'results'/'stock_features.jsonl',orient='records',lines=True)
    test.to_json(ROOT/'results'/'stock_predictions.jsonl',orient='records',lines=True)
    save('stock_summary.json',summary)
    return summary

def weather_pilot():
    markets=json.loads((ROOT/'results'/'weather_markets.json').read_text())
    days={}; rules={}
    for m in markets:
        date=datetime.datetime.strptime(m['event_ticker'].split('-')[-1],'%y%b%d').strftime('%Y-%m-%d')
        if not '2026-07-01'<=date<='2026-09-30' or not m.get('expiration_value'): continue
        value=float(m['expiration_value'])
        if date in days: assert days[date]==value
        days[date]=value
        rules[date]=m['rules_primary']
    h=pd.DataFrame(read('weather_2026')['hourly'])
    h['date']=h.time.str[:10]
    # Fixed-lead skill diagnostic only: these 24 hourly forecasts do NOT form one issuance.
    g=h.groupby('date').agg({'temperature_2m_previous_day1':['max','count'],'temperature_2m_previous_day2':['max','count']})
    g.columns=['forecast_day1','count_day1','forecast_day2','count_day2']
    g['observed_settlement']=pd.Series(days)
    g=g[(g.count_day1==24)&(g.count_day2==24)].copy()
    assert len(g)>60
    g['persistence']=g.observed_settlement.shift(1)
    g['trailing7']=g.observed_settlement.shift(1).rolling(7).mean()
    g=g.dropna()
    split=int(len(g)*2/3); train=g.iloc[:split]; test=g.iloc[split:].copy()
    for days in [1,2]:
        bias=float((train.observed_settlement-train[f'forecast_day{days}']).mean())
        test[f'corrected_day{days}']=test[f'forecast_day{days}']+bias
    metrics={}
    for col in ['persistence','trailing7','forecast_day1','forecast_day2','corrected_day1','corrected_day2']:
        error=test[col]-test.observed_settlement
        metrics[col]={'mae_f':float(error.abs().mean()),'rmse_f':float(np.sqrt(np.mean(error**2)))}
    summary={'status':'completed_forecast_skill_only_not_trading_backtest','matched_days':len(g),'train_days':len(train),'test_days':len(test),
             'train_dates':[str(train.index.min()),str(train.index.max())],'test_dates':[str(test.index.min()),str(test.index.max())],
             'metrics':metrics,'outcomes_source':'Kalshi expiration_value, not independent weather station validation',
             'rules_first':rules[min(rules)],'rules_last':rules[max(rules)],
             'limitation':'Hourly fixed-lead composites; not a single model issue. No market edge or executable returns inferred.'}
    save('weather_summary.json',summary)
    test.reset_index().to_json(ROOT/'results'/'weather_predictions.jsonl',orient='records',lines=True)
    return summary

def disclosures():
    z=zipfile.ZipFile(ROOT/'raw'/'house_index.raw')
    records=list(csv.DictReader(io.StringIO(z.read('2025FD.txt').decode('utf-8-sig')),delimiter='\t'))
    ptr=[r for r in records if r['FilingType']=='P']
    # The source's Year column need not equal the actual filing calendar year.
    ptr2025=[r for r in ptr if r['FilingDate'].endswith('/2025')]
    result={'status':'primary_source_index_verified_transactions_not_yet_parsed','index_rows':len(records),
            'periodic_transaction_reports':len(ptr),'ptr_filed_in_2025':len(ptr2025),
            'unique_filer_names_2025':len(set((r['First'],r['Last']) for r in ptr2025)),
            'sample_reports':[dict(r,document_url=f'https://disclosures-clerk.house.gov/public_disc/ptr-pdfs/2025/{r["DocID"]}.pdf') for r in ptr2025[:5]],
            'limitation':'Filing date is not verified public posting time. Index contains no trades or tickers; no return backtest performed.'}
    save('disclosure_summary.json',result)
    return result

if __name__=='__main__':
    for name,fn in [('stocks',stock_pilot),('weather',weather_pilot),('disclosures',disclosures)]:
        result=fn(); print(name,json.dumps(result,indent=2))
