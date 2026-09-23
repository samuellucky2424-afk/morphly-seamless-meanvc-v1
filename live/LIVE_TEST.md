# Live SeamlessStreaming -> MeanVC2 test

Architecture:

browser microphone -> SeamlessStreaming -> local HTTP bridge -> MeanVC2 120ms -> browser playback

MeanVC2 must not use `runtime/run_rt.py --mode realtime` on a remote GPU. That CLI opens a local sounddevice device on the GPU host. The bridge calls `VCRunner.process_chunk()` directly instead.

## Terminal A: MeanVC bridge

```bash
conda activate /workspace/envs/meanvc
python -m pip install --no-cache-dir fastapi "uvicorn[standard]" requests

export MEANVC_TARGET_WAV=/workspace/MeanVC2/test_audio/target.wav
export MEANVC_MODEL=120ms
export MEANVC_DEVICE=cuda

cd /workspace/morphly-seamless-meanvc-v1
uvicorn live.meanvc_bridge_server:app --host 127.0.0.1 --port 8766
```

Check:

```bash
curl http://127.0.0.1:8766/health
```

## Terminal B: Seamless browser demo

Clone the official Hugging Face Space if it is not already present:

```bash
cd /workspace
git clone https://huggingface.co/spaces/facebook/seamless-streaming seamless-live
```

Install only the server/frontend extras; do not replace the working torch/fairseq2 stack.

```bash
conda activate /workspace/envs/seamless
python -m pip install --no-cache-dir colorlog==6.7.0 python-socketio==5.9.0 \
  "uvicorn[standard]==0.23.2" starlette==0.32.0.post1 g2p_en==2.1.0 requests
```

Build the frontend if needed, then replace the demo helper with the Morphly bridge:

```bash
cp /workspace/morphly-seamless-meanvc-v1/live/transcoder_helpers_meanvc.py \
   /workspace/seamless-live/seamless_server/src/transcoder_helpers.py

export XDG_CACHE_HOME=/workspace/models/cache
export MORPHLY_MEANVC_ENABLED=1
export MORPHLY_MEANVC_URL=http://127.0.0.1:8766
```

Start the demo server from `/workspace/seamless-live/seamless_server`.

## Metrics

Watch GPU memory/utilization in a third terminal:

```bash
watch -n 0.5 nvidia-smi
```

The Seamless server log will print `MORPHLY_MEANVC ... meanvc_ms=... bridge_ms=...` for converted output chunks.
