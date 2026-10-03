# Idea lab: pre-registered tests of the user's ten new ideas (committed 2026-10-03, BEFORE any prices for these tests)

Free or sponsor data only. Sponsor check: the Massive key covers US stock bars, options and 8-K filings, but not futures or crypto;
we have no Databento or Webull key.

## Triage (no test possible or meaningful)
1. Starlink latency arbitrage: needs microsecond multi-venue ticks and colocated hardware; not backtestable by a team.
2. Stranded power: the long-IPP theme (VST/CEG/TLN) was chosen with hindsight; there is no ex-ante signal.
4. Cyber contagion: already tested as Massive trial 3 (peers did not gain). Not retested, to avoid an extra trial.
6. In-game economies: Steam covers PC only, and picking titles uses hindsight. Not testable in time.
7. Patent cliff: expiry dates are public years ahead, so likely priced; about 15 hand-picked events. Skipped.
9. Returns arbitrage: return-rate data is proprietary. 10. Adaptive reuse: no systematic signal.

## Test W: weather → soft commodities (systematic; primary candidate)
Hypothesis: rainfall shortfalls in the main growing regions cut future supply. Futures prices adjust slowly, because official crop
estimates (USDA, ICCO) lag the weather by weeks or months, so speculators can front-run the supply shock.
- Prices: Yahoo continuous front-month futures CC=F (cocoa), KC=F (coffee), SB=F (sugar), OJ=F (orange juice).
  Limitation: continuous series are not roll-adjusted, so roll gaps add noise. They are unrelated to the weather signal (no bias in the signal-return link).
- Weather: Open-Meteo ERA5 archive, daily precipitation. Cocoa = mean of Daloa CI (6.88,-6.45) and Kumasi GH (6.69,-1.62);
  coffee = Varginha BR (-21.55,-45.43); sugar = Ribeirao Preto BR (-21.17,-47.81); OJ = Lake Wales FL (27.90,-81.59).
- Signal at each month-end t: 90-day precipitation total ending t-7 days (allows for ERA5 publication lag), as a z-score against the
  same calendar window in all PRIOR years since 1990 (expanding window).
- Position: w = clip(-z, -2, 2)/2 × 0.10 / (60d EWMA vol × sqrt(4)), capped at |1|. Drought → long, very wet → short.
- Monthly rebalance, executed at close t+1. Cost 15 bps per side; also reported at 2x.
- IS: 2006-01..2024-09. OOS 2024-10..2026-09 stays LOCKED (run once, only if the IS rule passes).
- Pass (IS): net Sharpe >= 0.30, positive in >= 3 of 4 commodities, Sharpe >= 0.15 at 2x costs.

## Test G: GLP-1 news → "GLP-1 loser" basket (exploratory event study)
Hypothesis: investors over-react to vivid GLP-1 headlines in exposed consumer and medtech stocks (day 0..+1), then partly reverse
over the next 20 sessions as fundamentals barely move in the short run.
- Events (dates verified from public sources before testing): 2021-06-04 Wegovy approval; 2022-05-13 Mounjaro approval;
  2023-08-08 SELECT topline; 2023-10-04 Walmart CEO comment; 2023-10-10 FLOW stopped early; 2023-11-08 Zepbound approval;
  2024-03-08 Wegovy CV label; 2024-08-20 SURMOUNT-1 3-year; 2024-12-20 Zepbound OSA approval.
- Basket (equal weight): MDLZ HSY PEP KHC GIS STZ DEO SYK ZBH DXCM DVA. Abnormal return = basket − beta × SPY, with beta from
  days −260..−11.
- Report CAR[0,+1] (reaction) and CAR[+2,+21] (drift). Trade: long basket / short beta×SPY from close of day+1 for 20 sessions.
  Prediction: CAR[0,+1] < 0 and CAR[+2,+21] > 0. Only 9 events, so this is exploratory with no IS/OOS split.

## Test A: open-source AI releases → software (exploratory event study)
Hypothesis: free open-weight models erode the pricing power of application-software (SaaS) vendors, and the market prices this
gradually. So software underperforms broad tech after major open releases.
- Events (first session on or after the release date): LLaMA 2023-02-24; Llama 2 2023-07-18; Code Llama 2023-08-24;
  Llama 3 2024-04-18; Llama 3.1 2024-07-23; Llama 3.2 2024-09-25; Llama 3.3 2024-12-07; DeepSeek-R1 2025-01-20; Llama 4 2025-04-05.
- Spread = IGV (software) − QQQ (Nasdaq-100). Report CAR[0,+5] and CAR[0,+20]. Prediction: both < 0.
  Only 9 events, so this is exploratory.

Trial count after this lab: +3 (W, G, A).
