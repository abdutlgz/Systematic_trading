# Trial log (every variant run, for the Deflated Sharpe Ratio)

| # | Variant | Pre-registered? | IS net Sharpe | IS max DD |
|---|---|---|---:|---:|
| 1 | Base TSMOM, 12m lookback | yes (primary) | 0.250 | -29.4% |
| 2 | 12m + VIX>30 half-exposure overlay | yes (primary extension) | 0.257 | -28.3% |
| 3 | Base, 3m lookback | yes (plateau) | 0.180 | -44.0% |
| 4 | Base, 6m lookback | yes (plateau) | 0.304 | -30.9% |
| 5 | Base, 9m lookback | yes (plateau) | 0.262 | -32.7% |
| 6 | #2 and #1 at 2x costs (20 bps/side) | yes (sensitivity, not a new strategy) | 0.198 / 0.199 | |
| D | Same-bar execution (lookahead bug, diagnostic only) | yes | 0.306 | |
| P | 200 random-sign placebos (luck benchmark) | yes | mean -0.27, p95 0.10 | |

Distinct strategy trials N = 5. A conservative N = 20 also counts the earlier pilot models in experiments/.
In-sample run 2026-10-02. OOS NOT yet evaluated. No parameter was changed after seeing IS results.
Implementation notes made during IS work (no effect on the strategy rule): FRED CSV timed out, so VIX comes from
Yahoo ^VIX (the same CBOE close); the simulator was vectorized and reproduces identical numbers.

## Out-of-sample, run ONCE (2026-10-03): 2024-10-01..2026-09-30, `run_all.py --oos`, no spec changes
| | Ann. return | Vol | Sharpe | t | Max DD | Turnover/yr |
|---|---:|---:|---:|---:|---:|---:|
| 1 Base 12m, OOS | 11.2% | 12.6% | 0.90 | 1.28 | -12.6% | 7.3x |
| 2 VIX overlay 12m, OOS | 11.2% | 12.6% | 0.90 | 1.28 | -12.6% | 7.3x |
| 2 at 2x costs, OOS | 10.4% | 12.6% | 0.85 | 1.19 | -12.7% | 7.3x |
In-sample numbers reproduced exactly.
- The overlay NEVER triggered OOS: VIX closed above 30 on 14 days (peak 52.3 on 2025-04-08), but no month-end
  close was above 30 (max 25.2). Monthly checks miss intra-month spikes. This is a known limitation of the spec,
  not changed after the fact.
- OOS factor regression (to 2026-08-31): alpha -0.4%/yr (t -0.07), Mkt beta 0.50, Mom 0.09. OOS return is
  explained by equity-market exposure (trend was long equities in a rising market), not by alpha.
- Calendar years: 2024 +8.0%, 2025 +14.5%, 2026 YTD +12.1%.
- Two years is short: Sharpe t-stat 1.28. OOS Sharpe 0.90 > IS 0.26 is most likely regime luck, not improvement.
