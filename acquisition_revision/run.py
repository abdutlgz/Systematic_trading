"""One offline reproduction command; corrections, not a new strategy search."""
import argparse
from dataclasses import asdict
from datetime import datetime,timezone
import hashlib
import json
import os
from pathlib import Path

HERE=Path(__file__).resolve().parent
os.environ.setdefault('MPLCONFIGDIR',str(HERE/'.mplconfig'))
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from scipy.stats import norm

from ledger import Config,simulate

DATA=HERE/'data';OUT=HERE/'output'
WINDOWS={'IS':('2022-01-01','2025-09-30'),'historical_test':('2025-10-01','2026-09-30')}


def french(path):
    lines=path.read_text().splitlines()
    header=next(s for s in lines if s.startswith(','))
    rows=[s.split(',') for s in lines if s[:8].isdigit() and len(s.split(',')[0])==8]
    d=pd.DataFrame(rows,columns=['date']+[s.strip() for s in header.split(',')[1:]])
    d['date']=pd.to_datetime(d.date,format='%Y%m%d')
    return d.set_index('date').astype(float)/100


def metrics(d):
    r=d['return'];ex=d.excess_return
    n=len(d)
    if not n:return {}
    vol=r.std()*np.sqrt(252)
    sr=ex.mean()/ex.std()*np.sqrt(252) if ex.std()>0 else None
    equity=(1+r).cumprod();peak=equity.cummax().clip(lower=1.)
    months=(1+r).groupby(r.index.to_period('M')).prod()-1
    return {'sessions':n,'arithmetic_return':float(r.mean()*252),'cagr':float(equity.iloc[-1]**(252/n)-1),
       'vol':float(vol),'excess_sharpe':None if sr is None else float(sr),
       'total_return_sharpe':float(r.mean()/r.std()*np.sqrt(252)) if r.std()>0 else None,
       'naive_excess_t':None if sr is None else float(sr*np.sqrt(n/252)),
       'max_drawdown':float((equity/peak-1).min()),'worst_month':float(months.min()),
       'turnover_per_year':float(d.turnover.sum()/(n/252)),
       'trading_fee_per_year':float((d.trading_fee/d.nav.shift(1).fillna(1)).sum()/(n/252)),
       'borrow_per_year':float((d.borrow_fee/d.nav.shift(1).fillna(1)).sum()/(n/252)),
       'max_gross_short':float(d.gross_short.max()),'max_gross_total':float(d.gross_total.max()),
       'max_issuer_weight':float(d.max_issuer_weight.max()),'mean_unique_issuers':float(d.n_issuers.mean()),
       'max_stale_short_weight':float(d.stale_short_weight.max()),'stale_exposure_days':int((d.stale_short_weight>0).sum())}


def factors(excess,ff):
    d=pd.concat([excess.rename('y'),ff],axis=1,join='inner').dropna()
    names=['alpha','Mkt-RF','SMB','HML','RMW','CMA','Mom']
    X=np.column_stack([np.ones(len(d)),d[names[1:]].to_numpy()]);y=d.y.to_numpy()
    coef=np.linalg.lstsq(X,y,rcond=None)[0];e=y-X@coef
    inv=np.linalg.inv(X.T@X);xe=X*e[:,None];S=xe.T@xe
    for lag in range(1,6):
        G=xe[lag:].T@xe[:-lag];S+=(1-lag/6)*(G+G.T)
    se=np.sqrt(np.diag(inv@S@inv));t=coef/se
    return {'sessions':len(d),'end':str(d.index[-1].date()),'r2':float(1-e.var()/y.var()),
            'coefficients':{name:{'coefficient':float(b),'nw_t':float(z)} for name,b,z in zip(names,coef,t)},
            'alpha_annual':float(coef[0]*252),'alpha_p_two_sided_normal':float(2*norm.sf(abs(t[0]))),
            'rf_already_subtracted':True}


def placebo(events,prices,rf,dividends,settlements,n,actions):
    rng=np.random.default_rng(20261003)
    eligible=events[(events.filing_date>='2022-01-01')&(events.filing_date<='2025-07-01')]
    filings=events.groupby('ticker').filing_date.apply(list).to_dict()
    days=prices.index[(prices.index>='2022-01-03')&(prices.index<='2025-07-01')&prices.SPY.notna()]
    pools={}
    for ticker in eligible.ticker.unique():
        if ticker not in prices:continue
        keep=np.array([all(abs((d-f).days)>90 for f in filings[ticker]) for d in days])
        # Ensure that the actual following-session entry quote exists.
        valid_entry=prices[ticker].shift(-1).reindex(days).notna().to_numpy()
        pools[ticker]=days[keep&valid_entry]
    empty=[t for t in eligible.ticker if t not in pools or not len(pools[t])]
    # Never relax the exclusion rule or silently drop events only from controls.
    # Compare a matched observed subset and placebos on the same feasible issuers.
    excluded=eligible[eligible.ticker.isin(empty)]
    eligible=eligible[~eligible.ticker.isin(empty)].copy()
    matched_daily,*_=simulate(eligible,prices,rf,dividends,settlements,Config(controlled=True),end='2025-09-30',actions=actions)
    matched_daily.to_csv(OUT/'placebo_matched_observed_daily.csv',index_label='date')
    results=[]
    for i in range(n):
        dates=[pools[t][rng.integers(len(pools[t]))] for t in eligible.ticker]
        ev=eligible.copy();ev['filing_date']=dates
        d,*_=simulate(ev,prices,rf,dividends,settlements,Config(controlled=True),end='2025-09-30',detailed=False,actions=actions)
        results.append({'replicate':i,'events':len(ev),'excess_sharpe':metrics(d)['excess_sharpe']})
        if (i+1)%10==0:print(f'Placebos {i+1}/{n}',flush=True)
    return pd.DataFrame(results),{'original_eligible_events':len(eligible)+len(excluded),
          'excluded_no_control_dates':len(excluded),'excluded_tickers':sorted(set(excluded.ticker)),
          'matched_events':len(eligible),'observed_is_excess_sharpe':metrics(matched_daily)['excess_sharpe'],
          'deviation':'Infeasible issuers removed from BOTH observed and placebo samples, without relaxing exclusion window.'}


