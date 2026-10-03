# Strategy B, in-sample 2022-01..2025-09 (pre-registered rule applied unchanged)
| Variant | Sharpe | Ann. ret | Vol | Max DD | Trades | Halves |
|---|---:|---:|---:|---:|---:|---|
| **V2 abrupt (primary)** | **0.52** | 2.2% | 4.4% | -5.1% | 216 | 0.25 / 0.80 |
| V4 planned control | -0.11 | -0.6% | 4.4% | -7.2% | 294 | -0.26 / 0.01 |
| V1 all departures | -0.12 | -1.7% | 10.2% | -15.2% | 738 | -0.04 / -0.23 |
| V3 distress (abrupt + layoffs in prior 90d) | untestable: 4 events at >= $2B | | | | | |
| V2 hold 20 / 120 (sensitivity) | 0.11 / 0.58 | | | | | |
**Rule: PASS** (Sharpe >= 0.4, positive short return, beats control, both halves positive).
**But weak evidence:** random-date placebo on the same tickers beats it 9% of the time (mean 0.03, 95th pct 0.65); deflated Sharpe
probability 0.59 (N = 5); per-event 60d hedged return +1.92% (median +2.03%) with t = 1.33 (n = 216). Average gross short is only 27%
(max 46%), so the return on deployed capital is about 8.4%/yr. Yearly: 2022 +2.2%, 2023 -2.1%, 2024 +6.7%, 2025 YTD +1.4%.
OOS 2025-10..2026-09 is run next, ONCE, per the protocol.

## OOS 2025-10-01..2026-09-30, run ONCE (`python event8k/backtest.py --oos`), no changes after IS
| Variant | OOS Sharpe | Ann. ret | Vol | Max DD | New trades |
|---|---:|---:|---:|---:|---:|
| **V2 abrupt (primary)** | **+0.32** | +1.6% | 5.2% | -4.9% | 54 |
| V4 planned control | -0.69 | -3.4% | 4.8% | -6.8% | 67 |
| V1 all departures | -0.02 | -0.8% | 10.7% | -11.1% | 155 |
Same sign as IS, and V2 again beats the control (spread V2 - V4: IS +2.8%/yr, OOS +4.9%/yr). But the per-event mean of OOS-entered
trades is about 0 (t = -0.07, n = 54); part of the OOS return comes from positions opened in late IS and still held. Verdict: weakly
consistent, not significant. Short-selling after abrupt CFO exits beats short-selling after retirements in both periods, which is the
cleanest part of the result. Note: OOS overlaps the Jan-Aug 2026 window where exec-exit names rallied (known in advance; that works
against this short, and the strategy still stayed positive).
