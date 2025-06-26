#!/bin/bash

set -euo pipefail

# General arguments
ROOT=$PWD

export PUB_MULTI_ADDRS
export PEER_MULTI_ADDRS
export HOST_MULTI_ADDRS
export IDENTITY_PATH
export CONNECT_TO_TESTNET
export ORG_ID
export HF_HUB_DOWNLOAD_TIMEOUT=300  # 5 minutes for better stability

# Apple Silicon M4 optimizations
export PYTORCH_MPS_HIGH_WATERMARK_RATIO=0.0  # Disable MPS for CPU-only mode
export OMP_NUM_THREADS=$(sysctl -n hw.ncpu)  # Use all available cores
export MKL_NUM_THREADS=$(sysctl -n hw.ncpu)
export VECLIB_MAXIMUM_THREADS=$(sysctl -n hw.ncpu)
export NUMEXPR_NUM_THREADS=$(sysctl -n hw.ncpu)

# Memory optimization for Mac Mini M4
export MALLOC_ARENA_MAX=4
export PYTHONHASHSEED=0  # For reproducibility
export TOKENIZERS_PARALLELISM=true

# Check if we're running on macOS
if [[ "$OSTYPE" != "darwin"* ]]; then
    echo "This script is optimized for macOS. For other systems, use run_rl_swarm_uv.sh"
    exit 1
fi

# Detect Apple Silicon and optimize accordingly
if [[ $(uname -m) == "arm64" ]]; then
    echo ">> Detected Apple Silicon (M-series chip) - applying optimizations..."
    export ARCHFLAGS="-arch arm64"
    export _PYTHON_HOST_PLATFORM="macosx-$(sw_vers -productVersion | cut -d. -f1,2)-arm64"
    export HOMEBREW_PREFIX="/opt/homebrew"
else
    echo ">> Detected Intel Mac - using standard configuration..."
    export HOMEBREW_PREFIX="/usr/local"
fi

# Function to detect system resources and optimize
detect_system_resources() {
    local total_memory=$(sysctl -n hw.memsize)
    local cpu_cores=$(sysctl -n hw.ncpu)
    local performance_cores=$(sysctl -n hw.perflevel0.physicalcpu 2>/dev/null || echo $cpu_cores)
    
    echo ">> System Resources Detected:"
    echo "   - Total Memory: $((total_memory / 1024 / 1024 / 1024)) GB"
    echo "   - CPU Cores: $cpu_cores"
    echo "   - Performance Cores: $performance_cores"
    
    # Optimize based on available memory
    if [ $((total_memory / 1024 / 1024 / 1024)) -ge 16 ]; then
        export PYTORCH_CUDA_ALLOC_CONF="max_split_size_mb:128"
        export HF_HUB_CACHE_SIZE="2GB"
        echo "   - Memory optimization: High memory mode enabled"
    else
        export PYTORCH_CUDA_ALLOC_CONF="max_split_size_mb:64"
        export HF_HUB_CACHE_SIZE="1GB"
        echo "   - Memory optimization: Conservative memory mode enabled"
    fi
    
    # Set optimal worker count for parallel processing
    export UV_WORKER_COUNT=$((cpu_cores / 2))
    export TRANSFORMERS_OFFLINE=0
}

# Check if public multi-address is given else set to default
DEFAULT_PUB_MULTI_ADDRS=""
PUB_MULTI_ADDRS=${PUB_MULTI_ADDRS:-$DEFAULT_PUB_MULTI_ADDRS}

# Check if peer multi-address is given else set to default
DEFAULT_PEER_MULTI_ADDRS="/ip4/38.101.215.13/tcp/30002/p2p/QmQ2gEXoPJg6iMBSUFWGzAabS2VhnzuS782Y637hGjfsRJ" # gensyn coordinator node
PEER_MULTI_ADDRS=${PEER_MULTI_ADDRS:-$DEFAULT_PEER_MULTI_ADDRS}

# Check if host multi-address is given else set to default
DEFAULT_HOST_MULTI_ADDRS="/ip4/0.0.0.0/tcp/38331"
HOST_MULTI_ADDRS=${HOST_MULTI_ADDRS:-$DEFAULT_HOST_MULTI_ADDRS}