def capacity(daily,trades,prices):
    dv=pd.read_csv(DATA/'adv.csv',index_col=0,parse_dates=True)
    adv=dv.reindex(prices.index).rolling(20,min_periods=15).mean().shift(1)
    sigma=prices.ffill().pct_change(fill_method=None).rolling(60).std().shift(1)
    entries=trades[(trades.reason=='entry')&(trades.date<'2025-10-01')]
    rows=[]
    for aum in (1e7,5e7,1e8,1.5e8):
        q=[];impact=[];missing=0
        for t in entries.itertuples():
            if t.ticker not in adv or not np.isfinite(adv.at[t.date,t.ticker]) or adv.at[t.date,t.ticker]<=0:
                missing+=1;continue
            dollars=t.stock_notional/daily.at[t.date,'nav']*aum
            part=dollars/adv.at[t.date,t.ticker];q.append(part)
            s=sigma.at[t.date,t.ticker]
            if np.isfinite(s):impact.append(2*t.stock_notional/daily.at[t.date,'nav']*s*np.sqrt(part))
        years=len(daily.loc[WINDOWS['IS'][0]:WINDOWS['IS'][1]])/252
        rows.append({'aum':aum,'entries_with_adv':len(q),'missing_adv':missing,
           'median_participation':float(np.median(q)),'p95_participation':float(np.percentile(q,95)),
           'max_participation':float(np.max(q)),'share_over_5pct_adv':float(np.mean(np.array(q)>.05)),
           'share_requiring_over_3_days_at_5pct_adv':float(np.mean(np.array(q)>.15)),
           'illustrative_two_sided_entry_based_impact_per_year':float(sum(impact)/years)})
    return rows


