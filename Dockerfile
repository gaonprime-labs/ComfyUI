FROM nvidia/cuda:12.1.0-runtime-ubuntu20.04

# Install dependencies in a single layer
RUN apt-get update && apt-get install -y --no-install-recommends \
  software-properties-common \
  && add-apt-repository ppa:deadsnakes/ppa \
  && apt-get update \
  && apt-get install -y --no-install-recommends \
  build-essential \
  python3.8 \
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
  torch \
  torchvision \
  torchaudio \
  onnxruntime \
  --extra-index-url https://download.pytorch.org/whl/cu121

COPY requirements.txt .

RUN pip3 install --no-cache-dir \
  opencv-python \
  opencv-python-headless \
  opencv-contrib-python \
  insightface \
  matplotlib \
  basicsr \
  openai \
  numba

RUN pip3 install --no-cache-dir -r requirements.txt

COPY requirements-primelabs.txt .

RUN pip3 install --no-cache-dir -r requirements-primelabs.txt

# Copy source code
COPY . /app

# Set working directory
WORKDIR /app

# Run
CMD ["python3", "main.py", "--listen", "0.0.0.0", "--port", "8188"]
