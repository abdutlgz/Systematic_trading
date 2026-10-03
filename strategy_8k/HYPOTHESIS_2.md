# Trial 2 (POST-HOC, registered after seeing in-sample results): executive exits → protective put

Registered 2026-10-03, AFTER the in-sample run and sensitivity grid, BEFORE any out-of-sample (2026) data is requested.
This is a second hypothesis motivated by in-sample data. It must be judged mainly on out-of-sample replication.

## Motivation (from in-sample, see TRIALS.md)
After executive-exit 8-Ks the realized/implied move ratio was 1.00-1.13 vs 0.80-0.92 on ordinary days, and selling
puts lagged ordinary days in 49/54 tradeable specs (none significant). Reading: the chain under-prices post-exit
uncertainty because leadership change is hard to model, and dealers price it like an ordinary day.

## Fixed specification (identical to trial 1 except the strategy)
- Same pooled events, universe, dedupe rule, 3-6m bucket, entry = post, OTM 5%, fixed horizons, placebo design.
- Strategy: 3 · protective put (synthetic stock + long 5% OTM put). Long call is reported alongside as a check.
- OOS window: 2026-01-01..2026-08-31, run ONCE for both trial 1 (cash-secured put) and trial 2.

## Predictions for OOS
1. Protective put minus placebo > 0 at 42 and exp (in-sample: 21d -0.59%, 42d +0.41%, exp +0.92%, none significant).
2. Event realized/implied ratio above the placebo's.
Because the stock leg dominates a protective put, a positive result is credited to the OPTION only if the protective-put
edge exceeds the stock-only edge over placebo at the same horizon.
It fails if the OOS difference is <= 0 or its CI is entirely below 0.