def main():
    global DATA,OUT
    ap=argparse.ArgumentParser();ap.add_argument('--placebos',type=int,default=100)
    ap.add_argument('--data-dir',type=Path,default=DATA);ap.add_argument('--out-dir',type=Path,default=OUT)
    args=ap.parse_args();DATA=args.data_dir.resolve();OUT=args.out_dir.resolve();OUT.mkdir(parents=True,exist_ok=True)
    manifest=json.loads((OUT/'input_manifest.json').read_text())
    for filename,field in [('PROTOCOL.md','protocol_sha256'),('corporate_actions.csv','corporate_action_journal_sha256')]:
        expected=manifest.get(field)
        if expected and hashlib.sha256((HERE/filename).read_bytes()).hexdigest()!=expected:
            raise RuntimeError(f'Journal/protocol hash mismatch: {filename}')
    for filename,meta in manifest['files'].items():
        if hashlib.sha256((DATA/filename).read_bytes()).hexdigest()!=meta['sha256']:
            raise RuntimeError(f'Input hash mismatch: {filename}; rerun prepare.py after deliberate changes')
    coverage=json.loads((DATA/'dividend_coverage.json').read_text())
    if not coverage['complete']:raise RuntimeError('Dividend coverage incomplete')
    prices=pd.read_csv(DATA/'prices.csv',index_col=0,parse_dates=True).sort_index()
    events=pd.read_csv(DATA/'events.csv',parse_dates=['filing_date'])
    dividends=pd.read_csv(DATA/'dividends.csv',parse_dates=['ex_dividend_date','pay_date'])
    settlements=pd.read_csv(DATA/'settlements.csv',parse_dates=['date'])
    actions=pd.read_csv(HERE/'corporate_actions.csv',parse_dates=['date'])
    ff=french(DATA/'ff5.csv').join(french(DATA/'momentum.csv').rename(columns=lambda s:'Mom'))
    rf=ff.RF;last_rf=rf.index[-1]
    configs={'accounting_only':Config(),'issuer_controlled':Config(controlled=True),
             'stress_2x_fees_3pct_borrow':Config(controlled=True,stock_cost=.002,spy_cost=.0004,borrow=.03),
             'delay_5_sessions':Config(controlled=True,lag=5)}
    result={'generated_utc':datetime.now(timezone.utc).isoformat(),'rf_last_observed':str(last_rf.date()),
       'test_previously_examined':True,'no_parameter_selection_in_revision':True,'dividend_coverage':coverage['records'],
       'metrics':{},'configuration':{},'factor_attribution':{},'exceptions':{}}
    result['dividend_adjustments']=json.loads((DATA/'dividend_adjustments.json').read_text())
    main_daily=None;main_trades=None
    for name,c in configs.items():
        print('Running',name,flush=True)
        daily,trades,entries,exceptions=simulate(events,prices,rf,dividends,settlements,c,actions=actions)
        daily.to_csv(OUT/f'{name}_daily.csv',index_label='date')
        trades.to_csv(OUT/f'{name}_trades.csv',index=False)
        entries.to_csv(OUT/f'{name}_entries.csv',index=False)
        exceptions.to_csv(OUT/f'{name}_exceptions.csv',index=False)
        result['configuration'][name]=asdict(c)
        result['metrics'][name]={w:metrics(daily.loc[a:b]) for w,(a,b) in WINDOWS.items()}
        result['metrics'][name]['test_observed_rf_only']=metrics(daily.loc[WINDOWS['historical_test'][0]:last_rf])
        result['exceptions'][name]=exceptions.kind.value_counts().to_dict() if len(exceptions) else {}
        result['factor_attribution'][name]={w:factors(daily.excess_return.loc[a:b],ff) for w,(a,b) in WINDOWS.items()}
        for w,(a,b) in WINDOWS.items():
            e=entries[(entries.date>=a)&(entries.date<=b)]
            result['metrics'][name][w]['accepted_entries']=int(e.accepted.sum())
            result['metrics'][name][w]['entry_attempts']=len(e)
            result['metrics'][name][w]['skip_reasons']=e.loc[~e.accepted,'reason'].value_counts().to_dict()
        if name=='issuer_controlled':main_daily=daily;main_trades=trades
    result['capacity_illustrative']=capacity(main_daily,main_trades,prices)
    if args.placebos:
        p,matched=placebo(events,prices,rf,dividends,settlements,args.placebos,actions)
        p.to_csv(OUT/'placebo_results.csv',index=False)
        sr=matched['observed_is_excess_sharpe'];nbeat=int((p.excess_sharpe>=sr).sum())
        result['placebo']={'seed':20261003,'replicates':len(p),'observed_is_excess_sharpe':sr,
          'mean':float(p.excess_sharpe.mean()),'p95':float(p.excess_sharpe.quantile(.95)),
          'number_ge_observed':nbeat,'finite_sample_tail_fraction':float((nbeat+1)/(len(p)+1)),
          'not_family_wise_or_causal':True,'matched_sample':matched}
    identity=main_daily.free_cash+main_daily.restricted_cash+main_daily.dividend_receivable-main_daily.stock_short+main_daily.spy_long
    result['checks']={'max_nav_identity_error':float((identity-main_daily.nav).abs().max()),
       'rf_proxy_sessions':int((main_daily.index>last_rf).sum()),
       'max_close_gross_short':float(main_daily.gross_short.max()),
       'max_close_issuer_weight':float(main_daily.max_issuer_weight.max())}
    unresolved=result['exceptions']['issuer_controlled'].get('unresolved_overdue_exit',0)
    result['investable_validation_passed']=False
    result['unresolved_reasons']=['historical locate/recall and maintenance-margin data absent',
        'historical test window previously examined',f'{unresolved} overdue exits unresolved',
        'post-August RF uses disclosed proxy','issuer roles not human-verified',
        'BLD lender election unknown; cash-election proration estimate used',
        'CVRs reserved at contractual maximum, not observed fair value',
        'same-close issuer/gross maintenance assumes executable quotes and idealized close fills']
    (OUT/'results.json').write_text(json.dumps(result,indent=2,allow_nan=False))
    fig,(ax,dd)=plt.subplots(2,1,figsize=(9,5),sharex=True,gridspec_kw={'height_ratios':[2,1]})
    for name in ('accounting_only','issuer_controlled'):
        d=pd.read_csv(OUT/f'{name}_daily.csv',index_col=0,parse_dates=True)
        ax.plot(d.index,d.nav,label=name.replace('_',' '),lw=1.5)
        dd.plot(d.index,(d.nav/d.nav.cummax().clip(lower=1)-1)*100,lw=1)
    for a in (ax,dd):a.axvspan(pd.Timestamp('2025-10-01'),main_daily.index[-1],alpha=.12,color='gray');a.grid(alpha=.2)
    ax.set_ylabel('NAV, starting at $1');ax.legend(fontsize=10);dd.set_ylabel('Drawdown (%)')
    fig.tight_layout();fig.savefig(OUT/'equity.png',dpi=180);plt.close(fig)
    print(json.dumps({name:{w:round(v['excess_sharpe'],3) for w,v in ms.items()}
                           for name,ms in result['metrics'].items()},indent=2),flush=True)


if __name__=='__main__':main()
