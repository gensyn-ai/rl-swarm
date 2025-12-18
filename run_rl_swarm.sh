#!/usr/bin/env bash
set -euo pipefail

# General arguments
ROOT=$PWD

# GenRL Swarm version to use
GENRL_TAG="0.1.8"

export IDENTITY_PATH
export GENSYN_RESET_CONFIG
export CONNECT_TO_TESTNET=true
export ORG_ID
export HF_HUB_DOWNLOAD_TIMEOUT=120 # 2 minutes
export SWARM_CONTRACT="0xFaD7C5e93f28257429569B854151A1B8DCD404c2"
export PRG_CONTRACT="0x51D4db531ae706a6eC732458825465058fA23a35"
export HUGGINGFACE_ACCESS_TOKEN="None"
export PRG_GAME=true

# Path to an RSA private key. If this path does not exist, a new key pair will be created.
# Remove this file if you want a new PeerID.
DEFAULT_IDENTITY_PATH="$ROOT"/swarm.pem
IDENTITY_PATH=${IDENTITY_PATH:-$DEFAULT_IDENTITY_PATH}

DOCKER=${DOCKER:-""}
GENSYN_RESET_CONFIG=${GENSYN_RESET_CONFIG:-""}

# Bit of a workaround for the non-root docker container.
if [ -n "$DOCKER" ]; then
  volumes=(
    /home/gensyn/rl_swarm/modal-login/temp-data
    /home/gensyn/rl_swarm/keys
    /home/gensyn/rl_swarm/configs
    /home/gensyn/rl_swarm/logs
  )
  for volume in "${volumes[@]}"; do
    sudo chown -R 1001:1001 "$volume"
  done
fi

# Will ignore any visible GPUs if set.
CPU_ONLY=${CPU_ONLY:-""}

# Set if successfully parsed from modal-login/temp-data/userData.json.
ORG_ID=${ORG_ID:-""}

GREEN_TEXT="\033[32m"
BLUE_TEXT="\033[34m"
RED_TEXT="\033[31m"
RESET_TEXT="\033[0m"

echo_green() { echo -e "${GREEN_TEXT}$1${RESET_TEXT}"; }
echo_blue() { echo -e "${BLUE_TEXT}$1${RESET_TEXT}"; }
echo_red() { echo -e "${RED_TEXT}$1${RESET_TEXT}"; }

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

