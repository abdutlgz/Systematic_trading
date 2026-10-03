"""Reproduce every headline number: python strategy/run_all.py [--oos]"""
import subprocess
import sys
from pathlib import Path

here = Path(__file__).parent
extra = ["--oos"] if "--oos" in sys.argv else []
if not (here / "data" / "SPY.csv").exists():
    subprocess.run([sys.executable, str(here / "download.py")], check=True)
subprocess.run([sys.executable, str(here / "backtest.py"), *extra], check=True, cwd=here)
subprocess.run([sys.executable, str(here / "analysis.py"), *extra], check=True, cwd=here)
