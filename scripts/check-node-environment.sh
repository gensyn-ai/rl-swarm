#!/usr/bin/env bash
set -euo pipefail

echo "=== RL Swarm node environment check ==="
echo

# 1. OS information
echo "[1/4] Operating system:"
uname -a || echo "Could not determine OS via uname."
echo

# 2. Python version
echo "[2/4] Python version (expected: >= 3.10 and <= 3.13)..."
if command -v python3 >/dev/null 2>&1; then
  PYTHON_VERSION_RAW="$(python3 --version 2>&1 || true)"
  echo "Detected: ${PYTHON_VERSION_RAW}"
else
  echo "python3 is not on PATH. Please install a supported Python version."
fi
echo

# 3. Approximate RAM
echo "[3/4] Checking available system memory..."
MEM_INFO=""
if command -v free >/dev/null 2>&1; then
  # Linux: use free -g
  echo "free -g output:"
  free -g || true
elif [[ "$(uname -s)" == "Darwin" ]]; then
  # macOS: use sysctl
  if command -v sysctl >/dev/null 2>&1; then
    BYTES="$(sysctl -n hw.memsize 2>/dev/null || echo "")"
    if [[ -n "${BYTES}" ]]; then
      GIB=$((BYTES / 1024 / 1024 / 1024))
      echo "Approximate RAM: ${GIB} GiB"
    else
      echo "Could not determine RAM via sysctl."
    fi
  else
    echo "sysctl not available to query RAM."
  fi
else
  echo "Could not detect a standard method to query RAM on this platform."
fi

echo
echo "For RL Swarm, we recommend at least 32 GB of RAM for stable training."
echo

# 4. GPU / CUDA check
echo "[4/4] GPU / CUDA availability..."
if command -v nvidia-smi >/dev/null 2>&1; then
  echo "nvidia-smi found. Listing GPUs:"
  nvidia-smi || true
  echo
  echo "If your GPU matches one of the officially supported devices (e.g. RTX 3090/4090/5090, A100, H100),"
  echo "you should be able to use the GPU swarm configuration."
else
  echo "nvidia-smi not found. You are likely running on CPU-only hardware or without NVIDIA drivers."
  echo "CPU-only mode is supported but may be significantly slower."
fi

echo
echo "Environment check complete."
echo "Review the information above and compare it with the requirements in the RL Swarm README."
