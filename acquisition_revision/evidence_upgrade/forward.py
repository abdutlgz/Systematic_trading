"""Local freeze + tamper-evident prospective observations and pre-close plans.

No broker orders, scheduling, historical backdating or fabricated forward P&L.
Frozen journals are append-only through this interface; an external saved freeze
is necessary to make chain tampering independently detectable.
"""
import argparse
from datetime import datetime,timezone
import hashlib
import json
import math
from pathlib import Path

import numpy as np
import pandas as pd

from vendor import HERE,sha,utc

FROZEN_FILES=['FORWARD_PROTOCOL.md','nyse_sessions.csv','forward.py','review_decisions.py','vendor.py',
              'make_calendar.py','audit_labels.py','tests/test_evidence.py']


def stamp(value):
    t=pd.Timestamp(value)
    if t.tzinfo is None:raise ValueError('Timezone-aware timestamp required')
    return t.tz_convert('UTC')


def canonical(obj):return json.dumps(obj,sort_keys=True,separators=(',',':'),allow_nan=False)
def digest(obj):return hashlib.sha256(canonical(obj).encode()).hexdigest()


def verify_freeze(root=HERE):
    freeze=json.loads((root/'forward_freeze.json').read_text())
    for filename,expected in freeze['files_sha256'].items():
        if sha(root/filename)!=expected:raise RuntimeError('Frozen file changed: '+filename)
    return freeze


def read_journal(path,freeze):
    previous=digest(freeze);last=stamp(freeze['frozen_utc']);records=[]
    if not path.exists():return records
    for line in path.read_text().splitlines():
        record=json.loads(line);stored=record.pop('record_sha256')
        if digest(record)!=stored or record['previous_sha256']!=previous:raise RuntimeError('Journal chain mismatch')
        now=stamp(record['recorded_utc'])
        if now<last:raise RuntimeError('Journal timestamp went backward')
        if now>stamp(utc())+pd.Timedelta(seconds=5):raise RuntimeError('Future journal timestamp')
        if record['sequence']!=len(records)+1:raise RuntimeError('Journal sequence mismatch')
        record['record_sha256']=stored;records.append(record);previous=stored;last=now
    return records


def append(path,freeze,kind,payload,now):
    stamp(now);records=read_journal(path,freeze)
    last=records[-1]['recorded_utc'] if records else freeze['frozen_utc']
    if stamp(now)<stamp(last):raise RuntimeError('Cannot backdate a journal record')
    r={'sequence':len(records)+1,'recorded_utc':now,'previous_sha256':records[-1]['record_sha256'] if records else digest(freeze),
       'kind':kind,'payload':payload}
    r['record_sha256']=digest(r)
    path.parent.mkdir(parents=True,exist_ok=True)
    with path.open('a') as f:f.write(canonical(r)+'\n')
    return r


def entry_beta(history,decision):
    # Only completed prior sessions; [-260:-10] is relative to the entry session.
    h=pd.DataFrame(history)
    if h.empty:return 1.
    dates=pd.to_datetime(h['date']).dt.date
    if (dates>=stamp(decision).tz_convert('America/New_York').date()).any():raise ValueError('Future or same-day beta history')
    if dates.duplicated().any() or not dates.is_monotonic_increasing:raise ValueError('Beta history must be unique and sorted')
    sample=h.iloc[-260:-10]
    x=pd.to_numeric(sample.stock_return,errors='coerce').to_numpy()
    y=pd.to_numeric(sample.spy_return,errors='coerce').to_numpy();ok=np.isfinite(x)&np.isfinite(y)
    return float(np.clip(np.cov(x[ok],y[ok])[0,1]/y[ok].var(),.5,1.5)) if ok.sum()>=120 and y[ok].var()>0 else 1.


