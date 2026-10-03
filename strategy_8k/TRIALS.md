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

## Pre-declared sensitivity grid (2026-10-03, `grid.py`, cached data, no new API calls)
3 buckets × 2 entries × 3 OTM levels × 2 tag definitions = 36 specifications (plus the 1 headline already counted
inside it), each at 21/42/exp. Cash-secured put, events minus placebo:
- Tradeable (entry=post) cells: 54. Positive: 5. CI > 0: **0**. CI < 0: 0.
- Mean difference by bucket (all exits, post): 1m -0.54%, 2m -0.17%, 3-6m -0.10%. **Prediction 3 (stronger
  in short-dated puts) is reversed**: selling short-dated puts after exits does WORST.
- CEO+CFO only (n ≈ 44-53): uniformly negative (about -0.2% to -1.2%), none significant.
- 1m options expire before 42 sessions, so those cells are empty by construction.
Conclusion: the null result is robust, not a quirk of one parameter. Direction consistently points to exec exits
being under-priced (selling puts loses relative to ordinary days), matching the realized/implied ratio.
Trial count for the Deflated Sharpe / multiple-testing discussion: 37 specifications × 3 horizons.

## Out-of-sample, run ONCE (2026-10-03): 2026-01-01..2026-08-31, `run_window.py --label oos`
67 pooled events / 48 tickers (177 priced pairs, 22 drops); placebo 120 ordinary sessions (313 pairs, 41 drops).
A first launch crashed in the taxonomy cell (label lookup) before any OOS events or prices were requested.
(The log's "in-sample:" progress label is the notebook's hard-coded text; these are OOS events.)
Headline spec: 3-6m, entry=post, OTM 5%. Events minus placebo, 95% bootstrap CI:

| Horizon | Stock (synthetic) | Trial 1: cash-secured put | Trial 2: protective put | Long call |
|---|---|---|---|---|
| 21 | +6.8% [+1.4, +13.1]* | +0.7% [-0.4, +1.8] | +6.1% [+1.4, +11.9]* | +5.1% [+0.8, +10.1]* |
| 42 | +9.0% [+1.9, +17.1]* | +1.6% [+0.1, +3.1]* | +7.7% [+1.6, +14.9]* | +6.7% [+0.9, +12.8]* |
| 63 | +8.4% [-0.2, +16.7] | +2.5% [+0.8, +4.2]* | +5.5% [-2.4, +13.3] | +4.8% [-2.1, +11.6] |
| exp | +2.8% [-8.0, +12.2] | +1.6% [-0.4, +3.5] | -0.3% [-9.2, +6.9] | +1.6% [-7.1, +9.3] |

**Trial 1 (cash-secured put): FAILS replication.** OOS is positive (significant at 42/63) but in-sample was
negative/zero. The sign flip comes from the stock leg: exec-exit names rallied vs ordinary days in 2026, and a short
put is long delta.

**Trial 2 (protective put): FAILS its own pre-registered rule.** It is significant at 21/42 but NOT at exp (-0.3%),
and the pre-registered credit rule (option edge must exceed stock edge) fails: protective put +6.1/+7.7% <
stock +6.8/+9.0%. The put cost money relative to just holding the stock; the "edge" is 2026 post-exit stock drift,
which was not present in-sample (in-sample stock diff: 21d -0.90%, 42d +0.44%).

**What DID replicate: realized/implied ratio.** Exec-exit events moved more than the chain priced, relative to
ordinary days, in BOTH windows:
- in-sample 1-21 sessions: events 1.00-1.13 vs placebo 0.80-0.92
- OOS 5-21 sessions: events 1.28-1.43 vs placebo 0.92-1.06 (21d: 1.43 [1.08, 1.82] vs 0.99 [0.84, 1.15])
This is a measurement, not a traded edge. The natural trade is a delta-neutral long straddle, which was NOT
pre-registered and is not tested here. It is the stated next step for the sealed window.

Final trial count: 37 in-sample specs (trial 1 grid) + 1 post-hoc strategy (trial 2), each at 9 horizons;
OOS run once on the headline spec only.
