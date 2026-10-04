"""Keyless checks of saved ledgers and note metrics; full rerun is run.py.

This verifies arithmetic from derived ledgers, not a fresh licensed data rebuild.
"""
import hashlib
import json
from pathlib import Path
import unittest

import numpy as np
import pandas as pd

from run import HERE,OUT,WINDOWS,metrics


def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()


def main():
    suite=unittest.defaultTestLoader.discover(str(HERE/'tests'))
    result=unittest.TextTestRunner(verbosity=1).run(suite)
    if not result.wasSuccessful():raise RuntimeError('Accounting tests failed')
    saved=json.loads((OUT/'results.json').read_text());checks=[]
    for name in saved['configuration']:
        d=pd.read_csv(OUT/f'{name}_daily.csv',index_col=0,parse_dates=True)
        identity=d.free_cash+d.restricted_cash+d.dividend_receivable-d.stock_short+d.spy_long
        np.testing.assert_allclose(d.nav,identity,atol=1e-11,rtol=0)
        np.testing.assert_allclose(d['return'],d.nav/d.nav.shift(1).fillna(1)-1,atol=1e-12)
        np.testing.assert_allclose(d.excess_return,d['return']-d.rf,atol=1e-12)
        for window,(a,b) in WINDOWS.items():
            computed=metrics(d.loc[a:b]);expected=saved['metrics'][name][window]
            for key,value in computed.items():
                if value is None:assert expected[key] is None
                else:assert abs(value-expected[key])<1e-9,(name,window,key,value,expected[key])
        obs=metrics(d.loc[WINDOWS['historical_test'][0]:saved['rf_last_observed']])
        for key,value in obs.items():
            if value is not None:assert abs(value-saved['metrics'][name]['test_observed_rf_only'][key])<1e-9
        entries=pd.read_csv(OUT/f'{name}_entries.csv',parse_dates=['date','filing_date'])
        accepted=entries[entries.accepted]
        assert (accepted.date>accepted.filing_date).all()
        for r in accepted.itertuples():
            earliest=d.index.searchsorted(r.filing_date,side='right')+saved['configuration'][name]['lag']
            assert r.date==d.index[earliest]
        checks.append({'configuration':name,'sessions':len(d),'nav_identity_error':float((identity-d.nav).abs().max()),
                       'strict_entry_timing_checked':len(accepted),'metrics_recomputed':True})
    p=pd.read_csv(OUT/'placebo_results.csv');ps=saved['placebo']
    assert len(p)==ps['replicates']==100
    n=int((p.excess_sharpe>=ps['observed_is_excess_sharpe']).sum())
    assert n==ps['number_ge_observed']
    assert (n+1)/(len(p)+1)==ps['finite_sample_tail_fraction']
    audit={'accounting_tests_passed':result.testsRun,'ledger_checks':checks,
           'placebo_tail_recomputed':True,'keyless_derived_output_replay_only':True,
           'investable_validation_passed':False}
    (OUT/'verification.json').write_text(json.dumps(audit,indent=2))
    files=list(HERE.glob('*.py'))+list(HERE.glob('*.md'))+list(HERE.glob('*.csv'))
    files+=[HERE/'requirements.txt']+list((HERE/'tests').glob('*.py'))+list(OUT.glob('*.json'))
    files+=list(OUT.glob('*_daily.csv'))+list(OUT.glob('*_trades.csv'))+list(OUT.glob('*_entries.csv'))+list(OUT.glob('*_exceptions.csv'))
    files+=list(OUT.glob('placebo_results.csv'))+list(OUT.glob('*.html'))+list(OUT.glob('*.txt'))+list(OUT.glob('*.png'))+list((OUT/'pdf').glob('*.pdf'))
    files=[p for p in files if p.name!='artifact_manifest.json']
    fingerprints={str(p.relative_to(HERE)):sha(p) for p in sorted(files)}
    (OUT/'artifact_manifest.json').write_text(json.dumps({'sha256':fingerprints,
              'licensed_raw_inputs_hashes_in':'input_manifest.json'},indent=2))
    print(json.dumps(audit,indent=2))


if __name__=='__main__':main()
