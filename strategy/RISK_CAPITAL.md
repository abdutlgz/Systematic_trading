# Steps 1-4 results (`python strategy/risk_capital.py`). No signal or weight changes.

## 1. Financing correction (assumptions in FINANCING.md, committed first)
| Net Sharpe (ann. return) | In-sample | Out-of-sample |
|---|---:|---:|
| Original spec (0% cash, free leverage) | 0.26 (2.5%) | 0.90 (11.2%) |
| **A: institutional (RF on cash, RF+0.5% on debit, 0.3% borrow)** | **0.29 (2.8%)** | **0.72 (8.7%)** |
| B: retail (0% on cash, RF+3% debit, 0.5% borrow, no rebate) | 0.14 (1.0%) | 0.47 (5.3%) |
| A at 2x trading costs | 0.23 | 0.66 |
In-sample the strategy holds about 49% cash, which earns +0.58%/yr, while borrow fees cost -0.20%/yr. Out-of-sample it is
net long 1.47x, and financing costs -2.25%/yr. **The original spec overstated OOS returns by about 2.5%/yr.** Scenario A is
now the headline.

## 2. Validation against AQR's published TSMOM factor (monthly excess returns)
In-sample correlation **0.72** (201 months), with every asset-class sleeve 0.43-0.48. Beta 0.59. Our Sharpe is 0.21 vs AQR's 0.37:
AQR trades about 58 futures markets against our 10 ETFs, so it has more breadth (fundamental law). OOS (20 months to May 2026)
correlation is 0.56. **This confirms the implementation captures the documented TSMOM premium.**

## 3. Stress, tails, drawdown distribution
Strategy vs SPY / 60-40 over episodes: GFC +16.8% (SPY -46.4%); 2022 rates bear +23.5% (SPY -24.1%); COVID -3.2% (SPY -33.4%);
losses in sharp reversals: Volmageddon -10.9%, Q4 2018 -12.0%, Aug 2024 -6.9%, Apr 2025 -9.6%.
So it protects in slow, trending bear markets and loses in V-shaped shocks (this matches the trend literature).
Tails (IS): daily VaR95 1.26%, ES99 3.05%; monthly VaR95 4.95%, ES95 6.95%.
Bootstrap (IS monthly, 6-month blocks, 10k paths): 1-year return median +2.6%, 5th pct -13.9%, P(loss) 40%;
3-year median max DD -13.4%, 5th pct -28.1%, 1st pct -35.9%.
Correlation with SPY: 0.06 overall, -0.14 on days SPY falls more than 2%.

## 4. Capital deployment
Gross leverage averages 1.82x IS / 1.99x OOS. It drifts above 2.0x on 35% of days (max 2.23x), so Reg T initial margin needs up
to 1.12x equity at the peak. That requires a portfolio-margin or futures account, or rebalancing to a 1.8x gross cap.
Whole-share rounding error: $5k 5.3%, $10k 2.6%, $25k 1.1%, $100k 0.3%. **Minimum practical account is about $25k.**
About 5.7 orders per monthly rebalance, executed as market-on-close orders.
With a strict 5%-of-ADV limit on the 95th-percentile trade: UUP binds at about $2.9M and DBC at about $4.1M. Above that, those trades
are split over 2-5 days or replaced by futures (DX, BCOM); the next limits are VNQ/IEF at about $70M.
