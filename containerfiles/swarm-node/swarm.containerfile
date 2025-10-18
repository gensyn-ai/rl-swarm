ARG BASE_IMAGE=ubuntu:24.04
FROM ${BASE_IMAGE}
LABEL maintainer="Christopher Nies <christopher@gensyn.ai>"

ENV DEBIAN_FRONTEND=noninteractive TZ=Etc/UTC
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
    git curl jq neovim \
    gnupg && \
    useradd gensyn --user-group --create-home --shell /bin/bash && \
    echo "gensyn ALL=(ALL) NOPASSWD:ALL" > /etc/sudoers.d/gensyn && \
    echo 'export PATH=/usr/local/cuda/bin:$PATH' >> ~/.bashrc && \
    echo 'export LD_LIBRARY_PATH=/usr/local/cuda/lib64:$LD_LIBRARY_PATH' >> ~/.bashrc && \
    apt-get autoremove -y && \
    apt-get clean

# Install Quok (Debian/Ubuntu only)
RUN install -d -m 0755 /etc/apt/keyrings && \
    curl -fsSL https://repo.quok.it/quok.asc | gpg --dearmor | tee /etc/apt/keyrings/quok.gpg >/dev/null && \
    echo 'deb [signed-by=/etc/apt/keyrings/quok.gpg] https://repo.quok.it/ cross main' | tee /etc/apt/sources.list.d/quok-stable.list >/dev/null && \
    chmod 0644 /etc/apt/keyrings/quok.gpg /etc/apt/sources.list.d/quok-stable.list && \
    apt-get update && \
    apt-get install -y quok

WORKDIR /home/gensyn
USER gensyn

RUN curl -o- https://raw.githubusercontent.com/nvm-sh/nvm/v0.40.3/install.sh | bash
ENV NVM_DIR=/home/gensyn/.nvm NODE_VERSION=22.16.0
RUN . "$NVM_DIR/nvm.sh" && nvm install ${NODE_VERSION} && \
    . "$NVM_DIR/nvm.sh" && nvm use v${NODE_VERSION} && \
    . "$NVM_DIR/nvm.sh" && nvm alias default v${NODE_VERSION} && \
    npm install -g --silent yarn

COPY ./containerfiles/swarm-node/versions.json ./versions.json

COPY ./containerfiles/swarm-node/setup_python.sh ./setup_python.sh
RUN ./setup_python.sh

COPY ./containerfiles/swarm-node/install_pip.sh ./install_pip.sh
RUN ./install_pip.sh

ENV PATH="/home/gensyn/.pyenv/shims:/home/gensyn/.pyenv/bin:$NVM_DIR/versions/node/v${NODE_VERSION}/bin/:${PATH}"

COPY --chown=gensyn ./modal-login /home/gensyn/rl_swarm/modal-login
RUN cd /home/gensyn/rl_swarm/modal-login && yarn install --immutable && yarn build

RUN pip install gensyn-genrl==0.1.11
RUN pip install reasoning-gym>=0.1.20 # for reasoning gym env
RUN pip install hivemind@git+https://github.com/gensyn-ai/hivemind@639c964a8019de63135a2594663b5bec8e5356dd # We need the latest, 1.1.11 is broken

WORKDIR /home/gensyn/rl_swarm
ENV DOCKER=t
ENV IDENTITY_PATH=/home/gensyn/rl_swarm/keys/swarm.pem

COPY --chown=gensyn . /home/gensyn/rl_swarm

# Create Quok setup script
COPY --chown=gensyn ./scripts/setup_quok.sh /home/gensyn/setup_quok.sh
RUN chmod +x /home/gensyn/setup_quok.sh

CMD [ "bash", "-c", "/home/gensyn/setup_quok.sh && /home/gensyn/rl_swarm/run_rl_swarm.sh" ]
