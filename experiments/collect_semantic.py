"""Acquire public earnings filings and supporting research series, preserving provenance."""
import json,time,zipfile,io
from probe import ROOT,fetch

UNIVERSE={'AMD':2488,'ADBE':796343,'CRM':1108524,'ORCL':1341439,'NFLX':1065280,'COST':909832}

def main():
    manifest=[];events=[]
    def get(name,url):
        r=fetch(name,url);manifest.append(r)
        (ROOT/'results'/'semantic_source_manifest.json').write_text(json.dumps(manifest,indent=2))
        print(name,r.get('status',r.get('error')),flush=True)
        return r
    for symbol,cik in UNIVERSE.items():
        get('semantic_prices_'+symbol,f'https://query1.finance.yahoo.com/v8/finance/chart/{symbol}?range=2y&interval=1d')
        r=get('semantic_sec_'+symbol,f'https://data.sec.gov/submissions/CIK{cik:010d}.json')
        if 'error' in r:continue
        d=json.loads((ROOT/'raw'/f'semantic_sec_{symbol}.raw').read_text())['filings']['recent']
        for i,form in enumerate(d['form']):
            if form!='8-K' or '2.02' not in d['items'][i].split(',') or not '2024-11-01'<=d['filingDate'][i]<='2026-09-30':continue
            acc=d['accessionNumber'][i]
            events.append({'symbol':symbol,'cik':cik,'accession':acc,'filing_date':d['filingDate'][i],
                           'accepted_utc':d['acceptanceDateTime'][i],'primary_document':d['primaryDocument'][i],
                           'url':f'https://www.sec.gov/Archives/edgar/data/{cik}/{acc.replace("-","")}/{acc}.txt'})
        time.sleep(.25)
    events=sorted(events,key=lambda e:(e['filing_date'],e['symbol']))
    assert len(events)<=64, 'Protocol limit: stop rather than silently select events'
    (ROOT/'results'/'semantic_events.json').write_text(json.dumps(events,indent=2))
    # Probe first, then stop repeated forbidden requests instead of hammering SEC.
    for e in events:
        r=get('filing_'+e['accession'],e['url'])
        if 'error' in r and ('403' in r['error'] or '429' in r['error']):break
        time.sleep(.25)
    for name,url in {
        'french_five_daily':'https://mba.tuck.dartmouth.edu/pages/faculty/ken.french/ftp/F-F_Research_Data_5_Factors_2x3_daily_CSV.zip',
        'fred_vix':'https://fred.stlouisfed.org/graph/fredgraph.csv?id=VIXCLS&cosd=2024-10-01&coed=2026-09-30',
        'fred_yield_curve':'https://fred.stlouisfed.org/graph/fredgraph.csv?id=T10Y2Y&cosd=2024-10-01&coed=2026-09-30',
    }.items():get(name,url)
    print('Earnings events:',len(events))

if __name__=='__main__':main()
