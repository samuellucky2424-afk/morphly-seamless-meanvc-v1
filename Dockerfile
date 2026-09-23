FROM nvidia/cuda:12.1.1-cudnn8-runtime-ubuntu22.04

ENV DEBIAN_FRONTEND=noninteractive \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    HF_HOME=/models/huggingface \
    TORCH_HOME=/models/torch

RUN apt-get update && apt-get install -y --no-install-recommends \
    git git-lfs ffmpeg libsndfile1 build-essential ca-certificates curl \
    python3.11 python3.11-dev python3-pip && \
    rm -rf /var/lib/apt/lists/* && \
    python3.11 -m pip install --upgrade pip setuptools wheel

WORKDIR /opt/morphly

RUN git clone --depth 1 https://github.com/facebookresearch/seamless_communication.git /opt/seamless_communication && \
    git clone --depth 1 https://github.com/ASLP-lab/MeanVC2.git /opt/MeanVC2

COPY requirements.txt /opt/morphly/requirements.txt

RUN python3.11 -m pip install torch==2.5.1 torchaudio==2.5.1 --index-url https://download.pytorch.org/whl/cu121 && \
    python3.11 -m pip install -r /opt/MeanVC2/requirements.txt && \
    python3.11 -m pip install -r /opt/morphly/requirements.txt

COPY . /opt/morphly

ENTRYPOINT ["python3.11", "scripts/smoke_test.py"]
