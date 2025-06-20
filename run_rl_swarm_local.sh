#!/bin/bash

set -euo pipefail

# General arguments
ROOT=$PWD

export PUB_MULTI_ADDRS=""
export PEER_MULTI_ADDRS=""
export HOST_MULTI_ADDRS="/ip4/0.0.0.0/tcp/38331"
export IDENTITY_PATH="$ROOT/swarm.pem"
export CONNECT_TO_TESTNET=false
export ORG_ID=""
export HF_HUB_DOWNLOAD_TIMEOUT=120
export CPU_ONLY=1  # Force CPU mode for local testing

GREEN_TEXT="\033[32m"
BLUE_TEXT="\033[34m"
RED_TEXT="\033[31m"
RESET_TEXT="\033[0m"

echo_green() {
    echo -e "$GREEN_TEXT$1$RESET_TEXT"
}

echo_blue() {
    echo -e "$BLUE_TEXT$1$RESET_TEXT"
}

echo_red() {
    echo -e "$RED_TEXT$1$RESET_TEXT"
}

# Function to clean up upon exit
cleanup() {
    echo_green ">> Shutting down trainer..."
    exit 0
}

trap cleanup EXIT

echo -e "\033[38;5;224m"
cat << "EOF"
    ██████  ██            ███████ ██     ██  █████  ██████  ███    ███
    ██   ██ ██            ██      ██     ██ ██   ██ ██   ██ ████  ████
    ██████  ██      █████ ███████ ██  █  ██ ███████ ██████  ██ ████ ██
    ██   ██ ██                 ██ ██ ███ ██ ██   ██ ██   ██ ██  ██  ██
    ██   ██ ███████       ███████  ███ ███  ██   ██ ██   ██ ██      ██

    From Gensyn (Local Testing Mode)

EOF

# Ensure uv is available
if [ -f "$HOME/.local/bin/uv" ]; then
    export PATH="$HOME/.local/bin:$PATH"
fi

if ! command -v uv > /dev/null 2>&1; then
    echo_red ">> uv is not installed. Please install it first:"
    echo_red "   curl -LsSf https://astral.sh/uv/install.sh | sh"
    exit 1
fi

echo_green ">> Setting up local testing environment..."
echo_blue ">> Running in LOCAL MODE (no testnet connection)"

# Create logs directory if it doesn't exist
mkdir -p "$ROOT/logs"

# Install CPU dependencies only
echo_green ">> Installing CPU-only dependencies with uv..."
uv sync --no-dev

# Use local test config
CONFIG_PATH="$ROOT/hivemind_exp/configs/mac/grpo-qwen-2.5-0.5b-local.yaml"
GAME="gsm8k"

echo_green ">> Configuration:"
echo "   - Config: $CONFIG_PATH"
echo "   - Game: $GAME"
echo "   - Mode: Local (CPU-only)"

# Set HuggingFace token
HF_TOKEN=${HF_TOKEN:-""}
if [ -n "${HF_TOKEN}" ]; then
    HUGGINGFACE_ACCESS_TOKEN=${HF_TOKEN}
else
    echo -en $GREEN_TEXT
    read -p ">> Would you like to push models to Hugging Face Hub? [y/N] " yn
    echo -en $RESET_TEXT
    yn=${yn:-N}
    case $yn in
        [Yy]*) read -p "Enter your Hugging Face access token: " HUGGINGFACE_ACCESS_TOKEN ;;
        [Nn]*) HUGGINGFACE_ACCESS_TOKEN="None" ;;
        *) HUGGINGFACE_ACCESS_TOKEN="None" ;;
    esac
fi

echo_green ">> Starting local training..."
echo_blue ">> This will run without network connections to avoid P2P issues"

# Run the training script using uv in local mode
uv run python -m hivemind_exp.gsm8k.train_single_gpu \
    --hf_token "$HUGGINGFACE_ACCESS_TOKEN" \
    --identity_path "$IDENTITY_PATH" \
    --public_maddr "$PUB_MULTI_ADDRS" \
    --initial_peers "$PEER_MULTI_ADDRS" \
    --host_maddr "$HOST_MULTI_ADDRS" \
    --config "$CONFIG_PATH" \
    --game "$GAME" 