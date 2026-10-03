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
