from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path
import torch

ROOTS = {
    "seamless": Path("/opt/seamless_communication"),
    "meanvc2": Path("/opt/MeanVC2"),
}

def git_sha(path: Path):
    try:
        return subprocess.check_output(
            ["git", "-C", str(path), "rev-parse", "HEAD"], text=True
        ).strip()
    except Exception:
        return None

report = {
    "python": sys.version.split()[0],
    "torch": torch.__version__,
    "cuda_available": torch.cuda.is_available(),
    "cuda_runtime": torch.version.cuda,
    "gpu": torch.cuda.get_device_name(0) if torch.cuda.is_available() else None,
    "gpu_vram_gb": round(torch.cuda.get_device_properties(0).total_memory / 2**30, 2)
        if torch.cuda.is_available() else None,
    "sources": {
        name: {"exists": path.exists(), "sha": git_sha(path)}
        for name, path in ROOTS.items()
    },
}
print(json.dumps(report, indent=2))

if not torch.cuda.is_available():
    raise SystemExit("CUDA GPU is required for the Vast experiment.")
if not all(v["exists"] for v in report["sources"].values()):
    raise SystemExit("One or more upstream source trees are missing.")
print("SMOKE_TEST_OK")
