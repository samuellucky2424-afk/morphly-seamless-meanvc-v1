# Morphly Seamless + MeanVC2 v1

Experimental GPU pipeline for Morphly:

```
microphone/audio -> SeamlessStreaming -> MeanVC2 -> output audio
```

## Milestone 1

Build one reproducible CUDA/Python 3.11 container containing the official Seamless Communication and MeanVC2 source trees, verify RTX A6000 CUDA execution, then benchmark each model independently before joining them.

Upstreams:
- https://github.com/facebookresearch/seamless_communication
- https://github.com/ASLP-lab/MeanVC2

## Build

```bash
docker build -t morphly-seamless-meanvc:v1 .
docker run --rm --gpus all morphly-seamless-meanvc:v1
```

The default entrypoint is a CUDA/source-tree smoke test. The combined real-time pipeline is intentionally not marked complete until both upstream runtimes are verified on the target GPU.

## MeanVC2 checkpoints

Inside the container:

```bash
python3.11 scripts/download_models.py --meanvc
```

## Benchmark order

1. SeamlessStreaming alone.
2. MeanVC2 alone.
3. Combined translated-audio -> voice-conversion path.
4. Warm-session concurrency: one user, then two.
5. Record cold start separately from steady-state latency.

See `docs/BENCHMARK_PLAN.md`.

## Deployment

The production target is Docker ENTRYPOINT mode. Vast-specific serverless/session glue is added only after the model container passes the GPU smoke tests, so the core image remains portable to another NVIDIA host.