# Path to an RSA private key. If this path does not exist, a new key pair will be created.
# Remove this file if you want a new PeerID.
DEFAULT_IDENTITY_PATH="$ROOT"/swarm.pem
IDENTITY_PATH=${IDENTITY_PATH:-$DEFAULT_IDENTITY_PATH}

SMALL_SWARM_CONTRACT="0x69C6e1D608ec64885E7b185d39b04B491a71768C"
BIG_SWARM_CONTRACT="0x6947c6E196a48B77eFa9331EC1E3e45f3Ee5Fd58"

# Force CPU-only mode on Mac (optimized for Apple Silicon)
CPU_ONLY="true"

# Set if successfully parsed from modal-login/temp-data/userData.json.
ORG_ID=${ORG_ID:-""}

GREEN_TEXT="\033[32m"
BLUE_TEXT="\033[34m"
RED_TEXT="\033[31m"
YELLOW_TEXT="\033[33m"
RESET_TEXT="\033[0m"

echo_green() {
    echo -e "$GREEN_TEXT$1$RESET_TEXT"
}

echo_blue() {
    echo -e "$BLUE_TEXT$1$RESET_TEXT"
}

echo_red() {
    echo -e "$RED_TEXT$1$RESET_TEXT"
}

echo_yellow() {
    echo -e "$YELLOW_TEXT$1$RESET_TEXT"
}

ROOT_DIR="$(cd $(dirname ${BASH_SOURCE[0]}) && pwd)"

# Function to clean up the server process upon exit
cleanup() {
    echo_green ">> Shutting down trainer..."

    # Remove modal credentials if they exist
    rm -rf "$ROOT_DIR/modal-login/temp-data/"*.json 2> /dev/null || true

    # Kill all processes belonging to this script's process group
    kill -- -$$ 2>/dev/null || true

    exit 0
}

errnotify() {
    echo_red ">> An error was detected while running rl-swarm. See $ROOT/logs for full logs."
    echo_red ">> Common issues on Mac:"
    echo_red "   - Make sure Xcode Command Line Tools are installed: xcode-select --install"
    echo_red "   - Make sure Homebrew is installed: https://brew.sh"
    echo_red "   - Check that you have sufficient disk space and memory"
    echo_red "   - For Apple Silicon Macs, ensure you're using ARM64 native dependencies"
}

trap cleanup EXIT
trap errnotify ERR

echo -e "\033[38;5;224m"
cat << "EOF"
    ██████  ██            ███████ ██     ██  █████  ██████  ███    ███
    ██   ██ ██            ██      ██     ██ ██   ██ ██   ██ ████  ████
    ██████  ██      █████ ███████ ██  █  ██ ███████ ██████  ██ ████ ██
    ██   ██ ██                 ██ ██ ███ ██ ██   ██ ██   ██ ██  ██  ██
    ██   ██ ███████       ███████  ███ ███  ██   ██ ██   ██ ██      ██

    From Gensyn (Mac Mini M4 Optimized Edition)

EOF

echo_yellow ">> Running in CPU-only mode (optimized for Apple Silicon)"

# Display usage information for automatic configuration
echo_blue ">> 💡 自动配置提示:"
echo_blue "   要跳过交互式提示，可以设置以下环境变量："
echo_blue "   - AUTO_TESTNET=y|n    (是否连接测试网)"
echo_blue "   - AUTO_SWARM=a|b      (选择 Math(A) 或 Math Hard(B) swarm)"
echo_blue "   - AUTO_HF_HUB=y|n     (是否推送到 Hugging Face Hub)"
echo_blue "   - HF_TOKEN=your_token (Hugging Face 访问令牌)"
echo_blue ""
echo_blue "   示例: AUTO_TESTNET=y AUTO_SWARM=a AUTO_HF_HUB=n ./ops/scripts/run_rl_swarm_mac.sh"
echo_blue ""

# Detect and display system resources
detect_system_resources

