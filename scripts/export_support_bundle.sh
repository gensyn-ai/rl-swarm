#!/usr/bin/env bash
set -euo pipefail

TIMESTAMP="$(date +%Y%m%d-%H%M%S || echo unknown-time)"
BUNDLE_DIR="rl_swarm_support_${TIMESTAMP}"
BUNDLE_ARCHIVE="${BUNDLE_DIR}.tar.gz"

echo "=== RL Swarm support bundle exporter ==="
echo "Creating bundle directory: ${BUNDLE_DIR}"
echo

mkdir -p "${BUNDLE_DIR}"

echo "[1/4] Collecting basic host information..."
{
  echo "=== uname -a ==="
  uname -a 2>&1 || echo "uname failed"

  echo
  echo "=== python3 --version ==="
  python3 --version 2>&1 || echo "python3 not found"

  echo
  echo "=== docker --version ==="
  docker --version 2>&1 || echo "docker not found or version check failed"

  echo
  echo "=== docker compose version / docker-compose version ==="
  if command -v docker-compose >/dev/null 2>&1; then
    docker-compose version 2>&1 || echo "docker-compose version failed"
  elif docker compose version >/dev/null 2>&1; then
    docker compose version 2>&1 || echo "docker compose version failed"
  else
    echo "Neither docker-compose nor docker compose detected."
  fi

  echo
  echo "=== nvidia-smi (if available) ==="
  if command -v nvidia-smi >/dev/null 2>&1; then
    nvidia-smi 2>&1 || echo "nvidia-smi failed"
  else
    echo "nvidia-smi not found."
  fi
} > "${BUNDLE_DIR}/host_info.txt"

echo "  - host_info.txt collected."
echo

echo "[2/4] Collecting RL Swarm repository state..."
{
  echo "=== git status ==="
  git status --short --branch 2>&1 || echo "git status failed"

  echo
  echo "=== git rev-parse HEAD ==="
  git rev-parse HEAD 2>&1 || echo "git rev-parse failed"

  echo
  echo "=== git remote -v ==="
  git remote -v 2>&1 || echo "git remote failed"
} > "${BUNDLE_DIR}/repo_info.txt"

echo "  - repo_info.txt collected."
echo

echo "[3/4] Collecting logs (best-effort)..."

LOG_CANDIDATES=(
  "logs"
  "log"
  "output"
)

for path in "${LOG_CANDIDATES[@]}"; do
  if [ -d "${path}" ]; then
    echo "  - found log directory: ${path}"
    cp -r "${path}" "${BUNDLE_DIR}/" || echo "    failed to copy ${path}"
  fi
done

echo "If your RL Swarm logs live in a custom directory, you can copy them"
echo "into ${BUNDLE_DIR} before sending the archive."
echo

echo "[4/4] Creating archive..."
tar -czf "${BUNDLE_ARCHIVE}" "${BUNDLE_DIR}" || {
  echo "Failed to create archive ${BUNDLE_ARCHIVE}."
  exit 1
}

echo
echo "Support bundle created: ${BUNDLE_ARCHIVE}"
echo "You can attach this file (after reviewing and removing any secrets)"
echo "to GitHub issues or share it securely with maintainers."
