# Financing and borrow-cost correction (assumptions fixed 2026-10-03 BEFORE computing the corrected numbers)

The original spec credited 0% on cash and charged nothing for leverage or shorting. Measured holdings show that matters:
in-sample the strategy is net long 0.51 on average (about 49% idle cash); out-of-sample it is net long 1.47 (about 47% borrowed).
This correction changes no signal or weight. It only charges or credits the cash balance, cash = 1 - sum(weights),
using the prior day's close holdings.

Scenario A, institutional / prime broker (headline):
- Positive cash earns the 1-month T-bill rate (French RF, daily).
- Negative cash (margin debit) pays RF + 0.50%/yr.
- Short ETF positions pay a 0.30%/yr borrow fee on short notional (general collateral for liquid ETFs). Short proceeds sit in
  cash and earn RF (rebate).

Scenario B, retail margin account (stress):
- Positive cash earns 0%; margin debit pays RF + 3.00%/yr; short borrow 0.50%/yr; short proceeds earn 0%.

RF after 2026-08-31 (end of the French file) uses the last published value. Reported: IS and OOS for the original spec,
A and B.
