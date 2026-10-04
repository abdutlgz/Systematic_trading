"""Fixed-share, self-financing stock-short/SPY-long accounting.

All quantities use the same split-normalized basis as input closes/dividends.
No vendor access, selection search, or factor fitting occurs in this module.
"""
from dataclasses import dataclass
from typing import Optional

import numpy as np
import pandas as pd


@dataclass
class Config:
    weight: float = .02
    hold: int = 60
    stock_cost: float = .001
    spy_cost: float = .0002
    borrow: float = .01
    debit_spread: float = .015
    controlled: bool = False
    lag: int = 0
    fixed_beta: Optional[float] = None  # accounting fixtures only


def simulate(events, prices, rf, dividends=None, settlements=None, config=None, start='2022-01-03', end='2026-09-30', detailed=True, actions=None):
    c=config or Config()
    prices=prices.sort_index()
    days=prices.index[(prices.index>=pd.Timestamp(start))&(prices.index<=pd.Timestamp(end))&prices.SPY.notna()]
    cols={t:i for i,t in enumerate(prices.columns)}
    spycol=cols['SPY']
    raw=prices.reindex(days).to_numpy(dtype=float)
    marked=prices.ffill().reindex(days).to_numpy(dtype=float)
    rets=prices.pct_change(fill_method=None)
    rates=rf.reindex(prices.index).ffill().reindex(days)
    if rates.isna().any():raise ValueError('RF unavailable at beginning of simulation')
    rates=rates.to_numpy()
    first_valid={t:prices[t].first_valid_index() for t in prices}
    scheduled={}
    for row in events.sort_values(['filing_date','ticker'],kind='stable').itertuples():
        k=days.searchsorted(row.filing_date,side='right')+c.lag
        if k<len(days):scheduled.setdefault(k,[]).append((row.ticker,str(row.filing_date.date())))
    cash=1.; restricted=0.; pending=[]; active=[]; previous_nav=1.
    trades=[]; entries=[]; exceptions=[]; records=[]; serial=0
    action_days={};aliases={}
    if actions is not None:
        for a in actions.sort_values('date',kind='stable').itertuples():
            k=days.searchsorted(pd.Timestamp(a.date))
            if k<len(days):action_days.setdefault(k,[]).append(a)
            if a.type=='rename':aliases[a.ticker]=(pd.Timestamp(a.date),a.stock_ticker)
    def symbol(ticker,k):
        if ticker in aliases and days[k]>=aliases[ticker][0]:return aliases[ticker][1]
        return ticker
    settle={}
    if settlements is not None:
        for row in settlements.itertuples():
            if not row.source_url or not np.isfinite(row.split_adjusted_cash_price):
                raise ValueError('Settlement overrides require amount and source URL')
            d=pd.Timestamp(row.date);k=days.searchsorted(d)
            if k<len(days):settle[(k,row.ticker)]=float(row.split_adjusted_cash_price)
    dividend_by_day={}
    if dividends is not None:
        for row in dividends.itertuples():
            d=pd.Timestamp(row.ex_dividend_date)
            if d not in days or row.ticker not in cols:continue
            amount=getattr(row,'split_adjusted_cash_amount',np.nan)
            if not np.isfinite(amount) or getattr(row,'currency','USD')!='USD':
                exceptions.append({'date':str(d.date()),'ticker':row.ticker,'kind':'unusable_dividend','detail':'split-adjusted USD amount absent'})
                continue
            pay=pd.to_datetime(getattr(row,'pay_date',None),errors='coerce')
            if pd.isna(pay) or pay<d:
                pay=d
                exceptions.append({'date':str(d.date()),'ticker':row.ticker,'kind':'dividend_pay_date_proxy','detail':'ex-date used'})
            dividend_by_day.setdefault(days.get_loc(d),[]).append((row.ticker,float(amount),pay))
    terminated=set()
    day_cost=0.;day_turnover=0.

    def nav(k):
        return cash+restricted+sum(p['qs']*marked[k,p['col']]+p['qh']*marked[k,spycol] for p in active)+sum(v for _,v in pending)

    def close_fraction(p,k,f,reason,stock_price=None):
        nonlocal cash,restricted,day_cost,day_turnover
        sp=raw[k,p['col']] if stock_price is None else stock_price
        hp=raw[k,spycol]
        if not np.isfinite(sp) or not np.isfinite(hp):
            if detailed:exceptions.append({'date':str(days[k].date()),'ticker':p['ticker'],'kind':'blocked_'+reason,'detail':'no executable quote'})
            return False
        sold=f*p['qh'];covered=-f*p['qs'];release=f*p['collateral']
        fee=covered*sp*c.stock_cost+sold*hp*c.spy_cost
        cash+=sold*hp+release-covered*sp-fee
        restricted-=release;day_cost+=fee;day_turnover+=covered*sp+sold*hp
        if detailed:trades.append({'date':days[k],'id':p['id'],'ticker':p['ticker'],'reason':reason,
             'stock_symbol':symbol(p['ticker'],k),
             'stock_quantity':covered,'stock_price':sp,'spy_quantity':-sold,'spy_price':hp,
             'stock_notional':covered*sp,'spy_notional':sold*hp,'fee':fee})
        p['qs']*=1-f;p['qh']*=1-f;p['collateral']*=1-f
        if f>=1-1e-12:active.remove(p)
        return True

    for k,d in enumerate(days):
        day_cost=0.;day_turnover=0.;nav_start=previous_nav
        elapsed=(d-days[k-1]).days if k else 1
        interest=cash*rates[k] if cash>=0 else cash*(rates[k]+c.debit_spread*elapsed/365)
        cash+=interest
        liability_prev=sum(-p['qs']*marked[max(0,k-1),p['col']] for p in active)
        borrow=liability_prev*c.borrow*elapsed/365;cash-=borrow
        div_accrual=0.
        for ticker,amount,pay in dividend_by_day.get(k,[]):
            quantity=sum(p['qh'] for p in active) if ticker=='SPY' else sum(p['qs'] for p in active if p['ticker']==ticker)
            value=quantity*amount
            if value:pending.append((pay,value));div_accrual+=value
        due=sum(value for pay,value in pending if pay<=d)
        cash+=due;pending=[(pay,value) for pay,value in pending if pay>d]
        for a in action_days.get(k,[]):
            if a.type=='rename':continue
            positions=[p for p in active if p['ticker']==a.ticker]
            if a.type=='cash':
                terminated.add(a.ticker)
                for p in positions:
                    qty=-p['qs']
                    if close_fraction(p,k,1.,'verified_cash_merger',float(a.cash_amount)) and a.cvr_max>0:
                        reserve=qty*a.cvr_max
                        cash-=reserve;restricted+=reserve
                        pending.append((pd.Timestamp('2099-12-31'),-reserve))
                        if detailed:exceptions.append({'date':str(d.date()),'ticker':a.ticker,
                            'kind':'cvr_maximum_reserved','detail':f'USD liability reserve={reserve:.10g}; not observed fair value'})
            elif a.type=='stock_cash':
                terminated.add(a.ticker)
                for p in positions:
                    if a.stock_ticker not in cols or not np.isfinite(raw[k,cols.get(a.stock_ticker,spycol)]):
                        if detailed:exceptions.append({'date':str(d.date()),'ticker':a.ticker,'kind':'blocked_stock_conversion','detail':'successor quote absent'})
                        continue
                    oldq=p['qs'];sp=raw[k,cols[a.stock_ticker]]
                    total=a.cash_amount+a.stock_ratio*sp
                    cash+=oldq*a.cash_amount
                    release=p['collateral']*a.cash_amount/total if total>0 else 0.
                    restricted-=release;cash+=release;p['collateral']-=release
                    p['qs']=oldq*a.stock_ratio;p['col']=cols[a.stock_ticker];p['ticker']=a.stock_ticker
                    if detailed:trades.append({'date':d,'id':p['id'],'ticker':a.ticker,
                         'reason':'verified_stock_conversion','stock_symbol':a.stock_ticker,
                         'stock_quantity':0.,'stock_price':sp,'spy_quantity':0.,'spy_price':raw[k,spycol],
                         'stock_notional':0.,'spy_notional':0.,'fee':0.,'cash_consideration_flow':oldq*a.cash_amount,
                         'successor_quantity':p['qs'],'source_url':a.source_url})
            elif a.type=='spinoff':
                for p in positions:
                    if a.stock_ticker not in cols or not np.isfinite(raw[k,cols.get(a.stock_ticker,spycol)]):
                        if detailed:exceptions.append({'date':str(d.date()),'ticker':a.ticker,'kind':'blocked_spinoff_close','detail':'distributed-security quote absent'})
                        continue
                    value=p['qs']*a.stock_ratio*raw[k,cols[a.stock_ticker]]
                    fee=-value*c.stock_cost;cash+=value-fee;day_cost+=fee;day_turnover-=value
                    if detailed:trades.append({'date':d,'id':p['id'],'ticker':a.stock_ticker,
                        'reason':'spinoff_buyback','stock_symbol':a.stock_ticker,
                        'stock_quantity':-p['qs']*a.stock_ratio,'stock_price':raw[k,cols[a.stock_ticker]],
                        'spy_quantity':0.,'spy_price':raw[k,spycol],'stock_notional':-value,'spy_notional':0.,'fee':fee,
                        'source_url':a.source_url})
        for p in list(active):
            if not np.isfinite(raw[k,p['col']]) and detailed:
                exceptions.append({'date':str(d.date()),'ticker':p['ticker'],'kind':'carried_mark','detail':'last observed mark; current fill unavailable'})
            if (k,p['ticker']) in settle:
                cash_price=settle[(k,p['ticker'])]
                close_fraction(p,k,1.,'verified_settlement',cash_price);terminated.add(p['ticker'])
            elif k>=p['exit']:
                close_fraction(p,k,1.,'scheduled_exit')

        for ticker,filing in scheduled.get(k,[]):
            reason=None
            current_nav=nav(k)
            if current_nav<=0:raise RuntimeError('NAV is nonpositive; strategy insolvent')
            if ticker not in cols or not np.isfinite(raw[k,cols.get(ticker,spycol)]) or raw[k,cols.get(ticker,spycol)]<=0:reason='missing_entry_quote'
            elif ticker in terminated:reason='settled_security'
            elif c.controlled and any(symbol(p['ticker'],k)==symbol(ticker,k) for p in active):reason='issuer_overlap'
            elif not c.controlled and len(active)>=50:reason='event_slot_cap'
            elif c.controlled and sum(-p['qs']*marked[k,p['col']] for p in active)>=current_nav-1e-12:reason='short_cap'
            if reason:
                if detailed:entries.append({'date':d,'ticker':ticker,'filing_date':filing,'accepted':False,'reason':reason})
                continue
            j=prices.index.get_loc(d)
            h=rets[ticker].iloc[max(0,j-260):max(0,j-10)].to_numpy()
            m=rets.SPY.iloc[max(0,j-260):max(0,j-10)].to_numpy()
            ok=np.isfinite(h)&np.isfinite(m)
            beta=c.fixed_beta
            if beta is None:beta=float(np.clip(np.cov(h[ok],m[ok])[0,1]/m[ok].var(),.5,1.5)) if ok.sum()>=120 and m[ok].var()>0 else 1.
            unit_cost=c.stock_cost+beta*c.spy_cost
            notional=c.weight*current_nav
            if c.controlled:
                short=sum(-p['qs']*marked[k,p['col']] for p in active)
                notional=min(c.weight*current_nav/(1+c.weight*unit_cost),max(0.,(current_nav-short)/(1+unit_cost)))
            if notional<=1e-12:
                if detailed:entries.append({'date':d,'ticker':ticker,'filing_date':filing,'accepted':False,'reason':'short_cap'})
                continue
            sp=raw[k,cols[ticker]];hp=raw[k,spycol];fee=notional*unit_cost
            serial+=1
            p={'id':serial,'ticker':ticker,'col':cols[ticker],'qs':-notional/sp,
               'qh':notional*beta/hp,'collateral':notional,'exit':k+c.hold,'entry':k}
            active.append(p);restricted+=notional;cash-=notional*beta+fee
            day_cost+=fee;day_turnover+=notional*(1+beta)
            if detailed:
                entries.append({'date':d,'ticker':ticker,'filing_date':filing,'accepted':True,'reason':'entry','beta':beta,'entry_notional':notional,'id':serial})
                trades.append({'date':d,'id':serial,'ticker':ticker,'reason':'entry','stock_quantity':p['qs'],
                     'stock_symbol':symbol(ticker,k),
                     'stock_price':sp,'spy_quantity':p['qh'],'spy_price':hp,'stock_notional':notional,
                     'spy_notional':notional*beta,'fee':fee})

        if c.controlled:
            for _ in range(12):
                n=nav(k);changed=False
                if n<=0:raise RuntimeError('NAV is nonpositive; strategy insolvent before risk maintenance')
                by_ticker={}
                for p in active:by_ticker.setdefault(symbol(p['ticker'],k),[]).append(p)
                for ticker,positions in by_ticker.items():
                    exposure=sum(-p['qs']*marked[k,p['col']] for p in positions)
                    if exposure>c.weight*n+1e-11:
                        f=min(1.,max(0.,1-c.weight*n/exposure))
                        for p in list(positions):changed=close_fraction(p,k,f,'issuer_trim') or changed
                n=nav(k);liability=sum(-p['qs']*marked[k,p['col']] for p in active)
                if liability>n+1e-11:
                    f=min(1.,max(0.,1-n/liability))
                    for p in list(active):changed=close_fraction(p,k,f,'gross_trim') or changed
                if not changed:break
        n=nav(k)
        if not np.isfinite(n) or n<=0:raise RuntimeError('Nonpositive/invalid NAV')
        liability=sum(-p['qs']*marked[k,p['col']] for p in active)
        hedge=sum(p['qh']*marked[k,spycol] for p in active)
        per_issuer={}
        stale=0.
        for p in active:
            value=-p['qs']*marked[k,p['col']]
            sym=symbol(p['ticker'],k)
            per_issuer[sym]=per_issuer.get(sym,0.)+value
            if not np.isfinite(raw[k,p['col']]):stale+=value
        max_issuer=max(per_issuer.values(),default=0.)/n
        if c.controlled and (liability/n>1+1e-8 or max_issuer>c.weight+1e-8):
            if detailed:exceptions.append({'date':str(d.date()),'ticker':'PORTFOLIO','kind':'unexecutable_limit_breach','detail':f'gross={liability/n:.6f},issuer={max_issuer:.6f}'})
        records.append({'date':d,'nav':n,'return':n/nav_start-1,'rf':rates[k],
           'excess_return':n/nav_start-1-rates[k],'free_cash':cash,'restricted_cash':restricted,
           'dividend_receivable':sum(v for _,v in pending),'dividend_accrual':div_accrual,'dividend_cash':due,
           'funding_cashflow':interest,'borrow_fee':borrow,'trading_fee':day_cost,
           'turnover':day_turnover/nav_start,'stock_short':liability,'spy_long':hedge,
           'gross_short':liability/n,'gross_total':(liability+hedge)/n,
           'max_issuer_weight':max_issuer,'n_events':len(active),'n_issuers':len(per_issuer),
           'stale_short_weight':stale/n})
        previous_nav=n
    daily=pd.DataFrame(records).set_index('date')
    for p in active:
        if detailed and p['exit']<len(days):exceptions.append({'date':str(days[-1].date()),'ticker':p['ticker'],
              'kind':'unresolved_overdue_exit','detail':f"entry={days[p['entry']].date()}, due_session={p['exit']}"})
    return daily,pd.DataFrame(trades),pd.DataFrame(entries),pd.DataFrame(exceptions)
