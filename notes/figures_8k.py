"""Figure for the Massive note (run with the starter's venv: pickles are pandas 3)."""
from pathlib import Path
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
O = ROOT / "strategy_8k/output"
OUT = Path(__file__).parent
H = [1, 2, 3, 5, 10, 21, 42, 63]


def ratio(res):
    r = res[(res.bucket == "3-6m") & (res.entry == "pre") & (res.otm == 0.05)]
    rows = []
    rng = np.random.default_rng(0)
    for h in H:
        x = r.loc[r.horizon == h, "ratio"].dropna().to_numpy()
        m = rng.choice(x, (2000, len(x))).mean(1)
        rows.append((h, x.mean(), *np.percentile(m, [2.5, 97.5]), len(x)))
    return pd.DataFrame(rows, columns=["h", "mean", "lo", "hi", "n"]).set_index("h")


fig, axes = plt.subplots(1, 3, figsize=(7.4, 2.25), sharey=True)
for ax, lab, title in zip(axes, ["straddle_2223", "is", "oos"], ["2022-23 (straddle test)", "2024-25 (in-sample)", "Jan-Aug 2026 (OOS)"]):
    for key, col, name in [("results", "#b33", "Exec-exit events"), ("placebo_results", "#777", "Same names, ordinary days")]:
        d = ratio(pd.read_pickle(O / f"{lab}_{key}.pkl"))
        x = np.arange(len(H)) + (0.12 if key == "results" else -0.12)
        ax.errorbar(x, d["mean"], yerr=[d["mean"] - d["lo"], d["hi"] - d["mean"]], fmt="o", ms=3.5, color=col,
                    capsize=2, lw=1, label=name)
        d.to_csv(OUT / f"ratio_{lab}_{key}.csv")
    ax.axhline(1, color="k", lw=0.7, ls="--"); ax.set_xticks(range(len(H))); ax.set_xticklabels(H, fontsize=7)
    ax.set_title(title, fontsize=9); ax.set_xlabel("Sessions after filing", fontsize=8); ax.grid(alpha=0.25)
axes[0].set_ylabel("|realized| / implied move"); axes[0].legend(frameon=False, fontsize=7)
fig.tight_layout(); fig.savefig(OUT / "fig3_8k_ratio.png", dpi=220)
print("ok")