def plan(event,market,state,freeze,sessions,now):
    n=stamp(now);local=n.tz_convert('America/New_York');date=str(local.date())
    def no(reason):return {'accepted':False,'reason':reason,'accession_number':event.get('accession_number'),'decision_date':date}
    required_event=['accession_number','cik','ticker','first_observed_utc','filing_utc','reviewed_utc','role','event_kind']
    required_market=['stock_quote_utc','spy_quote_utc','locate_quote_utc','cap_known_utc','adv_known_utc','history_known_utc','state_known_utc','cap_asof','adv_asof','stock_reference_price','spy_reference_price','prior_market_cap','prior_20_session_adv','borrow_rate_annual','located_shares']
    required_state=['nav','positions','admissions','free_cash','restricted_cash','accrued_obligations','gross_short_dollars','spy_long_dollars']
    if any(k not in obj for obj,keys in [(event,required_event),(market,required_market),(state,required_state)] for k in keys):return no('missing_input_packet')
    if not freeze['admissions_start']<=date<=freeze['admissions_end']:return no('outside_admission_window')
    if date not in sessions.index:return no('not_exchange_session')
    cutoff=stamp(sessions.at[date,'decision_utc'])
    if not cutoff<=n<=cutoff+pd.Timedelta(minutes=5):return no('outside_decision_cutoff')
    received=stamp(event['first_observed_utc']);filed=stamp(event['filing_utc']);review=stamp(event['reviewed_utc'])
    if received<stamp(freeze['frozen_utc']) or filed<stamp(freeze['frozen_utc']):return no('pre_freeze_event')
    if not filed<=received<=review<=cutoff:return no('late_or_inconsistent_evidence_times')
    if event['role']!='acquirer' or event['event_kind']!='new_agreement':return no('role_or_event_exclusion')
    if not event.get('source_verified') or not event.get('evidence_anchor') or not event.get('source_sha256'):return no('unverified_source')
    if event.get('ambiguous') and not event.get('human_signoff'):return no('ambiguous_without_human_signoff')
    observed_date=received.tz_convert('America/New_York').date();filing_date=filed.tz_convert('America/New_York').date()
    allowed=sessions.index[(sessions.index>str(max(observed_date,filing_date)))]
    if not len(allowed) or date!=allowed[0]:return no('not_first_observable_entry_session')
    if not market.get('margin_approved') or not market.get('locate_available'):return no('missing_locate_or_margin')
    for field in ['stock_quote_utc','spy_quote_utc','locate_quote_utc']:
        t=stamp(market[field])
        if t>cutoff or (cutoff-t).total_seconds()>60:return no('stale_or_future_quote')
    for field in ['cap_known_utc','adv_known_utc','history_known_utc','state_known_utc']:
        if stamp(market[field])>cutoff:return no('future_known_input')
    if (cutoff-stamp(market['state_known_utc'])).total_seconds()>60:return no('stale_state_snapshot')
    previous=sessions.index[sessions.index<date][-1] if any(sessions.index<date) else None
    # First calendar row has no prior row; previous-day facts still must predate entry.
    latest=previous or date
    if market['cap_asof']>=date or market['adv_asof']>=date:return no('same_day_or_future_cap_adv')
    if previous and (market['cap_asof']!=previous or market['adv_asof']!=previous):return no('stale_cap_adv')
    nav=float(state['nav']);sp=float(market['stock_reference_price']);hp=float(market['spy_reference_price'])
    cap=float(market['prior_market_cap']);adv=float(market['prior_20_session_adv']);borrow=float(market['borrow_rate_annual'])
    if not all(math.isfinite(x) for x in [nav,sp,hp,cap,adv,borrow]):return no('invalid_numeric_input')
    if nav<=0 or sp<=0 or hp<=0 or adv<=0 or borrow<0:return no('invalid_numeric_input')
    if cap<2e9:return no('market_cap_below_2B')
    if any(p['cik']==event['cik'] for p in state['positions']):return no('issuer_overlap')
    if any(e['cik']==event['cik'] and (pd.Timestamp(date)-pd.Timestamp(e['decision_date'])).days<=30 for e in state['admissions']):return no('issuer_30_day_dedupe')
    if state.get('unreconciled') or state.get('stale_marks'):return no('unreconciled_or_stale_state')
    balance=float(state['free_cash'])+float(state['restricted_cash'])+float(state['accrued_obligations'])-float(state['gross_short_dollars'])+float(state['spy_long_dollars'])
    if not math.isfinite(balance) or abs(balance-nav)>1e-6:return no('state_balance_mismatch')
    if abs(sum(float(p['marked_short_dollars']) for p in state['positions'])-float(state['gross_short_dollars']))>1e-6:return no('position_exposure_mismatch')
    if state['positions'] and max(float(p['marked_short_dollars']) for p in state['positions'])>.02*nav+1e-6:return no('existing_issuer_cap_breach')
    beta=entry_beta(market.get('beta_history',[]),cutoff)
    existing=float(state['gross_short_dollars'])
    if existing<0 or not math.isfinite(existing):return no('invalid_existing_exposure')
    unit=.001+beta*.0002
    dollars=min(.02*nav/(1+.02*unit),max(0.,(nav-existing)/(1+unit)),.05*adv)
    q=min(math.floor(dollars/sp),int(market['located_shares']))
    if q<=0:return no('no_executable_size')
    hedge=math.floor(beta*q*sp/hp)
    if hedge<=0:return no('hedge_rounds_to_zero')
    return {'accepted':True,'reason':'entry_plan','accession_number':event['accession_number'],
       'cik':event['cik'],'ticker':event['ticker'],'decision_date':date,'quote_cutoff_utc':cutoff.isoformat(),
       'stock_shares_to_short':q,'spy_shares_to_buy':hedge,'stock_reference_price':sp,'spy_reference_price':hp,
       'beta':beta,'borrow_rate_annual':borrow,'predicted_fees':q*sp*.001+hedge*hp*.0002,
       'planned_exit_session_offset':60,'close_fill_price_does_not_set_order_size':True}


