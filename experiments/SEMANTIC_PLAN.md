# Earnings-text pilot, frozen before new outcomes are analyzed

- New fixed universe: AMD, ADBE, CRM, ORCL, NFLX, COST. These stocks were not in the earlier pilot.
- SEC 8-K Item 2.02 filings dated 2024-11-01 through 2026-09-30. Original earnings exhibits only, maximum 64 documents. Never ask Gemini to recall historical outcomes.
- Train on events through 2025-12-31; evaluate 2026 events once. Same market dates as earlier work, so this is a new-stock replication, not a wholly independent market regime.
- Read original earnings text; extract revenue growth, stated guidance changes, repurchases/dividends, restructuring and acquisition mentions with exact supporting quotations. Missing data remain missing; numerical surprise requires an explicit comparison and cannot be invented from model memory.
- Use a low-cost available Gemini Flash-Lite model with fixed prompt, temperature 0 and JSON schema. Save prompts, source hashes, raw outputs and token use. Maximum 64 extraction calls plus one smoke test; no web grounding or outcome data in requests.
- Volume target is next eligible full session's log-relative volume, using a trailing 20-session median. Require filing acceptance +30 minutes before 09:25 Eastern. Full filings may appear after the original press release; this studies filing-time information, not first-publication speed.
- Baseline: training-only ticker effects, lagged relative volume and return volatility. Every included event is an earnings filing, so its presence is controlled by construction.
- Fixed ridge penalty 10, training-only scaling; no tuning to test results. Compare baseline, baseline + mechanical text counts, baseline + semantic features. Report sample size, event MAE and day-block uncertainty.
- Context: French factors downloaded as ex-post attribution data, not same-day tradable features. Current FRED series are not point-in-time macro vintages; do not use revised macro observations as historical signals.
- All results are pilot forecasts, not executable trading returns. No Webull or Databento access assumed.
