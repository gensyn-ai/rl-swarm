#!/bin/bash

source /home/gensyn/.profile
set -euo pipefail

#General args
ROOT=$PWD

export CONFIG_PATH
CONFIG_PATH="$ROOT/hivemind_exp/configs/gpu/grpo-qwen-2.5-0.5b-deepseek-r1.yaml"

echo "Good luck in the swarm!"

python -m hivemind_exp.gsm8k.train_single_gpu \
    --identity_path "$IDENTITY_PATH" \
    --wallet_private_key "$WALLET_PRIVATE_KEY" \
    --public_maddr "$PUB_MULTI_ADDRS" \
    --host_maddr "$HOST_MULTI_ADDRS" \
    --config "$CONFIG_PATH"
