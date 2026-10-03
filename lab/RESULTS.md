# Idea lab results (run 2026-10-03, `python lab/lab.py`). Rules unchanged from LAB_PLAN.md.

**W: weather → softs (in-sample 2006-01..2024-09): FAILS.** Net Sharpe -0.37 (t -1.60), 2x costs -0.43, halves +0.08 / -0.78.
By commodity: cocoa -0.18, coffee +0.12, sugar -0.35, OJ -0.31 (only 1 of 4 positive; pass needed 3 of 4 and Sharpe >= 0.30).
The OOS window stays unused. The sign is consistently wrong-way (droughts did not lead to price rises one month later), which suggests
weather is priced quickly, or that 90-day rainfall at one or two grid points is too crude. Flipping the sign now would be a new
post-hoc trial; we do not do it.

**G: GLP-1 news → loser basket: no effect.** 9 events. CAR[0,+1] mean -0.45% (t -0.85, 4/9 positive, placebo p = 0.17);
CAR[+2,+21] mean -0.57% (t -0.43, placebo p = 0.55). There is no reliable over-reaction and no reversal. The famous headline
days (Walmart comment -2.6%, FLOW -3.0%) did reverse (+1.5%, +5.1%), but SELECT and Mounjaro kept falling (-5.3%, -7.6%).

**A: open-source AI releases → IGV - QQQ: no effect.** 9 events. CAR[0,+5] +0.47% (t +0.54, placebo p = 0.19 for "positive");
CAR[0,+20] -0.21% (t -0.16). Software did NOT underperform broad tech after open-weight releases.

Lab trial count: +3. Running total for the project: 27 pre-registered trials.