# Check for Xcode Command Line Tools (essential for Apple Silicon)
if ! xcode-select -p &> /dev/null; then
    echo_yellow ">> Xcode Command Line Tools not found. Installing..."
    xcode-select --install
    echo_yellow ">> Please complete the Xcode Command Line Tools installation and run this script again."
    exit 1
fi

# Check if Homebrew is installed
if ! command -v brew > /dev/null 2>&1; then
    echo_yellow ">> Homebrew not found. Installing Homebrew..."
    /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
    
    # Add Homebrew to PATH for Apple Silicon Macs
    if [[ $(uname -m) == "arm64" ]]; then
        echo 'eval "$(/opt/homebrew/bin/brew shellenv)"' >> ~/.zprofile
        eval "$(/opt/homebrew/bin/brew shellenv)"
    else
        echo 'eval "$(/usr/local/bin/brew shellenv)"' >> ~/.zprofile
        eval "$(/usr/local/bin/brew shellenv)"
    fi
fi

# Update Homebrew and ensure we have the latest packages
echo_green ">> Updating Homebrew..."
brew update &> /dev/null || true

# Check if uv is installed
if ! command -v uv > /dev/null 2>&1; then
    echo_green ">> Installing uv via Homebrew..."
    brew install uv
else
    echo_green ">> uv is already installed: $(uv --version)"
    # Update uv to latest version for better Apple Silicon support
    brew upgrade uv &> /dev/null || true
fi

echo_green ">> Setting up virtual environment with uv (Apple Silicon optimized)..."

# Initialize uv project if not already done
if [ ! -f "pyproject.toml" ]; then
    echo_red ">> pyproject.toml not found. Please ensure the project is properly configured."
    exit 1
fi

# Always use CPU-only dependencies on Mac with Apple Silicon optimizations
echo_green ">> Installing CPU-only dependencies with Apple Silicon optimizations..."

# Set Python path for Apple Silicon if needed
if [[ $(uname -m) == "arm64" ]]; then
    export UV_PYTHON_PREFERENCE="only-managed"
    export UV_PYTHON="3.11"  # Use a stable Python version
fi

# Function to install dependencies with better error handling
install_dependencies() {
    echo_green ">> Creating virtual environment..."
    if ! uv venv --python 3.11 --quiet; then
        echo_red ">> Failed to create virtual environment"
        return 1
    fi
    
    echo_green ">> Installing basic dependencies first..."
    # Install basic dependencies without Git-based packages
    local basic_deps=(
        "colorlog"
        "datasets"
        "hf-transfer"
        "peft"
        "pytest"
        "tensorboard"
        "transformers>=4.46.0"
        "trl"
        "wandb"
        "web3"
        "torch --index-url https://download.pytorch.org/whl/cpu"  # CPU-only torch
    )
    
    for dep in "${basic_deps[@]}"; do
        echo_yellow "   Installing: $dep"
        if ! uv add $dep --quiet; then
            echo_yellow "   Retrying $dep with uv pip..."
            uv pip install $dep --quiet || true
        fi
        sleep 1  # Small delay to avoid overwhelming the system
    done
    
    echo_green ">> Installing hivemind (this may take a few minutes)..."
    # Special handling for hivemind
    export CC=clang
    export CXX=clang++
    if ! uv add "hivemind @ git+https://github.com/learning-at-home/hivemind@1.11.11" --quiet; then
        echo_yellow "   Trying alternative installation method for hivemind..."
        uv pip install "git+https://github.com/learning-at-home/hivemind@1.11.11" --quiet || {
            echo_red "   Failed to install hivemind. Trying with conda-forge..."
            # Fallback: try to install hivemind from conda-forge if available
            if command -v conda > /dev/null 2>&1; then
                conda install -c conda-forge hivemind -y --quiet || true
            fi
        }
    fi
    
    echo_green ">> Verifying installation..."
    if uv run python -c "import hivemind; print('Hivemind version:', hivemind.__version__)" 2>/dev/null; then
        echo_green "   ✓ Hivemind installed successfully"
    else
        echo_yellow "   ⚠ Hivemind installation may have issues, but continuing..."
    fi
    
    return 0
}

