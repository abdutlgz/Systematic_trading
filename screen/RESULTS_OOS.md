# Portfolio OOS, run ONCE (2026-10-03): 2024-10-01..2026-09-30, `python screen/portfolio.py --oos`
Scale factors fixed from in-sample: H5 1.94, H7 0.65, TSMOM 0.90. Equal risk weights. No changes after IS.

| Sleeve / portfolio | IS Sharpe (2011-2024) | OOS Sharpe | OOS ann. return | OOS max DD |
|---|---:|---:|---:|---:|
| H5 Month-end Treasury | 0.64 | **-0.29** | -2.5% | -16.7% |
| H7 Timed short vol | 0.62 | **+0.11** | +0.6% | -11.3% |
| TSMOM | 0.26 | +0.90 | +10.1% | -11.4% |
| **Portfolio (equal risk)** | **0.85** (t 3.13) | **+0.46** (t 0.64) | +2.8% | **-6.4%** |
| Portfolio at 2x costs | 0.66 | +0.29 | +1.7% | -6.8% |

- **Neither near-miss sleeve replicated.** H5 lost money and H7 was about flat. The Deflated Sharpe warning
  (0.84 / 0.71 < 0.90) was right: in-sample Sharpe 0.6+ chosen from 15 trials did not survive.
- The portfolio stays positive OOS with half the drawdown of TSMOM alone (-6.4% vs -12.6%), but its Sharpe (0.46)
  is BELOW TSMOM alone (0.90). Diversification lowered risk but also diluted the one sleeve that worked.
- OOS factor regression: alpha -4.8%/yr (t -1.64), market beta 0.27. No evidence of alpha OOS.
- Two years is short (OOS t-stats below 1.3 for everything), so none of these OOS numbers is decisive.
- Conclusion for the note: the pre-registered rule (promote nothing) was the correct call. The deviation is reported
  as a cautionary result.
