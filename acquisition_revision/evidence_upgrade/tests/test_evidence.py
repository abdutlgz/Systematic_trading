"""Adversarial time-ordering, order sizing, provenance and reconstruction fixtures."""
import copy
import json
from pathlib import Path
import sys
import tempfile
import unittest

import pandas as pd

HERE=Path(__file__).resolve().parents[1];sys.path.insert(0,str(HERE))
from forward import plan,append,read_journal,entry_beta,verify_freeze
from reconstruct import event_table


class EvidenceTests(unittest.TestCase):
    def fixture(self):
        freeze={'frozen_utc':'2026-10-04T04:00:00+00:00','admissions_start':'2026-10-05','admissions_end':'2027-10-04'}
        sessions=pd.read_csv(HERE/'nyse_sessions.csv',dtype=str).set_index('date')
        now='2026-10-07T19:00:01+00:00'
        event={'accession_number':'fixture-accession','cik':'123','ticker':'A','role':'acquirer','event_kind':'new_agreement',
            'filing_utc':'2026-10-05T14:00:00+00:00','first_observed_utc':'2026-10-06T12:00:00+00:00',
            'reviewed_utc':'2026-10-06T13:00:00+00:00','source_verified':True,'source_sha256':'fixturehash',
            'evidence_anchor':'fixture paragraph'}
        market={'stock_reference_price':100.,'spy_reference_price':500.,'stock_quote_utc':'2026-10-07T18:59:50+00:00',
            'spy_quote_utc':'2026-10-07T18:59:50+00:00','locate_quote_utc':'2026-10-07T18:59:50+00:00',
            'cap_known_utc':'2026-10-07T12:00:00+00:00','adv_known_utc':'2026-10-07T12:00:00+00:00',
            'history_known_utc':'2026-10-07T12:00:00+00:00','state_known_utc':'2026-10-07T18:59:50+00:00',
            'cap_asof':'2026-10-06','adv_asof':'2026-10-06','prior_market_cap':3e9,'prior_20_session_adv':1e6,
            'borrow_rate_annual':.01,'located_shares':1000,'margin_approved':True,'locate_available':True}
        state={'nav':1e6,'positions':[],'admissions':[],'gross_short_dollars':0.,'free_cash':1e6,
               'restricted_cash':0.,'accrued_obligations':0.,'spy_long_dollars':0.}
        return event,market,state,freeze,sessions,now

    def test_precommitted_integer_shares_fee_and_adv_safe(self):
        e,m,s,f,c,n=self.fixture();d=plan(e,m,s,f,c,n)
        self.assertTrue(d['accepted']);self.assertEqual(d['stock_shares_to_short'],199)
        self.assertLessEqual(d['stock_shares_to_short']*100,.05*m['prior_20_session_adv'])
        self.assertTrue(d['close_fill_price_does_not_set_order_size'])

    def test_receipt_delay_cannot_backdate_entry_to_filing(self):
        e,m,s,f,c,n=self.fixture();e['first_observed_utc']='2026-10-07T12:00:00+00:00';e['reviewed_utc']='2026-10-07T13:00:00+00:00'
        self.assertEqual(plan(e,m,s,f,c,n)['reason'],'not_first_observable_entry_session')

    def test_target_mixed_and_termination_never_admitted(self):
        e,m,s,f,c,n=self.fixture()
        for role,event in [('target','new_agreement'),('mixed_or_complex','new_agreement'),('acquirer','termination'),('acquirer','financing_update')]:
            e['role']=role;e['event_kind']=event
            self.assertEqual(plan(e,m,s,f,c,n)['reason'],'role_or_event_exclusion')

    def test_late_review_and_future_known_inputs_rejected(self):
        e,m,s,f,c,n=self.fixture();e['reviewed_utc']='2026-10-07T19:01:00+00:00'
        self.assertEqual(plan(e,m,s,f,c,n)['reason'],'late_or_inconsistent_evidence_times')
        e,m,s,f,c,n=self.fixture();m['cap_known_utc']='2026-10-07T20:00:00+00:00'
        self.assertEqual(plan(e,m,s,f,c,n)['reason'],'future_known_input')

    def test_missing_locate_stale_quote_and_stale_state_block(self):
        e,m,s,f,c,n=self.fixture();m['locate_available']=False
        self.assertEqual(plan(e,m,s,f,c,n)['reason'],'missing_locate_or_margin')
        e,m,s,f,c,n=self.fixture();m['stock_quote_utc']='2026-10-07T18:00:00+00:00'
        self.assertEqual(plan(e,m,s,f,c,n)['reason'],'stale_or_future_quote')
        e,m,s,f,c,n=self.fixture();m['state_known_utc']='2026-10-07T18:00:00+00:00'
        self.assertEqual(plan(e,m,s,f,c,n)['reason'],'stale_state_snapshot')

    def test_same_day_cap_and_issuer_overlap_block(self):
        e,m,s,f,c,n=self.fixture();m['cap_asof']='2026-10-07'
        self.assertEqual(plan(e,m,s,f,c,n)['reason'],'same_day_or_future_cap_adv')
        e,m,s,f,c,n=self.fixture();s['positions']=[{'cik':'123','marked_short_dollars':10000.}]
        self.assertEqual(plan(e,m,s,f,c,n)['reason'],'issuer_overlap')

    def test_prior_admission_cannot_be_retried_with_new_accession(self):
        e,m,s,f,c,n=self.fixture();s['admissions']=[{'cik':'123','decision_date':'2026-10-06'}]
        self.assertEqual(plan(e,m,s,f,c,n)['reason'],'issuer_30_day_dedupe')

    def test_adv_and_remaining_gross_reduce_actual_shares(self):
        e,m,s,f,c,n=self.fixture();m['prior_20_session_adv']=100000.
        self.assertEqual(plan(e,m,s,f,c,n)['stock_shares_to_short'],50)
        e,m,s,f,c,n=self.fixture();s['gross_short_dollars']=999000.
        s['restricted_cash']=999000.;s['positions']=[{'cik':str(i+400),'marked_short_dollars':19980.} for i in range(50)]
        self.assertEqual(plan(e,m,s,f,c,n)['stock_shares_to_short'],9)

    def test_first_session_requires_previous_session_facts(self):
        e,m,s,f,c,n=self.fixture();e['filing_utc']='2026-10-04T12:00:00+00:00';e['first_observed_utc']='2026-10-04T13:00:00+00:00';e['reviewed_utc']='2026-10-04T14:00:00+00:00'
        for field in ['stock_quote_utc','spy_quote_utc','locate_quote_utc','state_known_utc']:m[field]='2026-10-05T18:59:50+00:00'
        for field in ['cap_known_utc','adv_known_utc','history_known_utc']:m[field]='2026-10-05T12:00:00+00:00'
        m['cap_asof']='2026-10-01';m['adv_asof']='2026-10-02'
        self.assertEqual(plan(e,m,s,f,c,'2026-10-05T19:00:01+00:00')['reason'],'stale_cap_adv')

    def test_beta_history_refuses_same_day_returns(self):
        with self.assertRaisesRegex(ValueError,'Future or same-day'):
            entry_beta([{'date':'2026-10-07','stock_return':1.,'spy_return':1.}],'2026-10-07T19:00:00+00:00')

    def test_false_nav_and_omitted_short_holdings_block(self):
        e,m,s,f,c,n=self.fixture();s['free_cash']=1.1e6
        self.assertEqual(plan(e,m,s,f,c,n)['reason'],'state_balance_mismatch')
        e,m,s,f,c,n=self.fixture();s['gross_short_dollars']=10000.;s['restricted_cash']=10000.
        self.assertEqual(plan(e,m,s,f,c,n)['reason'],'position_exposure_mismatch')

    def test_early_close_cutoff_and_holiday_calendar(self):
        c=pd.read_csv(HERE/'nyse_sessions.csv',dtype=str).set_index('date')
        self.assertEqual(c.at['2026-11-27','decision_utc'],'2026-11-27T17:00:00+00:00')
        self.assertNotIn('2026-11-26',c.index);self.assertIn('2027-12-31',c.index)

    def test_journal_detects_tampering_and_backdating(self):
        f={'frozen_utc':'2026-01-01T00:00:00+00:00'}
        with tempfile.TemporaryDirectory() as tmp:
            p=Path(tmp)/'journal.jsonl'
            append(p,f,'observation',{'value':1},'2026-01-02T00:00:00+00:00')
            with self.assertRaisesRegex(RuntimeError,'backdate'):
                append(p,f,'review',{},'2026-01-01T23:00:00+00:00')
            text=p.read_text().replace('"value":1','"value":2');p.write_text(text)
            with self.assertRaisesRegex(RuntimeError,'chain mismatch'):read_journal(p,f)

    def test_missing_input_logged_as_skip(self):
        e,m,s,f,c,n=self.fixture();del m['stock_reference_price']
        self.assertEqual(plan(e,m,s,f,c,n)['reason'],'missing_input_packet')

    def test_freeze_detects_changed_code(self):
        import hashlib
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);code=root/'code.py';code.write_text('original')
            (root/'forward_freeze.json').write_text(json.dumps({'files_sha256':{'code.py':hashlib.sha256(code.read_bytes()).hexdigest()}}))
            verify_freeze(root);code.write_text('changed')
            with self.assertRaisesRegex(RuntimeError,'Frozen file changed'):verify_freeze(root)

    def test_raw_event_dedupe_uses_issuer_and_last_kept_date(self):
        raw=[{'cik':'00000123','tickers':['A'],'filing_date':d} for d in ['2022-01-03','2022-01-20','2022-02-04']]
        d=event_table(raw)
        self.assertEqual(list(d.filing_date.dt.strftime('%Y-%m-%d')),['2022-01-03','2022-02-04'])


if __name__=='__main__':unittest.main()
