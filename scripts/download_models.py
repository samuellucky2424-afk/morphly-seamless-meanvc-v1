from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

p = argparse.ArgumentParser()
p.add_argument("--meanvc", action="store_true")
args = p.parse_args()

if not args.meanvc:
    p.error("No model group selected. Start with --meanvc.")

root = Path("/opt/MeanVC2")
if not root.exists():
    raise SystemExit(f"MeanVC2 source not found at {root}")

subprocess.run(
    [sys.executable, "initialization.py", "--task", "all"],
    cwd=root,
    check=True,
)
print("MeanVC2 upstream model initialization complete.")
