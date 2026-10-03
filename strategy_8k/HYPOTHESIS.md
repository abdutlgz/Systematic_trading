# Pre-registered hypothesis (Massive "Trade the 8-K" bonus): executive exits → cash-secured put

Written and committed 2026-10-02/03, BEFORE any option prices or outcomes for these events were requested.
Only per-tag event COUNTS (no prices or returns) were looked at to check sample size.

## Hypothesis
After an 8-K discloses an unscheduled executive departure at a top-100 US company, put buyers overpay for crash
protection. A leadership exit is vivid, ambiguous news: hedgers and nervous holders bid up downside puts. But for
mega-caps the realized move is usually small, because the bench is deep, successors are often named, and the
business does not change overnight. So selling a 5% OTM put after the filing earns more than the same trade on
ordinary days for the same names. That gap is the event premium on top of the ordinary variance risk premium.

**Who is on the other side:** holders and hedgers buying protection after a salient but mostly non-fundamental
headline (behavioral overreaction / demand pressure on puts, Garleanu, Pedersen & Poteshman 2009).
**Why it persists:** dealers who absorb put demand charge for inventory risk, and the event is unscheduled, so
there is no calendar for supply to line up against.

## Fixed specification
- Events: Massive 8-K tertiary tags `ceo_departure` + `cfo_departure` + `executive_officer_departure`, pooled.
  One event per (ticker, filing date). If the same ticker has more than one pooled tag within 5 calendar days,
  keep the first.
- Universe: the notebook's static TOP_100 (survivorship caveat disclosed).
- Strategy: 5 · cash-secured put, short the put about 5% below spot (OTM_PCT = 0.05).
- Headline: 3-6m expiry bucket, ENTRY = "post" (close of the filing session, which can be traded), fixed horizons
  [1, 2, 3, 5, 10, 21, 42, 63, exp].
- Baseline: the notebook's placebo (same tickers, ordinary sessions, the gap rule) using the identical measurement.
- Windows: in-sample 2024-01-01..2025-12-31; out-of-sample 2026-01-01..2026-08-31 (run once); the sealed window
  belongs to the judges.

## Testable predictions
1. Cash-secured put mean P&L (events minus placebo) > 0 at the 21, 42 and expiry horizons in-sample, with the same
   sign out-of-sample.
2. |realized| / implied move ratio for events is BELOW the placebo's at 21+ sessions (the market over-priced it).
3. The effect should be stronger in the 1m bucket than in 3-6m (event premium concentrated in short-dated puts).
   This is a secondary prediction.

**It fails if:** the difference CI includes 0 at all of 21/42/exp, or the sign flips OOS, or the result is driven by
1-2 events (checked by dropping the largest 2).

## Pre-declared sensitivity grid (all reported, counted as trials)
OTM 3/5/10% × buckets 1m/2m/3-6m × entry pre/post × tag definition (all three pooled vs CEO+CFO only).
