import json, sys
from pathlib import Path
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from probe import ROOT

def read(name):return json.loads((ROOT/'results'/name).read_text())
s=read('stock_summary.json');w=read('weather_summary.json');m=read('weather_market_summary.json');d=read('disclosure_summary.json')
fig,axes=plt.subplots(1,2,figsize=(12,5.3),layout='constrained')
fig.patch.set_facecolor('#fafafa')
names=['Market history','+ Filing counts','+ Earnings flag','+ All categories']
vals=[s['metrics'][x]['mae_log_relative_volume'] for x in ['market','attention','earnings_only','categories']]
colors=['#94a3b8','#64748b','#0f766e','#3b82f6']
axes[0].barh(names,vals,color=colors)
axes[0].invert_yaxis();axes[0].set_xlim(0,.245)
axes[0].set_title('Daily volume: small incremental gain',loc='left',fontweight='bold')
axes[0].set_xlabel('Mean absolute log-relative-volume error — lower is better')
for i,v in enumerate(vals):axes[0].text(v+.003,i,f'{v:.4f}',va='center',fontsize=10)
axes[1].bar(['Weather model','Market midpoint'],[m['model_brier'],m['market_midpoint_brier']],color=['#3b82f6','#0f766e'],width=.55)
axes[1].set_ylim(0,.175)
axes[1].set_title('Weather: market probabilities were better',loc='left',fontweight='bold')
axes[1].set_ylabel('Brier score — lower is better')
for i,v in enumerate([m['model_brier'],m['market_midpoint_brier']]):axes[1].text(i,v+.004,f'{v:.4f}',ha='center')
for ax in axes:
    ax.spines[['top','right']].set_visible(False)
    ax.set_axisbelow(True)
fig.suptitle('Real public-data pilots • no demonstrated trading edge',fontsize=15,fontweight='bold')
fig.supxlabel('Volume: 1,870 held-out stock-sessions. Weather: 165 contracts, 29 daily outcomes. No execution/P&L test.',fontsize=10)
fig.savefig(ROOT/'results'/'pilot_results.png',dpi=160)

