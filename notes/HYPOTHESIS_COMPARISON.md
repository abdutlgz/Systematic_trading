# Repository hypothesis review — October 3, 2026

Recommendation for the supplied five-criterion, 50-point rubric: **cross-asset time-series momentum**, with its existing fixed VIX overlay described accurately. This is the most complete entry, not a demonstrated alpha discovery. Choose the existing specification; do not create a new variant by dropping the overlay after seeing its results.

In simple words: once a month, buy markets that have been rising over the past year and short those that have been falling. Spread exposure across stocks, bonds, commodities, currencies and real estate, size volatile markets smaller, and reduce exposure when the specified month-end VIX threshold is exceeded. The economic explanation is slow adjustment and persistent investment flows; it loses when trends reverse abruptly.

## Rubric comparison

These are reviewer estimates, not competition scores. Risk scores distinguish implemented limits from plans; evidence scores distinguish transparent analysis from proven profitable trades. None receives credit for demonstrated alpha. The criterion-5 cap is conditional on judges verifying reproducibility and the original evaluation process.

| Most developed candidate | Economic | Innovation | Risk | Liquidity/capital | Evidence | Total |
|---|---:|---:|---:|---:|---:|---:|
| Cross-asset momentum, existing VIX specification | 8 | 3 | 6 | 6 | 6 | **29/50** |
| AI capex surprise × constrained memory, newly locked plan | 7 | 6 | 6 | 5 | 4 | **28/50** |
| Momentum + Treasury/short-vol sleeve portfolio | 7 | 3 | 6 | 5 | 4 | **25/50** |
| Executive-exit options hypothesis and decay analysis | 6 | 6 | 4 | 4 | 5 | **25/50** |
| CPI/XLF continuation, locked plan | 6 | 4 | 6 | 5 | 3 | **24/50** |
| TSMC revenue → connected stocks | 7 | 5 | 4 | 4 | 3 | **23/50** |
| Hiring indicators → payroll/trading | 6 | 5 | 4 | 4 | 3 | **22/50** |
| Earnings 8-K categories → volume | 6 | 5 | 3 | 3 | 4 | **21/50** |

Momentum narrowly leads and wins the first tie-breaker, analytical evidence, if a judge scores AI slightly higher on innovation. It has long-history tests, neighboring lookbacks, explicit financing and borrowing assumptions, factor comparisons, reversal stress tests and capital analysis. Its financed historical test-period Sharpe is 0.72 under institutional assumptions and 0.47 under retail assumptions. These are saved historical results, not expected future Sharpe. Reported factor alpha is approximately zero.

Important deductions: the 2x gross limit applies at rebalancing, and recorded gross later reaches 2.23x. Per-position targets also drift. The VIX overlay checks month ends and never triggered in the historical test period. The initial economic description refers to excess-return momentum, while code uses total-return signs. Capacity estimates are assumed ADV/impact diagnostics, not verified fills. The latest strict ADV calculation limits UUP/DBC near $3–4m, so do not headline the older $40–50m impact estimate as an executable capacity promise. Fix descriptions to match the existing implementation; rule changes would need a new evaluation.

The cached momentum return series was recomputed during this review: 4,716 sessions matched saved daily returns to a maximum absolute difference of approximately 1e-16. This verifies that calculation against the cache; it is not a fresh data acquisition, full accounting audit, or proof that the judging cap cannot apply. Historical periods have now been examined repeatedly; retain original spec/run chronology without calling later comparisons fresh holdouts.

## Remaining hypothesis families

All ten ETF screen hypotheses were reviewed through SCREEN_PLAN, RESULTS_IS, RESULTS_OOS and AUDIT. None passed the original promotion rule. This includes sector momentum, betting against beta, overnight drift, turn-of-month, month-end Treasury extension, Treasury auctions, timed short volatility, FX carry, weekly reversal and pre-FOMC drift. Treasury extension and timed short volatility were the strongest historical near-misses but did not replicate when evaluated in the later portfolio. There is no reason to replace the momentum entry with an isolated in-sample winner.

All nine logged Massive trials were reviewed: executive-exit cash-secured puts, protective puts, competitor calls, settlement cash-secured puts, CFO-appointment puts, CEO-appointment puts, CFO-departure puts, CFO-appointment expiry confirmation, and executive-exit ATM straddles. None establishes a trading rule satisfying its stated tests. The latest straddle trial loses relative to ordinary days after costs. Filing-day movement relative to implied movement is the more consistent measurement; the multi-week pattern reverses in 2022–23. An event-session total move does not identify post-publication executable profit.

Other tested families: weather→soft commodities fails; GLP-1 news→loser basket has no reliable effect; open-source AI→software-relative performance has no reliable effect; recession searches→SPY and stock hype→NVDA do not improve their forecasts; Gemini earnings semantics worsen volume forecasts; SEC categories do not establish directional skill; weather prediction-market probabilities lose to the market baseline. These have less complete executable strategy evidence than momentum.

Blocked or untested families: parent/subsidiary mispricing, politician portfolios, hurricane→retailers, parking imagery, general news semantics, dynamic hedging, and 8-K/prediction-market arbitrage. Their economic stories do not compensate for missing matched prices, vintages, exposures, quotes or execution evidence. AI refinements improved provenance and specificity, but true consensus surprise and delayed repricing remain untested under the strict data gates.

## Connection to Massive and 8-Ks

**The frozen momentum baseline has no direct 8-K connection.** Its implemented data source is public ETF price history and VIX. After this review, the user authorized a separate [momentum × 8-K extension](../strategy_8k/momentum_bridge/RESULTS.md): a Massive guidance-withdrawal ETF overlay and a conditional executive-exit protective-put pilot. The first has zero eligible events; the second's event advantage reverses in 2026 and its SPY momentum gate never excludes a sample. These do not establish incremental alpha or justify increasing the estimated rubric score. The options pilot uses the sponsor's library, but is not yet an arbitrary-date acquisition/sealed-replication submission.

For the separate Massive bonus, choose the existing **executive-exit → options mispricing/decay** submission as an honest null-result study. A leadership departure creates uncertainty, so the original hypothesis was that option selling could earn excess compensation. The tests reject that trading claim; observed repricing is concentrated around the filing day. It directly uses Massive disclosure categories, historical option contracts and aggregates, ordinary-day controls, parameter sensitivity and date-window reruns.

The starter notebook's bonus rubric is different: hypothesis/novelty30, analytical rigor30, sealed-window replication20, trade realism10 and communication10. It explicitly says a well-argued null result with a decay curve can beat a lucky backtest. Sealed-window points cannot be assumed before judges run it. Keep the failed long-straddle result and regime reversal in the write-up; do not promote it as profitable volatility arbitrage.

AI capex could eventually connect through 8-K earnings/guidance exhibits and Massive supplier-price data. It currently uses issuer releases, public SEC facts and cached public prices, lacks eligible matched consensus, and has no tested sponsor-library options implementation. That connection is a possible extension, not a completed bonus strategy.

Sources: `strategy/HYPOTHESIS.md`, `strategy/TRIALS.md`, `strategy/RISK_CAPITAL.md`, saved financed outputs and inspected backtest code; `screen/*RESULTS*.md` and `AUDIT.md`; `strategy_8k/TRIALS.md` through trial9; `experiments/RESULTS.md` and `SEMANTIC_RESULTS.md`; `lab/RESULTS.md`; event-research reports, alpha audit and latest AI lock/preflight; Massive starter challenge and submission sections. This review changed no strategy parameters and sent no orders.
