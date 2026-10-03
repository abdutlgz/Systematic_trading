# Secondary weather-market pilot

Written after the temperature-skill diagnostic but before inspecting market comparison scores.
This is exploratory and uses the same Sep 2–30, 2026 holdout (29 dates), not a new untouched replication.

- Model: empirical residual distribution of the 48-hour-lead daily composite, calibrated only on July 8–September 1.
- Forecast timing: the latest component of the previous_day2 series is from approximately 48 hours before 23:00 target-local-time. Query comparison is at 20:00 Eastern the previous day, about 21 hours after that latest component's nominal availability. This is a conservative research assumption, not independently verified forecast publication metadata.
- Probability bins: integer-temperature outcomes use half-degree boundaries. Evaluate all available contracts, not hindsight-selected winners. Dirichlet smoothing of 0.5 pseudo-count per bin; these are model probabilities, never invented observations.
- Comparison quote: bid/ask close of the hourly candle ending at 20:00 Eastern the previous day. Require an exact candle timestamp, valid non-crossed bid/ask, and a contract already opened.
- Main score: Brier error against actual binary settlement, model versus quoted midpoint; all contracts within a day form one dependent group.
- Report all missing data and daily-group uncertainty. No P&L or fill claim: candle quotes omit executable depth and order latency.
- Training/test settlement source wording differs; report this structural limitation.
