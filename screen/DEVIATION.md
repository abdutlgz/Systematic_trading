# Disclosed deviation from SCREEN_PLAN.md (committed BEFORE any out-of-sample run of these sleeves)

The pre-registered promotion rule promoted NO hypothesis. That verdict stands and is reported as-is.

Deviation: we ALSO run the out-of-sample test once for a combined portfolio of TSMOM + H5 (month-end Treasury)
+ H7 (term-structure-timed short vol).
Why these two: each passed every pre-registered criterion (Sharpe >= 0.40, >= 0.25 at 2x costs, positive in both
halves) except the Deflated Sharpe probability (H5 0.84, H7 0.71 vs 0.90). H5's t = 3.21 clears the Harvey-Liu-Zhu
t > 3 hurdle. No other hypothesis came within reach. The choice was made from in-sample numbers only.

Portfolio construction is exactly the pre-registered portfolio rule, unchanged: each sleeve scaled to 10% annualized
volatility using IN-SAMPLE volatility only (fixed scale factors), equal risk weights (1/3 each), and no optimization.
Sleeve rules, costs and parameters are unchanged from SCREEN_PLAN.md / strategy/HYPOTHESIS.md.
OOS 2024-10-01..2026-09-30 is run once (`python screen/portfolio.py --oos`), and every sleeve is reported
individually as well as combined, good or bad.

Because the selection used in-sample results across 15 trials, judges should discount the OOS result accordingly.
The note will report N = 15 trials, the DSR values above, and this deviation.