# Try initial sync, if fails, use custom installation
if ! uv sync --no-dev --quiet; then
    echo_yellow ">> Initial sync failed. Using step-by-step installation..."
    
    # Remove any partial installation
    rm -rf .venv 2>/dev/null || true
    
    # Try custom installation method
    if ! install_dependencies; then
        echo_red ">> Custom installation failed. Trying alternative approach..."
        
        # Last resort: minimal installation
        echo_yellow ">> Attempting minimal installation..."
        uv venv --python 3.11 --quiet
        
        # Install only essential packages
        essential_packages=(
            "torch --index-url https://download.pytorch.org/whl/cpu"
            "transformers>=4.46.0"
            "datasets"
            "trl"
            "colorlog"
        )
        
        for pkg in "${essential_packages[@]}"; do
            echo_yellow "   Installing essential: $pkg"
            uv pip install $pkg --quiet || true
        done
        
        # Try to install hivemind separately
        echo_yellow "   Attempting hivemind installation with extended timeout..."
        uv pip install "git+https://github.com/learning-at-home/hivemind@1.11.11" --quiet || {
            echo_red "   Could not install hivemind. You may need to install it manually later."
            echo_red "   Run: uv pip install 'git+https://github.com/learning-at-home/hivemind@1.11.11'"
        }
    fi
else
    echo_green ">> Dependencies installed successfully via uv sync"
fi

# Final verification
echo_green ">> Performing final dependency check..."
missing_deps=()

critical_imports=(
    "torch:PyTorch"
    "transformers:Transformers"
    "datasets:Datasets"
    "trl:TRL"
)

for import_check in "${critical_imports[@]}"; do
    module="${import_check%:*}"
    name="${import_check#*:}"
    if ! uv run python -c "import $module" 2>/dev/null; then
        missing_deps+=("$name")
    fi
done

if [ ${#missing_deps[@]} -gt 0 ]; then
    echo_yellow ">> Some dependencies may be missing: ${missing_deps[*]}"
    echo_yellow ">> The system will try to continue, but you may encounter issues."
    echo_yellow ">> Consider running: uv sync --no-dev again after the script completes."
else
    echo_green ">> All critical dependencies verified successfully!"
fi

CONFIG_PATH="$ROOT/hivemind_exp/configs/mac/grpo-qwen-2.5-0.5b-deepseek-r1.yaml"
GAME="gsm8k"

# Check for automatic configuration via environment variables
AUTO_TESTNET=${AUTO_TESTNET:-""}
AUTO_SWARM=${AUTO_SWARM:-""}
AUTO_HF_HUB=${AUTO_HF_HUB:-""}

# Testnet connection configuration
if [ -n "$AUTO_TESTNET" ]; then
    case $AUTO_TESTNET in
        [Yy]*)  
            CONNECT_TO_TESTNET=true 
            echo_green ">> 🤖 自动配置: 连接到测试网 (AUTO_TESTNET=$AUTO_TESTNET)"
            ;;
        [Nn]*)  
            CONNECT_TO_TESTNET=false 
            echo_green ">> 🤖 自动配置: 本地模式 (AUTO_TESTNET=$AUTO_TESTNET)"
            ;;
        *)  
            echo_yellow ">> ⚠️ AUTO_TESTNET 值无效 ($AUTO_TESTNET)，将进入交互模式"
            AUTO_TESTNET=""
            ;;
    esac
fi

if [ -z "$AUTO_TESTNET" ]; then
    while true; do
        echo -en $GREEN_TEXT
        read -p ">> Would you like to connect to the Testnet? [Y/n] " yn
        echo -en $RESET_TEXT
        yn=${yn:-Y}  # Default to "Y" if the user presses Enter
        case $yn in
            [Yy]*)  CONNECT_TO_TESTNET=true && break ;;
            [Nn]*)  CONNECT_TO_TESTNET=false && break ;;
            *)  echo ">>> Please answer yes or no." ;;
        esac
    done
fi

