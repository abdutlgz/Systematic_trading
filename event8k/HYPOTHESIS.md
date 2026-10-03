# Main-track strategy B: abrupt CFO departures → short the stock, market-hedged
Committed 2026-10-03 BEFORE any stock price for these events was downloaded. Only event counts and filing text were inspected
(4,621 cfo_departure 8-Ks in 2022-2026; 287 with a layoff/restructuring 8-K within ±90 days; AI/automation mentions too rare
to test: 7 workforce-reduction and 20 restructuring filings).

## Hypothesis and counterparty
The CFO sees the numbers first. An abrupt, unplanned CFO exit (effective immediately, interim replacement, "pursue other
opportunities", termination) is disproportionately followed by negative news: earnings misses, guidance cuts, write-downs,
restatements (Mian 2001; Hennes, Leone & Miller 2008; Bushman et al.). Investors under-react, because the 8-K wording is boilerplate
("not the result of any disagreement") and is lumped in with routine retirements. Prices drift down over the following quarter as
the news arrives. The other side: holders who read the departure as routine, plus index and passive owners who do not trade on it.
Why it persists: the information is soft (text, not numbers), shorting has costs and limits, and each event is small and idiosyncratic.
Distress cluster: a departure in a firm that has ALREADY announced layoffs or restructuring (within the prior 90 days) is more likely
to signal trouble than a career move.
**Prediction:** abrupt departures → negative market-adjusted drift over 60 sessions; planned retirements → no drift (control).
**It fails if:** the abrupt subset does not earn positive short returns in-sample, or the control earns as much, or the OOS sign flips.

## Data and universe
- Events: Massive 8-K disclosures, tag `cfo_departure`, all US filers, 2022-01-01..2026-09-30 (taxonomy coverage starts 2022).
  One event per filer per 30 days.
- Universe: filer market cap >= $2B on the day before filing (Massive point-in-time reference data). That excludes micro-caps, and
  delisted firms remain in the sample (no survivorship filter on the event side).
- Prices: Massive daily bars (split/dividend adjusted), SPY as the hedge.
- Text classes (from `supporting_text`, keyword rules fixed now):
  ABRUPT = matches (immediate|interim|terminat|other opportunit|pursue other|without cause|for cause|mutual|separation)
           AND does not match (retire).
  PLANNED (control) = matches (retire) AND not ABRUPT.
  DISTRESS = ABRUPT and the same filer has a workforce_reduction or restructuring_plan 8-K filed in the 90 days BEFORE (never after).

## Trade (fixed)
Entry at the close of the first session strictly AFTER the filing date (8-Ks can be accepted after the close; no same-day trading).
Short the stock at 2% of capital per event, and hedge with long SPY = beta × 2% (beta from sessions -260..-11, clipped to [0.5, 1.5]).
Hold 60 sessions, then exit at the close. Gross short exposure is capped at 100% of capital (new events are skipped while full).
Costs: 10 bps per side on stocks, 2 bps on SPY, 1.0%/yr borrow fee on the short notional; idle cash earns the T-bill rate and the
SPY hedge is financed at the T-bill rate (net zero).

## Variants (pre-declared; all reported; N = 4 for the deflated Sharpe)
V1 all departures · **V2 ABRUPT (primary)** · V3 DISTRESS · V4 PLANNED control (predicted about 0).
Holding-period sensitivity for V2 (not separate trials): 20 and 120 sessions.

## Split (track rule: the most recent 20% or 2 years, whichever is shorter)
4.75 years of data, so 20% = 0.95 years binds. **IS 2022-01-01..2025-09-30; OOS 2025-10-01..2026-09-30, run ONCE.**
Disclosure: our Massive options study already showed (stock-only line) that pooled exec-exit names ROSE vs ordinary days in
Jan-Aug 2026. That knowledge works AGAINST this short hypothesis. Nothing in this spec is tuned to it.
**Pass (IS):** V2 net Sharpe >= 0.4, with a positive short return (stock underperforms its hedge), V2 > V4, and positive in both IS halves.
