# 8-K event grid search with multiple-testing control (committed 2026-10-03 BEFORE running any configuration below)
Goal (organizer guidance): find the single most statistically significant strategy. The search is wide, so significance is only
claimed AFTER correcting for every configuration tried.

## Search space (every cell reported)
Event definitions (Massive 8-K tags, all US filers, one event per filer per tag per 30 days):
cfo_departure, cfo_departure[ABRUPT], ceo_departure, ceo_departure[ABRUPT], executive_officer_departure, director_departure,
cfo_appointment, ceo_appointment, workforce_reduction, restructuring_plan, share_repurchase_program, dividend_policy_change,
guidance_issuance_or_update, goodwill_impairment, material_charge_or_gain, material_litigation, regulatory_investigation,
settlement_agreement, cybersecurity_incident, acquisition_agreement, divestiture_agreement, deal_termination, public_offering,
debt_issuance, credit_rating_change, auditor_dismissal, auditor_resignation, internal_control_weakness, financial_restatement,
strategic_initiative, significant_contract_award, regulatory_decision;
combinations: CEO_AND_CFO = a ceo_departure and a cfo_departure from the same filer within 90 days (entry at the later one);
LAYOFF_THEN_CFO = cfo_departure within 90 days AFTER a workforce_reduction/restructuring_plan (the same as V3, size permitting).
ABRUPT uses the HYPOTHESIS.md keyword rule.
× holding period {20, 60, 120} sessions × size filter {>= $2B, >= $10B} (point-in-time market cap on the day before filing).

Trade mechanics: identical to strategy B (enter at the close of the first session strictly after the filing date; 2% per event;
SPY beta hedge; 100% gross cap; 10 bps stock / 2 bps SPY per side; 1%/yr borrow on shorts). Direction: long or short, set by the
sign of the in-sample mean (two-sided tests account for this).

## Selection on in-sample only (2022-01-01..2025-09-30)
- Valid cells: >= 40 in-sample events. Statistic: portfolio Sharpe t-stat (Sharpe × sqrt(years)), two-sided p-value.
- Multiple-testing control across ALL valid cells: Benjamini-Hochberg-Yekutieli FDR 5% (valid under dependence), plus a deflated
  Sharpe with N = number of valid cells.
- **Winner = the highest in-sample t among cells that survive BHY.** If none survive, the winner is the highest deflated-Sharpe cell,
  and we state plainly that nothing is significant after correction.
- Robustness required for the winner (reported): same sign in both IS halves; random-date placebo share < 5%; neighbouring holding
  periods with the same sign.

## Out-of-sample
2025-10-01..2026-09-30, run ONCE for the winner only. Disclosure: this window was evaluated once before (strategy B V2, Sharpe +0.32);
the winner is chosen without looking at it.
