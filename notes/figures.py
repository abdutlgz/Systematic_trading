"""Figures for the quant note (main venv). python notes/figures.py"""
from pathlib import Path
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
OUT = Path(__file__).parent
plt.rcParams.update({"font.size": 9, "axes.spines.top": False, "axes.spines.right": False})

r = pd.read_csv(ROOT / "strategy/output/financed_daily.csv", index_col=0, parse_dates=True)["A_institutional_1x"].loc["2008-01-02":]
spy = pd.read_csv(ROOT / "strategy/data/SPY.csv", index_col=0, parse_dates=True)["adjclose"].loc[r.index[0]:r.index[-1]]
eq = (1 + r).cumprod()
dd = eq / eq.cummax() - 1
fig, (a, b) = plt.subplots(2, 1, figsize=(7.2, 3.6), sharex=True, gridspec_kw={"height_ratios": [2.2, 1]})
a.plot(eq, color="#1f4e8c", lw=1.3, label="TSMOM + VIX overlay (net of 10 bps/side and financing)")
a.plot(spy / spy.iloc[0], color="#999", lw=0.8, label="SPY buy & hold (total return)")
a.set_yscale("log"); a.set_ylabel("Growth of $1")
for ax in (a, b):
    ax.axvspan(pd.Timestamp("2024-10-01"), r.index[-1], color="#f2c14e", alpha=0.25, lw=0)
a.text(pd.Timestamp("2024-10-20"), a.get_ylim()[0] * 1.08, "OOS", fontsize=8)
a.legend(frameon=False, fontsize=7.5, loc="upper left"); a.grid(alpha=0.25)
b.fill_between(dd.index, dd, 0, color="#b33", alpha=0.6, lw=0); b.set_ylabel("Drawdown")
b.yaxis.set_major_formatter(matplotlib.ticker.PercentFormatter(1.0, decimals=0)); b.grid(alpha=0.25)
fig.tight_layout(); fig.savefig(OUT / "fig1_equity.png", dpi=220)

t = pd.read_csv(ROOT / "strategy/output/results_is.csv", index_col=[0, 1])
lb = {"3m": "3_base_3m", "6m": "4_base_6m", "9m": "5_base_9m", "12m": "1_base_12m"}
fig, ax = plt.subplots(figsize=(3.0, 1.9))
ax.bar(list(lb), [t.loc[(v, "IS"), "sharpe"] for v in lb.values()], color=["#9db4d6"] * 3 + ["#1f4e8c"])
ax.set_ylabel("IS net Sharpe"); ax.set_xlabel("Lookback"); ax.grid(alpha=0.25, axis="y"); ax.set_ylim(0, 0.4)
fig.tight_layout(); fig.savefig(OUT / "fig2_plateau.png", dpi=220)
print("ok")
