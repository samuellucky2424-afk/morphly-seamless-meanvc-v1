from __future__ import annotations

import json
import os
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

def env_probe(python_path: str):
    code = (
        "import json,torch,torchaudio;"
        "print(json.dumps({'python':__import__('sys').version.split()[0],"
        "'torch':torch.__version__,'torchaudio':torchaudio.__version__,"
        "'cuda':torch.version.cuda,'cuda_available':torch.cuda.is_available(),"
        "'gpu':torch.cuda.get_device_name(0) if torch.cuda.is_available() else None,"
        "'vram_gb':round(torch.cuda.get_device_properties(0).total_memory/2**30,2) "
        "if torch.cuda.is_available() else None}))"
    )
    return json.loads(subprocess.check_output([python_path, "-c", code], text=True))

meanvc_py = os.environ.get("MEANVC_PY", "/opt/venvs/meanvc/bin/python")
seamless_py = os.environ.get("SEAMLESS_PY", "/opt/venvs/seamless/bin/python")

report = {
    "launcher_python": sys.executable,
    "sources": {
        name: {"exists": path.exists(), "sha": git_sha(path)}
        for name, path in ROOTS.items()
    },
    "meanvc_env": env_probe(meanvc_py),
    "seamless_env": env_probe(seamless_py),
}
print(json.dumps(report, indent=2))

if not all(v["exists"] for v in report["sources"].values()):
    raise SystemExit("One or more upstream source trees are missing.")
if not report["meanvc_env"]["cuda_available"]:
    raise SystemExit("MeanVC2 environment cannot see CUDA.")
if not report["seamless_env"]["cuda_available"]:
    raise SystemExit("Seamless environment cannot see CUDA.")

print("SMOKE_TEST_OK")
