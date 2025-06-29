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

# Local training configuration 
echo_green ">> Configuration:"
echo "   - Mode: Local GRPO Training (CPU-only)"
echo "   - Dataset: gsm8k"
echo "   - Model: unsloth/Qwen2.5-0.5B-Instruct"
echo "   - Max Steps: 20 (for quick testing)"

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

echo_green ">> Starting local GRPO training..."
echo_blue ">> This will run without network connections to avoid P2P issues"

# Create output directory
OUTPUT_DIR="runs/gsm8k/local/Qwen2.5-0.5B-Instruct-Local"
mkdir -p "$OUTPUT_DIR"

# Run TRL GRPO training script for local mode
uv run python -m trl.scripts.grpo \
    --model_name_or_path "unsloth/Qwen2.5-0.5B-Instruct" \
    --dataset_name "gsm8k" \
    --dataset_config "main" \
    --dataset_train_split "train" \
    --output_dir "$OUTPUT_DIR" \
    --overwrite_output_dir \
    --do_train \
    --per_device_train_batch_size 2 \
    --gradient_accumulation_steps 4 \
    --learning_rate 5e-7 \
    --max_steps 20 \
    --warmup_ratio 0.03 \
    --logging_steps 2 \
    --save_strategy "steps" \
    --save_steps 25 \
    --use_cpu \
    --torch_dtype "float32" \
    --gradient_checkpointing \
    --logging_dir "logs" \
    --run_name "rl-swarm-local-test" \
    --report_to "wandb" \
    --max_prompt_length 256 \
    --max_completion_length 1024 \
    --num_generations 2 \
    --temperature 1.0 \
    --top_p 1.0 \
    --beta 0.001 \
    --epsilon 0.2 \
    --loss_type "bnpo" \
    --steps_per_generation 4 \
    --scale_rewards \
    --shuffle_dataset 