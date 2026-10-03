# Pre-registered trials 3 and 4 (Massive 8-K options). Committed 2026-10-03 BEFORE any option prices for these events.
Only event COUNTS were inspected (to check feasibility and materiality).

## Ideas from the brief that are NOT tested, and why (no data is fabricated)
- Satellite parking-lot traffic / cloud cover, job-posting growth, B2B invoice timeliness, product-review sentiment:
  no historical, point-in-time dataset is available to us before the deadline (all are paid vendor feeds:
  Orbital Insight/RS Metrics, LinkUp/Revelio, Dun & Bradstreet/Creditsafe, review scrapes). Listed as next steps.
- "Contract win + hiring growth → calls": only 3 in-sample `significant_contract_award` events in the top 100, and no
  hiring data. Not testable.

## Trial 3: competitor spillover → long call on the peer
**Hypothesis.** When a company discloses an operational disruption (cyber incident, natural disaster, facility closure,
exit from a business line, bankruptcy, going-concern doubt), demand shifts to close competitors. Investors focus on
the troubled firm and are slow to price the spillover to rivals: limited attention / slow cross-firm information
diffusion (Cohen & Frazzini 2008 "Economic links"; Hou 2007). So competitors' upside is under-priced.
- Events: Massive tags cybersecurity_incident, natural_disaster_impact, facility_closure, business_line_exit,
  voluntary_bankruptcy, going_concern, at ANY filer.
- Competitor map: top-100 names with the same SEC 4-digit SIC code as the filer (SEC submissions; current snapshot,
  SIC rarely changes; disclosed). A company is never its own peer.
- Materiality: filer market cap >= $1B on the day before filing (Massive point-in-time reference data).
- Unit: one event per (peer ticker, filing date). Peer events from the same filing are clustered, so uncertainty is
  also reported with a filing-level cluster bootstrap.
- Strategy: 1 · long ATM call on the PEER. Headline: 3-6m bucket, entry=post, fixed horizons, placebo.
- Prediction: long call (events minus placebo) > 0 at 21/42 sessions, and the peer's stock-only difference > 0.
  Fails if the CIs include 0 at both 21 and 42, or the sign flips OOS.

## Trial 4: settlement / resolution → cash-secured put
**Hypothesis.** A settlement 8-K resolves a known legal overhang. Implied volatility still carries the litigation
premium on the filing day, and realized volatility falls afterwards, so sold puts earn more than on ordinary days.
- Events: `settlement_agreement` tag, top-100 filers (24 in-sample events, a small sample, disclosed).
- Strategy: 5 · cash-secured put, OTM 5%, 3-6m, entry=post. Prediction: CSP minus placebo > 0 at 21/42/exp AND the
  realized/implied ratio is below the placebo's. Fails if both conditions fail or the sign flips OOS.

Windows: IS 2024-01-01..2025-12-31, OOS 2026-01-01..2026-08-31 (run once each). Trial count after this: 4 Massive
hypotheses (exec-exit CSP, exec-exit protective put, these two).
