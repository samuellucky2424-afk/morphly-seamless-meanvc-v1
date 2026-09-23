#!/usr/bin/env bash
set -euo pipefail

echo "=== Morphly on-demand GPU preflight ==="
echo
echo "[1/5] GPU"
nvidia-smi --query-gpu=name,memory.total,driver_version --format=csv,noheader
echo
echo "[2/5] CUDA compiler/runtime visibility"
python - <<'PY'
import torch
print("python torch:", torch.__version__)
print("cuda runtime:", torch.version.cuda)
print("cuda available:", torch.cuda.is_available())
if torch.cuda.is_available():
    print("gpu:", torch.cuda.get_device_name(0))
    print("vram_gb:", round(torch.cuda.get_device_properties(0).total_memory/2**30, 2))
PY
echo
echo "[3/5] Disk"
df -h /workspace || df -h .
echo
echo "[4/5] CPU/RAM"
python - <<'PY'
import os
try:
    import psutil
    print("cpu_count:", os.cpu_count())
    print("ram_gb:", round(psutil.virtual_memory().total/2**30, 2))
except Exception as e:
    print("psutil unavailable:", e)
PY
echo
echo "[5/5] Repo"
git rev-parse --short HEAD
echo "PREFLIGHT_OK"
