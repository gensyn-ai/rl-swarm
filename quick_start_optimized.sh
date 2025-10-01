#!/usr/bin/env bash

# Quick Start Script for RL-Swarm with macOS Memory Optimizations
# This script provides a one-click solution for running RL-Swarm with optimizations

set -euo pipefail

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    local color=$1
    local message=$2
    echo -e "${color}${message}${NC}"
}

# Function to check prerequisites
check_prerequisites() {
    print_status $BLUE "🔍 Checking prerequisites..."
    
    # Check for required commands
    local missing_commands=()
    
    if ! command -v python3 >/dev/null 2>&1; then
        missing_commands+=("python3")
    fi
    
    if ! command -v git >/dev/null 2>&1; then
        missing_commands+=("git")
    fi
    
    if ! command -v curl >/dev/null 2>&1; then
        missing_commands+=("curl")
    fi
    
    if [ ${#missing_commands[@]} -gt 0 ]; then
        print_status $RED "Missing required commands: ${missing_commands[*]}"
        print_status $YELLOW "Please install the missing commands and run this script again."
        exit 1
    fi
    
    print_status $GREEN "✅ All prerequisites satisfied"
}

# Function to setup memory optimizations
setup_memory_optimizations() {
    print_status $BLUE "⚙️ Setting up memory optimizations..."
    
    # Set environment variables
    export PYTORCH_MPS_HIGH_WATERMARK_RATIO=0.0
    export PYTORCH_MPS_ALLOCATOR_POLICY=expandable_segments
    export MPS_DEVICE_MEMORY_LIMIT=0.8
    export OMP_NUM_THREADS=4
    export MKL_NUM_THREADS=4
    export NUMEXPR_NUM_THREADS=4
    
    # Memory management
    export MALLOC_TRIM_THRESHOLD_=131072
    export MALLOC_MMAP_THRESHOLD_=131072
    export MALLOC_MMAP_MAX_=65536
    
    print_status $GREEN "✅ Memory optimizations configured"
}

# Function to optimize system settings
optimize_system_settings() {
    print_status $BLUE "🔧 Optimizing system settings..."
    
    # Set memory limits
    ulimit -v 8388608  # 8GB virtual memory limit
    
    # Configure memory management
    sudo sysctl vm.swappiness=10 2>/dev/null || print_status $YELLOW "Could not set swappiness"
    sudo sysctl vm.vfs_cache_pressure=50 2>/dev/null || print_status $YELLOW "Could not set cache pressure"
    sudo sysctl vm.compressor=1 2>/dev/null || print_status $YELLOW "Could not enable compressor"
    
    print_status $GREEN "✅ System settings optimized"
}

# Function to clean up memory
cleanup_memory() {
    print_status $BLUE "🧹 Cleaning up memory..."
    
    # Clear Python caches
    python3 -c "
import gc
import torch
if torch.backends.mps.is_available():
    torch.mps.empty_cache()
gc.collect()
print('Memory cleanup completed')
" 2>/dev/null || true
    
    # Clear macOS memory pressure
    sudo purge 2>/dev/null || print_status $YELLOW "purge command requires sudo"
    
    print_status $GREEN "✅ Memory cleanup completed"
}

# Function to start monitoring
start_monitoring() {
    print_status $BLUE "📊 Starting memory monitoring..."
    
    # Start memory monitoring in background
    bash scripts/memory_manager.sh monitor &
    local monitor_pid=$!
    
    # Store PID for cleanup
    echo $monitor_pid > .monitor_pid
    
    print_status $GREEN "✅ Memory monitoring started (PID: $monitor_pid)"
}

# Function to stop monitoring
stop_monitoring() {
    print_status $BLUE "🛑 Stopping memory monitoring..."
    
    if [ -f .monitor_pid ]; then
        local monitor_pid=$(cat .monitor_pid)
        kill $monitor_pid 2>/dev/null || true
        rm -f .monitor_pid
        print_status $GREEN "✅ Memory monitoring stopped"
    fi
}

# Function to show status
show_status() {
    print_status $BLUE "📊 Current Status:"
    echo ""
    
    # Check if RL-Swarm is running
    if pgrep -f "run_rl_swarm" >/dev/null; then
        print_status $GREEN "✅ RL-Swarm is running"
    else
        print_status $YELLOW "⚠️ RL-Swarm is not running"
    fi
    
    # Check memory status
    bash scripts/memory_manager.sh status
}

# Function to start RL-Swarm
start_rl_swarm() {
    print_status $BLUE "🚀 Starting RL-Swarm with optimizations..."
    
    # Clean up memory first
    cleanup_memory
    
    # Start monitoring
    start_monitoring
    
    # Start RL-Swarm with optimizations
    exec ./run_rl_swarm_optimized.sh "$@"
}

# Function to show help
show_help() {
    print_status $GREEN "=== RL-Swarm Quick Start with macOS Optimizations ==="
    echo ""
    echo "Usage: $0 [command] [options]"
    echo ""
    echo "Commands:"
    echo "  start     Start RL-Swarm with optimizations"
    echo "  stop      Stop monitoring and cleanup"
    echo "  status    Show current status"
    echo "  cleanup   Clean up memory"
    echo "  optimize  Optimize system settings"
    echo "  monitor   Start memory monitoring"
    echo "  help      Show this help"
    echo ""
    echo "Examples:"
    echo "  $0 start                    # Start with optimizations"
    echo "  $0 start --cpu-only         # Start in CPU-only mode"
    echo "  $0 status                   # Check status"
    echo "  $0 cleanup                  # Clean up memory"
    echo ""
}

# Signal handlers for graceful shutdown
cleanup_on_exit() {
    print_status $YELLOW "🛑 Shutting down gracefully..."
    stop_monitoring
    cleanup_memory
    exit 0
}

trap cleanup_on_exit SIGINT SIGTERM

# Main execution
main() {
    print_status $GREEN "🎯 RL-Swarm Quick Start with macOS Memory Optimizations"
    echo ""
    
    # Check prerequisites
    check_prerequisites
    
    # Setup memory optimizations
    setup_memory_optimizations
    
    # Handle commands
    case ${1:-start} in
        "start")
            optimize_system_settings
            start_rl_swarm "${@:2}"
            ;;
        "stop")
            stop_monitoring
            cleanup_memory
            ;;
        "status")
            show_status
            ;;
        "cleanup")
            cleanup_memory
            ;;
        "optimize")
            optimize_system_settings
            ;;
        "monitor")
            start_monitoring
            ;;
        "help")
            show_help
            ;;
        *)
            print_status $RED "Unknown command: $1"
            show_help
            exit 1
            ;;
    esac
}

# Run main function
main "$@"
