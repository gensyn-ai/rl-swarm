#!/usr/bin/env bash
set -euo pipefail

echo "Setting up Quok GPU audit..."

# Detect if we're on Debian/Ubuntu (not Mac)
if [[ -f /etc/debian_version ]] || [[ -f /etc/lsb-release ]] || command -v apt-get &> /dev/null; then
    echo "Detected Debian/Ubuntu system"
    
    # Check if we have GPU support (NVIDIA CUDA)
    if command -v nvidia-smi &> /dev/null || [[ -n "${CUDA_VISIBLE_DEVICES:-}" ]] || [[ -f /usr/local/cuda/version.txt ]]; then
        echo "GPU detected - Quok security audit available"
        
        # Ask user if they want to run Quok audit
        echo ""
        read -p "Do you want to run Quok security audit? (Y/N): " -n 1 -r
        echo ""
        
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            # Check if QUOK_API_KEY is provided via environment variable
            if [ -z "${QUOK_API_KEY:-}" ]; then
                echo ""
                echo "Quok API key not found in environment variables."
                read -p "Please enter your Quok API key: " -s QUOK_API_KEY
                echo ""
                
                if [ -z "$QUOK_API_KEY" ]; then
                    echo "No API key provided. Skipping Quok setup."
                    exit 0
                fi
            else
                echo "Using Quok API key from environment variable."
            fi
            
            # Check if Quok is installed
            if ! command -v quok &> /dev/null; then
                echo "❌ Quok not found. Please ensure it was installed during container build."
                exit 1
            fi
            
            # Initialize Quok with API key
            echo "Initializing Quok..."
            echo "$QUOK_API_KEY" | quok init
            
            # Run Quok audit
            echo "Running Quok auditme..."
            quok auditme
            
            echo "Quok setup and audit completed successfully."
        else
            echo "Skipping Quok security audit."
        fi
    else
        echo "No GPU detected - skipping Quok setup (CPU-only mode)"
    fi
else
    echo "ℹNon-Debian/Ubuntu system detected (likely macOS). Skipping Quok setup."
fi
