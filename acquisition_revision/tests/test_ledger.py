"""Accounting invariants and adversarial fixtures; no vendor data required."""
import sys
from pathlib import Path
import unittest

import numpy as np
import pandas as pd

sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from ledger import Config,simulate


class AccountingTests(unittest.TestCase):
    def fixture(self,stock,hold=2,**kw):
        days=pd.bdate_range('2022-01-03',periods=len(stock))
        px=pd.DataFrame({'A':stock,'SPY':100.},index=days)
        ev=pd.DataFrame({'ticker':['A'],'filing_date':[pd.Timestamp('2022-01-02')]})
        c=Config(weight=.2,hold=hold,stock_cost=0,spy_cost=0,borrow=0,debit_spread=0,fixed_beta=1,**kw)
        return days,px,ev,c

    def test_fixed_shares_not_constant_daily_weights(self):
        days,px,ev,c=self.fixture([100.,120.,150.,150.])
        d,t,e,x=simulate(ev,px,pd.Series(0.,index=days),config=c)
        self.assertAlmostEqual(d.nav.iloc[0],1.)
        self.assertAlmostEqual(d.nav.iloc[1],.96)
        self.assertAlmostEqual(d.nav.iloc[2],.90)
        self.assertAlmostEqual(d['return'].iloc[2],.90/.96-1)
        self.assertAlmostEqual(t.iloc[0].stock_quantity,-.002)
        self.assertAlmostEqual(t.iloc[-1].stock_quantity,.002)

    def test_dividend_accrual_and_later_cash_settlement(self):
        days,px,ev,c=self.fixture([100.,90.,90.,90.,90.],hold=2)
        div=pd.DataFrame({'ticker':['A'],'ex_dividend_date':[days[1]],'pay_date':[days[4]],
                          'currency':['USD'],'split_adjusted_cash_amount':[10.]})
        d,*_=simulate(ev,px,pd.Series(0.,index=days),dividends=div,config=c)
        np.testing.assert_allclose(d.nav,1.)
        self.assertAlmostEqual(d.dividend_receivable.iloc[1],-.02)
        self.assertAlmostEqual(d.dividend_cash.iloc[4],-.02)
        self.assertAlmostEqual(d.dividend_receivable.iloc[4],0.)

    def test_missing_quote_carries_mark_and_captures_resumption(self):
        days,px,ev,c=self.fixture([100.,np.nan,150.,150.],hold=1)
        d,t,e,x=simulate(ev,px,pd.Series(0.,index=days),config=c)
        self.assertAlmostEqual(d.nav.iloc[1],1.)
        self.assertAlmostEqual(d.nav.iloc[2],.90)
        self.assertIn('blocked_scheduled_exit',set(x.kind))
        self.assertEqual(t.iloc[-1].date,days[2])

    def test_fees_use_exit_marked_notional(self):
        days,px,ev,c=self.fixture([100.,120.,150.,150.])
        c.stock_cost=.001;c.spy_cost=.0002
        d,t,e,x=simulate(ev,px,pd.Series(0.,index=days),config=c)
        self.assertAlmostEqual(t.iloc[0].fee,.00024)
        self.assertAlmostEqual(t.iloc[-1].fee,.00034)
        self.assertAlmostEqual(d.nav.iloc[-1],.89942)

    def test_same_issuer_overlap_is_rejected_and_close_cap_charged(self):
        days,px,ev,c=self.fixture([100.,120.,150.,150.],hold=3,controlled=True)
        c.weight=.02;c.stock_cost=.001;c.spy_cost=.0002
        ev=pd.concat([ev,pd.DataFrame({'ticker':['A'],'filing_date':[days[0]]})],ignore_index=True)
        d,t,e,x=simulate(ev,px,pd.Series(0.,index=days),config=c)
        self.assertIn('issuer_overlap',set(e.reason))
        self.assertLessEqual(d.max_issuer_weight.max(),.02+1e-8)
        self.assertIn('issuer_trim',set(t.reason))
        self.assertGreater(t.loc[t.reason=='issuer_trim','fee'].sum(),0.)

    def test_nav_balance_identity(self):
        days,px,ev,c=self.fixture([100.,120.,150.,150.])
        d,*_=simulate(ev,px,pd.Series(.0001,index=days),config=c)
        identity=d.free_cash+d.restricted_cash+d.dividend_receivable-d.stock_short+d.spy_long
        np.testing.assert_allclose(d.nav,identity,atol=1e-12)

    def test_short_proceeds_are_not_free_cash(self):
        days,px,ev,c=self.fixture([100.,100.,100.,100.],hold=3)
        d,*_=simulate(ev,px,pd.Series(0.,index=days),config=c)
        self.assertAlmostEqual(d.free_cash.iloc[0],.8)
        self.assertAlmostEqual(d.restricted_cash.iloc[0],.2)

    def test_debit_financing_not_riskfree_credit(self):
        days,px,ev,c=self.fixture([100.,100.,100.,100.],hold=3)
        c.weight=1.;c.fixed_beta=1.5;c.debit_spread=.0365
        d,*_=simulate(ev,px,pd.Series(0.,index=days),config=c)
        self.assertAlmostEqual(d.free_cash.iloc[0],-.5)
        self.assertAlmostEqual(d.funding_cashflow.iloc[1],-.00005)

    def test_calendar_day_borrow(self):
        days,px,ev,c=self.fixture([100.]*7,hold=6)
        c.borrow=.365
        d,*_=simulate(ev,px,pd.Series(0.,index=days),config=c)
        self.assertAlmostEqual(d.borrow_fee.loc['2022-01-10'],.2*.365*3/365)

    def test_verified_cash_settlement_can_close_missing_security(self):
        days,px,ev,c=self.fixture([100.,np.nan,np.nan,np.nan],hold=2)
        settlements=pd.DataFrame({'ticker':['A'],'date':[days[1]],'split_adjusted_cash_price':[120.],
                                  'source_url':['https://example.org/verified-fixture']})
        d,t,e,x=simulate(ev,px,pd.Series(0.,index=days),settlements=settlements,config=c)
        self.assertAlmostEqual(d.nav.iloc[1],.96)
        self.assertEqual(t.iloc[-1].reason,'verified_settlement')
        self.assertEqual(d.n_events.iloc[1],0)

    def action(self,days,kind,cash=0.,successor='B',ratio=0.,cvr=0.):
        return pd.DataFrame({'ticker':['A'],'date':[days[1]],'type':[kind],
             'cash_amount':[cash],'stock_ticker':[successor],'stock_ratio':[ratio],
             'cvr_max':[cvr],'source_url':['https://example.org/verified-fixture']})

    def test_stock_cash_conversion_preserves_value_and_original_expiry(self):
        days,px,ev,c=self.fixture([100.,np.nan,np.nan,np.nan],hold=2)
        px['B']=[160.,160.,200.,210.]
        d,t,e,x=simulate(ev,px,pd.Series(0.,index=days),config=c,
                       actions=self.action(days,'stock_cash',cash=20.,ratio=.5))
        self.assertAlmostEqual(d.nav.iloc[1],1.)
        self.assertAlmostEqual(d.nav.iloc[2],.96)
        exit=t[t.reason=='scheduled_exit'].iloc[0]
        self.assertEqual(exit.stock_symbol,'B')
        self.assertEqual(exit.date,days[2])
        self.assertAlmostEqual(exit.stock_quantity,.001)

    def test_spinoff_obligation_offsets_parent_price_drop(self):
        days,px,ev,c=self.fixture([100.,80.,80.,80.],hold=2)
        px['B']=[np.nan,20.,20.,20.]
        d,t,e,x=simulate(ev,px,pd.Series(0.,index=days),config=c,
                       actions=self.action(days,'spinoff',ratio=1.))
        np.testing.assert_allclose(d.nav,1.,atol=1e-12)
        spin=t[t.reason=='spinoff_buyback'].iloc[0]
        self.assertAlmostEqual(spin.stock_notional,.04)
        self.assertEqual(d.n_events.iloc[1],1)

    def test_cvr_reserve_is_liability_not_realized_fee(self):
        days,px,ev,c=self.fixture([100.,np.nan,np.nan,np.nan])
        d,t,e,x=simulate(ev,px,pd.Series(0.,index=days),config=c,
                       actions=self.action(days,'cash',cash=100.,cvr=10.))
        self.assertAlmostEqual(d.nav.iloc[1],.98)
        self.assertAlmostEqual(d.restricted_cash.iloc[1],.02)
        self.assertAlmostEqual(d.dividend_receivable.iloc[1],-.02)
        self.assertAlmostEqual(d.trading_fee.iloc[1],0.)
        self.assertEqual(d.n_events.iloc[1],0)

    def test_renamed_symbol_cannot_bypass_issuer_overlap(self):
        days,px,ev,c=self.fixture([100.,100.,100.,100.],hold=3,controlled=True)
        px['B']=100.
        ev=pd.concat([ev,pd.DataFrame({'ticker':['B'],'filing_date':[days[0]]})],ignore_index=True)
        d,t,e,x=simulate(ev,px,pd.Series(0.,index=days),config=c,
                       actions=self.action(days,'rename',ratio=1.))
        self.assertEqual(e.iloc[1].reason,'issuer_overlap')

    def test_future_prices_do_not_change_past_positions_or_returns(self):
        days,px,ev,c=self.fixture([100.,110.,120.,130.,140.],hold=4,controlled=True)
        first=simulate(ev,px,pd.Series(0.,index=days),config=c)[0]
        altered=px.copy();altered.loc[days[3]:,'A']=200.
        second=simulate(ev,altered,pd.Series(0.,index=days),config=c)[0]
        pd.testing.assert_frame_equal(first.loc[:days[2]],second.loc[:days[2]])

    def test_insolvency_stops_instead_of_inventing_recovery(self):
        days,px,ev,c=self.fixture([100.,10000.,10000.],controlled=True)
        with self.assertRaisesRegex(RuntimeError,'insolvent'):
            simulate(ev,px,pd.Series(0.,index=days),config=c)


if __name__=='__main__':unittest.main()
