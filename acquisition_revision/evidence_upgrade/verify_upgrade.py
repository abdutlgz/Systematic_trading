"""Keyless public evidence checks; additionally verify licensed sources when local."""
import hashlib
import json
import unittest
from pathlib import Path
import pandas as pd
from vendor import HERE,sha,utc
from forward import verify_freeze,read_journal,digest
from audit_labels import normalize
from review_decisions import DECISIONS


def main():
    suite=unittest.defaultTestLoader.discover(str(HERE/'tests'))
    tests=unittest.TextTestRunner(verbosity=1).run(suite)
    if not tests.wasSuccessful():raise RuntimeError('Evidence tests failed')
    out=HERE/'output';summary=json.loads((out/'label_audit_summary.json').read_text())
    sample=pd.read_csv(HERE/'review_sample.csv',dtype={'cik':str})
    audit=pd.read_csv(out/'verified_role_audit.csv',dtype={'cik':str})
    collection=json.loads((out/'review_collection.json').read_text())
    assert sha(HERE/'review_sample.csv')==summary['sample_sha256']==collection['frozen_sample_sha256']
    assert sha(out/'verified_role_audit.csv')==summary['labels_sha256']
    assert len(sample)==len(audit)==len(DECISIONS)==30
    assert not audit.accession_number.duplicated().any()
    assert set(sample.accession_number)==set(audit.accession_number)
    assert audit.reviewed_role.value_counts().to_dict()==summary['issuer_role_counts']
    assert audit.event_kind.value_counts().to_dict()==summary['event_kind_counts']
    assert not audit.human_verified.any() and audit.items_verified.all()
    assert not audit.full_filing_and_exhibits_verified.any()
    eligible=(audit.reviewed_role=='acquirer') & (audit.event_kind=='new_agreement')
    assert (eligible==audit.eligible_under_forward_rule).all()
    assert int(eligible.sum())==summary['forward_rule_eligible_in_sample']==14
    for row in audit.itertuples():
        expected=DECISIONS[row.ticker]
        assert (row.reviewed_role,row.event_kind,row.consideration_type,row.evidence_anchor,row.reasoning)==expected
        assert row.source_url.startswith('https://www.sec.gov/Archives/edgar/data/')
    licensed=HERE/'data/review_items.json';local_verified=False
    if licensed.exists():
        assert sha(licensed)==collection['items_sha256']
        sources={x['accession_number']:x for x in json.loads(licensed.read_text())}
        for row in audit.itertuples():
            source=sources[row.accession_number]
            assert source['cik'].lstrip('0')==row.cik.lstrip('0') and source['filing_date']==row.filing_date
            assert hashlib.sha256(source['items_text'].encode()).hexdigest()==row.items_text_sha256
            assert normalize(row.evidence_anchor) in normalize(source['items_text'])
        for receipt in collection['receipts']:
            assert sha(HERE/'cache'/receipt['response_file'])==receipt['response_sha256']
        local_verified=True
    comparison=json.loads((out/'reconstruction_comparison.json').read_text())
    assert comparison['rebuilt_events']==1109 and comparison['source_response_count']==4080
    assert comparison['metrics_match_1e_8'] and comparison['daily_return_match_1e_10']
    assert comparison['maximum_metric_difference']==comparison['maximum_daily_return_difference']==0
    assert comparison['reconstructed_placebos']==100 and comparison['clean_input_reconstruction']
    # Saved comparison is a receipt/report, not a new licensed download on this run.
    root=HERE/'data/clean_reconstruction';checked=0
    if root.exists():
        for receiptfile in (root/'cache').glob('*.receipt.json'):
            receipt=json.loads(receiptfile.read_text())
            assert sha(root/'cache'/receipt['response_file'])==receipt.get('response_sha256',receipt.get('sha256'))
            if 'response_sha256' in receipt:checked+=1
        assert checked==comparison['source_response_count']
        for path in (HERE.parent/'output').glob('*_daily.csv'):
            other=root/'output'/path.name
            pd.testing.assert_frame_equal(pd.read_csv(path),pd.read_csv(other),check_exact=True)
    freeze=verify_freeze();records=read_journal(HERE/'runtime/forward_journal.jsonl',freeze)
    result={'checked_utc':utc(),'evidence_tests_passed':tests.testsRun,'public_label_checks_passed':True,
            'licensed_items_verified_locally':local_verified,'licensed_rebuild_receipts_verified_locally':checked,
            'saved_reconstruction_report_checked':True,'fresh_download_performed_by_this_verifier':False,
            'freeze_sha256':digest(freeze),'frozen_utc':freeze['frozen_utc'],'journal_records':len(records),
            'external_timestamp_anchor':False,'prospective_performance_available':False}
    (out/'upgrade_verification.json').write_text(json.dumps(result,indent=2))
    files=list(HERE.glob('*.py'))+list(HERE.glob('*.md'))+list(HERE.glob('*.csv'))+list(HERE.glob('*.json'))
    files+=list((HERE/'tests').glob('*.py'))+list(out.glob('*.csv'))+list(out.glob('*.json'))
    files=[p for p in files if p.name!='upgrade_artifact_manifest.json']
    (out/'upgrade_artifact_manifest.json').write_text(json.dumps({'sha256':{str(p.relative_to(HERE)):sha(p) for p in sorted(files)}},indent=2))
    print(json.dumps(result,indent=2))


if __name__=='__main__':main()
