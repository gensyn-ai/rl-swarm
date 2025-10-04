# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Overview

RL Swarm is a peer-to-peer system for decentralized reinforcement learning, powered by the [GenRL](https://github.com/gensyn-ai/genrl) library. The system enables collaborative model training through a distributed swarm that coordinates via blockchain and communicates through libp2p/hivemind.

The current implementation trains models on the [reasoning-gym](https://github.com/open-thought/reasoning-gym) dataset with optional participation in an AI Prediction Market game.

## Architecture

### Core Components

The system has three main parts:

1. **Training Infrastructure (`rgym_exp/`)**: Main RL training pipeline
   - `runner/swarm_launcher.py`: Entry point using Hydra for configuration
   - `src/manager.py`: `SwarmGameManager` orchestrates training rounds/stages
   - `src/trainer.py`: `GRPOTrainerModule` implements Group Relative Policy Optimization
   - `src/data.py`: `ReasoningGymDataManager` manages datasets from reasoning-gym
   - `src/coordinator.py`: `ModalSwarmCoordinator` handles blockchain coordination via Alchemy Modal
   - `src/prg_module.py`: `PRGModule` manages Prediction Market game participation
   - `config/rg-swarm.yaml`: Main configuration file with Hydra/OmegaConf

2. **Identity & Authentication (`modal-login/`)**: Next.js app for user authentication
   - Creates Alchemy-hosted EOA wallets linked to email addresses
   - Generates and registers `swarm.pem` peer identity files
   - Exposes API at `http://localhost:3000` for authentication flow

3. **Web API (`web/`)**: FastAPI server for metrics and gossip
   - `api/server.py`: Main FastAPI application
   - Uses OpenTelemetry for observability
   - Connects to DHT for swarm communication

### Key Protocols

- **Communication**: Hivemind DHT (distributed hash table) via libp2p for peer discovery and model sharing
- **Coordination**: Ethereum smart contracts (`SwarmCoordinator_0.4.2.json`) on Gensyn Testnet for round/stage synchronization and reward submission
- **Authentication**: Alchemy Modal for managed wallet creation and transaction signing
- **Training**: GRPO (Group Relative Policy Optimization) for policy updates

### Configuration System

Hydra configuration in `rgym_exp/config/rg-swarm.yaml`:
- Custom resolver `gpu_model_choice` automatically selects models based on hardware (large pool for GPU, small pool for CPU)
- Environment variable interpolation via `${oc.env:VAR_NAME,default}`
- Configuration is copied to `configs/rg-swarm.yaml` for user customization

## Development Commands

### Running the Swarm

**Docker (recommended):**
```bash
# CPU-only
docker-compose run --rm --build -Pit swarm-cpu

# GPU-enabled (requires NVIDIA drivers >=525.60.13 and nvidia-container-toolkit)
docker-compose run --rm --build -Pit swarm-gpu
```

**Shell script (advanced/experimental):**
```bash
python3 -m venv .venv
source .venv/bin/activate
./run_rl_swarm.sh
```

The script:
1. Installs Node.js/Yarn if needed
2. Starts modal-login server on port 3000
3. Waits for authentication (creates `modal-login/temp-data/userData.json`)
4. Installs GenRL library (version specified by `GENRL_TAG` in script)
5. Prompts for HuggingFace token and model selection
6. Launches training via `python -m rgym_exp.runner.swarm_launcher`

### Web Server

```bash
# Build and run web server + OpenTelemetry
docker-compose build --no-cache
docker-compose up

# Access at http://0.0.0.0:8080
```

### Modal Login Development

```bash
cd modal-login
yarn install
yarn build
yarn start  # Runs on port 3000
```

## Important Files and Paths

- `swarm.pem`: Peer identity (RSA key). Delete to generate new peer ID. Must match the email used for authentication.
- `modal-login/temp-data/userData.json`: Contains org_id from authentication
- `configs/rg-swarm.yaml`: User-editable config (backed up as `.bak` on version changes)
- `logs/swarm.log`: Main swarm logs
- `logs/yarn.log`: Modal login server logs
- `logs/prg_record.txt`: Prediction Market game history

## Environment Variables

Set in `run_rl_swarm.sh` or Docker:
- `IDENTITY_PATH`: Path to peer identity file (default: `./swarm.pem`)
- `SWARM_CONTRACT`: SwarmCoordinator contract address
- `PRG_CONTRACT`: Prediction Market contract address
- `CONNECT_TO_TESTNET`: Enable blockchain integration (default: true)
- `MODEL_NAME`: Override model selection (HuggingFace format: `repo/name`)
- `HUGGINGFACE_ACCESS_TOKEN`: For pushing trained models
- `PRG_GAME`: Enable Prediction Market participation (default: true)
- `CPU_ONLY`: Force CPU mode even if GPU available
- `GENSYN_RESET_CONFIG`: Reset config to defaults
- `HF_TOKEN`: HuggingFace token (Docker only)

## GenRL Integration

This codebase extends GenRL base classes:
- `BaseGameManager` → `SwarmGameManager`: Adds HuggingFace pushing, PRG game support
- `SwarmCoordinator` → `ModalSwarmCoordinator`: Uses Alchemy Modal API instead of direct wallet
- `GRPOLanguageTrainerModule` → `GRPOTrainerModule`: Adds judge evaluation endpoint
- `LocalMemoryTextDataManager` → `ReasoningGymDataManager`: Integrates reasoning-gym datasets

Key GenRL concepts:
- **GameState**: Tracks current round/stage
- **WorldState**: Synchronized state across peers via DHT
- **RewardManager**: Computes rewards using `RGRewards` (accuracy-based)
- **Communication**: Abstracted via `HivemindBackend`

## Identity Management Critical Rules

**Working scenarios:**
1. First run: New email + generates new `swarm.pem` ✓
2. Re-run: Same email + keep same `swarm.pem` ✓

**Broken scenarios:**
1. Keep `swarm.pem` but use different email ✗
2. Use same email but delete `swarm.pem` (creates new peer, still works but different identity)

**To run multiple nodes:** Use same email for each, each gets unique `swarm.pem`

## Testing

No test framework currently configured in the repository. The codebase includes some test files:
- `web/api/dht_pub_test.py`
- `web/api/kinesis_test.py`

## Common Issues

- **Port 3000 not accessible on VM**: Use SSH port forwarding: `ssh -L 3000:localhost:3000 user@host`
- **OOM on MacBook**: Set `export PYTORCH_MPS_HIGH_WATERMARK_RATIO=0.0`
- **Peer skips rounds**: Device too slow for swarm pace, it will catch up
- **Viem package issues**: Update in `modal-login/package.json` to `"viem": "2.25.0"`
- **Protobuf warnings**: Can be ignored (yanked version warning is expected)

## Contract Interaction

Smart contract ABIs located in:
- `rgym_exp/contracts/SwarmCoordinator_0.4.2.json`
- `hivemind_exp/contracts/SwarmCoordinator_0.4.2.json`

Main contract functions (via Modal API proxy):
- `register-peer`: Register peer_id on-chain (idempotent)
- `submit-reward`: Submit round/stage rewards
- `get-current-round`: Query active round
- `get-current-stage`: Query active stage

## Contributing

Contributions are managed via private repo with copybara:
- One feature per branch
- Clear commit messages
- Link to relevant issues
- Include logs (not screenshots) for bug reports
