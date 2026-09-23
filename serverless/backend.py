from __future__ import annotations

import json
import os
import subprocess
import time
from fastapi import FastAPI

app = FastAPI(title="Morphly GPU Smoke Backend", version="0.1.0")

MEANVC_PY = os.environ.get("MEANVC_PY", "/opt/venvs/meanvc/bin/python")
SEAMLESS_PY = os.environ.get("SEAMLESS_PY", "/opt/venvs/seamless/bin/python")

PROBE = r"""
import json, torch, torchaudio
out = {
    "torch": torch.__version__,
    "torchaudio": torchaudio.__version__,
    "cuda_runtime": torch.version.cuda,
    "cuda_available": torch.cuda.is_available(),
    "gpu": torch.cuda.get_device_name(0) if torch.cuda.is_available() else None,
    "vram_gb": round(torch.cuda.get_device_properties(0).total_memory / 2**30, 2)
        if torch.cuda.is_available() else None,
}
print(json.dumps(out))
"""

def probe_env(python_path: str) -> dict:
    started = time.perf_counter()
    raw = subprocess.check_output([python_path, "-c", PROBE], text=True, timeout=90)
    data = json.loads(raw.strip())
    data["probe_ms"] = round((time.perf_counter() - started) * 1000, 1)
    return data

@app.get("/health")
async def health():
    return {"ok": True, "service": "morphly-gpu-smoke"}

@app.post("/diagnostics")
async def diagnostics(payload: dict | None = None):
    started = time.perf_counter()
    meanvc = probe_env(MEANVC_PY)
    seamless = probe_env(SEAMLESS_PY)
    return {
        "ok": bool(meanvc["cuda_available"] and seamless["cuda_available"]),
        "meanvc": meanvc,
        "seamless": seamless,
        "total_probe_ms": round((time.perf_counter() - started) * 1000, 1),
        "note": "GPU/environment smoke test only; model checkpoints are not loaded yet.",
    }
