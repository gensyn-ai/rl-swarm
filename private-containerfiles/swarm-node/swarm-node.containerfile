FROM europe-docker.pkg.dev/gensyn-main/registry/nvidia-cuda:12.6.3-cudnn-devel-ubuntu24.04 AS base
LABEL maintainer="Christopher Nies <christopher@gensyn.ai>"

# Common libraries used by Python. These pre-requisited are recommended for the general Python
RUN apt update -y && \
    apt install -y \
    sudo \
    make \
    gcc \
    lld \
    libncurses-dev \
    libffi-dev \
    liblzma-dev \
    zlib1g zlib1g-dev \
    build-essential \
    libssl-dev \
    libbz2-dev \
    libreadline-dev \
    libsqlite3-dev \
    xz-utils \
    tk-dev \
    libxml2-dev libxmlsec1-dev \
    git curl jq neovim && \
    useradd gensyn --user-group --create-home --shell /bin/bash && \
    echo 'export PATH=/usr/local/cuda/bin:$PATH' >> ~/.bashrc && \
    echo 'export LD_LIBRARY_PATH=/usr/local/cuda/lib64:$LD_LIBRARY_PATH' >> ~/.bashrc && \
    apt-get autoremove -y && \
    apt-get clean

WORKDIR /home/gensyn

COPY ./private-containerfiles/swarm-node/versions.json ./versions.json
COPY ./private-containerfiles/swarm-node/setup_python.sh ./setup_python.sh
COPY ./private-containerfiles/swarm-node/install_pip.sh ./install_pip.sh
COPY ./requirements.txt ./requirements.txt
COPY ./requirements-hivemind.txt ./requirements-hivemind.txt
COPY ./requirements_gpu.txt ./requirements_gpu.txt

USER gensyn

RUN ./setup_python.sh
RUN ./install_pip.sh

COPY --chown=gensyn . /home/gensyn/rl_swarm

WORKDIR /home/gensyn/rl_swarm
