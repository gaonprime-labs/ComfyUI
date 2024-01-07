FROM nvidia/cuda:12.1.0-runtime-ubuntu20.04

# Install dependencies in a single layer
RUN apt-get update && apt-get install -y --no-install-recommends \
  software-properties-common \
  && add-apt-repository ppa:deadsnakes/ppa \
  && apt-get update \
  && apt-get install -y --no-install-recommends \
  wget \
  build-essential \
  gcc \
  git \
  libgl1-mesa-glx \
  && rm -rf /var/lib/apt/lists/*

# install conda
RUN wget https://repo.anaconda.com/miniconda/Miniconda3-latest-Linux-x86_64.sh -O ~/miniconda.sh && \
  bash ~/miniconda.sh -b -p /opt/conda && \
  rm ~/miniconda.sh && \
  /opt/conda/bin/conda clean -tipy && \
  ln -s /opt/conda/etc/profile.d/conda.sh /etc/profile.d/conda.sh && \
  echo ". /opt/conda/etc/profile.d/conda.sh" >> ~/.bashrc
RUN bash -c "source ~/.bashrc"

# setup venv
ENV PYTHON_VERSION=3.11
RUN /opt/conda/bin/conda update -n base conda
RUN /opt/conda/bin/conda install -y python=$PYTHON_VERSION
RUN /opt/conda/bin/conda create -n py311 python=$PYTHON_VERSION
RUN /opt/conda/bin/conda clean --all -y

# use python3.11 in container
RUN ln -s /opt/conda/envs/py311/bin/python3.11 /usr/bin/python3.11

ENV PATH /opt/conda/envs/py311/bin:$PATH

# Consolidate pip installs with conda installs
RUN /opt/conda/envs/py311/bin/pip install --no-cache-dir \
  torch \
  torchvision \
  torchaudio \
  onnxruntime \
  --extra-index-url https://download.pytorch.org/whl/cu121

RUN /opt/conda/envs/py311/bin/pip install --no-cache-dir \
  opencv-python \
  opencv-python-headless \
  opencv-contrib-python \
  insightface \
  matplotlib \
  basicsr \
  openai \
  numba \
  simple_lama_inpainting \
  segment_anything \
  ultralytics \
  clip_interrogator \
  pyOpenSSL \
  watchdog

COPY requirements.txt .

RUN /opt/conda/envs/py311/bin/pip install --no-cache-dir -r requirements.txt

COPY requirements-primelabs.txt .

RUN /opt/conda/envs/py311/bin/pip install --no-cache-dir -r requirements-primelabs.txt

# Copy source code
COPY . /app

# Set working directory
WORKDIR /app

# Run whit conda env
CMD ["/opt/conda/envs/py311/bin/python3", "main.py", "--listen", "0.0.0.0", "--port", "8188"]
