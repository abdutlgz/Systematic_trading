# Pre-registered hypothesis: cross-asset time-series momentum with a VIX de-risking overlay

Written and committed 2026-10-02, BEFORE any price data for this strategy was downloaded or backtested.

## Economic hypothesis
We expect liquid cross-asset ETFs (equities, bonds, commodities, currencies, real estate) to keep trending in the
direction of their own trailing 12-month excess return over the following month, because investors underreact to
new information at first and later chase the move (Moskowitz, Ooi & Pedersen 2012). Hedgers and slow-moving
capital who need to trade regardless of trend are on the other side. The edge persists because it is a behavioral bias
plus a crisis-alpha risk premium: trend followers lose in choppy, trendless markets and at sharp reversals.

**Extension (our addition):** TSMOM crashes cluster at sharp reversals after volatility spikes (Daniel & Moskowitz
2016 make the same point for cross-sectional momentum). We predict that cutting gross exposure when the
prior day's VIX close is high improves risk-adjusted returns and drawdown without killing the edge.

Testable predictions: (1) positive net Sharpe in-sample and out-of-sample; (2) nearby lookbacks (3/6/9 months) also
positive (a plateau, not a spike); (3) the overlay lowers max drawdown versus the base strategy.
It fails if OOS net Sharpe is <= 0, or if only the 12-month lookback works.

## Fixed specification (no tuning)
- Universe (10 ETFs, all listed by 2007): SPY, EFA, EEM, IWM (equity); TLT, IEF (bonds); GLD, DBC (commodities);
  UUP (USD); VNQ (real estate). Survivorship: hand-picked liquid ETFs that still trade, which is disclosed as a bias.
- Data: Yahoo daily adjusted closes (split and dividend adjusted), 2008-01-02 to 2026-09-30. Missing days are dropped,
  never forward-filled with later data.
- Signal: sign of the trailing 252-trading-day total return, computed at month-end close t.
- Sizing: each asset is scaled to 10%/sqrt(N) annualized volatility using a 60-day EWMA vol estimate known at t;
  portfolio gross leverage is capped at 2.0x; per-asset weight is capped at |0.5|.
- Execution: rebalance monthly; weights set at close t are traded at close t+1 (one-bar lag).
- Costs: 5 bps commission/spread + 5 bps slippage per side = 10 bps per unit of turnover. Rationale: these ETFs'
  quoted spreads are about 1-3 bps; 10 bps is conservative. A 2x cost (20 bps) result is also reported.
- Overlay: multiply all weights by 0.5 when the VIX close on day t (FRED VIXCLS, known at t) is above 30.
  The 30 threshold is fixed a priori (a commonly used stress level) and will not be tuned.
- Cash earns 0 (conservative; the risk-free rate is not added).

## Sample split (track rule: most recent 20% or 2 years, whichever is shorter)
- About 18.75 years of history; 20% is about 3.75 years, so the 2-year cap binds.
- In-sample: 2008-01-02 to 2024-09-30. Out-of-sample: 2024-10-01 to 2026-09-30. OOS is run ONCE, at the end.

## Pre-declared trials (all are reported, for the Deflated Sharpe Ratio)
1. Base TSMOM 12m (primary)  2. Base + VIX overlay (primary extension)
3-5. Lookback plateau 3m / 6m / 9m (IS only, robustness)  6. 2x costs (sensitivity, not a new strategy)
Any extra variant tried later is appended to TRIALS.md with a timestamp.

## Earlier ideas that failed (from experiments/)
SEC-category volume forecast (+1.0%, below the 5% bar), directional next-day price (no skill), Gemini earnings
semantics (worse than baseline), weather vs Kalshi (model loses to market). See experiments/RESULTS.md.
