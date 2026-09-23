from __future__ import annotations

import argparse
import importlib
import json
import subprocess
import sys
import torch

p = argparse.ArgumentParser()
p.add_argument("--mode", choices=["meanvc", "seamless"], required=True)
args = p.parse_args()

modules = {
    "meanvc": ["torch", "torchaudio", "numpy", "soundfile", "einops", "x_transformers", "s3prl"],
    "seamless": ["torch", "torchaudio", "fairseq2", "seamless_communication"],
}[args.mode]

def version(name: str):
    try:
        mod = importlib.import_module(name)
        return getattr(mod, "__version__", "import-ok")
    except Exception as exc:
        return f"ERROR: {type(exc).__name__}: {exc}"

check = subprocess.run(
    [sys.executable, "-m", "pip", "check"],
    text=True,
    capture_output=True,
)

report = {
    "mode": args.mode,
    "python_executable": sys.executable,
    "python": sys.version.split()[0],
    "torch": torch.__version__,
    "torch_cuda": torch.version.cuda,
    "cuda_available_at_build": torch.cuda.is_available(),
    "imports": {m: version(m) for m in modules},
    "pip_check": {
        "code": check.returncode,
        "stdout": check.stdout.strip(),
        "stderr": check.stderr.strip(),
    },
}
print(json.dumps(report, indent=2))

bad_imports = [k for k, v in report["imports"].items() if str(v).startswith("ERROR:")]
if bad_imports:
    raise SystemExit(f"{args.mode}: import failures: {bad_imports}")
if check.returncode != 0:
    raise SystemExit(f"{args.mode}: dependency consistency check failed.")
