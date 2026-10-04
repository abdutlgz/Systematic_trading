"""Traceable filing-text review worksheet; suggestions are not trading filters."""
import hashlib
import json
from pathlib import Path
import re

import pandas as pd

HERE=Path(__file__).resolve().parent


def suggestion(text):
    s=' '.join(str(text).split())
    acquirer=[r'\bwe (?:have )?(?:acquired|purchased|agreed to acquire)\b',
              r'\b(?:the )?company (?:has |had )?(?:acquired|purchased|agreed to acquire)\b',
              r'\bcompany.{0,100}\b(?:as purchaser|as buyer)\b']
    target=[r'\bcompany.{0,120}\b(?:as seller|as target)\b',
            r'\bmerger sub.{0,100}merge.{0,80}into the company\b',
            r'\bcompany.{0,100}(?:be acquired by|will be acquired)\b']
    a=[p for p in acquirer if re.search(p,s,re.I)]
    t=[p for p in target if re.search(p,s,re.I)]
    role='ambiguous' if a and t else 'acquirer_suggested' if a else 'target_suggested' if t else 'unknown'
    finance='mixed_or_unclear'
    if re.search(r'\ball[- ]cash\b',s,re.I):finance='cash_suggested'
    elif re.search(r'\ball[- ]stock\b',s,re.I):finance='stock_suggested'
    return role,finance,'; '.join(a+t)


def main():
    rows=json.loads((HERE/'data/disclosures.json').read_text())
    d=pd.DataFrame(rows)
    d['ticker']=d.tickers.map(lambda t:str(t[0]).upper().replace('/','.') if isinstance(t,list) and t else None)
    d['cik']=d.cik.astype(str).str.lstrip('0')
    d['filing_date']=pd.to_datetime(d.filing_date)
    ev=pd.read_csv(HERE/'data/events.csv',dtype={'cik':str},parse_dates=['filing_date'])
    ev.cik=ev.cik.str.lstrip('0')
    d=d.drop_duplicates(['cik','ticker','filing_date'])
    merged=ev.merge(d[['cik','ticker','filing_date','accession_number','supporting_text','filing_url']],
                    on=['cik','ticker','filing_date'],how='left',validate='many_to_one')
    suggestions=merged.supporting_text.fillna('').map(suggestion)
    merged['role_suggestion']=[v[0] for v in suggestions]
    merged['financing_suggestion']=[v[1] for v in suggestions]
    merged['matched_patterns']=[v[2] for v in suggestions]
    merged['text_sha256']=merged.supporting_text.fillna('').map(lambda s:hashlib.sha256(s.encode()).hexdigest())
    merged['human_role_label']='';merged['human_financing_label']='';merged['reviewer']='';merged['review_notes']=''
    merged['full_filing_verified']=False
    merged.to_csv(HERE/'output/role_review.csv',index=False)
    # Outcomes are never used in selecting this worksheet sample.
    sample=pd.concat([g.sample(n=min(10,len(g)),random_state=20261003) for _,g in merged.groupby('role_suggestion')])
    sample.to_csv(HERE/'output/role_review_sample.csv',index=False)
    summary={'events':len(merged),'text_missing':int(merged.supporting_text.isna().sum()),
       'heuristic_role_counts':merged.role_suggestion.value_counts().to_dict(),
       'heuristic_financing_counts':merged.financing_suggestion.value_counts().to_dict(),
       'human_labeled_events':0,'classifier_accuracy':None,
       'not_used_as_trading_filter':True,'post_event_prices_not_used':True,
       'sample_events':len(sample),'sample_seed':20261003,
       'warning':'Suggestions use supporting-text snippets, not verified full filings. Unknown is retained.'}
    (HERE/'output/classification_summary.json').write_text(json.dumps(summary,indent=2))
    print(json.dumps(summary,indent=2))


if __name__=='__main__':main()
