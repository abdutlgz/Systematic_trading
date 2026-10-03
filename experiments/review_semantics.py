"""Documented, source-checked corrections made before fitting the semantic model.

Raw API responses are retained. This makes the audited result reproducible and
explicitly a Gemini-plus-human-review experiment, not an autonomous model result.
"""
import json
from probe import ROOT
from semantic_pilot import validate_extraction

CORRECTIONS=[
('0000002488-25-000009','revenue_growth_pct',24,'We closed 2024 with a strong fourth quarter, delivering record revenue up 24% year-over-year','Noncontiguous quote replaced with exact quarterly evidence.'),
('0001108524-24-000033','acquisition_announced',False,'','Already closed in November, not a new announcement.'),
('0000002488-25-000045','acquisition_announced',False,'','Completed transaction, not new announcement.'),
('0001065280-25-000033','revenue_growth_pct',16,'In Q4, revenue increased 16% year over year','Annual quotation replaced with quarterly quotation; value unchanged.'),
('0001108524-25-000234','acquisition_announced',False,'','Completed transaction, not new announcement.'),
('0001065280-26-000033','acquisition_announced',False,'','January release refers to December announcement.'),
('0001065280-26-000033','revenue_growth_pct',18,'Q4 revenue grew 18% year over year','Annual growth incorrectly used instead of quarterly reported growth.'),
('0000002488-26-000072','revenue_growth_pct',38,'Revenue ($M) $10,253 $7,438 Up 38%','Noncontiguous quote replaced with exact quarterly table span.'),
('0001065280-26-000137','buyback_announced',False,'','Resumption of existing authorization, not new authorization.'),
('0001065280-26-000137','acquisition_announced',False,'','April release refers to March announcement.'),
('0001065280-26-000211','buyback_announced',False,'','July release refers to April authorization.'),
('0001108524-26-000125','buyback_announced',False,'','Accelerated repurchase execution, not new authorization.'),
('0001193125-26-100148','restructuring_announced',False,'','Efficiency commentary does not announce restructuring.'),
('0000002488-26-000121','acquisition_announced',False,'','Acquired MEXT describes a completed deal, excluded by fixed definition.'),
]

def main():
    docs={json.loads(x)['accession']:json.loads(x) for x in (ROOT/'results'/'earnings_documents.jsonl').read_text().splitlines()}
    review=[]
    for p in sorted((ROOT/'results'/'gemini').glob('*.json')):
        r=json.loads(p.read_text());d=docs[r['accession']]
        parts=r['raw_response']['candidates'][0]['content']['parts']
        raw=json.loads(''.join(x.get('text','') for x in parts if not x.get('thought')))
        corrected=json.loads(json.dumps(raw));changes=[]
        edits=[x for x in CORRECTIONS if x[0]==r['accession']]
        # The fixed prompt asks for total revenue. Costco net sales exclude membership fees.
        # Do not mix a different denominator into the same numerical feature.
        if d['symbol']=='COST' and raw['revenue_growth_pct']['value'] is not None:
            edits.append((r['accession'],'revenue_growth_pct',None,'','Net-sales growth is not total revenue including membership fees; strict missing value.'))
        for acc,field,value,evidence,reason in edits:
            assert not evidence or evidence in d['text'],(acc,field)
            changes.append({'field':field,'original':raw[field],'corrected':{'value':value,'evidence':evidence},'reason':reason})
            corrected[field]={'value':value,'evidence':evidence}
        r['parsed']=corrected;r['validation_errors']=validate_extraction(corrected,d['text'])
        r.pop('manual_review',None);r['manual_reviews']=changes
        p.write_text(json.dumps(r,indent=2))
        review.append({'accession':r['accession'],'symbol':d['symbol'],'corrections':changes,'remaining_validation_errors':r['validation_errors']})
    (ROOT/'results'/'semantic_review.json').write_text(json.dumps({'scope':'Targeted evidence/type/period/new-announcement checks; not exhaustive independent gold labels.',
        'documents':len(review),'documents_corrected':sum(bool(x['corrections']) for x in review),
        'field_corrections':sum(len(x['corrections']) for x in review),'reviews':review},indent=2))
    assert not any(x['remaining_validation_errors'] for x in review)
    print('Source-grounded review complete:',sum(bool(x['corrections']) for x in review),'documents corrected.')

if __name__=='__main__':main()
