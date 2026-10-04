"""Published NYSE 2026/2027 sessions relevant to the frozen admission/exit horizon."""
import pandas as pd
from vendor import HERE

def main():
    holidays={'2026-11-26','2026-12-25','2027-01-01','2027-01-18','2027-02-15','2027-03-26',
              '2027-05-31','2027-06-18','2027-07-05','2027-09-06','2027-11-25','2027-12-24','2028-01-17'}
    early={'2026-11-27','2026-12-24','2027-11-26'}
    rows=[]
    for d in pd.bdate_range('2026-10-02','2028-01-31'):
        date=d.strftime('%Y-%m-%d')
        if date in holidays:continue
        close='13:00:00' if date in early else '16:00:00'
        c=pd.Timestamp(date+' '+close,tz='America/New_York')
        rows.append({'date':date,'close_utc':c.tz_convert('UTC').isoformat(),
                     'decision_utc':(c-pd.Timedelta(hours=1)).tz_convert('UTC').isoformat()})
    pd.DataFrame(rows).to_csv(HERE/'nyse_sessions.csv',index=False)
    print('Published sessions saved:',len(rows))

if __name__=='__main__':main()
