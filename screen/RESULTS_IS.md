# Screen results, in-sample only (run 2026-10-03; data before 2024-10-01). Pre-registered rule applied unchanged.

| Hypothesis | Net Sharpe | 2x costs | Halves | t | Max DD | Turnover/yr | DSR prob (N=15) | Rule |
|---|---:|---:|---|---:|---:|---:|---:|---|
| H5 Month-end Treasury extension | **0.68** | 0.45 | 0.75 / 0.62 | **3.21** | -13% | 24x | 0.84 | fails DSR >= 0.90 only |
| H7 Term-structure-timed short vol | **0.63** | 0.60 | 0.96 / 0.35 | 2.34 | -25% | 4.9x | 0.71 | fails DSR only |
| H10 Pre-FOMC drift | 0.47 | 0.25 | 0.79 / **0.06** | 1.91 | -8% | 16x | 0.49 | fails (decayed, as in the literature after 2015) |
| H4 Turn-of-month | 0.27 | 0.12 | 0.29 / 0.25 | 1.37 | -19% | 24x | 0.15 | fails |
| H6 Treasury auction cycle | 0.24 | 0.09 | 0.34 / 0.16 | 1.04 | -23% | 31x | 0.16 | fails |
| H2 BAB on sectors | 0.16 | 0.15 | 0.08 / 0.36 | 0.80 | -79% | 5x | 0.06 | fails |
| H1 Sector momentum | -0.01 | -0.05 | 0.01 / -0.04 | -0.06 | -50% | 12x | 0.01 | fails |
| H3 Overnight drift | -0.15 (gross +) | -1.05 | -0.24 / -0.05 | -0.75 | -72% | 504x | 0.00 | fails: costs kill it |
| H8 FX carry (CurrencyShares) | -0.18 | -0.20 | -0.28 / -0.03 | -0.74 | -49% | 2x | 0.00 | fails |
| H9 Weekly sector reversal | -0.23 | -0.66 | 0.06 / -0.62 | -1.16 | -85% | 137x | 0.00 | fails |

**Promoted under the pre-registered rule: none.** H5 and H7 pass every criterion except the Deflated Sharpe
probability (0.84 and 0.71 vs the 0.90 threshold). H5's t-stat of 3.21 clears the Harvey-Liu-Zhu t > 3 hurdle.
Daily-return correlations: H5 vs TSMOM 0.02, H7 vs TSMOM 0.22, H5 vs H7 -0.08, so they diversify well.
Data notes: FRED rejects browser user-agents (fixed). The FOMC parser was corrected before the screen ran
(it had dropped projection meetings and month-spanning meetings), which gives 159 scheduled meetings for 2008-2027.
