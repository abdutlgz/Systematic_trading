# Trial log: 8-K executive exits (in-sample 2024-01-01..2025-12-31)

Run 1, 2026-10-03, pre-registered spec (3-6m bucket, entry=post, OTM 5%). 189 pooled events / 77 tickers;
485 priced (event, bucket) pairs, 66 drops; placebo 120 ordinary sessions.
(The notebook's printed labels say "cfo_appointment": that's the unused EVENT_TAG default, cosmetic only. The event
table is the pooled exec exits.)

**Prediction 1 (cash-secured put beats ordinary days): NOT supported.** Events minus placebo:
21d -0.38% [-1.00, +0.25], 42d +0.10% [-0.89, +1.06], exp +0.11% [-1.23, +1.47]. No CI excludes 0.

**Prediction 2 (realized < implied vs placebo): OPPOSITE.** Mean |realized|/implied ratio for events is
1.00-1.13 at 1-21 sessions vs 0.80-0.92 for the placebo; the event CIs sit mostly above the placebo's.
Exec-exit names moved MORE than the chain priced, which runs against the put-overpricing story. Any long-vol
follow-up is a NEW, post-hoc hypothesis and will be labeled as such.

In-sample ranking (edge over placebo, avg of 21/42/exp): protective put +0.25%, long call +0.17%, collar -0.03%,
cash-secured put -0.06%, covered call -0.35%. None significant at any horizon.

Trials so far: 1 (pre-registered). The pre-declared sensitivity grid is next.