# Swarm selection configuration
if [ -n "$AUTO_SWARM" ]; then
    case $AUTO_SWARM in
        [Aa]*)  
            USE_BIG_SWARM=false 
            echo_green ">> 🤖 自动配置: 选择 Math (A) swarm (AUTO_SWARM=$AUTO_SWARM)"
            ;;
        [Bb]*)  
            USE_BIG_SWARM=true 
            echo_green ">> 🤖 自动配置: 选择 Math Hard (B) swarm (AUTO_SWARM=$AUTO_SWARM)"
            ;;
        *)  
            echo_yellow ">> ⚠️ AUTO_SWARM 值无效 ($AUTO_SWARM)，将进入交互模式"
            AUTO_SWARM=""
            ;;
    esac
fi

if [ -z "$AUTO_SWARM" ]; then
    while true; do
        echo -en $GREEN_TEXT
        read -p ">> Which swarm would you like to join (Math (A) or Math Hard (B))? [A/b] " ab
        echo -en $RESET_TEXT
        ab=${ab:-A}  # Default to "A" if the user presses Enter
        case $ab in
            [Aa]*)  USE_BIG_SWARM=false && break ;;
            [Bb]*)  USE_BIG_SWARM=true && break ;;
            *)  echo ">>> Please answer A or B." ;;
        esac
    done
fi

if [ "$USE_BIG_SWARM" = true ]; then
    SWARM_CONTRACT="$BIG_SWARM_CONTRACT"
else
    SWARM_CONTRACT="$SMALL_SWARM_CONTRACT"
fi

# Optimized model selection for Mac Mini M4
echo_yellow ">> For optimal Mac Mini M4 performance, using 0.5B parameter model"
echo_yellow ">> This model is specifically chosen to balance performance and memory usage"
PARAM_B="0.5"

# Create logs directory if it doesn't exist
mkdir -p "$ROOT/logs"

if [ "$CONNECT_TO_TESTNET" = true ]; then
    # Run modal_login server.
    echo "Please login to create an Ethereum Server Wallet"
    cd modal-login
    
    # Install Node.js via Homebrew if not present (ensure ARM64 version)
    if ! command -v node > /dev/null 2>&1; then
        echo_green ">> Installing Node.js via Homebrew (ARM64 optimized)..."
        brew install node
    else
        # Check if Node.js version is >= 18 (better for Apple Silicon)
        NODE_VERSION=$(node -v | sed 's/v//' | cut -d. -f1)
        if [ "$NODE_VERSION" -lt 18 ]; then
            echo_yellow ">> Node.js version $(node -v) is outdated. Updating for better Apple Silicon support..."
            brew upgrade node
        else
            echo_green ">> Node.js is already installed: $(node -v)"
        fi
    fi

    # Install Yarn via Homebrew if not present
    if ! command -v yarn > /dev/null 2>&1; then
        echo_green ">> Installing Yarn via Homebrew (ARM64 optimized)..."
        brew install yarn
    else
        echo_green ">> Yarn is already installed: $(yarn --version)"
    fi

    ENV_FILE="$ROOT/modal-login/.env"
    # macOS version of sed
    if [ -f "$ENV_FILE" ]; then
        sed -i '' "3s/.*/SMART_CONTRACT_ADDRESS=$SWARM_CONTRACT/" "$ENV_FILE"
    else
        echo_red ">> .env file not found in modal-login directory"
        exit 1
    fi

    echo_green ">> Installing dependencies with Apple Silicon optimizations..."
    # Use more aggressive caching and parallel installation
    yarn install --immutable --silent --network-timeout 100000
    echo_green ">> Building server with optimizations..."
    yarn build > "$ROOT/logs/yarn.log" 2>&1
    yarn start >> "$ROOT/logs/yarn.log" 2>&1 & # Run in background and log output

    SERVER_PID=$!  # Store the process ID
    echo_green ">> Started server process: $SERVER_PID"
    sleep 8  # Give more time for server to start

    # Try to open the URL in the default browser
    if open http://localhost:3000 2> /dev/null; then
        echo_green ">> Successfully opened http://localhost:3000 in your default browser."
    else
        echo_yellow ">> Please open http://localhost:3000 manually in your browser."
    fi

    cd ..

    echo_green ">> Waiting for modal userData.json to be created..."
    WAIT_COUNT=0
    while [ ! -f "modal-login/temp-data/userData.json" ]; do
        sleep 5  # Wait for 5 seconds before checking again
        echo -n "."
        WAIT_COUNT=$((WAIT_COUNT + 1))
        if [ $WAIT_COUNT -gt 60 ]; then  # 5 minutes timeout
            echo_red ">> Timeout waiting for userData.json. Please check the modal login process."
            exit 1
        fi
    done
    echo ""
    echo_green ">> Found userData.json. Proceeding..."

    ORG_ID=$(awk 'BEGIN { FS = "\"" } !/^[ \t]*[{}]/ { print $(NF - 1); exit }' modal-login/temp-data/userData.json)
    echo_green ">> Your ORG_ID is set to: $ORG_ID"

    # Wait until the API key is activated by the client
    echo_yellow ">> Waiting for API key to become activated..."
    API_WAIT_COUNT=0
    while true; do
        STATUS=$(curl -s "http://localhost:3000/api/get-api-key-status?orgId=$ORG_ID" 2>/dev/null || echo "error")
        if [[ "$STATUS" == "activated" ]]; then
            echo_green ">> API key is activated! Proceeding..."
            break
        else
            echo -n "."
            sleep 5
            API_WAIT_COUNT=$((API_WAIT_COUNT + 1))
            if [ $API_WAIT_COUNT -gt 120 ]; then  # 10 minutes timeout
                echo_red ">> Timeout waiting for API key activation. Please check the process."
                exit 1
            fi
        fi
    done
    echo ""
