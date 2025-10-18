#!/usr/bin/env bash

# macOS Memory Manager for RL-Swarm
# This script provides comprehensive memory management for macOS systems

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

# Function to check memory status
check_memory_status() {
    print_status $BLUE "🔍 Current Memory Status:"
    echo ""
    
    # Physical memory
    print_status $GREEN "Physical Memory:"
    vm_stat | head -10
    echo ""
    
    # Swap usage
    print_status $GREEN "Swap Usage:"
    sysctl vm.swapusage
    echo ""
    
    # Memory pressure
    print_status $GREEN "Memory Pressure:"
    if command -v memory_pressure >/dev/null 2>&1; then
        memory_pressure
    else
        echo "Memory pressure command not available"
    fi
    echo ""
    
    # Process memory usage
    print_status $GREEN "Top Memory Consuming Processes:"
    ps aux | sort -nr -k 4 | head -10
    echo ""
}

# Function to clean up memory
cleanup_memory() {
    print_status $BLUE "🧹 Cleaning up memory..."
    
    # Force Python garbage collection
    if command -v python3 >/dev/null 2>&1; then
        python3 -c "
import gc
import sys
try:
    import torch
    if torch.backends.mps.is_available():
        torch.mps.empty_cache()
        print('PyTorch MPS cache cleared')
except ImportError:
    pass
gc.collect()
print('Python garbage collection completed')
" 2>/dev/null || true
    fi
    
    # Clear macOS memory pressure
    print_status $YELLOW "Clearing macOS memory pressure..."
    sudo purge 2>/dev/null || print_status $YELLOW "purge command requires sudo"
    
    # Clear swap if possible
    print_status $YELLOW "Checking swap usage..."
    sysctl vm.swapusage
    
    print_status $GREEN "✅ Memory cleanup completed"
}

# Function to optimize memory settings
optimize_memory_settings() {
    print_status $BLUE "⚙️ Optimizing memory settings..."
    
    # Set memory limits (macOS compatible)
    # ulimit -v 8388608  # 8GB virtual memory limit - disabled for macOS compatibility
    
    # Configure memory management
    print_status $YELLOW "Configuring memory management..."
    sudo sysctl vm.swappiness=10 2>/dev/null || print_status $YELLOW "Could not set swappiness"
    sudo sysctl vm.vfs_cache_pressure=50 2>/dev/null || print_status $YELLOW "Could not set cache pressure"
    
    # Enable memory compression
    sudo sysctl vm.compressor=1 2>/dev/null || print_status $YELLOW "Could not enable compressor"
    
    # Set memory allocation policies
    export MALLOC_TRIM_THRESHOLD_=131072
    export MALLOC_MMAP_THRESHOLD_=131072
    export MALLOC_MMAP_MAX_=65536
    
    print_status $GREEN "✅ Memory settings optimized"
}

# Function to monitor memory continuously
monitor_memory_continuous() {
    print_status $BLUE "📊 Starting continuous memory monitoring..."
    
    while true; do
        clear
        print_status $GREEN "=== RL-Swarm Memory Monitor ==="
        echo ""
        check_memory_status
        
        # Check if RL-Swarm is running
        if pgrep -f "run_rl_swarm" >/dev/null; then
            print_status $GREEN "✅ RL-Swarm is running"
        else
            print_status $YELLOW "⚠️ RL-Swarm is not running"
        fi
        
        echo ""
        print_status $BLUE "Press Ctrl+C to stop monitoring"
        sleep 10
    done
}

# Function to create memory optimization script
create_optimization_script() {
    print_status $BLUE "📝 Creating memory optimization script..."
    
    cat > memory_optimize.sh << 'EOF'
#!/usr/bin/env bash

# Auto-generated memory optimization script
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

# Clear memory before starting
sudo purge 2>/dev/null || true

echo "Memory optimization environment loaded"
EOF
    
    chmod +x memory_optimize.sh
    print_status $GREEN "✅ Optimization script created: memory_optimize.sh"
}

# Function to show memory usage by process
show_process_memory() {
    print_status $BLUE "🔍 Process Memory Usage:"
    echo ""
    
    # Python processes
    print_status $GREEN "Python Processes:"
    ps aux | grep python | grep -v grep | sort -nr -k 4 | head -5
    echo ""
    
    # RL-Swarm related processes
    print_status $GREEN "RL-Swarm Processes:"
    ps aux | grep -E "(swarm|genrl|torch)" | grep -v grep | sort -nr -k 4 | head -5
    echo ""
}

# Function to kill memory-intensive processes
kill_memory_intensive() {
    print_status $BLUE "🔄 Killing memory-intensive processes..."
    
    # Kill Python processes using too much memory (>2GB)
    ps aux | awk '$4 > 20.0 && /python/ {print $2}' | while read pid; do
        if [ ! -z "$pid" ]; then
            print_status $YELLOW "Killing Python process $pid"
            kill -9 "$pid" 2>/dev/null || true
        fi
    done
    
    # Kill zombie processes
    ps aux | awk '$8 ~ /^Z/ {print $2}' | while read pid; do
        if [ ! -z "$pid" ]; then
            print_status $YELLOW "Killing zombie process $pid"
            kill -9 "$pid" 2>/dev/null || true
        fi
    done
    
    print_status $GREEN "✅ Memory-intensive processes cleaned up"
}

# Main menu
show_menu() {
    print_status $GREEN "=== RL-Swarm Memory Manager ==="
    echo ""
    echo "1. Check memory status"
    echo "2. Clean up memory"
    echo "3. Optimize memory settings"
    echo "4. Monitor memory continuously"
    echo "5. Show process memory usage"
    echo "6. Kill memory-intensive processes"
    echo "7. Create optimization script"
    echo "8. Exit"
    echo ""
    read -p "Choose an option (1-8): " choice
    
    case $choice in
        1) check_memory_status ;;
        2) cleanup_memory ;;
        3) optimize_memory_settings ;;
        4) monitor_memory_continuous ;;
        5) show_process_memory ;;
        6) kill_memory_intensive ;;
        7) create_optimization_script ;;
        8) exit 0 ;;
        *) print_status $RED "Invalid option" ;;
    esac
}

# Main execution
main() {
    if [ $# -eq 0 ]; then
        show_menu
    else
        case $1 in
            "status") check_memory_status ;;
            "cleanup") cleanup_memory ;;
            "optimize") optimize_memory_settings ;;
            "monitor") monitor_memory_continuous ;;
            "processes") show_process_memory ;;
            "kill") kill_memory_intensive ;;
            "create") create_optimization_script ;;
            *) show_menu ;;
        esac
    fi
}

# Run main function
main "$@"
