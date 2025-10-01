#!/usr/bin/env bash

# macOS Swap Manager for RL-Swarm
# This script manages swap memory to prevent OOM issues

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

# Function to check swap status
check_swap_status() {
    print_status $BLUE "🔍 Current Swap Status:"
    echo ""
    
    # Swap usage
    print_status $GREEN "Swap Usage:"
    sysctl vm.swapusage
    echo ""
    
    # Swap files
    print_status $GREEN "Swap Files:"
    ls -la /private/var/vm/ 2>/dev/null || echo "No swap files found"
    echo ""
    
    # Memory pressure
    print_status $GREEN "Memory Pressure:"
    if command -v memory_pressure >/dev/null 2>&1; then
        memory_pressure
    else
        echo "Memory pressure command not available"
    fi
    echo ""
}

# Function to clear swap
clear_swap() {
    print_status $BLUE "🧹 Clearing swap memory..."
    
    # Check if we have swap to clear
    local swap_used=$(sysctl vm.swapusage | awk '{print $7}' | sed 's/M//')
    
    if [ "$swap_used" -gt 0 ]; then
        print_status $YELLOW "Current swap usage: ${swap_used}MB"
        
        # Force memory cleanup
        print_status $YELLOW "Forcing memory cleanup..."
        sudo purge 2>/dev/null || print_status $YELLOW "purge command requires sudo"
        
        # Clear swap files
        print_status $YELLOW "Clearing swap files..."
        sudo rm -f /private/var/vm/swapfile* 2>/dev/null || true
        
        # Restart swap
        print_status $YELLOW "Restarting swap..."
        sudo launchctl unload /System/Library/LaunchDaemons/com.apple.dynamic_pager.plist 2>/dev/null || true
        sudo launchctl load /System/Library/LaunchDaemons/com.apple.dynamic_pager.plist 2>/dev/null || true
        
        print_status $GREEN "✅ Swap cleared successfully"
    else
        print_status $GREEN "✅ No swap usage detected"
    fi
}

# Function to optimize swap settings
optimize_swap_settings() {
    print_status $BLUE "⚙️ Optimizing swap settings..."
    
    # Set swappiness to low value to prefer physical memory
    sudo sysctl vm.swappiness=10 2>/dev/null || print_status $YELLOW "Could not set swappiness"
    
    # Set memory pressure to be more aggressive
    sudo sysctl vm.vfs_cache_pressure=50 2>/dev/null || print_status $YELLOW "Could not set cache pressure"
    
    # Enable memory compression
    sudo sysctl vm.compressor=1 2>/dev/null || print_status $YELLOW "Could not enable compressor"
    
    # Set swap file size limits
    sudo sysctl vm.swapfile_max_size=8388608 2>/dev/null || print_status $YELLOW "Could not set swap file size"
    
    print_status $GREEN "✅ Swap settings optimized"
}

# Function to create swap file
create_swap_file() {
    print_status $BLUE "📁 Creating dedicated swap file..."
    
    local swap_size=${1:-2048}  # Default 2GB
    
    print_status $YELLOW "Creating ${swap_size}MB swap file..."
    
    # Create swap file
    sudo dd if=/dev/zero of=/private/var/vm/swapfile_custom bs=1m count=$swap_size 2>/dev/null || {
        print_status $RED "Failed to create swap file"
        return 1
    }
    
    # Set permissions
    sudo chmod 600 /private/var/vm/swapfile_custom
    
    # Enable swap file
    sudo swapon /private/var/vm/swapfile_custom 2>/dev/null || {
        print_status $YELLOW "Could not enable swap file (may require reboot)"
    }
    
    print_status $GREEN "✅ Swap file created: /private/var/vm/swapfile_custom"
}

