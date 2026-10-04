"""Source-linked foreign-dividend normalization; paying-agent proxies are explicit.

Default: replay public FX caches. --download: collect official rates with macOS curl.
No credential or trading parameter is involved.
"""
import argparse
import json
import subprocess

import pandas as pd

from prepare import DATA,HERE

BOC='https://www.bankofcanada.ca/valet/observations/FXCADUSD/json?start_date=2024-08-15&end_date=2026-08-14'
BOC2022='https://www.bankofcanada.ca/valet/observations/FXEURCAD,FXCADUSD/json?start_date=2022-04-14&end_date=2022-04-14'
CNHI2023='https://www.sec.gov/Archives/edgar/data/1567094/000162828023016804/R26.htm'
CNHI2022='https://www.sec.gov/Archives/edgar/data/1567094/000119312522104429/d293057dex991.htm'


def main():
    ap=argparse.ArgumentParser();ap.add_argument('--download',action='store_true');a=ap.parse_args()
    if a.download:
        for url,filename in [(BOC,'boc_fx.json'),(BOC2022,'boc_2022_fx.json')]:
            subprocess.run(['/usr/bin/curl','--fail','--location','--max-time','60',url,
                           '--output',str(HERE/'cache'/filename)],check=True)
    div=pd.read_csv(DATA/'original_dividends.csv')
    boc=json.loads((HERE/'cache/boc_fx.json').read_text())
    cad={r['d']:float(r['FXCADUSD']['v']) for r in boc['observations'] if 'FXCADUSD' in r}
    observation=json.loads((HERE/'cache/boc_2022_fx.json').read_text())['observations'][0]
    if observation['d']!='2022-04-14':raise RuntimeError('Unexpected FX observation date')
    eur=float(observation['FXEURCAD']['v'])*float(observation['FXCADUSD']['v'])
    rows=[]
    for r in div[div.currency!='USD'].itertuples():
        if r.ticker=='CNHI' and r.ex_dividend_date=='2022-04-19':
            amount=.28*eur;source=CNHI2022;rate_source=BOC2022;method='USD_proxy_BOC_2022_04_14_not_exact_ECB';known='2022-04-14'
        elif r.ticker=='CNHI' and r.ex_dividend_date=='2023-04-24':
            amount=.39398;source=CNHI2023;rate_source='issuer_exact_cash_payment';method='issuer_fixed_2023_04_20';known='2023-04-20'
        elif r.ticker=='ENB' and r.currency=='CAD':
            amount=float(r.cash_amount)*cad[r.ex_dividend_date]
            source='https://www.enbridge.com/investment-center/faqs';rate_source=BOC
            method='paying_agent_USD_proxy_BOC_ex_record_date';known=r.ex_dividend_date
        else:raise RuntimeError('Unsupported foreign dividend: '+r.ticker+' '+r.ex_dividend_date)
        rows.append({'ticker':r.ticker,'ex_dividend_date':r.ex_dividend_date,
                     'split_adjusted_cash_amount':amount,'known_at_date':known,'method':method,
                     'source_url':source,'rate_source':rate_source})
    pd.DataFrame(rows).to_csv(DATA/'dividend_overrides.csv',index=False)
    summary={'corrected_foreign_rows':len(rows),'paying_agent_proxy_rows':sum('proxy' in r['method'] for r in rows),
             'boc_proxy_2022_04_14_USD_per_EUR':eur,'not_verified_broker_cash_for_ENB_and_2022_CNHI':True,
             'rejected_ECB_download':'did not contain the required 2022-04-14 observation'}
    (DATA/'dividend_adjustments.json').write_text(json.dumps(summary,indent=2))
    print(json.dumps(summary,indent=2))


if __name__=='__main__':main()
