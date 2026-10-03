# Gator Quant Hacks 2026: Systematic Trading Track

**Submission:** cross-asset time-series momentum with a pre-registered VIX overlay ([quant note](notes/quant_note.pdf)),
plus the Massive "Trade the 8-K" bonus ([bonus note](notes/massive_note.pdf)).

| | In-sample 2008–Sep 2024 | Out-of-sample Oct 2024–Sep 2026 (run once) |
|---|---:|---:|
| Net Sharpe (10 bps/side + financing) | 0.29 | 0.72 |
| Annual return | 2.8% | 8.7% |
| Max drawdown | −27.5% | −13.3% |
| Turnover | 7.3×/yr | 7.3×/yr |

Correlation with AQR's published TSMOM factor: 0.72. Unfinanced original spec: 0.26 / 0.90 (see `strategy/FINANCING.md`).
We do not claim a proven edge (in-sample t ≈ 1.05; out-of-sample alpha ≈ 0). The project's value is the testing:
27 pre-registered trials, a nine-pitfall statistical audit, and every failure reported.

## Reproduce (main track)
```sh
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
python run_all.py
```
All data is free and public, downloaded by the scripts (Yahoo Finance, CBOE VIX, Kenneth French, US Treasury Fiscal Data,
Federal Reserve FOMC calendars, FRED, Open-Meteo ERA5). No data or keys are committed.

## Reproduce (Massive bonus, needs a Massive API key)
```sh
cd gqh-massive-8k-starter && ./setup.sh          # creates .venv; put MASSIVE_API_KEY in .env (git-ignored)
.venv/bin/python ../strategy_8k/run_window.py --events exec --start 2024-01-01 --end 2025-12-31 --label is
.venv/bin/python ../strategy_8k/run_window.py --events exec --start 2026-01-01 --end 2026-08-31 --label oos
.venv/bin/python ../strategy_8k/run_window.py --events exec --start A --end B --label sealed   # judges' window
cd .. && gqh-massive-8k-starter/.venv/bin/python strategy_8k/grid.py && gqh-massive-8k-starter/.venv/bin/python notes/figures_8k.py
```

## Map of the repo (pre-registration first, then results; see `git log`)
| Folder | What | Key files |
|---|---|---|
| `strategy/` | Momentum strategy (submission) | `HYPOTHESIS.md` (committed before any data), `backtest.py`, `analysis.py`, `TRIALS.md` |
| `screen/` | 10-hypothesis ETF screen, portfolio, audit | `SCREEN_PLAN.md`, `DEVIATION.md`, `RESULTS_IS.md`, `RESULTS_OOS.md`, `AUDIT.md` |
| `lab/` | Thematic ideas: weather→softs, GLP-1, open-source AI | `LAB_PLAN.md`, `RESULTS.md` |
| `strategy_8k/` | Massive 8-K options bonus | `HYPOTHESIS*.md`, `run_window.py`, `grid.py`, `peers.py`, `TRIALS.md` |
| `experiments/` | Earlier pilots (SEC→volume, Gemini earnings text, weather vs Kalshi) | `PLAN.md`, `RESULTS.md`, `SEMANTIC_*.md` |
| `notes/` | Quant note and bonus note (HTML → PDF), figure scripts | `quant_note.pdf`, `massive_note.pdf` |
| `gqh-*-starter/` | Sponsor starter kits (Webull backtrader, Massive notebook) | unchanged except `examples/backtest/public_data.py` |

Rebuild a PDF after editing: `"/Applications/Google Chrome.app/Contents/MacOS/Google Chrome" --headless=new --no-pdf-header-footer --print-to-pdf=notes/quant_note.pdf "file://$PWD/notes/quant_note.html"`
