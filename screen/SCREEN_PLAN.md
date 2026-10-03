# Pre-registered 10-hypothesis screen

Written and committed 2026-10-03 BEFORE any of these ten backtests were run.
Screening uses IN-SAMPLE data only (everything before 2024-10-01). The out-of-sample period 2024-10-01..2026-09-30
stays locked and is run ONCE, only for the final portfolio chosen by the rules below.
Caveat to disclose: we have already seen the momentum strategy's OOS result for the same calendar period, so we know
broadly how markets behaved in 2024-26. No screened rule uses that knowledge, and all rules are fixed below.

Data: Yahoo daily OHLC + adjusted close (split/dividend adjusted), CBOE indices via Yahoo, US Treasury auction
records (fiscaldata.treasury.gov), Federal Reserve FOMC calendars (federalreserve.gov), FRED short rates.
Signals use data known at close t. Trades are executed at close t+1 unless stated otherwise.
Costs per side (half-spread + slippage): SPY/TLT/IEF/sector SPDRs 5 bps; VIXY / CurrencyShares / GLD / GDX 10 bps.
Overnight strategy: 2 bps per side at the open/close auctions. Every result is also reported at 2x costs.

| # | Hypothesis | Edge source / who is on the other side | Rule (fixed) |
|---|---|---|---|
| H1 | **Sector momentum** (Moskowitz & Grinblatt 1999) | Behavioral: slow diffusion of industry news | 9 original SPDR sectors; monthly; rank on 12-1 month return; long top 3, short bottom 3, equal weight (gross 2) |
| H2 | **Betting against beta, sectors** (Frazzini & Pedersen 2014) | Structural: leverage-constrained investors overpay for high-beta | Monthly; 252d beta to SPY; long 3 lowest-beta scaled to beta 1, short 3 highest-beta scaled to beta 1 |
| H3 | **Overnight drift** (Lou, Polk & Skouras 2019) | Risk/clientele: overnight holders bear gap risk; intraday flows push the other way | Long SPY close-to-open only, every day |
| H4 | **Turn-of-the-month** (Lakonishok & Smidt 1988; Etula et al. 2020) | Structural: payroll/pension cash flows and month-end funding demand | Long SPY from close of the 2nd-to-last trading day to close of the 3rd trading day of the next month; cash otherwise |
| H5 | **Month-end Treasury extension** | Structural: index duration extension forces month-end Treasury buying | Long TLT from close of the 4th-to-last trading day to close of the last trading day; cash otherwise |
| H6 | **Treasury auction cycle** (Lou, Yan & Zhang 2013) | Liquidity provision: dealers absorb supply and need a price concession before auctions | Short TLT from close 5 trading days before each 10y/30y auction to the auction-day close; flat otherwise |
| H7 | **Term-structure-timed short volatility** (Simon & Campasano 2014) | Risk premium: insurance buyers overpay for VIX futures in contango | Short VIXY at weight 0.25 when VIX/VIX3M < 1 at close t; flat otherwise; daily |
| H8 | **Currency carry via ETFs** (Lustig & Verdelhan; Koijen et al. 2018) | Risk premium for crash risk in high-yielders | CurrencyShares AUD/GBP/CAD/EUR/CHF/JPY; monthly; rank on 3m interbank rate (FRED, 1-month publication lag); long top 2, short bottom 2 |
| H9 | **Weekly sector reversal** (Lehmann 1990; Nagel 2012) | Liquidity provision to price-pressure traders | Each week, rank 9 sectors on 5-day return; long bottom 3, short top 3; hold 1 week |
| H10 | **Pre-FOMC drift** (Lucca & Moench 2015) | Risk premium / uncertainty resolution before scheduled Fed news | Long SPY from close of the day before each scheduled FOMC announcement to the announcement-day close; cash otherwise |

Backup if a data source cannot be obtained (declared now): H8 → GDX/GLD 60-day z-score pair reversion (|z|>2 entry,
exit at 0); H10 → option-expiration-week long SPY.

## Promotion rule (fixed before results)
A hypothesis is promoted only if ALL of these hold in-sample:
1. Net annualized Sharpe >= 0.40, and Sharpe >= 0.25 at 2x costs.
2. Positive net Sharpe in both halves of its in-sample history.
3. Probabilistic Sharpe vs the Deflated benchmark >= 0.90 with N = 15 trials (these 10 + the 5 momentum trials).

## Final portfolio (fixed before results)
Promoted sleeves + the existing TSMOM strategy, each scaled to 10% in-sample volatility, combined with equal risk
weights. No optimization of weights. Its OOS is run once. If no hypothesis is promoted, we report the screen as a
documented failure, and TSMOM remains the submission.
