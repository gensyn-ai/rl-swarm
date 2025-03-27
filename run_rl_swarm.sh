#!/bin/bash

# General args
ROOT=$PWD

export PUB_MULTI_ADDRS
export PEER_MULTI_ADDRS
export HOST_MULTI_ADDRS
export IDENTITY_PATH
export ENABLE_PEER_DISCOVERY
export ENABLE_LOCAL_DISCOVERY
export DISCOVERY_WAIT

# Check if public multi-address is given else set to default
DEFAULT_PUB_MULTI_ADDRS=""
PUB_MULTI_ADDRS=${PUB_MULTI_ADDRS:-$DEFAULT_PUB_MULTI_ADDRS}

# Check if peer multi-address is given else set to default
# With peer discovery, this becomes optional, used only as a fallback
DEFAULT_PEER_MULTI_ADDRS="/ip4/38.101.215.13/tcp/30002/p2p/QmQ2gEXoPJg6iMBSUFWGzAabS2VhnzuS782Y637hGjfsRJ" # gensyn coordinator node
PEER_MULTI_ADDRS=${PEER_MULTI_ADDRS:-$DEFAULT_PEER_MULTI_ADDRS}

# Check if host multi-address is given else set to default
DEFAULT_HOST_MULTI_ADDRS="/ip4/0.0.0.0/tcp/38331"
HOST_MULTI_ADDRS=${HOST_MULTI_ADDRS:-$DEFAULT_HOST_MULTI_ADDRS}

# Path to an RSA private key. No need to specify if you
# just want a random Peer ID for this run.
DEFAULT_IDENTITY_PATH=""
IDENTITY_PATH=${IDENTITY_PATH:-$DEFAULT_IDENTITY_PATH}

# Peer discovery settings
DEFAULT_ENABLE_PEER_DISCOVERY="true"
ENABLE_PEER_DISCOVERY=${ENABLE_PEER_DISCOVERY:-$DEFAULT_ENABLE_PEER_DISCOVERY}

DEFAULT_ENABLE_LOCAL_DISCOVERY="true"
ENABLE_LOCAL_DISCOVERY=${ENABLE_LOCAL_DISCOVERY:-$DEFAULT_ENABLE_LOCAL_DISCOVERY}

DEFAULT_DISCOVERY_WAIT="10"
DISCOVERY_WAIT=${DISCOVERY_WAIT:-$DEFAULT_DISCOVERY_WAIT}

# let's go!
echo "Getting requirements..."
pip install -r "$ROOT"/requirements-hivemind.txt
pip install -r "$ROOT"/requirements.txt

# Install zeroconf for mDNS local network discovery if peer discovery is enabled
if [ "$ENABLE_PEER_DISCOVERY" = "true" ] && [ "$ENABLE_LOCAL_DISCOVERY" = "true" ]; then
    echo "Installing zeroconf for local peer discovery..."
    pip install zeroconf
fi

if ! which nvidia-smi; then
   # You don't have a NVIDIA GPU
   CONFIG_PATH="$ROOT/hivemind_exp/configs/mac/grpo-qwen-2.5-0.5b-deepseek-r1.yaml"
elif [ -n "$CPU_ONLY" ]; then
   # ... or we don't want to use it
   CONFIG_PATH="$ROOT/hivemind_exp/configs/mac/grpo-qwen-2.5-0.5b-deepseek-r1.yaml"
else
   # NVIDIA GPU found
   pip install -r "$ROOT"/requirements_gpu.txt
   CONFIG_PATH="$ROOT/hivemind_exp/configs/gpu/grpo-qwen-2.5-0.5b-deepseek-r1.yaml"
fi

echo ">> Done!"
echo "Good luck in the swarm!"

# Build peer discovery arguments
DISCOVERY_ARGS=""
if [ "$ENABLE_PEER_DISCOVERY" = "true" ]; then
  DISCOVERY_ARGS="--enable_peer_discovery"

  if [ "$ENABLE_LOCAL_DISCOVERY" = "true" ]; then
    DISCOVERY_ARGS="$DISCOVERY_ARGS --enable_local_discovery"
  else
    DISCOVERY_ARGS="$DISCOVERY_ARGS --no-enable_local_discovery"
  fi

  DISCOVERY_ARGS="$DISCOVERY_ARGS --discovery_wait $DISCOVERY_WAIT"
else
  DISCOVERY_ARGS="--no-enable_peer_discovery"
fi

python3 -m hivemind_exp.gsm8k.train_single_gpu \
  --identity_path "$IDENTITY_PATH" \
  --public_maddr "$PUB_MULTI_ADDRS" \
  --initial_peer "$PEER_MULTI_ADDRS" \
  --host_maddr "$HOST_MULTI_ADDRS" \
  $DISCOVERY_ARGS \
  --config "$CONFIG_PATH"