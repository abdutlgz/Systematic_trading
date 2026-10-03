# Trial 8 (FOLLOW-UP, chosen from 2022-23 discovery data): CFO appointment → cash-secured put held to EXPIRY
Committed 2026-10-03 AFTER trial 5's discovery run (2022-23) and BEFORE any 2024-25 or 2026 data for cfo_appointment was requested.
Disclosure: the horizon (expiry) was picked because it was the strongest, nearly starred cell in discovery
(+2.34%, 95% CI [-0.31%, +5.06%], n = 31). Discovery therefore cannot count as evidence. Only the stages below can.

Economic reading: the uncertainty premium in 3-6m puts written after a CFO appointment decays over the option's whole life, not in
the first weeks, because the new CFO's first earnings call and guidance (usually 1-3 months later) is when the uncertainty actually
resolves. So the put seller's edge should show up at expiry, not at 10-21 sessions.

Spec: identical to trial 5 (tag cfo_appointment, top-100, 3-6m bucket, entry = post, OTM 5%, notebook placebo, API cell unchanged).
Primary metric: CSP events minus placebo at horizon "exp".

1. Confirmation, 2024-01-01..2025-12-31 (never requested for this tag). PASS if the exp difference is > 0 AND starred
   (95% bootstrap CI excludes 0). WEAK if > 0 but not starred. FAIL if <= 0.
2. Final, 2026-01-01..2026-08-31, run ONCE, only if step 1 is PASS or WEAK. Many 2026 options have not expired yet, so the
   exp horizon only covers resolved events. We report the exp and 63-session differences; consistent = both > 0.
Massive trial count after this: 8.
