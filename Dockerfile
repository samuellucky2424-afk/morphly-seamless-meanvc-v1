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
COPY requirements.meanvc-runtime.txt /opt/morphly/requirements.meanvc-runtime.txt

# MeanVC2 runtime does not import fairseq. fairseq is listed only in the
# upstream evaluation dependency group, and conflicts with modern pip/
# OmegaConf on Python 3.11. Keep the inference image lean and isolated.
RUN python3.11 -m pip install torch==2.5.1 torchaudio==2.5.1 --index-url https://download.pytorch.org/whl/cu121 && \
    python3.11 -m pip install -r /opt/morphly/requirements.meanvc-runtime.txt && \
    python3.11 -m pip install -r /opt/morphly/requirements.txt

# Install Meta Seamless separately so fairseq2/PyTorch ABI problems are
# visible as their own Docker layer instead of being mixed with MeanVC2.
RUN cd /opt/seamless_communication && python3.11 -m pip install .

COPY . /opt/morphly

RUN python3.11 scripts/verify_environment.py

ENTRYPOINT ["python3.11", "scripts/smoke_test.py"]
