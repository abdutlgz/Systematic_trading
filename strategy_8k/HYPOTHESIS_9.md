# Trial 9: executive exits → LONG ATM straddle (committed 2026-10-03 BEFORE any 2022-23 straddle P&L was computed)
Motivation (disclosed): the measurement that replicated in 2024-25 and 2026: after exec-exit 8-Ks, realized moves exceed the
chain's implied move relative to placebo days. So the trade is to BUY volatility. Untested until now.
Data overlap: the 2022-23 cfo_departure events (25 of the pool) were used for the trial 7 CSP discovery run. Straddle P&L was
never computed on any 2022-23 event, and ceo_departure and executive_officer_departure for 2022-23 were never requested.

Trade: buy the ATM call + ATM put (the strike nearest the parity spot, same expiry) at the close of the filing session (entry = post);
mark at the fixed horizons. P&L per $1 of spot = (ΔC_K + ΔP_K) / S_entry. Unhedged; an ATM straddle is about delta-neutral at entry.
Events: pooled ceo_departure + cfo_departure + executive_officer_departure, top-100, one per ticker per 5 days (same as H-A).
Comparison: the notebook's placebo (same tickers on ordinary days), with the identical trade.
Costs: daily bars are last trades, not quotes, so we charge a round-trip 4% of the straddle premium (2% half-spread per side,
conservative for top-100 ATM options) to both events and placebo, and report net P&L.

Primary test: 1m expiry bucket (21-45 DTE), horizon 21 sessions (about the option's life). PASS if events minus placebo > 0 AND starred
(95% bootstrap CI excludes 0). WEAK if > 0 and not starred. FAIL if <= 0.
Secondary (reported, not the pass criterion): 1m bucket at 5/10 sessions; 3-6m bucket at 21/42 sessions.
Window: 2022-01-01..2023-12-31, run ONCE. Massive trial count after this: 9.
