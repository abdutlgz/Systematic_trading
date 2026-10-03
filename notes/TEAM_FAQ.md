# Team FAQ: likely judge questions, with short answers (every member should be able to give these)

## The strategy in 30 seconds
We hold 10 liquid ETFs (US/intl/EM/small-cap equities, long and medium Treasuries, gold, commodities, US dollar, REITs).
Each month, each ETF goes long if its past 12-month return is positive and short if negative. Each is sized so it contributes
equal volatility (10%/sqrt(10) each), with caps of 0.5 per ETF and 2x gross. We trade the day after the signal and pay 10 bps per side
plus financing. If the VIX is above 30 at month-end, we halve everything. Rules were committed to git before we downloaded any data.

## Results
**Q: Headline numbers?** Net of trading costs and institutional financing: in-sample 2008-Sep 2024 Sharpe 0.29 (2.8%/yr,
max DD -27.5%); out-of-sample Oct 2024-Sep 2026 Sharpe 0.72 (8.7%/yr, max DD -13.3%). Turnover 7.3x/yr.

**Q: Why should we believe it?** (1) 0.72 correlation with AQR's published TSMOM factor, so it's the real documented effect, not a bug.
(2) Every lookback (3/6/9/12m) is positive, a plateau. (3) Only 0.5% of 200 random-sign placebos beat it. (4) Survives 2x costs.
(5) The rule was never changed after seeing data (git history).

**Q: Is it statistically significant?** No, and we say so. In-sample t is about 1.05; the out-of-sample 95% interval is roughly ±1.4 Sharpe.
At a true Sharpe of 0.3 you need about 45 years of data to reach t = 2. We expect about 0.3 going forward, not 0.7.

**Q: Isn't OOS just the bull market?** Mostly yes. OOS market beta was 0.50 and alpha t = -0.07. Trend was long equities while
equities rose. We report that ourselves.

**Q: Why is OOS lower than your first draft (0.90)?** The first spec ignored financing. OOS the strategy was net long 1.47x, i.e.
borrowing 47% of capital; charging T-bill + 0.5% for that costs about 2.3%/yr. We fixed the assumptions in git BEFORE computing them.

**Q: What does the VIX overlay do?** In-sample it cut max drawdown slightly (-29.4% → -28.3%). OOS it never triggered: VIX hit 52
intraday-month in April 2025, but no month-end close was above 30. Monthly checks miss short spikes. That is a lesson, not something we tuned away.

## Testing honesty
**Q: How many things did you try?** 31 pre-registered trials: 4 early pilots, 5 momentum variants, 10-idea ETF screen, 3 thematic
ideas (weather→cocoa/coffee, GLP-1 news, open-source AI releases), 8 Massive options hypotheses, 1 portfolio. All are reported.

**Q: How do you correct for that?** Deflated Sharpe Ratio, Holm/BHY multiple-testing corrections, and CSCV probability of backtest
overfitting (0.21). The Deflated Sharpe flagged our two best screen ideas (0.84, 0.71 < 0.90) and both then failed OOS.

**Q: Lookahead?** Signals use the close at t; trades happen at t+1. Same-bar trading (a deliberate bug) only adds +0.05 Sharpe, and lags
of 2 and 5 days decay smoothly. VIX, FOMC and auction schedules are known in advance; no revised macro data is used.

**Q: Survivorship?** Only broad index ETFs that existed before we used them, no single stocks. Residual bias: the ETF menu was picked
in 2026.

**Q: Did you look at the OOS before finishing?** No. Each OOS run has a commit before it fixing the spec. One deviation (testing a
portfolio with two screen near-misses) was disclosed in DEVIATION.md before running, and it underperformed.

## Risk and capacity
**Q: When does it lose?** In sharp V-shaped reversals: Feb 2018 -10.9%, Q4 2018 -12%, Apr 2025 -9.6%. It wins in slow bear markets:
2008 +16.8% (SPY -46%), 2022 +23.5% (SPY -24%). Expect about a 40% chance of a losing year, and a 3-year worst drawdown around -13%
(1 in 20: -28%).

**Q: Max loss on one position?** Per-ETF weight is capped at 0.5, so a 10% gap in one ETF costs at most 5% of capital.

**Q: Capacity?** About $40-50M before square-root market impact eats half the edge. UUP and DBC are the thin ones; with a strict
5%-of-ADV rule they bind at $3-4M, so we would split those orders over days or switch to futures. Minimum account is about $25k
(whole-share rounding).

**Q: Leverage/margin?** Gross is about 1.8-2.0x, drifting to 2.23x, so we need a portfolio-margin or futures account. Retail margin
rates cut OOS Sharpe to 0.47, which we report.

## Massive bonus
**Q: What did you find?** Our pre-registered trade (sell puts after executive departures) failed: about zero in-sample, positive OOS only
because the stocks rallied. But one measurement replicated in both windows: after exec exits, stocks move MORE than options priced
(21-day ratio 1.43 vs 0.99 OOS). The market under-prices this risk. Our sealed-window predictions are in FORWARD_LEDGER.md.

**Q: The workshop said to use starred cells. Did you?** Yes, with a rule fixed in advance. 2022-23 discovery: 0 of 97 key cells starred
(about 5 expected by chance); 8 of 135 across all horizons (about 7 expected). The best near-star (CFO appointment → CSP at expiry, +2.34%)
was registered as a follow-up and tested on unseen 2024-25: -0.23%. Stars appear at the chance rate.

**Q: Why not trade the straddle then?** It wasn't pre-registered, so testing it now on seen data would be p-hacking. It is stated as a
prediction for the judges' sealed window instead.

## Where things are
Note: notes/quant_note.pdf · Reproduce: `pip install -r requirements.txt && python run_all.py` · Trial logs: strategy/TRIALS.md,
screen/RESULTS_*.md, lab/RESULTS.md, strategy_8k/TRIALS.md · Audit: screen/AUDIT.md · Financing: strategy/RISK_CAPITAL.md
