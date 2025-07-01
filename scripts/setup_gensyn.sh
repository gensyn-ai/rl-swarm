#!/usr/bin/env bash
# One-liner installer for Gensyn RL-Swarm
# Usage:
#   curl -sSL https://raw.githubusercontent.com/VasilenkoViktor/rl-swarm/main/scripts/setup_gensyn.sh | bash

set -e

echo "[1/5] Updating system and installing base packages…"
sudo apt-get update -y
sudo apt-get install -y python3.10 python3-venv git screen

echo "[2/5] Cloning rl-swarm…"
git clone https://github.com/gensyn-ai/rl-swarm.git ~/rl-swarm || true
cd ~/rl-swarm

echo "[3/5] Creating venv and installing Python deps…"
python3 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
pip install protobuf==3.20.3        # patch mismatched-protobuf bug

echo "[4/5] Launching worker inside screen…"
screen -dmS gensyn bash -c "./run_rl_swarm.sh"

echo "[5/5] Done!  Attach logs any time:  screen -r gensyn"
