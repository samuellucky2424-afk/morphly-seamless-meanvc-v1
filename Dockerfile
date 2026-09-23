FROM nvidia/cuda:12.1.1-cudnn8-runtime-ubuntu22.04

ENV DEBIAN_FRONTEND=noninteractive \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    HF_HOME=/models/huggingface \
    TORCH_HOME=/models/torch \
    MEANVC_PY=/opt/venvs/meanvc/bin/python \
    SEAMLESS_PY=/opt/venvs/seamless/bin/python \
    WORKER_PY=/opt/venvs/worker/bin/python \
    MODEL_SERVER_PORT=18000

RUN apt-get update && apt-get install -y --no-install-recommends \
    git git-lfs ffmpeg libsndfile1 libsndfile1-dev build-essential ca-certificates curl \
    python3.11 python3.11-dev python3.11-venv python3-pip && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /opt/morphly

ARG SEAMLESS_REF=main
ARG MEANVC2_REF=main

RUN git clone https://github.com/facebookresearch/seamless_communication.git /opt/seamless_communication && \
    git -C /opt/seamless_communication checkout "$SEAMLESS_REF" && \
    git clone https://github.com/ASLP-lab/MeanVC2.git /opt/MeanVC2 && \
    git -C /opt/MeanVC2 checkout "$MEANVC2_REF"

COPY requirements.txt /opt/morphly/requirements.txt
COPY requirements.meanvc-runtime.txt /opt/morphly/requirements.meanvc-runtime.txt
COPY requirements.worker.txt /opt/morphly/requirements.worker.txt
COPY constraints.seamless.txt /opt/morphly/constraints.seamless.txt

# MeanVC2 and Seamless/fairseq2 require different PyTorch ABI stacks.
# Keep them isolated and communicate between services over loopback later.
RUN python3.11 -m venv /opt/venvs/meanvc && \
    /opt/venvs/meanvc/bin/python -m pip install --upgrade "pip==24.0" "setuptools==69.5.1" "wheel==0.43.0" && \
    /opt/venvs/meanvc/bin/python -m pip install torch==2.5.1 torchaudio==2.5.1 --index-url https://download.pytorch.org/whl/cu121 && \
    /opt/venvs/meanvc/bin/python -m pip install -r /opt/morphly/requirements.meanvc-runtime.txt && \
    /opt/venvs/meanvc/bin/python -m pip install -r /opt/morphly/requirements.txt

RUN python3.11 -m venv /opt/venvs/seamless && \
    /opt/venvs/seamless/bin/python -m pip install --upgrade "pip==24.0" "setuptools==67.8.0" "wheel==0.40.0" "packaging==23.2" && \
    /opt/venvs/seamless/bin/python -m pip install torch==2.2.2 torchaudio==2.2.2 --index-url https://download.pytorch.org/whl/cu121 && \
    cd /opt/seamless_communication && \
    /opt/venvs/seamless/bin/python -m pip install -c /opt/morphly/constraints.seamless.txt .

RUN python3.11 -m venv /opt/venvs/worker && \
    /opt/venvs/worker/bin/python -m pip install --upgrade "pip==24.0" && \
    /opt/venvs/worker/bin/python -m pip install -r /opt/morphly/requirements.worker.txt

COPY . /opt/morphly

RUN /opt/venvs/meanvc/bin/python scripts/verify_environment.py --mode meanvc && \
    /opt/venvs/seamless/bin/python scripts/verify_environment.py --mode seamless && \
    /opt/venvs/worker/bin/python -c "from vastai import Worker, WorkerConfig, HandlerConfig, BenchmarkConfig, LogActionConfig; print('VAST_WORKER_IMPORT_OK')" && \
    chmod +x /opt/morphly/serverless/start.sh

EXPOSE 3000 3001
ENTRYPOINT ["bash", "/opt/morphly/serverless/start.sh"]
