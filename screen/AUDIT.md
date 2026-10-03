# Nine-pitfall statistical audit (`python screen/audit.py`, in-sample unless marked OOS)

| # | Pitfall | Test | Result | Verdict |
|---|---|---|---|---|
| 1 | P-hacking | Bonferroni / Holm / BHY on 15 trial t-stats; HLZ t > 3 | Only H5 survives Holm (p 0.02) and t > 3; nothing survives BHY. TSMOM t = 1.05 alone. | Disclosed. No strategy is significant after the strictest correction; H5 is borderline and failed OOS |
| 2 | Overfitting | CSCV probability of backtest overfitting, 15 trials, 164 months, 12,870 splits | PBO = 0.21; IS winner Sharpe 0.92 → OOS 0.40 | Selection process is not mostly luck, but expect about half the IS Sharpe |
| 3 | Lookahead | Execution lag 0 / 1 / 2 / 5 bars; H5 window ±1 day | TSMOM 0.31 / 0.26 / 0.21 / 0.25; H7 0.81 / 0.63 / 0.74 / 0.67: smooth, no collapse. H5: 0.67 as specified, **0.12 one day earlier**, 0.41 one day later | No leakage. H5 is concentrated on the final days (consistent with month-end index flows) and fragile to timing |
| 4 | Survivorship | ETF inception vs sample start | All ETFs listed before use; broad indices, none delisted | Low. Residual: the ETF menu is chosen today. Massive top-100 list is static (bias acknowledged) |
| 5 | Costs | Break-even cost per side vs assumed | TSMOM 54 bps (5.4x assumed); H5 19 bps (3.9x); H7 209 bps (21x); H1, H3, H9 break even BELOW realistic costs | TSMOM/H5/H7 robust to costs; overnight, weekly reversal and sector momentum die on costs |
| 6 | Test-set leakage | git commit order | Every spec committed before its results; strategy/HYPOTHESIS.md has never been edited (1 commit); deviation committed before its OOS | Clean, with one disclosed deviation |
| 7 | Misleading Sharpe | Monthly Sharpe ± SE, PSR, skew/kurtosis, CVaR | TSMOM OOS 0.94, 95% CI [-0.48, +2.35]; Portfolio IS 0.94 [+0.40, +1.48]; H7 daily skew -1.81; H5 kurtosis 31 | OOS Sharpes are too short to be conclusive. H7 has short-vol tail risk: its largest loss day was -10.8% of sleeve capital (VIXY +43% on 2024-08-05) |
| 8 | Regime dependence | Best-year share of gains; Sharpe ex best year; ex 2008/2020/2022; VIX > 25 vs ≤ 25 | Best year is about 15-17% of gains for all. TSMOM ex best 0.26; H5 0.48; H7 0.46. TSMOM: VIX>25 -0.07 vs 0.46 calm; H7: 1.29 vs 0.45 | No single-year dependence. TSMOM earns in calm trends, not crises (no crisis alpha in this sample) |
| 9 | Capacity | Square-root impact at $10M / $100M | SPY < 2 bps; TLT 7 / 23 bps; VIXY **74 / 233 bps**; UUP 0.9x ADV and DBC 1.1x ADV at $100M | TSMOM ≈ $50M (UUP/DBC bind); H7 capacity ≈ a few $M (VIXY ADV only $73M); H5 scales to $100M+ |
