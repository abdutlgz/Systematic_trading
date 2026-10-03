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
