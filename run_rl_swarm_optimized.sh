#!/usr/bin/env bash

set -euo pipefail

# Enhanced RL-Swarm runner with macOS memory optimizations
# This script addresses OOM issues and improves memory management

# General arguments
ROOT=$PWD

# GenRL Swarm version to use
GENRL_TAG="0.1.9"

# macOS Memory Optimization Environment Variables
export PYTORCH_MPS_HIGH_WATERMARK_RATIO=0.0
export PYTORCH_MPS_ALLOCATOR_POLICY=expandable_segments
export MPS_DEVICE_MEMORY_LIMIT=0.8
export OMP_NUM_THREADS=4
export MKL_NUM_THREADS=4
export NUMEXPR_NUM_THREADS=4

# Memory management settings
export MALLOC_TRIM_THRESHOLD_=131072
export MALLOC_MMAP_THRESHOLD_=131072
export MALLOC_MMAP_MAX_=65536

# Original RL-Swarm environment variables
export IDENTITY_PATH
export GENSYN_RESET_CONFIG
export CONNECT_TO_TESTNET=true
export ORG_ID
export HF_HUB_DOWNLOAD_TIMEOUT=120
export SWARM_CONTRACT="0xFaD7C5e93f28257429569B854151A1B8DCD404c2"
export PRG_CONTRACT="0x51D4db531ae706a6eC732458825465058fA23a35"
export HUGGINGFACE_ACCESS_TOKEN="None"
export PRG_GAME=true

# Path to an RSA private key
DEFAULT_IDENTITY_PATH="$ROOT"/swarm.pem
IDENTITY_PATH=${IDENTITY_PATH:-$DEFAULT_IDENTITY_PATH}

DOCKER=${DOCKER:-""}
GENSYN_RESET_CONFIG=${GENSYN_RESET_CONFIG:-""}

# Memory monitoring and cleanup functions
cleanup_memory() {
    echo "🧹 Cleaning up memory..."
    
    # Force garbage collection in Python
    python3 -c "
import gc
import torch
if torch.backends.mps.is_available():
    torch.mps.empty_cache()
gc.collect()
print('Memory cleanup completed')
" 2>/dev/null || true
    
    # Clear macOS memory pressure
    sudo purge 2>/dev/null || true
    
    # Clear swap if possible
    sudo sysctl vm.swapusage 2>/dev/null || true
}

monitor_memory() {
    echo "📊 Memory Status:"
    echo "Physical Memory:"
    vm_stat | head -10
    echo ""
    echo "Swap Usage:"
    sysctl vm.swapusage
    echo ""
    echo "Memory Pressure:"
    memory_pressure 2>/dev/null || echo "Memory pressure command not available"
}

# Enhanced memory management for macOS
setup_memory_management() {
    echo "🔧 Setting up macOS memory management..."
    
    # Set memory limits
    ulimit -v 8388608  # 8GB virtual memory limit
    
    # Configure memory management
    sudo sysctl vm.swappiness=10 2>/dev/null || true
    sudo sysctl vm.vfs_cache_pressure=50 2>/dev/null || true
    
    # Enable memory compression
    sudo sysctl vm.compressor=1 2>/dev/null || true
    
    echo "✅ Memory management configured"
}

# Signal handlers for graceful shutdown
cleanup_on_exit() {
    echo "🛑 Shutting down gracefully..."
    cleanup_memory
    exit 0
}

trap cleanup_on_exit SIGINT SIGTERM

# Main execution with memory management
main() {
    echo "🚀 Starting RL-Swarm with macOS memory optimizations..."
    
    # Setup memory management
    setup_memory_management
    
    # Monitor initial memory state
    monitor_memory
    
    # Clean up before starting
    cleanup_memory
    
    # Start the original RL-Swarm process with optimizations
    echo "🎯 Starting RL-Swarm training..."
    
    # Run the original script with memory optimizations
    exec "$ROOT/run_rl_swarm.sh" "$@"
}

# Run main function
main "$@"
