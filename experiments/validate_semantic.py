"""Checks on downloaded records and derived artifacts; no synthetic data."""
import hashlib,json
import pandas as pd
from probe import ROOT
from semantic_pilot import validate_extraction,PROMPT

records=json.loads((ROOT/'results'/'semantic_source_manifest.json').read_text());verified=0
for r in records:
    if 'sha256' not in r:continue
    data=(ROOT/'raw'/(r['name']+'.raw')).read_bytes()
    assert hashlib.sha256(data).hexdigest()==r['sha256'],r['name']
    verified+=1
docs={json.loads(x)['accession']:json.loads(x) for x in (ROOT/'results'/'earnings_documents.jsonl').read_text().splitlines()}
assert len(docs)==46
for acc,d in docs.items():
    assert hashlib.sha256(d['text'].encode()).hexdigest()==d['text_sha256']
    r=json.loads((ROOT/'results'/'gemini'/(acc+'.json')).read_text())
    assert r['text_sha256']==d['text_sha256']
    assert r['prompt_sha256']==hashlib.sha256(PROMPT.encode()).hexdigest()
    assert not validate_extraction(r['parsed'],d['text'])
frame=pd.read_json(ROOT/'results'/'semantic_features.jsonl',lines=True,convert_dates=False)
test=pd.read_json(ROOT/'results'/'semantic_predictions.jsonl',lines=True,convert_dates=False)
assert len(frame)==46 and len(test)==18 and frame.semantic_available.all()
assert (test.date>='2026-01-01').all() and (test.date<='2026-09-30').all()
assert not frame[['date','symbol']].duplicated().any()
for _,r in frame.iterrows():
    decision=pd.Timestamp(r.date+' 09:25',tz='America/New_York').tz_convert('UTC')
    assert pd.Timestamp(docs[r.accession]['accepted_utc'])+pd.Timedelta(minutes=30)<=decision
summary=json.loads((ROOT/'results'/'semantic_summary.json').read_text())
for name in ['market_history','mechanical_text','semantic']:
    actual=float(abs(test.target-test['pred_'+name]).mean())
    assert abs(actual-summary['metrics'][name]['mae_log_relative_volume'])<1e-8
print(f'PASS: {verified} public-response hashes, 46 source/output pairs, strict evidence quotations, event timing, held-out rows and reported errors.')
