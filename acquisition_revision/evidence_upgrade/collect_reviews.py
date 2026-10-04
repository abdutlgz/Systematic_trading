"""Fetch complete parsed 8-K Items by exact accession for the frozen 30-row sample.

SEC direct retrieval was denied. Parsed Items are obtained through Massive's
licensed text endpoint and retain the originating SEC URL; exhibits may be absent.
This does not reuse the supporting snippets being evaluated.
"""
import argparse
from concurrent.futures import ThreadPoolExecutor
import json
from pathlib import Path

import pandas as pd

from vendor import HERE,Vendor,sha,utc


def main():
    ap=argparse.ArgumentParser();ap.add_argument('--offline',action='store_true');a=ap.parse_args()
    v=Vendor(HERE,offline=a.offline)
    sample=HERE/'review_sample.csv'
    original=HERE.parent/'output/role_review_sample.csv'
    d=pd.read_csv(original if original.exists() else sample,dtype={'cik':str})
    # Freeze membership independently of any outcome or eventual source availability.
    membership=d[['ticker','cik','filing_date','accession_number','role_suggestion','filing_url']]
    if sample.exists():pd.testing.assert_frame_equal(pd.read_csv(sample,dtype={'cik':str}),membership.reset_index(drop=True))
    else:membership.to_csv(sample,index=False)
    def one(r):
        rows=v.rows('/stocks/filings/8-K/vX/text',{'cik':str(r.cik).zfill(10),'filing_date':r.filing_date,
                    'limit':100,'sort':'filing_date.asc'},max_pages=2)
        matches=[x for x in rows if x.get('accession_number')==r.accession_number]
        if len(matches)!=1 or not matches[0].get('items_text'):
            raise RuntimeError('Missing or ambiguous exact accession: '+r.ticker)
        row=matches[0]
        if str(row.get('cik','')).lstrip('0')!=str(r.cik).lstrip('0'):raise RuntimeError('Issuer mismatch')
        return row
    with ThreadPoolExecutor(4) as pool:rows=list(pool.map(one,d.itertuples()))
    (HERE/'data/review_items.json').write_text(json.dumps(rows,indent=2))
    (HERE/'output/review_collection.json').write_text(json.dumps({'count':len(rows),'retrieved_utc':utc(),
       'frozen_sample_sha256':sha(sample),'items_sha256':sha(HERE/'data/review_items.json'),
       'sources':'exact-accession SEC Items retrieved through licensed Massive text endpoint',
       'exhibits_not_guaranteed':True,'human_review':False,'receipts':v.receipts},indent=2))
    print('Exact-accession parsed Items obtained:',len(rows))


if __name__=='__main__':main()