fi

echo_green ">> Configuration complete!"

HF_TOKEN=${HF_TOKEN:-""}
if [ -n "${HF_TOKEN}" ]; then # Check if HF_TOKEN is already set and use if so. Else give user a prompt to choose.
    HUGGINGFACE_ACCESS_TOKEN=${HF_TOKEN}
    echo_green ">> 🤖 自动配置: 使用预设的 HF_TOKEN"
else
    # Check for automatic HF Hub configuration
    if [ -n "$AUTO_HF_HUB" ]; then
        case $AUTO_HF_HUB in
            [Yy]*) 
                if [ -n "$HF_TOKEN" ]; then
                    HUGGINGFACE_ACCESS_TOKEN=${HF_TOKEN}
                    echo_green ">> 🤖 自动配置: 启用 Hugging Face Hub 推送 (AUTO_HF_HUB=$AUTO_HF_HUB)"
                else
                    echo_red ">> ❌ 错误: AUTO_HF_HUB=y 但未设置 HF_TOKEN 环境变量"
                    echo_yellow ">> 请设置 HF_TOKEN 环境变量或进入交互模式"
                    AUTO_HF_HUB=""
                fi
                ;;
            [Nn]*) 
                HUGGINGFACE_ACCESS_TOKEN="None"
                echo_green ">> 🤖 自动配置: 不推送到 Hugging Face Hub (AUTO_HF_HUB=$AUTO_HF_HUB)"
                ;;
            *)  
                echo_yellow ">> ⚠️ AUTO_HF_HUB 值无效 ($AUTO_HF_HUB)，将进入交互模式"
                AUTO_HF_HUB=""
                ;;
        esac
    fi
    
    if [ -z "$AUTO_HF_HUB" ] || [ -z "$HUGGINGFACE_ACCESS_TOKEN" ]; then
        echo -en $GREEN_TEXT
        read -p ">> Would you like to push models you train in the RL swarm to the Hugging Face Hub? [y/N] " yn
        echo -en $RESET_TEXT
        yn=${yn:-N} # Default to "N" if the user presses Enter
        case $yn in
            [Yy]*) 
                echo -en $GREEN_TEXT
                read -p "Enter your Hugging Face access token: " HUGGINGFACE_ACCESS_TOKEN 
                echo -en $RESET_TEXT
                ;;
            [Nn]*) HUGGINGFACE_ACCESS_TOKEN="None" ;;
            *) echo_yellow ">>> No answer was given, so NO models will be pushed to Hugging Face Hub" && HUGGINGFACE_ACCESS_TOKEN="None" ;;
        esac
    fi
