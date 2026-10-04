# Acquisition-filer revision protocol

Written after review on 2026-10-03, before revision results. This is an accounting correction and retrospective risk-control study, not a new preregistration or untouched holdout. Preserve the original `event8k/` and `notes/quant_note.pdf`.

## Frozen signal and windows

Use the already selected `acquisition_agreement` filers with prior-day cap >= $2B. Enter the first trading-session close strictly after the filing date; beta uses prior sessions [-260:-10], clipped to [0.5,1.5], fallback 1 if fewer than 120 valid observations. Hold 60 sessions. IS 2022-01-01..2025-09-30; previously examined historical test 2025-10-01..2026-09-30. Do not rerun selection or optimize parameters.

## Accounting correction

Start NAV at 1. Allocate 2% of current NAV to stock short per accepted event, buy entry-beta times that notional in SPY, keep split-normalized share quantities fixed until exit. Charge stocks 10 bps and SPY 2 bps on actual traded notional. Short-sale proceeds are restricted and earn zero rebate; free positive cash earns the daily French RF proxy; negative free cash pays RF plus 150 bps/year. Stock borrow costs 1%/year on previous marked stock liability using calendar days/365. Accrue split-adjusted dividends on the ex-date and settle on pay-date; missing/earlier pay dates settle on ex-date and are flagged. These are assumptions, not verified broker terms. Short collateral is initial sale proceeds; maintenance margin and locate availability are not historical inputs.

Headline Sharpe uses daily NAV return minus RF. Also report total-return Sharpe explicitly. RF ends 2026-08-31 in the existing cache: later sessions use the last observed daily rate only as a disclosed proxy; separately report the test through the last observed RF date.

Missing marks carry only the last observed price, including resumption changes. Never fill orders on stale quotes. Explicit settlement overrides require a dated source and cash amount on the split-normalized price basis. Missing terminal settlements and blocked exits remain unresolved, and prevent calling the results investable. Report both unresolved exposure and data exceptions.

## Two separate, unselected configurations

1. `accounting_only`: original event slots (at most 50 events), overlap permitted. Exposures drift; no claim of a live 100%-NAV cap or 2%-issuer cap.
2. `issuer_controlled`: new retrospective control, no concurrent same-issuer entries; entry stock notional <=2% NAV and total short <=100% NAV. At each close, if tradable stock liabilities exceed either limit, proportionally cover stock and sell its paired SPY shares, with costs. Iterate using updated NAV; report violations when a current quote is unavailable. No stop-loss/size hedge/momentum filter is added.

Run both without ranking/selecting a winner. Stress trading fees at 2x and borrow at 3% for the controlled version. A 5-session delayed entry is a diagnostic, not a fill/capacity simulation.

## Evidence and classification

Use seed 20261003 for 100 IS random-date placebos with the same eligible IS event ticker multiplicities, sampling available dates ending by 2025-07-01, outside +/-90 calendar days of acquisition filings for each issuer. Keep both the same ticker multiset and event-count diagnostics; report exchangeability limitations. This is a new, reproducible diagnostic on an already selected candidate, not a family-wise significance test.

Save cached supporting text and source URLs. Build an issuer-role manual-review sheet using filing text only, with transparent heuristic suggestions and an `unknown` category. Do not use post-event volatility or heuristic suggestions as trading filters; do not claim classifier accuracy without human labels. No Gemini/API inference is necessary to correct financial accounting.

Report FF5+momentum attribution using the same cash-excess daily return used for Sharpe, with Newey-West errors and the factor-data endpoint date. No additional RF subtraction of an already excess series.

Capacity remains illustrative: entry-known prior-20-session ADV, historical trade sizes, explicit 5%-ADV feasibility counts, and no assertion that a delayed full entry proves multi-day fill feasibility. Borrow recalls and margin liquidation are not simulated.

## Reproducibility

Snapshot licensed data under ignored `data/` and `cache/`; record SHA256 and source paths in an input manifest. Environment-based Massive authentication, no saved credentials or keys in manifests/logs. Save NAV, cash, short liabilities, holdings/trades, exception logs, fees, dividends, funding, and machine-readable metrics. Include deterministic accounting tests and one offline reproduction command. Preserve original and revised outputs separately.
