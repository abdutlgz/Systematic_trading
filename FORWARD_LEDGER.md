# Forward ledger: predictions recorded BEFORE the outcome exists (written Sat 2026-10-03; last known close Fri 2026-10-02)
The git commit timestamp and the SHA-256 below (in notes/quant_note) let anyone verify this file was not edited afterwards.

## 1. Momentum strategy: live positions for October 2026 (rule: decided at the 2026-09-30 close, traded at the next close)
| ETF | SPY | EFA | EEM | IWM | TLT | IEF | GLD | DBC | UUP | VNQ |
|---|---|---|---|---|---|---|---|---|---|---|
| Weight | +0.209 | +0.175 | +0.097 | +0.170 | -0.219 | -0.369 | +0.092 | +0.113 | +0.369 | +0.188 |
Gross 2.00x, net +0.83. VIX at the 2026-09-30 close was 16.34, so the overlay is off.
Forward evaluation window: close 2026-10-02 → close 2026-10-30 (no data after 2026-10-02 existed when this was written),
then monthly by the unchanged rule. Expectation, from the in-sample financed results: mean about +0.2%/month,
P(losing month) about 45%, monthly 5% VaR about 5%. We predict nothing about this month's sign; the ledger
records the positions so live results can be compared with the backtest.

## 2. Massive "Trade the 8-K", judges' sealed window (executive exits, 3-6m options, entry = post, OTM 5%)
P1. Cash-secured put minus placebo: the 95% CI includes 0 at both 21 sessions and expiry (selling puts after exits does NOT pay).
P2. |Realized|/implied move ratio: event mean > placebo mean at 21 sessions (exits are under-priced, as in both of our windows).
P3. Protective put minus placebo is no larger than stock-only minus placebo at 21 and 42 sessions (the put adds no value).
P4 (untested trade idea, stated as a prediction only): a delta-hedged long 1-month ATM straddle on the filer, entered at the
    filing-session close and held 21 sessions, earns more than the same trade on placebo days.

## 3. Strategies we expect NOT to work going forward (from failed OOS tests)
Month-end Treasury extension (H5), timed short vol (H7), and the exec-exit cash-secured put: each failed its OOS test, so we
expect live Sharpe <= 0.3.
