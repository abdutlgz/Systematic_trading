"""Normalize the user's public research sources without treating them as live signals."""
import io,json,re,zipfile
import pandas as pd
from probe import ROOT

z=zipfile.ZipFile(ROOT/'raw'/'french_five_daily.raw')
text=z.read(z.namelist()[0]).decode('utf-8-sig')
lines=[line for line in text.splitlines() if re.match(r'^\d{8},',line)]
df=pd.read_csv(io.StringIO('date,Mkt-RF,SMB,HML,RMW,CMA,RF\n'+'\n'.join(lines)),dtype={'date':str})
df['date']=pd.to_datetime(df.date,format='%Y%m%d').dt.strftime('%Y-%m-%d')
for col in df.columns[1:]:
    df[col]=pd.to_numeric(df[col],errors='raise').replace({-99.99:float('nan'),-999:float('nan')})/100
assert not df.date.duplicated().any()
df=df[df.date>='2024-10-01']
df.to_json(ROOT/'results'/'french_factors.jsonl',orient='records',lines=True)
summary={'french':{'rows':len(df),'start':df.date.min(),'end':df.date.max(),'units':'decimal returns; original percentage points divided by 100',
                   'role':'Ex-post risk attribution only. Current revised factors are not contemporaneously available predictor data.'},'fred':{}}
for file,series in [('fred_vix','VIXCLS'),('fred_yield_curve','T10Y2Y')]:
    frame=pd.read_csv(ROOT/'raw'/(file+'.raw'),dtype={'observation_date':str})
    frame[series]=pd.to_numeric(frame[series],errors='coerce')
    frame.to_json(ROOT/'results'/(file+'.jsonl'),orient='records',lines=True)
    summary['fred'][series]={'rows':len(frame),'nonmissing':int(frame[series].notna().sum()),'start':frame.observation_date.min(),'end':frame.observation_date.max(),
                            'role':'Context only; current download does not establish vintage/publication-time availability.'}
(ROOT/'results'/'research_sources_summary.json').write_text(json.dumps(summary,indent=2))
print(json.dumps(summary,indent=2))
