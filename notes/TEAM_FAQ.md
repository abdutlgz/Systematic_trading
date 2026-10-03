# Team FAQ: likely judge questions, with short answers (every member should be able to give these)

## Lead strategy in 30 seconds
When a US company worth $2B+ files an 8-K saying it signed an ACQUISITION AGREEMENT (Massive 8-K data), we short its stock at the
next close, hedge with SPY (sized to the stock's beta), and hold 60 trading days, 2% of capital per event, at most 100% gross short.
Why: acquirers overpay (winner's curse, hubris; Roll 1986), and the market only slowly realizes the deal destroyed value, so the
stock lags for months (Loughran & Vijh 1997; Moeller et al. 2005).

**Headline numbers (net of 10 bps/side and 1%/yr borrow):** in-sample Jan 2022-Sep 2025 Sharpe 0.98 (8.3%/yr, max DD -7.6%);
out-of-sample Oct 2025-Sep 2026, run once: Sharpe 0.82 (9.9%/yr, max DD -12.2%). Beta to SPY about 0. Every year 2022-26 positive.

## How did you find it? (be upfront)
After 32 pre-registered hypotheses, we committed a grid to git BEFORE running it: 34 event types × 3 holding periods × 2 size filters.
The winner rule was fixed in advance, and the selection used in-sample data only. 165 cells were valid. **None survived the multiple-testing
correction (BHY/Holm).** This one won by the pre-set fallback (highest deflated Sharpe), then passed its single out-of-sample test.

**Q: So isn't it p-hacked?** It came from a search, and we say so on page 1. What makes it more than luck: (1) out-of-sample 0.82 on 303 new
events, chosen without looking; (2) shorting the same stocks on random dates LOSES (Sharpe -0.53) and 0 of 100 placebos beat it;
(3) the profit comes from acquirers (+2.8% per event), not deal targets, as the theory predicts; (4) every neighbouring setting
(20/60/120 days, $2B/$10B) is positive; (5) it matches a 40-year academic literature. But we don't call it proven.

**Q: Is it just a market bet?** No: beta to SPY is -0.01 (IS) and -0.14 (OOS); P&L on big market up/down days is about 0.
**Q: Is it the size factor?** Partly, and we disclose it: SMB loading -0.49, factor-adjusted alpha +3.2%/yr with t 0.93. The placebo carries the
same size exposure and loses, so the post-deal window adds something, but we can't reject zero alpha after factors.
**Q: Lookahead?** Filing dates have no time of day, so we enter at the close of the next session. Entering 1 or 5 days later still works
(Sharpe 0.92, 1.12). Market cap is point-in-time (day before), and beta uses only past data.
**Q: Survivorship?** All filers, including companies later acquired or delisted; the size filter is point-in-time.
**Q: Costs?** 10 bps/side stocks, 2 bps SPY, 1%/yr borrow. Doubling costs AND 3% borrow still gives Sharpe 0.68 IS / 0.58 OOS.

## Risk and capacity
**Q: Biggest risk?** Short squeezes in speculative acquirers: IonQ +83% in 60 days (-1.7% of capital), Rocket Lab +68%, QXO +59%.
The 2% per-name cap limits the damage. Daily VaR95 about 1%, skew -0.16 (no hidden crash profile). The OOS drawdown (-12%, early 2026) came in
a speculative rally.
**Q: Capacity?** Median entry stock trades $72M/day. Square-root impact costs 1%/yr at $10M, 3.3% at $100M, so capacity is about $100-150M.
About 4 trades a week. It needs a margin/prime account (short book + SPY hedge, about 1.7x gross).
**Q: Why only 2022-2026?** Massive's 8-K categories start in 2022. The next step is parsing SEC EDGAR back to 2004.

## Strategy 2: cross-asset momentum (our first, fully pre-registered strategy)
12-month trend on 10 ETFs, vol-scaled, monthly, VIX overlay. Net of costs and financing: IS 2008-2024 Sharpe 0.29, OOS 0.72.
It correlates 0.72 with AQR's published TSMOM factor (so the code is right) and -0.10 with the acquirer short (a diversifier).
OOS gains were mostly equity beta (0.50). It protects in slow bear markets (2008 +17%, 2022 +24%) and loses in sharp reversals.

## Honesty and testing
**Q: How many things did you try?** 32 hypothesis-level trials (pilots, momentum variants, a 10-idea ETF screen, weather/GLP-1/AI themes,
9 Massive options tests, the CFO-exit short) plus the 165-cell 8-K grid. All are reported in git.
**Q: Did you look at OOS and then change things?** No. Every OOS run follows a commit fixing the rule. The OOS year used for the
grid winner had been evaluated once before for a different 8-K strategy (abrupt CFO exits, Sharpe 0.32), which we disclose.
**Q: What's the forward test?** FORWARD_LEDGER_3.md (hash-stamped) lists the 50 live shorts as of 2026-10-02; anyone can check them later.

## Massive bonus (options)
No tradable option edge in leadership 8-Ks: selling puts after exits or CFO appointments doesn't beat ordinary days, and a straddle after
exits loses. The consistent pattern: the filing-day move is bigger than options priced, but it reprices within a day. Stars in the
scoreboard appear at the chance rate (0 of 97 key cells).

## Where things are
Note: notes/quant_note.pdf · Lead strategy: event8k/ (GRID_PLAN.md, GRID_RESULTS.md, grid.py, acq_analysis.py) · Momentum: strategy/
· Bonus: notes/massive_note.pdf, strategy_8k/ · Forward ledgers: FORWARD_LEDGER*.md
