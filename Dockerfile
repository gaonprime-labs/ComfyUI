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
ENV PYTHON_VERSION=3.9
RUN /opt/conda/bin/conda update -n base conda
RUN /opt/conda/bin/conda install -y python=$PYTHON_VERSION
RUN /opt/conda/bin/conda create -n py39 python=$PYTHON_VERSION
RUN /opt/conda/bin/conda clean --all -y

# activate venv
RUN echo "source activate py39" > ~/.bashrc

# Consolidate pip installs
RUN /opt/conda/envs/py39/bin/pip install --no-cache-dir \
  torch \
  torchvision \
  torchaudio \
  onnxruntime \
  --extra-index-url https://download.pytorch.org/whl/cu121

RUN /opt/conda/envs/py39/bin/pip install --no-cache-dir \
  opencv-python \
  opencv-python-headless \
  opencv-contrib-python \
  insightface \
  matplotlib \
  basicsr \
  openai \
  numba \
  python-dotenv \
  boto3 \
  pika \
  simple_lama_inpainting \
  segment_anything \
  ultralytics \
  clip_interrogator \
  pyOpenSSL \
  watchdog 

COPY requirements.txt .

RUN /opt/conda/envs/py39/bin/pip install --no-cache-dir -r requirements.txt

# Copy source code
COPY . /app

# Set working directory
WORKDIR /app

# Run
CMD ["python3", "main.py", "--listen", "0.0.0.0", "--port", "8188"]
