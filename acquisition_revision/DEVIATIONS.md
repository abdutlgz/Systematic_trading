# Recorded implementation deviations

## Placebo date feasibility

After the frozen-date feasibility check, seven eligible event records had no ordinary-date pool satisfying available entry quotes and the +/-90-day acquisition exclusion. Instead of weakening the exclusion or dropping them only from controls, the runner removes these issuers from BOTH the observed comparison and every placebo. It reports the removed tickers/count, matched event count and matched observed Sharpe. The main candidate's full-universe metrics remain unchanged. This is a feasibility correction, not parameter selection. Placebo results cannot be compared directly with the full-universe IS Sharpe or described as an untouched validation.

## Corporate-action corrections discovered during accounting audit

The first accounting run carried stale marks through completed mergers and ticker changes. Those provisional outputs were discarded. The source-linked `corporate_actions.csv` journal now specifies verified cash settlements, one-for-one ticker identity changes, stock/cash successor obligations and FBHS's MBC distribution. The journal describes return accounting; it does not filter entry signals or choose profitable cases. Identity histories are joined only for verified one-for-one renames. Stock conversions preserve the original expiry and paired hedge.

Cash-merger liabilities and the paired SPY hedge are settled at the event session's close. Actual broker settlement timing, fractional-share cash-in-lieu and historical lender elections are unavailable. For BLD, the published cash-election estimate ($249.71 plus 10.211 QXO shares) is a proxy subject to final exchange-agent determination; the lender's election is unknown. This is a material execution assumption, not a verified short-account delivery.

Contingent value rights (CVRs) are reserved at their contractual maximum. The ledger subtracts the maximum short liability from NAV, puts equal cash in non-interest-bearing restricted escrow and leaves the obligation outstanding. This is a conservative liability bound, not an observed fair value or confirmed payout. It is not counted as trading turnover or a realized fee.

For the FBHS/MBC spinoff, the distributed short MBC shares are bought back at the first regular-way close, with stock trading costs. This additional execution rule was necessary to settle the new obligation and was added after the original protocol. Original-parent expiry and SPY hedge are retained.

## Dividend currency and rate conventions

CNHI's exact 2023 NYSE cash payment is $0.39398 per share, fixed before the ex-date. Its 2022 conversion was fixed on April 14 by reference to the ECB, but the retrieved ECB file lacked the required observation and was rejected. A same-date Bank of Canada EUR/CAD x CAD/USD rate is used as an explicit proxy for that one payment. ENB's CAD dividends also use Bank of Canada ex/record-date CAD/USD observations as a proxy for the paying agent's conversion. These are not verified broker USD cash. Foreign-currency raw records and override provenance are preserved. These corrections do not change entry eligibility; the controlled candidate holds neither CNHI at the 2022 ex-date nor ENB at these nine ex-dates, so only the exact CNHI 2023 correction affects its main results.

French RF observations end August 31, 2026. Subsequent sessions use the last published daily value, clearly reported separately. The test through August is also shown. Current historical data snapshots, future-informed split normalization and manual action corrections do not establish a pristine point-in-time data feed.

## Risk-control execution limitation

The issuer-controlled variant is a new retrospective strategy change, separate from the accounting-only frozen-rule correction. Maintenance uses marked exposure and fee-aware sizing, but same-close sizing and fills are idealized. On November 8, 2024, CLSK has no vendor close: its last observed mark is carried, no trade is fabricated, and a 2.0137% issuer weight breach is logged. There is no historical locate, recall or maintenance-margin model. A live implementation must stop entries on stale feeds and obtain executable prices and broker limits before it can claim enforceable risk caps.
