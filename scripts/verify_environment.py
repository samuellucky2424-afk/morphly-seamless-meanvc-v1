from __future__ import annotations

import importlib
import json
import subprocess
import sys
import torch

MODULES = ["seamless_communication", "soundfile", "numpy"]

def version(name: str):
    try:
        mod = importlib.import_module(name)
        return getattr(mod, "__version__", "import-ok")
    except Exception as exc:
        return f"ERROR: {type(exc).__name__}: {exc}"

def pip_check():
    p = subprocess.run(
        [sys.executable, "-m", "pip", "check"],
        text=True, capture_output=True
    )
    return {"code": p.returncode, "stdout": p.stdout.strip(), "stderr": p.stderr.strip()}

report = {
    "python": sys.version,
    "torch": torch.__version__,
    "torch_cuda": torch.version.cuda,
    "cuda_available": torch.cuda.is_available(),
    "gpu": torch.cuda.get_device_name(0) if torch.cuda.is_available() else None,
    "imports": {m: version(m) for m in MODULES},
    "pip_check": pip_check(),
}
print(json.dumps(report, indent=2))
if report["pip_check"]["code"] != 0:
    raise SystemExit("Dependency consistency check failed.")
