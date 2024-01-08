FROM nvidia/cuda:12.1.0-runtime-ubuntu20.04

# Install dependencies in a single layer
RUN apt-get update && apt-get install -y --no-install-recommends \
  software-properties-common \
  && add-apt-repository ppa:deadsnakes/ppa \
  && apt-get update \
  && apt-get install -y --no-install-recommends \
  build-essential \
  gcc \
  git \
  libgl1-mesa-glx \
  wget \
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

# create symlinks
RUN ln -s /opt/conda/envs/py311/bin/python /usr/local/bin/python
RUN ln -s /opt/conda/envs/py311/bin/python /usr/local/bin/python3
RUN ln -s /opt/conda/envs/py311/bin/pip /usr/local/bin/pip
RUN ln -s /opt/conda/envs/py311/bin/pip /usr/local/bin/pip3

# Consolidate pip installs
RUN /opt/conda/envs/py311/bin/pip install --no-cache-dir \
  torch==2.1.1 \
  torchaudio==2.1.1 \
  torchvision==0.16.1 \
  --extra-index-url https://download.pytorch.org/whl/cu121

COPY requirements-primelabs.txt .

RUN /opt/conda/envs/py311/bin/pip install --no-cache-dir -r requirements-primelabs.txt

COPY requirements.txt .

RUN /opt/conda/envs/py311/bin/pip install --no-cache-dir -r requirements.txt

# Copy source code
COPY . /app

# Set working directory
WORKDIR /app

# Run
CMD ["/opt/conda/envs/py311/bin/python", "main.py", "--listen", "0.0.0.0", "--port", "8188"]