fi

# Performance monitoring function
monitor_performance() {
    echo_blue ">> System Performance Monitor (Press Ctrl+C to stop training)"
    echo_blue ">> Monitor logs: tail -f $ROOT/logs/performance.log"
    
    # Start performance monitoring in background
    (
        while true; do
            TIMESTAMP=$(date '+%Y-%m-%d %H:%M:%S')
            CPU_USAGE=$(top -l 1 -s 0 | grep "CPU usage" | awk '{print $3}' | cut -d'%' -f1)
            MEMORY_PRESSURE=$(memory_pressure | grep "System-wide memory free percentage" | awk '{print $5}' | cut -d'%' -f1)
            echo "[$TIMESTAMP] CPU: ${CPU_USAGE}%, Memory Free: ${MEMORY_PRESSURE}%" >> "$ROOT/logs/performance.log"
            sleep 30
        done
    ) &
    MONITOR_PID=$!
    
    # Cleanup monitor on exit
    trap "kill $MONITOR_PID 2>/dev/null || true" EXIT
}

echo_green ">> Starting RL Swarm training with Mac Mini M4 optimizations..."
echo_blue ">> Good luck in the swarm!"
echo_blue ">> Post about rl-swarm on X/twitter! --> https://tinyurl.com/swarmtweet"
echo_blue ">> And remember to star the repo on GitHub! --> https://github.com/gensyn-ai/rl-swarm"

# Start performance monitoring
monitor_performance

# Run the training script using uv with Apple Silicon optimizations
echo_green ">> Launching training with optimized settings for Mac Mini M4..."
echo_blue ">> Applying Apple Silicon compatibility fixes..."

# Apply accelerate fix for Apple Silicon
if [ -f "$ROOT/fix_mac_accelerate.py" ]; then
    echo_green ">> 🔧 Applying accelerate compatibility patch..."
    uv run --quiet python fix_mac_accelerate.py
else
    echo_yellow ">> Warning: fix_mac_accelerate.py not found, skipping patch"
fi

if [ -n "$ORG_ID" ]; then
    echo_green ">> Running with Testnet connection..."
    uv run --quiet python -c "
# Apply Apple Silicon compatibility fixes
import sys, os
sys.path.insert(0, '$ROOT')
try:
    import fix_mac_accelerate
    fix_mac_accelerate.apply_mac_optimizations()
    fix_mac_accelerate.patch_accelerate_dataloader()
    print('✅ Apple Silicon 兼容性修复已应用')
except Exception as e:
    print(f'⚠️ 修复应用失败: {e}')

# Now run the actual training
os.system('python -m hivemind_exp.gsm8k.train_single_gpu --hf_token \"$HUGGINGFACE_ACCESS_TOKEN\" --identity_path \"$IDENTITY_PATH\" --modal_org_id \"$ORG_ID\" --contract_address \"$SWARM_CONTRACT\" --config \"$CONFIG_PATH\" --game \"$GAME\"')
"
else
    echo_green ">> Running in local mode..."
    uv run --quiet python -c "
# Apply Apple Silicon compatibility fixes
import sys, os
sys.path.insert(0, '$ROOT')
try:
    import fix_mac_accelerate
    fix_mac_accelerate.apply_mac_optimizations()
    fix_mac_accelerate.patch_accelerate_dataloader()
    print('✅ Apple Silicon 兼容性修复已应用')
except Exception as e:
    print(f'⚠️ 修复应用失败: {e}')

# Now run the actual training
os.system('python -m hivemind_exp.gsm8k.train_single_gpu --hf_token \"$HUGGINGFACE_ACCESS_TOKEN\" --identity_path \"$IDENTITY_PATH\" --public_maddr \"$PUB_MULTI_ADDRS\" --initial_peers \"$PEER_MULTI_ADDRS\" --host_maddr \"$HOST_MULTI_ADDRS\" --config \"$CONFIG_PATH\" --game \"$GAME\"')
"
fi

wait  # Keep script running until Ctrl+C 