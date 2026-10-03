# Gator Quant Hacks 2026: Systematic Trading Track

**Lead strategy: short acquisition-agreement 8-K filers, SPY-hedged** ([quant note](notes/quant_note.pdf)). Found by a pre-registered
165-cell 8-K event grid (selection on in-sample only), then confirmed once out of sample. Strategy 2: cross-asset momentum.
Bonus: Massive "Trade the 8-K" ([bonus note](notes/massive_note.pdf)).

| Short acquisition filers ≥ $2B, 60 sessions, net of costs + borrow | In-sample Jan 2022–Sep 2025 | Out-of-sample Oct 2025–Sep 2026 (run once) |
|---|---:|---:|
| Sharpe | 0.98 | 0.82 |
| Annual return | 8.3% | 9.9% |
| Max drawdown | −7.6% | −12.2% |
| Beta to SPY | −0.01 | −0.14 |

Not proven alpha: it does not survive BHY/Holm across the 165 cells, and part of the return is the size factor (alpha t 0.93).
Random-date placebo: 0 of 100 beat it. 32 hypotheses + 165 grid cells are reported in total.

## Reproduce (lead strategy)
Quick check, no key needed: `python event8k/replay.py` recomputes Table 1 from the committed daily returns.

Full rebuild (needs a Massive API key, sponsor data):
```sh
cd gqh-massive-8k-starter && ./setup.sh             # put MASSIVE_API_KEY in .env (git-ignored)
.venv/bin/python ../event8k/build_grid.py           # events + point-in-time caps + prices (~45 min first time, cached after)
.venv/bin/python ../event8k/acq_volume.py           # dollar volume for capacity
cd .. && python event8k/grid.py --oos               # grid, BHY/DSR selection, winner OOS
python event8k/acq_analysis.py                      # Table 1, robustness, capacity, Figure 1
```
Derived Massive data is not committed (licensed); the scripts rebuild it.

## Reproduce (Strategy 2 momentum, screen, audit, labs: free data)
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
# or open strategy_8k/exec_exits_8k.ipynb (set START/END) with the starter's kernel
cd .. && gqh-massive-8k-starter/.venv/bin/python strategy_8k/grid.py && gqh-massive-8k-starter/.venv/bin/python notes/figures_8k.py
```

## Map of the repo (pre-registration first, then results; see `git log`)
| Folder | What | Key files |
|---|---|---|
| `event8k/` | **Lead strategy**: 8-K event grid + acquirer short | `GRID_PLAN.md`, `GRID_RESULTS.md`, `grid.py`, `acq_analysis.py`, `HYPOTHESIS.md` (CFO-exit short) |
| `strategy/` | Strategy 2: momentum | `HYPOTHESIS.md` (committed before any data), `backtest.py`, `analysis.py`, `TRIALS.md` |
| `screen/` | 10-hypothesis ETF screen, portfolio, audit | `SCREEN_PLAN.md`, `DEVIATION.md`, `RESULTS_IS.md`, `RESULTS_OOS.md`, `AUDIT.md` |
| `lab/` | Thematic ideas: weather→softs, GLP-1, open-source AI | `LAB_PLAN.md`, `RESULTS.md` |
| `strategy_8k/` | Massive 8-K options bonus | `HYPOTHESIS*.md`, `run_window.py`, `grid.py`, `peers.py`, `TRIALS.md` |
| `experiments/` | Earlier pilots (SEC→volume, Gemini earnings text, weather vs Kalshi) | `PLAN.md`, `RESULTS.md`, `SEMANTIC_*.md` |
| `FORWARD_LEDGER.md` | Hash-stamped live positions and sealed-window predictions, written before outcomes exist | `FORWARD_LEDGER.sha256` |
| `notes/` | Quant note and bonus note (HTML → PDF), figure scripts, team FAQ | `quant_note.pdf`, `massive_note.pdf` |
| `gqh-*-starter/` | Sponsor starter kits (Webull backtrader, Massive notebook) | unchanged except `examples/backtest/public_data.py` |

Rebuild a PDF after editing: `"/Applications/Google Chrome.app/Contents/MacOS/Google Chrome" --headless=new --no-pdf-header-footer --print-to-pdf=notes/quant_note.pdf "file://$PWD/notes/quant_note.html"`
