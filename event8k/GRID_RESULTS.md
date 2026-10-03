# 8-K grid results, in-sample 2022-01..2025-09 (GRID_PLAN.md applied unchanged; `python event8k/grid.py`)
Search: 34 event definitions × 3 holds × 2 size filters = 204 cells; 165 valid (>= 40 IS events).
**Survive BHY 5%: 0. Survive Holm 5%: 0.** The highest |t| is 1.90 (p = 0.058, uncorrected).
Winner by the pre-registered fallback rule (highest deflated-Sharpe probability): **acquisition_agreement, >= $2B, 60-session hold,
SHORT** (hedged with SPY). IS Sharpe 0.98, t 1.90, DSR 0.67, halves 1.17 / 0.70, 732 events, average gross 86%.
Neighbours: 120-session hold 0.88; >= $10B / 120 sessions 0.83.

Top 10 by p-value (all short, all hedged): acquisition_agreement 2B/60 0.98; internal_control_weakness 2B/20 0.92;
acquisition_agreement 2B/120 0.88; CEO_AND_CFO 2B/60 0.88; financial_restatement 2B/20 0.87; acquisition_agreement 10B/120 0.83;
divestiture_agreement 10B/20 0.83; auditor_dismissal 2B/20 0.80; ceo_departure 2B/60 0.76; divestiture_agreement 10B/60 0.76.
Strategy B's cfo_departure[ABRUPT] is not in the top 15 under this grid's mechanics.

Caveat to test: nearly every top cell is a SHORT hedged with cap-weighted SPY. In 2023-24 mega-cap tech drove SPY far above the average
stock, so "short any $2B stock / long SPY" may earn money regardless of the event. Random-date placebo on the winner: see below.

## Winner diagnostics (in-sample, before OOS)
- **Random-date placebo** (the same 732 tickers, random dates, short + SPY hedge, 100 runs): mean Sharpe **-0.53**, 95th pct -0.13; **0%**
  reach the winner's 0.98. So the mega-cap/SPY explanation is ruled out: on ordinary dates these stocks BEAT their hedge.
- **Decomposition** (per event, 60 sessions): stock -0.07%, beta × SPY +2.61%, so a short-hedged P&L of +2.67% (event-level t 4.66,
  overlapping dates, so overstated; the portfolio-level t of 1.90 is the honest one).
  Likely deal targets (post-announcement vol < 50% of pre-vol): n = 43, +0.85%. Others (mostly acquirers): n = 689, **+2.79%**.
- **Economic reading:** acquirers that sign deals then lag the market for about 3 months (overpayment / winner's curse, Roll 1986;
  post-merger underperformance, Loughran & Vijh 1997; Moeller, Schlingemann & Stulz 2005). It is a known anomaly re-found by a
  blind search, which is reassuring for the pipeline but limits its novelty.
