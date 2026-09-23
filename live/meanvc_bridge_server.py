from __future__ import annotations

import os
import sys
import threading
import time
from pathlib import Path

import numpy as np
import torch
import torchaudio.functional as AF
from fastapi import FastAPI, Request, Response

MEANVC_ROOT = Path(os.environ.get("MEANVC_ROOT", "/workspace/MeanVC2"))
TARGET_WAV = os.environ.get("MEANVC_TARGET_WAV", str(MEANVC_ROOT / "test_audio/target.wav"))
MODEL = os.environ.get("MEANVC_MODEL", "120ms")
DEVICE = os.environ.get("MEANVC_DEVICE", "cuda")

sys.path.insert(0, str(MEANVC_ROOT / "runtime"))
from run_rt import VCRunner  # noqa: E402

app = FastAPI(title="Morphly MeanVC Live Bridge", version="0.1.0")

_lock = threading.Lock()
_input_buffer = np.zeros(0, dtype=np.float32)

print(f"[MeanVC bridge] loading model={MODEL} device={DEVICE} target={TARGET_WAV}")
vc = VCRunner(target_wav=TARGET_WAV, device=DEVICE, model=MODEL)

# Warm CUDA/model kernels, then reset stream state before accepting live audio.
warmup = np.zeros(vc.CHUNK, dtype=np.float32)
for _ in range(3):
    vc.process_chunk(warmup)
vc._init_cache()
print(f"[MeanVC bridge] ready chunk={vc.CHUNK} samples @16kHz")


def _to_16k(x: np.ndarray, sr: int) -> np.ndarray:
    if sr == 16000:
        return x.astype(np.float32, copy=False)
    t = torch.from_numpy(x.astype(np.float32, copy=False))
    y = AF.resample(t, orig_freq=sr, new_freq=16000)
    return y.cpu().numpy().astype(np.float32, copy=False)


@app.get("/health")
def health():
    return {
        "ok": True,
        "device": DEVICE,
        "model": MODEL,
        "target_wav": TARGET_WAV,
        "cuda": torch.cuda.is_available(),
        "gpu": torch.cuda.get_device_name(0) if torch.cuda.is_available() else None,
        "chunk_samples": vc.CHUNK,
    }


@app.post("/reset")
def reset():
    global _input_buffer
    with _lock:
        _input_buffer = np.zeros(0, dtype=np.float32)
        vc._init_cache()
    return {"ok": True}


@app.post("/convert")
async def convert(request: Request):
    global _input_buffer

    sr = int(request.headers.get("x-sample-rate", "16000"))
    raw = await request.body()
    if not raw:
        return Response(content=b"", media_type="application/octet-stream", headers={"X-Sample-Rate": "16000"})

    x = np.frombuffer(raw, dtype="<f4").astype(np.float32, copy=False)
    x = _to_16k(x, sr)

    started = time.perf_counter()
    out_parts: list[np.ndarray] = []

    with _lock:
        _input_buffer = np.concatenate([_input_buffer, x])

        while _input_buffer.size >= vc.CHUNK:
            chunk = _input_buffer[: vc.CHUNK]
            _input_buffer = _input_buffer[vc.CHUNK :]
            out = vc.process_chunk(chunk)
            if out is not None and out.size:
                out_parts.append(out.astype(np.float32, copy=False))

    elapsed_ms = (time.perf_counter() - started) * 1000.0
    if out_parts:
        y = np.concatenate(out_parts).astype("<f4", copy=False)
        body = y.tobytes()
        n_out = y.size
    else:
        body = b""
        n_out = 0

    return Response(
        content=body,
        media_type="application/octet-stream",
        headers={
            "X-Sample-Rate": "16000",
            "X-MeanVC-Proc-Ms": f"{elapsed_ms:.2f}",
            "X-MeanVC-Out-Samples": str(n_out),
        },
    )