report=f'''# Public-data experiment results

Run on October 2, 2026 Eastern / October 3 UTC. All observations are downloaded public records. No market data or results were synthesized. Random resampling is used only for uncertainty estimates.

**Decision: no demonstrated trading edge. Continue with a narrowly scoped earnings-content → volume experiment, not a general directional bot. Defer hedging until usable historical option quotes exist.**

## 1. Daily filing-category volume pilot — completed

Public Yahoo daily bars for 10 fixed stocks (AAPL, MSFT, NVDA, AMZN, META, GOOGL, TSLA, WMT, JPM, XOM) and SEC submissions histories. SPY supplies the exploratory price benchmark.

- Training: {s['train_rows']:,} stock-sessions, {s['train_dates'][0]}–{s['train_dates'][1]}.
- Held-out test: {s['test_rows']:,} stock-sessions / {s['test_days']} dates, {s['test_dates'][0]}–{s['test_dates'][1]}.
- Outcome: daily log(volume / trailing-20-session median volume).
- Features available before the 09:25 Eastern decision; filings require 30 minutes after the API's acceptance timestamp. Intraday filings predict a later session, never the already-started one.
- Original 30-minute news experiment was NOT performed. This is a daily structured-SEC-category proxy, not a Gemini or X model.

| Model | Held-out MAE; lower is better |
|---|---:|
| Market-history baseline | {s['metrics']['market']['mae_log_relative_volume']:.6f} |
| Plus filing counts | {s['metrics']['attention']['mae_log_relative_volume']:.6f} |
| Plus earnings flag only (exploratory ablation) | {s['metrics']['earnings_only']['mae_log_relative_volume']:.6f} |
| Plus all preselected 8-K categories | {s['metrics']['categories']['mae_log_relative_volume']:.6f} |

All categories improve error by **{s['category_vs_attention']['improvement_pct']:.2f}%** versus filing counts, below the 5% continuation gate. Day-resampled 95% interval: {s['bootstrap_day_95pct_improvement_interval'][0]:.2f}% to {s['bootstrap_day_95pct_improvement_interval'][1]:.2f}%. This descriptive bootstrap assumes days are exchangeable; it does not establish independent replication or trading profitability.

On the {s['event_days']['n']} 8-K-event sessions, the reduction is {s['event_days']['improvement_pct']:.2f}%; on other sessions it is {s['no_event_days']['improvement_pct']:.2f}%. The full model improves in 7/10 stocks and both chronological test halves, but earnings alone actually does better than all categories. The earnings-only ablation was added after seeing the primary result and is explicitly exploratory.

There are {s['descriptive_test_volume']['earnings_8k']['n']} earnings-event sessions. Their median volume is {s['descriptive_test_volume']['earnings_8k']['median_relative_volume']:.2f}× trailing median, versus {s['descriptive_test_volume']['no_8k']['median_relative_volume']:.2f}× on no-8-K sessions. This is descriptive and is not evidence of novel alpha; a known earnings-calendar baseline is still needed.

**Next hypothesis:** among earnings events, do guidance changes, quantified surprise and announcement novelty add predictive value beyond the calendar, recent volume and a simple earnings flag? Use a new holdout, not this already-inspected period.

## 2. Directional price pilot — completed, negative

Exploratory target: next session's open-to-close return minus SPY's same-session return. Same chronological split and features.

- Category model direction accuracy: {s['exploratory_price_metrics']['categories']['direction_accuracy']:.2%}.
- Market-only accuracy: {s['exploratory_price_metrics']['market']['direction_accuracy']:.2%}.
- Category return MAE: {s['exploratory_price_metrics']['categories']['mae_return']:.6f}; zero-return predictor MAE: {s['price_zero_return_mae']:.6f}.

No useful incremental directional result; no strategy profitability calculated.

## 3. Weather skill and market comparison — completed, negative market result

Real Open-Meteo archived NOAA GFS fixed-lead forecasts at Central Park coordinates, July–September 2026. Actual outcomes come from Kalshi's settled `expiration_value`, not reanalysis or fabricated station data. An independent IEM observation request failed (HTTP 422) and was not used.

Temperature diagnostic: 56 calibration days and 29 test days. Mean absolute errors:

| Forecast | Test MAE, °F |
|---|---:|
| Previous observed daily maximum | {w['metrics']['persistence']['mae_f']:.2f} |
| Seven-day trailing average | {w['metrics']['trailing7']['mae_f']:.2f} |
| 24-hour-lead composite | {w['metrics']['forecast_day1']['mae_f']:.2f} |
| 48-hour-lead composite | {w['metrics']['forecast_day2']['mae_f']:.2f} |
| Training-bias-corrected 48-hour composite | {w['metrics']['corrected_day2']['mae_f']:.2f} |

These hourly fixed-lead series are not a single forecast issuance. The day-1 diagnostic is not treated as a day-before trading signal.

For a secondary market comparison, we used only the older 48-hour composite and training residuals. Compare with bid/ask midpoint at **20:00 Eastern the preceding day**. Require the exact pre-outcome candle; do not substitute settled last prices. The preceding-day comparison is conservatively later than nominal component availability, but actual publication timestamps are not independently verified.

| Probability model | Brier score; lower is better |
|---|---:|
| Empirical weather model | {m['model_brier']:.6f} |
| Market bid/ask midpoint | {m['market_midpoint_brier']:.6f} |

- {m['contracts']} valid contract comparisons across {m['test_days']} days; {len(m['missing'])} missing exact candles excluded and listed in `weather_market_summary.json`.
- Weather model wins on {m['days_model_better']}/{m['test_days']} dates.
- Day-resampled 95% interval for model-minus-market Brier: {m['model_minus_market_brier_95pct_day_bootstrap'][0]:.4f} to {m['model_minus_market_brier_95pct_day_bootstrap'][1]:.4f}; positive means the model is worse.
- The 165 contracts are NOT 165 independent daily outcomes. All bins for one date are related.
- Training/test contract rules change source wording from NWS to The Weather Company. This is a structural comparability limitation.
- Midpoint is a probability baseline, not an executable fill. No P&L, return, Sharpe, or arbitrage claim.

**Decision:** this simple weather implementation does not justify betting. A better next weather model would use a timestamped, newer single-run forecast or ensemble and must face a fresh holdout.

## 4. Other ideas: exact status and missing inputs

| Idea | What actually happened | What is still needed |
|---|---|---|
| Politician portfolios | Downloaded official House 2025 disclosure index: {d['ptr_filed_in_2025']} periodic transaction reports filed in 2025, {d['unique_filer_names_2025']} distinct filer-name pairs. No transaction-return test. | Parse original PDFs; validate tickers, amendments and posting times; then construct sector-adjusted tests. Public index alone is insufficient. |
| Dynamic hedging | Not run. No option prices or Greeks invented. | Historical option and underlying bid/ask quotes, contract terms, timestamps and a documented Greek/valuation source. |
| 8-K + prediction-market/options arbitrage | SEC histories acquired; no matched corporate-event contract backtest. | Exact event/settlement matches plus pre-event contract/option quotes. |
| Walmart parking imagery | Not run; no images or car counts invented. | Repeated usable high-resolution imagery with acquisition metadata for a fixed store sample. |
| X/general news semantics | Not run. | Timestamped original news corpus, source/revision information and Gemini access for extraction. |

## Resource usage and next action

These runs use local CPU, NumPy and pandas. No ARCC jobs, Gemini calls, Webull orders or Solana transactions occurred. Large GPU allocations are unnecessary for these pilots.

Priority order based on actual evidence:
1. Earnings-content volume experiment: strongest concrete next hypothesis, but current gains are explained by earnings identification.
2. More timely weather probabilities: public data pipeline is viable, current model loses to market.
3. Dynamic hedging: only after data access is established; the volume result does not establish hedging benefit.

See `API_SETUP.md` for Gemini/Webull setup and exact input schemas. Secrets are entered using a hidden terminal prompt, never in chat.

## Reproduce from the saved observations

```sh
cd /Users/atoleugazin/Documents/Projects/QGHACKS
python3 experiments/analyze.py
python3 experiments/weather_market.py
python3 experiments/make_report.py
python3 experiments/validate.py
```

`probe.py`, `collect.py`, `collect_more.py`, and `weather_market.py --collect` are the network acquisition scripts. Prefer the saved snapshots for exact reproduction: provider responses and relative two-year requests can change. All successful responses have URL, UTC retrieval timestamp and SHA-256 in the manifests. HTML bot-check pages are saved as failed usability probes and never analyzed as prices. Re-running acquisition scripts can replace their files; copy this snapshot before a fresh download.

Environment: Python {sys.version.split()[0]}, numpy {np.__version__}, pandas {pd.__version__}, matplotlib {matplotlib.__version__}.

## Public sources

- SEC submissions documentation: https://www.sec.gov/search-filings/edgar-application-programming-interfaces
- Stock endpoint example (retrieval URL preserved in manifest): https://query1.finance.yahoo.com/v8/finance/chart/AAPL?range=2y&interval=1d
- Archived forecast semantics: https://open-meteo.com/en/docs/previous-runs-api
- Kalshi public historical market API: https://docs.kalshi.com/api-reference/historical/get-historical-markets
- Kalshi pre-outcome candle API: https://docs.kalshi.com/api-reference/market/batch-get-market-candlesticks
- House disclosure archive: https://disclosures-clerk.house.gov/FinancialDisclosure
'''
(ROOT/'RESULTS.md').write_text(report)
print('Wrote experiments/RESULTS.md and experiments/results/pilot_results.png')
