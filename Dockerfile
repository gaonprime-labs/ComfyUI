FROM nvidia/cuda:12.1.0-runtime-ubuntu20.04

# Install dependencies in a single layer
RUN apt-get update && apt-get install -y --no-install-recommends \
  software-properties-common \
  && add-apt-repository ppa:deadsnakes/ppa \
  && apt-get update \
  && apt-get install -y --no-install-recommends \
  build-essential \
  python3.11 \
  python3-pip \
  python3-setuptools \
  python3-wheel \
  python3-dev \
  gcc \
  git \
  libgl1-mesa-glx \
  && rm -rf /var/lib/apt/lists/*

# Consolidate pip installs
RUN pip3 install --no-cache-dir \
  torch==2.1.1 \
  torchaudio==2.1.1 \
  torchvision==0.16.1 \
  --extra-index-url https://download.pytorch.org/whl/cu121

COPY requirements-primelabs.txt .

RUN pip3 install --no-cache-dir -r requirements-primelabs.txt

COPY requirements.txt .

RUN pip3 install --no-cache-dir -r requirements.txt

RUN pip3 install --no-cache-dir \
  clip_interrogator

# Copy source code
COPY . /app

# Set working directory
WORKDIR /app

# Run
CMD ["python3", "main.py", "--listen", "0.0.0.0", "--port", "8188"]
