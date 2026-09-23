FROM nvidia/cuda:12.1.1-cudnn8-runtime-ubuntu22.04

ENV DEBIAN_FRONTEND=noninteractive \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    HF_HOME=/models/huggingface \
    TORCH_HOME=/models/torch

RUN apt-get update && apt-get install -y --no-install-recommends \
    git git-lfs ffmpeg libsndfile1 libsndfile1-dev build-essential ca-certificates curl \
    python3.11 python3.11-dev python3-pip && \
    rm -rf /var/lib/apt/lists/* && \
    python3.11 -m pip install --upgrade pip setuptools wheel

WORKDIR /opt/morphly

ARG SEAMLESS_REF=main
ARG MEANVC2_REF=main

RUN git clone https://github.com/facebookresearch/seamless_communication.git /opt/seamless_communication && \
    git -C /opt/seamless_communication checkout "$SEAMLESS_REF" && \
    git clone https://github.com/ASLP-lab/MeanVC2.git /opt/MeanVC2 && \
    git -C /opt/MeanVC2 checkout "$MEANVC2_REF"

COPY requirements.txt /opt/morphly/requirements.txt

# MeanVC2 runtime baseline. Install fairseq from the upstream v0.12.2 source
# tree because its PyPI sdist can fail under modern isolated builds.
RUN python3.11 -m pip install torch==2.5.1 torchaudio==2.5.1 --index-url https://download.pytorch.org/whl/cu121 && \
    git clone --branch v0.12.2 --depth 1 https://github.com/facebookresearch/fairseq.git /tmp/fairseq && \
    python3.11 -m pip install --no-build-isolation /tmp/fairseq && \
    sed -E '/^(torch|torchaudio|fairseq)([<>=].*)?$/d' /opt/MeanVC2/requirements.txt > /tmp/meanvc2-requirements.txt && \
    python3.11 -m pip install -r /tmp/meanvc2-requirements.txt && \
    python3.11 -m pip install -r /opt/morphly/requirements.txt

# Install Meta Seamless separately so any fairseq2/PyTorch compatibility
# problem is isolated in the Docker build log.
RUN cd /opt/seamless_communication && python3.11 -m pip install .

COPY . /opt/morphly

ENTRYPOINT ["python3.11", "scripts/smoke_test.py"]
