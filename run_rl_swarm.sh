#!/bin/bash

#General args
ROOT=$PWD

export PUB_MULTI_ADDRS
export PEER_MULTI_ADDRS
export HOST_MULTI_ADDRS
export IDENTITY_PATH
export CONNECT_TO_TESTNET
export ORG_ID
export HF_HUB_DOWNLOAD_TIMEOUT=120  # 2 minutes

#Check if public multi-address is given else set to default
DEFAULT_PUB_MULTI_ADDRS=""
PUB_MULTI_ADDRS=${PUB_MULTI_ADDRS:-$DEFAULT_PUB_MULTI_ADDRS}

#Check if peer multi-address is given else set to default
DEFAULT_PEER_MULTI_ADDRS="/ip4/38.101.215.13/tcp/30002/p2p/QmQ2gEXoPJg6iMBSUFWGzAabS2VhnzuS782Y637hGjfsRJ" # gensyn coordinator node
PEER_MULTI_ADDRS=${PEER_MULTI_ADDRS:-$DEFAULT_PEER_MULTI_ADDRS}

#Check if host multi-address is given else set to default
DEFAULT_HOST_MULTI_ADDRS="/ip4/0.0.0.0/tcp/38331"
HOST_MULTI_ADDRS=${HOST_MULTI_ADDRS:-$DEFAULT_HOST_MULTI_ADDRS}

# Path to an RSA private key. If this path does not exist, a new key pair will be created.
# Remove this file if you want a new PeerID.
DEFAULT_IDENTITY_PATH="$ROOT"/swarm.pem
IDENTITY_PATH=${IDENTITY_PATH:-$DEFAULT_IDENTITY_PATH}

while true; do
    read -p "Would you like to connect to the Testnet? [Y/n] " yn
    yn=${yn:-Y}  # Default to "Y" if the user presses Enter
    case $yn in
        [Yy]* ) CONNECT_TO_TESTNET=True && break;;
        [Nn]* ) CONNECT_TO_TESTNET=False && break;;
        * ) echo ">>> Please answer yes or no.";;
    esac
done

if [ "$CONNECT_TO_TESTNET" = "True" ]; then
    # run modal_login server
    echo "Please login to create an Ethereum Server Wallet"
cd modal-login

# Check if the npm command exists; if not, install npm.
source ~/.bashrc

if ! command -v npm >/dev/null 2>&1; then
    # Detect Ubuntu (including WSL Ubuntu) and install npm accordingly
    if grep -qi "ubuntu" /etc/os-release 2>/dev/null || uname -r | grep -qi "microsoft"; then
        echo "Detected Ubuntu or WSL Ubuntu. Installing npm via apt..."
        sudo apt update
        sudo apt install -y npm
    else
        echo "npm is not installed. Installing npm..."
        curl -L https://npmjs.org/install.sh | sh
    fi
fi

# Install dependencies using npm with --legacy-peer-deps
npm install --legacy-peer-deps # Why so?, I discovered a lot of peer dependency issues, this is probably why I ran into the dev error (https://github.com/gensyn-ai/rl-swarm/issues/74) I decided it's best to use npm and ignore them with this flag

# Run the server in the background and suppress output
npm run dev > /dev/null 2>&1 &


    SERVER_PID=$!  # Store the process ID
    sleep 5
    open http://localhost:3000
    cd ..

    # Wait until modal-login/temp-data/userData.json exists
    while [ ! -f "modal-login/temp-data/userData.json" ]; do
        echo "Waiting for userData.json to be created..."
        sleep 5  # Wait for 5 seconds before checking again
    done
    echo "userData.json found. Proceeding..."

    ORG_ID=$(awk 'BEGIN { FS = "\"" } !/^[ \t]*[{}]/ { print $(NF - 1); exit }' modal-login/temp-data/userData.json)
    echo "ORG_ID set to: $ORG_ID"

    # Wait until the API key is activated by the client
    echo "Waiting for API key to become activated..."
    while true; do
        STATUS=$(curl -s "http://localhost:3000/api/get-api-key-status?orgId=$ORG_ID")
        if [[ "$STATUS" == "activated" ]]; then
            echo "API key is activated! Proceeding..."
            break
        else
            echo "Waiting for API key to be activated..."
            sleep 5
        fi
    done

    # Function to clean up the server process
    cleanup() {
        echo "Shutting down server..."
        kill $SERVER_PID
        rm -r modal-login/temp-data/*.json
        exit 0
    }

    # Set up trap to catch Ctrl+C and call cleanup
    trap cleanup INT
fi
#lets go!
echo "Getting requirements..."
pip install -r "$ROOT"/requirements-hivemind.txt > /dev/null
pip install -r "$ROOT"/requirements.txt > /dev/null

if ! which nvidia-smi; then
   #You don't have a NVIDIA GPU
   CONFIG_PATH="$ROOT/hivemind_exp/configs/mac/grpo-qwen-2.5-0.5b-deepseek-r1.yaml"
elif [ -n "$CPU_ONLY" ]; then
   # ... or we don't want to use it
   CONFIG_PATH="$ROOT/hivemind_exp/configs/mac/grpo-qwen-2.5-0.5b-deepseek-r1.yaml"
else
   #NVIDIA GPU found
   pip install -r "$ROOT"/requirements_gpu.txt > /dev/null
   CONFIG_PATH="$ROOT/hivemind_exp/configs/gpu/grpo-qwen-2.5-0.5b-deepseek-r1.yaml"
fi

echo ">> Done!"
echo ""
echo ""

if [ -n "${HF_TOKEN}" ]; then # Check if HF_TOKEN is already set and use if so. Else give user a prompt to choose.
   HUGGINGFACE_ACCESS_TOKEN=${HF_TOKEN}
else
   read -p "Would you like to push models you train in the RL swarm to the Hugging Face Hub? [y/N] " yn
   yn=${yn:-N}  # Default to "N" if the user presses Enter
   case $yn in
      [Yy]* ) read -p "Enter your Hugging Face access token: " HUGGINGFACE_ACCESS_TOKEN;;
      [Nn]* ) HUGGINGFACE_ACCESS_TOKEN="None";;
      * ) echo ">>> No answer was given, so NO models will be pushed to Hugging Face Hub" && HUGGINGFACE_ACCESS_TOKEN="None";;
   esac
fi

echo ""
echo ""
echo "Good luck in the swarm!"

if [ -n "$ORG_ID" ]; then
    python -m hivemind_exp.gsm8k.train_single_gpu \
        --hf_token "$HUGGINGFACE_ACCESS_TOKEN" \
        --identity_path "$IDENTITY_PATH" \
        --modal_org_id "$ORG_ID" \
        --config "$CONFIG_PATH"
else
    python -m hivemind_exp.gsm8k.train_single_gpu \
        --hf_token "$HUGGINGFACE_ACCESS_TOKEN" \
        --identity_path "$IDENTITY_PATH" \
        --public_maddr "$PUB_MULTI_ADDRS" \
        --initial_peers "$PEER_MULTI_ADDRS"\
        --host_maddr "$HOST_MULTI_ADDRS" \
        --config "$CONFIG_PATH"
fi

wait  # Keep script running until Ctrl+C