# Function to monitor swap usage
monitor_swap() {
    print_status $BLUE "📊 Monitoring swap usage..."
    
    while true; do
        clear
        print_status $GREEN "=== Swap Monitor ==="
        echo ""
        check_swap_status
        
        # Check if RL-Swarm is running
        if pgrep -f "run_rl_swarm" >/dev/null; then
            print_status $GREEN "✅ RL-Swarm is running"
        else
            print_status $YELLOW "⚠️ RL-Swarm is not running"
        fi
        
        echo ""
        print_status $BLUE "Press Ctrl+C to stop monitoring"
        sleep 5
    done
}

# Function to prevent swap usage
prevent_swap() {
    print_status $BLUE "🚫 Preventing swap usage..."
    
    # Set very low swappiness
    sudo sysctl vm.swappiness=1 2>/dev/null || print_status $YELLOW "Could not set swappiness"
    
    # Disable swap files
    sudo launchctl unload /System/Library/LaunchDaemons/com.apple.dynamic_pager.plist 2>/dev/null || true
    
    print_status $GREEN "✅ Swap usage prevented"
}

# Function to enable swap
enable_swap() {
    print_status $BLUE "✅ Enabling swap..."
    
    # Enable dynamic pager
    sudo launchctl load /System/Library/LaunchDaemons/com.apple.dynamic_pager.plist 2>/dev/null || true
    
    # Set normal swappiness
    sudo sysctl vm.swappiness=60 2>/dev/null || print_status $YELLOW "Could not set swappiness"
    
    print_status $GREEN "✅ Swap enabled"
}

# Function to show swap recommendations
show_recommendations() {
    print_status $BLUE "💡 Swap Management Recommendations:"
    echo ""
    print_status $GREEN "For RL-Swarm on macOS:"
    echo "1. Use the optimized run script: ./run_rl_swarm_optimized.sh"
    echo "2. Set PYTORCH_MPS_HIGH_WATERMARK_RATIO=0.0"
    echo "3. Monitor memory usage regularly"
    echo "4. Clear swap before starting training"
    echo "5. Use memory monitoring tools"
    echo ""
    print_status $GREEN "Environment variables to set:"
    echo "export PYTORCH_MPS_HIGH_WATERMARK_RATIO=0.0"
    echo "export PYTORCH_MPS_ALLOCATOR_POLICY=expandable_segments"
    echo "export MPS_DEVICE_MEMORY_LIMIT=0.8"
    echo ""
    print_status $GREEN "System settings to optimize:"
    echo "sudo sysctl vm.swappiness=10"
    echo "sudo sysctl vm.vfs_cache_pressure=50"
    echo "sudo sysctl vm.compressor=1"
    echo ""
}

# Main menu
show_menu() {
    print_status $GREEN "=== RL-Swarm Swap Manager ==="
    echo ""
    echo "1. Check swap status"
    echo "2. Clear swap"
    echo "3. Optimize swap settings"
    echo "4. Create swap file"
    echo "5. Monitor swap usage"
    echo "6. Prevent swap usage"
    echo "7. Enable swap"
    echo "8. Show recommendations"
    echo "9. Exit"
    echo ""
    read -p "Choose an option (1-9): " choice
    
    case $choice in
        1) check_swap_status ;;
        2) clear_swap ;;
        3) optimize_swap_settings ;;
        4) read -p "Enter swap size in MB (default 2048): " size; create_swap_file ${size:-2048} ;;
        5) monitor_swap ;;
        6) prevent_swap ;;
        7) enable_swap ;;
        8) show_recommendations ;;
        9) exit 0 ;;
        *) print_status $RED "Invalid option" ;;
    esac
}

# Main execution
main() {
    if [ $# -eq 0 ]; then
        show_menu
    else
        case $1 in
            "status") check_swap_status ;;
            "clear") clear_swap ;;
            "optimize") optimize_swap_settings ;;
            "create") create_swap_file $2 ;;
            "monitor") monitor_swap ;;
            "prevent") prevent_swap ;;
            "enable") enable_swap ;;
            "recommendations") show_recommendations ;;
            *) show_menu ;;
        esac
    fi
}

# Run main function
main "$@"
