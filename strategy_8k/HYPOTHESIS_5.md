# Trials 5-7 (Massive 8-K options): leadership appointments → cash-secured put
Committed 2026-10-03 BEFORE any option price or outcome for these tags or windows was requested.
Only event COUNTS were looked at (cfo_appointment top-100: 39 in 2022-23, 34 in 2024-25; large-cap tech 6 + 7).
Prompted by guidance from the Massive workshop (CFO appointment as a CSP signal; use starred scoreboard cells; widen
the window; focus on large-cap tech). The design below turns that guidance into a test that can fail.

## Thesis (trial 5, primary)
**After a CFO-appointment 8-K at a top-100 US company, a 5% OTM cash-secured put earns more than the same trade on ordinary
days for the same names.**
Economic reason: the CFO seat is the market's main channel for financial information. While it is open (or a transition
is pending), uncertainty about guidance, capital allocation and accounting rises, and options carry a premium for it.
The appointment filing *resolves* that uncertainty, but implied volatility mean-reverts with a lag, because dealers and
hedgers keep paying for protection until realized volatility confirms calm. The put seller collects that lagging premium on
top of the ordinary variance risk premium, and the placebo nets the ordinary premium out.
Who is on the other side: holders who bought protection during the transition and roll it, and dealers pricing from
recent implied volatility.
It fails if: realized moves after appointments are as large as or larger than implied (for example, a new CFO's "kitchen-sink"
write-downs or a guidance reset), or the edge is just the ordinary variance risk premium (no gap vs placebo).

## Fixed specification (the notebook's defaults, so it matches what judges run)
Tag `cfo_appointment`; one event per (filer, filing date); TOP_100 universe; 3-6m expiry bucket; ENTRY = post (close of the
filing session); OTM 5%; fixed HORIZONS [1, 2, 3, 5, 10, 21, 42, 63, exp]; the notebook's placebo (same tickers, ordinary
sessions, 30-day gap). The API cell and all pipeline cells run unchanged; only the window and the event table are configured.

## Side trials (pre-declared, all reported)
- Trial 6: `ceo_appointment` → CSP (same spec). Same mechanism, fewer events.
- Trial 7: `cfo_departure` → CSP (same spec). The opposite situation (uncertainty opens), so we predict NO edge or a negative one.
- Sub-group (not a separate trial): the large-cap tech subset of each tag (AAPL MSFT NVDA GOOGL META AMZN AVGO ORCL CRM ADBE AMD
  CSCO IBM INTC INTU NOW QCOM TXN PLTR ACN NFLX TSLA UBER), with placebo days restricted to the same tickers. Small n, so
  descriptive only.
- Also recorded for all five strategies (every starred cell is counted, so readers see the full search space).

## Three-stage design with a fixed star rule
Key horizons: 10, 21, 42 sessions and expiry. A cell is "starred" when the 95% bootstrap CI of (events − placebo) excludes 0.
1. **Discovery, 2022-01-01..2023-12-31.** Trial 5 passes if CSP is starred with the SAME sign (positive) at >= 2 of the 4 key
   horizons. We also report the total starred cells across all tags × strategies × horizons vs the 5% expected by chance.
2. **Confirmation, 2024-01-01..2025-12-31**, run only for whatever passed discovery: the difference is positive at >= 3 of the
   4 key horizons AND at least 1 of them is starred.
3. **Final, 2026-01-01..2026-08-31**, run ONCE for the confirmed thesis: positive at >= 2 of the resolved key horizons.
If trial 5 fails discovery, we stop and report a null result; we do not search other tags for stars to replace it.
Massive trial count after this: 7.