cleanup() {
  echo_green ">> Shutting down trainer..."
  rm -r "$ROOT_DIR"/modal-login/temp-data/*.json 2>/dev/null || true
  kill -- -$$ || true
  exit 0
}

errnotify() {
  echo_red ">> An error was detected while running rl-swarm. See $ROOT/logs for full logs."
}

trap cleanup EXIT
trap errnotify ERR

echo -e "\033[38;5;224m"
cat << "EOF"
██████  ██       ███████  ██      ██   █████   ██████
██   ██ ██       ██      ██      ██   ██   ██ ██   ██
██████  ██       █████   ██      ██   ███████ ██████
██      ██       ██      ██      ██   ██   ██ ██   ██
██      ███████ ███████ ███████ ██   ██   ██ ██   ██
From Gensyn
EOF

mkdir -p "$ROOT/logs"

if [ "$CONNECT_TO_TESTNET" = true ]; then
  echo "Please login to create an Ethereum Server Wallet"
  cd modal-login

  # Node.js + NVM setup
  if ! command -v node >/dev/null 2>&1; then
    echo "Node.js not found. Installing NVM and latest Node.js..."
    export NVM_DIR="$HOME/.nvm"
    if [ ! -d "$NVM_DIR" ]; then
      curl -o- https://raw.githubusercontent.com/nvm-sh/nvm/v0.39.7/install.sh | bash
    fi
    [ -s "$NVM_DIR/nvm.sh" ] && . "$NVM_DIR/nvm.sh"
    [ -s "$NVM_DIR/bash_completion" ] && . "$NVM_DIR/bash_completion"
    nvm install node
  else
    echo "Node.js is already installed: $(node -v)"
  fi

  if ! command -v yarn >/dev/null 2>&1; then
    if grep -qi "ubuntu" /etc/os-release 2>/dev/null || uname -r | grep -qi "microsoft"; then
      echo "Detected Ubuntu or WSL Ubuntu. Installing Yarn via apt..."
      curl -sS https://dl.yarnpkg.com/debian/pubkey.gpg | sudo apt-key add -
      echo "deb https://dl.yarnpkg.com/debian/ stable main" | sudo tee /etc/apt/sources.list.d/yarn.list
      sudo apt update && sudo apt install -y yarn
    else
      echo "Yarn not found. Installing Yarn globally with npm (no profile edits)…"
      npm install -g --silent yarn
    fi
  fi

  ENV_FILE="$ROOT"/modal-login/.env
  if [[ "$OSTYPE" == "darwin"* ]]; then
    sed -i '' "3s/.*/SWARM_CONTRACT_ADDRESS=$SWARM_CONTRACT/" "$ENV_FILE"
    sed -i '' "4s/.*/PRG_CONTRACT_ADDRESS=$PRG_CONTRACT/" "$ENV_FILE"
  else
    sed -i "3s/.*/SWARM_CONTRACT_ADDRESS=$SWARM_CONTRACT/" "$ENV_FILE"
    sed -i "4s/.*/PRG_CONTRACT_ADDRESS=$PRG_CONTRACT/" "$ENV_FILE"
  fi

  if [ -z "$DOCKER" ]; then
    yarn install --immutable
    echo "Building server"
    yarn build >"$ROOT/logs/yarn.log" 2>&1
  fi

  yarn start >>"$ROOT/logs/yarn.log" 2>&1 &
  SERVER_PID=$!
  echo "Started server process: $SERVER_PID"
  sleep 5

  if [ -z "$DOCKER" ]; then
    if open http://localhost:3000 2>/dev/null; then
      echo_green ">> Successfully opened http://localhost:3000 in your default browser."
    else
      echo ">> Failed to open http://localhost:3000. Please open it manually."
    fi
  else
    echo_green ">> Please open http://localhost:3000 in your host browser."
  fi

  cd ..
  echo_green ">> Waiting for modal userData.json to be created..."
  while [ ! -f "modal-login/temp-data/userData.json" ]; do
    sleep 5
  done

  echo "Found userData.json. Proceeding..."
  ORG_ID=$(awk 'BEGIN { FS = "\"" } !/^[ \t]*[{}]/ { print $(NF - 1); exit }' modal-login/temp-data/userData.json)
  echo "Your ORG_ID is set to: $ORG_ID"

  echo "Waiting for API key to become activated..."
  while true; do
    STATUS=$(curl -s "http://localhost:3000/api/get-api-key-status?orgId=$ORG_ID")
    if [[ "$STATUS" == "activated" ]]; then
      echo "API key is activated! Proceeding..."
      break
    else
      echo "Waiting for API key to be activated..."
      sleep 5
    fi
  done
fi

echo_green ">> Getting requirements..."
pip install --upgrade pip

echo_green ">> Installing GenRL..."
pip install "gensyn-genrl==${GENRL_TAG}"
pip install "reasoning-gym>=0.1.20"
pip install "hivemind@git+https://github.com/gensyn-ai/hivemind@639c964a8019de63135a2594663b5bec8e5356dd"

if [ ! -d "$ROOT/configs" ]; then
  mkdir "$ROOT/configs"
fi

if [ -f "$ROOT/configs/rg-swarm.yaml" ]; then
  if ! cmp -s "$ROOT/rgym_exp/config/rg-swarm.yaml" "$ROOT/configs/rg-swarm.yaml"; then
    if [ -z "$GENSYN_RESET_CONFIG" ]; then
      echo_green ">> Found differences in rg-swarm.yaml. Set GENSYN_RESET_CONFIG to reset to defaults."
    else
      echo_green ">> Backing up existing rg-swarm.yaml and restoring default."
      mv "$ROOT/configs/rg-swarm.yaml" "$ROOT/configs/rg-swarm.yaml.bak"
      cp "$ROOT/rgym_exp/config/rg-swarm.yaml" "$ROOT/configs/rg-swarm.yaml"
    fi
  fi
else
  cp "$ROOT/rgym_exp/config/rg-swarm.yaml" "$ROOT/configs/rg-swarm.yaml"
fi

if [ -n "$DOCKER" ]; then
  sudo chmod -R 0777 /home/gensyn/rl_swarm/configs
fi

echo_green ">> Done!"

echo -en "$GREEN_TEXT"
read -p ">> Would you like to push models you train in the RL swarm to the Hugging Face Hub? [y/N] " yn
echo -en "$RESET_TEXT"

yn=${yn:-N}
case $yn in
  [Yy]*)
    read -p "Enter your Hugging Face access token: " HUGGINGFACE_ACCESS_TOKEN
    ;;
  [Nn]*)
    HUGGINGFACE_ACCESS_TOKEN="None"
    ;;
  *)
    echo ">>> No answer was given, so NO models will be pushed to Hugging Face Hub"
    HUGGINGFACE_ACCESS_TOKEN="None"
    ;;
esac

echo -en "$GREEN_TEXT"
read -p ">> Enter the name of the model you want to use in huggingface repo/name format, or press [Enter] to use the default model. " MODEL_NAME
echo -en "$RESET_TEXT"

if [ -n "$MODEL_NAME" ]; then
  export MODEL_NAME
  echo_green ">> Using model: $MODEL_NAME"
else
  echo_green ">> Using default model from config"
fi

echo -en "$GREEN_TEXT"
read -p ">> Would you like your model to participate in the AI Prediction Market? [Y/n] " yn
echo -en "$RESET_TEXT"

if [ "$yn" = "n" ] || [ "$yn" = "N" ]; then
  PRG_GAME=false
  echo_green ">> Playing PRG game: false"
else
  echo_green ">> Playing PRG game: true"
fi

echo_green ">> Good luck in the swarm!"
echo_blue ">> And remember to star the repo on GitHub! --> https://github.com/gensyn-ai/rl-swarm"

python -m rgym_exp.runner.swarm_launcher \
  --config-path "$ROOT/rgym_exp/config" \
  --config-name "rg-swarm.yaml"

wait
