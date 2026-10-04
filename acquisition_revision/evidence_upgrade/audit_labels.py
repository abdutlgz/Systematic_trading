"""Validate review provenance and summarize a stratified audit, not population accuracy."""
import hashlib
import json
import re

import pandas as pd

from vendor import HERE,sha,utc
from review_decisions import DECISIONS


def normalize(s):
    s=str(s).replace('\u201c','"').replace('\u201d','"').replace('\u2019',"'")
    return ' '.join(s.split()).casefold()


def main():
    sample=pd.read_csv(HERE/'review_sample.csv',dtype={'cik':str})
    source=json.loads((HERE/'data/review_items.json').read_text())
    by={r['accession_number']:r for r in source};rows=[]
    if len(sample)!=30 or len(DECISIONS)!=30:raise RuntimeError('Frozen audit requires all 30 cases')
    collected=json.loads((HERE/'output/review_collection.json').read_text())
    if sha(HERE/'review_sample.csv')!=collected['frozen_sample_sha256']:raise RuntimeError('Sample changed')
    if sha(HERE/'data/review_items.json')!=collected['items_sha256']:raise RuntimeError('Items changed')
    for r in sample.itertuples():
        s=by[r.accession_number];role,event,finance,anchor,reason=DECISIONS[r.ticker]
        if str(s['cik']).lstrip('0')!=str(r.cik).lstrip('0') or s['filing_date']!=r.filing_date:raise RuntimeError('Source identity/date mismatch')
        if normalize(anchor) not in normalize(s['items_text']):raise RuntimeError('Evidence anchor absent: '+r.ticker)
        if len(anchor.split())>25:raise RuntimeError('Source quote too long')
        rows.append({'ticker':r.ticker,'cik':r.cik,'filing_date':r.filing_date,'accession_number':r.accession_number,
             'heuristic_role':r.role_suggestion,'reviewed_role':role,'event_kind':event,'consideration_type':finance,
             'source_url':s['filing_url'],'evidence_anchor':anchor,'reasoning':reason,
             'items_text_sha256':hashlib.sha256(s['items_text'].encode()).hexdigest(),
             'reviewer':'Codex assistant source review','human_verified':False,'items_verified':True,
             'full_filing_and_exhibits_verified':False,'eligible_under_forward_rule':role=='acquirer' and event=='new_agreement',
             'reviewed_utc':utc()})
    d=pd.DataFrame(rows);d.to_csv(HERE/'output/verified_role_audit.csv',index=False)
    known=d[d.heuristic_role!='unknown'].copy()
    known['expected']=known.heuristic_role.str.replace('_suggested','',regex=False)
    summary={'reviewed_events':len(d),'issuer_role_counts':d.reviewed_role.value_counts().to_dict(),
       'event_kind_counts':d.event_kind.value_counts().to_dict(),'forward_rule_eligible_in_sample':int(d.eligible_under_forward_rule.sum()),
       'suggested_cases':len(known),'suggestion_role_agreements':int((known.expected==known.reviewed_role).sum()),
       'suggestion_role_disagreements':known.loc[known.expected!=known.reviewed_role,['ticker','heuristic_role','reviewed_role']].to_dict('records'),
       'previous_unknown_roles':d.loc[d.heuristic_role=='unknown','reviewed_role'].value_counts().to_dict(),
       'human_gold_labels':0,'classifier_population_accuracy':None,
       'scope':'30 original stratified cases; exact-accession parsed SEC Items through licensed vendor; no exhibits',
       'not_independent_human_validation':True,'not_used_to_refilter_historical_results':True,
       'labels_sha256':sha(HERE/'output/verified_role_audit.csv'),'sample_sha256':sha(HERE/'review_sample.csv')}
    (HERE/'output/label_audit_summary.json').write_text(json.dumps(summary,indent=2))
    print(json.dumps(summary,indent=2))


if __name__=='__main__':main()