def freeze(root=HERE):
    path=root/'forward_freeze.json'
    if path.exists():return verify_freeze(root)
    data={'protocol_version':1,'frozen_utc':utc(),'admissions_start':'2026-10-05','admissions_end':'2027-10-04',
          'initial_paper_nav':1000000.,'external_timestamp_anchor':False,'prospective_returns_observed':0,
          'files_sha256':{n:sha(root/n) for n in FROZEN_FILES}}
    path.write_text(json.dumps(data,indent=2));return data


def main():
    ap=argparse.ArgumentParser();ap.add_argument('command',choices=['freeze','check','observe','review','decide','fill'])
    ap.add_argument('--input',type=Path);a=ap.parse_args()
    f=freeze() if a.command=='freeze' else verify_freeze();journal=HERE/'runtime/forward_journal.jsonl'
    now=utc();records=read_journal(journal,f)
    if a.command in ('freeze','check'):
        if a.command=='freeze':
            journal.parent.mkdir(parents=True,exist_ok=True);journal.touch(exist_ok=True)
        print(json.dumps({'freeze_sha256':digest(f),'frozen_utc':f['frozen_utc'],'journal_records':len(records),
                          'external_anchor':False,'actual_forward_returns':0},indent=2));return
    if not a.input:raise RuntimeError('--input JSON required')
    payload=json.loads(a.input.read_text())
    if a.command=='observe':
        # The clock, never the incoming file, determines first-observation time.
        if any(r['kind']=='observation' and r['payload']['accession_number']==payload['accession_number'] for r in records):raise RuntimeError('Accession already observed')
        payload['first_observed_utc']=now;stamp(payload['filing_utc'])
        if stamp(payload['filing_utc'])>stamp(now):raise RuntimeError('Future filing timestamp')
        kind='observation'
    elif a.command=='review':
        if not payload.get('reviewer') or payload.get('review_method') not in ('assistant','independent_human'):raise RuntimeError('Named reviewer and explicit review method required')
        if payload.get('human_signoff') and payload['review_method']!='independent_human':raise RuntimeError('Assistant review cannot claim human signoff')
        source=a.input.parent/payload['source_file']
        text=source.read_text();normalized=lambda s:' '.join(s.split()).casefold()
        if normalized(payload['evidence_anchor']) not in normalized(text):raise RuntimeError('Review anchor absent from source')
        payload['source_sha256']=sha(source);payload['source_verified']=True;payload['reviewed_utc']=now
        observations=[r for r in records if r['kind']=='observation' and r['payload']['accession_number']==payload['accession_number']]
        if not observations:raise RuntimeError('Source accession must first be observed')
        if payload.get('cik')!=observations[-1]['payload']['cik']:raise RuntimeError('Review issuer differs from observed issuer')
        kind='review'
    elif a.command=='decide':
        accession=payload['accession_number']
        obs=[r['payload'] for r in records if r['kind']=='observation' and r['payload']['accession_number']==accession]
        rev=[r['payload'] for r in records if r['kind']=='review' and r['payload']['accession_number']==accession]
        if not obs or not rev:raise RuntimeError('Observation and source review required before decision')
        if any(r['kind']=='decision' and r['payload'].get('accession_number')==accession for r in records):raise RuntimeError('Decision already logged; no profitable retry')
        event=dict(obs[-1]);event.update(rev[-1]);event['first_observed_utc']=obs[-1]['first_observed_utc']
        event['filing_utc']=obs[-1]['filing_utc'];event['ticker']=obs[-1]['ticker']
        payload['state']['admissions']=[r['payload']['decision'] for r in records if r['kind']=='decision' and r['payload']['decision']['accepted']]
        sessions=pd.read_csv(HERE/'nyse_sessions.csv',dtype=str).set_index('date')
        decision=plan(event,payload['market'],payload['state'],f,sessions,now)
        payload={'accession_number':accession,'decision':decision,'source_event':event,
                 'market':payload['market'],'state':payload['state']};kind='decision'
    else:
        decisions=[r for r in records if r['kind']=='decision' and r['payload']['accession_number']==payload['accession_number']]
        if not decisions or not decisions[-1]['payload']['decision']['accepted']:raise RuntimeError('Accepted precommitted decision required before fill')
        if any(r['kind']=='fill' and r['payload']['accession_number']==payload['accession_number'] for r in records):raise RuntimeError('Aggregate fill already logged')
        d=decisions[-1]['payload']['decision'];filled=stamp(payload['filled_utc'])
        if not stamp(decisions[-1]['recorded_utc'])<=filled<=stamp(now):raise RuntimeError('Fill outside committed/observed time ordering')
        sessions=pd.read_csv(HERE/'nyse_sessions.csv',dtype=str).set_index('date')
        close=stamp(sessions.at[d['decision_date'],'close_utc'])
        if abs((filled-close).total_seconds())>60:raise RuntimeError('Entry must be documented closing-auction fill')
        for field,limit in [('stock_filled_shares','stock_shares_to_short'),('spy_filled_shares','spy_shares_to_buy')]:
            if not 0<=payload[field]<=d[limit]:raise RuntimeError('Fill exceeds committed shares')
        for field in ['stock_filled_price','spy_filled_price']:
            if not math.isfinite(payload[field]) or payload[field]<=0:raise RuntimeError('Invalid fill price')
        if payload['execution_mode']!='paper_auction_model':raise RuntimeError('This journal records paper fills, not broker orders')
        source=a.input.parent/payload['source_file']
        payload['source_sha256']=sha(source)
        fee=float(payload.get('extra_broker_fee',0))
        if not math.isfinite(fee) or fee<0:raise RuntimeError('Invalid additional fee')
        payload['modeled_trading_fee']=payload['stock_filled_shares']*payload['stock_filled_price']*.001+payload['spy_filled_shares']*payload['spy_filled_price']*.0002+fee
        kind='fill'
    result=append(journal,f,kind,payload,now)
    print(json.dumps({'sequence':result['sequence'],'kind':kind,'record_sha256':result['record_sha256']},indent=2))


if __name__=='__main__':main()
