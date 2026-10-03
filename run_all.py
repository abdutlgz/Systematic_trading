"""Reproduce every headline number in notes/quant_note.pdf with one command:

    python run_all.py            # downloads public data on first run (Yahoo, CBOE, French, Treasury, Fed, FRED, Open-Meteo)

The out-of-sample periods were evaluated once (see git history); rerunning reproduces the same numbers.
The Massive bonus pipeline needs an API key and its own venv; see README.md.
"""
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).parent
STEPS = [
    ["strategy/run_all.py", "--oos"],      # momentum: data, backtest, analysis (Table 1, Fig 1, Sections 5-7)
    ["screen/download.py"],                # data for the 10-hypothesis screen
    ["screen/screen.py"],                  # Appendix A
    ["screen/portfolio.py", "--oos"],      # Section 5.3 portfolio row
    ["screen/audit.py"],                   # Appendix B, nine-pitfall audit
    ["lab/lab.py"],                        # Section 5.3 thematic lab row
    ["notes/figures.py"],                  # Figures 1-2
]
for step in STEPS:
    print(f"\n>>> python {' '.join(step)}", flush=True)
    subprocess.run([sys.executable, str(ROOT / step[0]), *step[1:]], check=True, cwd=ROOT)
print("\nDone. Outputs: strategy/output/, screen/output/, notes/")
