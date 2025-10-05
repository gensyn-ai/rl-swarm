# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Overview

**This is a fork of [Gensyn RL Swarm](https://github.com/gensyn-ai/rl-swarm)** modified to support **Google Drive-only mode** without blockchain, Docker, or authentication requirements.

RL Swarm is a system for decentralized reinforcement learning, powered by the [GenRL](https://github.com/gensyn-ai/genrl) library. This fork enables collaborative model training through Google Drive file-based coordination instead of blockchain and P2P networking.

The current implementation trains models on the [reasoning-gym](https://github.com/open-thought/reasoning-gym) dataset.

## Architecture

### Core Components

This fork is **Google Drive-only**. All blockchain, Hivemind, and Hydra dependencies have been removed.

**Training Infrastructure (`rgym_exp/`)**:
   - `runner/swarm_launcher.py`: **Simple entry point** - reads env vars, directly instantiates components
   - `src/manager.py`: `SwarmGameManager` orchestrates training rounds/stages
   - `src/trainer.py`: `GRPOTrainerModule` implements Group Relative Policy Optimization
   - `src/data.py`: `ReasoningGymDataManager` manages datasets from reasoning-gym
   - `src/gdrive_coordinator.py`: File-based coordinator (replaces blockchain)
   - `src/gdrive_logger.py`: Persistent logging to Google Drive
   - `src/gdrive_rollout_sharing.py`: Core rollout publishing/fetching
   - `communication/gdrive_backend.py`: GenRL-compatible communication backend
   - `utils/experiment_manager.py`: Experiment management utilities

**Colab Notebooks**:
   - `notebooks/colab_coordinator.ipynb`: Coordinator setup for Colab
   - `notebooks/colab_worker.ipynb`: Worker setup for Colab
   - `notebooks/colab_monitoring.ipynb`: Experiment monitoring dashboard

**Configuration**: All configuration via **environment variables only** (no YAML files)

### Removed Components

The following have been **completely removed** from this fork:
   - ❌ **Hydra/OmegaConf**: No config file parsing, direct Python instantiation
   - ❌ **Hivemind**: No P2P networking, uses Google Drive file sharing
   - ❌ **Blockchain**: No smart contracts, Modal login, or Web3
   - ❌ **Docker**: No containers, runs directly on Colab/local Python
   - ❌ **Config files**: No `rg-swarm.yaml` or `colab-gdrive.yaml`
   - ❌ **Contract ABIs**: No `SwarmCoordinator_0.4.2.json`
   - ❌ `modal-login/`: Authentication system
   - ❌ `web/`: FastAPI metrics server
   - ❌ `run_rl_swarm.sh`: Shell launcher

### Key Protocols

**Google Drive Mode:**
- **Communication**: File-based rollout sharing via Google Drive
- **Coordination**: Google Drive state files (JSON)
- **Training**: GRPO (Group Relative Policy Optimization) for policy updates
- **Rollout Sharing**: Configurable frequency (generation/stage/round)
- **Retention**: Configurable cleanup and archiving policies
- **Configuration**: 100% environment variables (no config files)

### Configuration

**All configuration via environment variables:**
- `GDRIVE_PATH`: Path to Google Drive folder
- `EXPERIMENT_NAME`: Unique experiment identifier
- `NODE_ROLE`: 'coordinator' or 'worker'
- `NODE_ID`: Unique node identifier
- `MODEL_NAME`: HuggingFace model ID
- `SEED`: Random seed
- `ROLLOUT_PUBLISH_FREQUENCY`: 'generation', 'stage', or 'round'
- `ROLLOUT_CLEANUP_ENABLED`: Enable/disable old rollout cleanup
- `ROLLOUT_KEEP_LAST_N_ROUNDS`: How many rounds to keep
- `ROLLOUT_ARCHIVE_OLD`: Archive instead of delete

**No Hydra, no YAML files** - all parameters are read directly from environment variables in `swarm_launcher.py`

## Development Commands

### Running the Swarm (Google Drive Mode)

**Google Colab (Recommended):**

See [`README.md`](README.md) for detailed Colab instructions.

Quick summary:
1. Open `notebooks/colab_coordinator.ipynb` in Colab
2. Configure experiment name and model
3. Run all cells
4. (Optional) Add workers with `notebooks/colab_worker.ipynb`

**Local Testing:**

```bash
# Clone repository
git clone https://github.com/Elrashid/rl-swarm
cd rl-swarm

# Install dependencies
pip install -r requirements.txt
pip install gensyn-genrl==0.1.9

# Terminal 1 - Coordinator
export GDRIVE_PATH="/path/to/shared/folder"
export EXPERIMENT_NAME="test_experiment"
export NODE_ROLE="coordinator"
export NODE_ID="coordinator_0"
export MODEL_NAME="Gensyn/Qwen2.5-0.5B-Instruct"
export ROLLOUT_PUBLISH_FREQUENCY="stage"
export ROLLOUT_CLEANUP_ENABLED="False"

python -m rgym_exp.runner.swarm_launcher

# Terminal 2 - Worker (optional)
export GDRIVE_PATH="/path/to/shared/folder"  # SAME
export EXPERIMENT_NAME="test_experiment"      # SAME
export NODE_ROLE="worker"
export NODE_ID="worker_1"                     # DIFFERENT
export MODEL_NAME="Gensyn/Qwen2.5-0.5B-Instruct"
export ROLLOUT_PUBLISH_FREQUENCY="stage"
export ROLLOUT_CLEANUP_ENABLED="False"

python -m rgym_exp.runner.swarm_launcher
```

**Original Docker/Shell Methods (Removed):**
- ~~Docker compose commands~~ (removed, no longer available)
- ~~`run_rl_swarm.sh` script~~ (removed, no longer available)
- ~~Modal login server~~ (removed, no longer available)

## Important Files and Paths

**Google Drive Mode:**
- `/MyDrive/rl-swarm/experiments/{EXPERIMENT_NAME}/`: Experiment root
  - `state/current_state.json`: Current round/stage state
  - `peers/*.json`: Peer registrations
  - `rewards/round_X/stage_Y/*.json`: Reward submissions
  - `rollouts/round_X/stage_Y/*.json`: Rollout sharing files
  - `checkpoints/round_X/*.pt`: Model checkpoints
  - `logs/{NODE_ID}/metrics.jsonl`: Training metrics (JSONL format)
  - `logs/{NODE_ID}/training_events.jsonl`: Event logs
- `/MyDrive/rl-swarm/archives/`: Archived rollouts (if archiving enabled)

**Local Files:**
- `rgym_exp/runner/swarm_launcher.py`: Main entry point (env vars → direct instantiation)
- `rgym_exp/src/gdrive_rollout_sharing.py`: Rollout sharing implementation
- `rgym_exp/communication/gdrive_backend.py`: Communication backend
- `requirements.txt`: Python dependencies
- `GDRIVE_IMPLEMENTATION.md`: Complete Google Drive mode documentation

**Removed Files (No Longer Available):**
- ~~`swarm.pem`: Peer identity~~ (no longer needed)
- ~~`modal-login/temp-data/userData.json`~~ (removed with modal-login)
- ~~`rgym_exp/config/*.yaml`~~: Config files (replaced with env vars)
- ~~`rgym_exp/contracts/*.json`~~: Smart contract ABIs (removed)
- ~~`rgym_exp/src/coordinator.py`~~: Blockchain coordinator (ModalSwarmCoordinator)
- ~~`rgym_exp/src/prg_module.py`~~: Prediction Game module
- ~~`rgym_exp/runner/coordinator_node.py`~~: Legacy Hydra launcher
- ~~`rgym_exp/src/utils/omega_gpu_resolver.py`~~: Hydra/OmegaConf resolver
- ~~`logs/swarm.log`~~ (now in Google Drive)
- ~~`logs/yarn.log`~~ (removed with modal-login)
- ~~`logs/prg_record.txt`~~ (PRG game removed)

## Environment Variables

**Google Drive Mode:**
- `GDRIVE_PATH`: Path to Google Drive base folder (required)
- `EXPERIMENT_NAME`: Unique experiment identifier (required)
- `NODE_ROLE`: 'coordinator' or 'worker' (default: worker)
- `NODE_ID`: Unique node identifier (default: auto-generated UUID)
- `MODEL_NAME`: HuggingFace model (default: Gensyn/Qwen2.5-0.5B-Instruct)
- `SEED`: Random seed (default: 42)
- `ROLLOUT_PUBLISH_FREQUENCY`: 'generation', 'stage', or 'round' (default: stage)
- `ROLLOUT_CLEANUP_ENABLED`: 'True' or 'False' (default: False)
- `ROLLOUT_KEEP_LAST_N_ROUNDS`: Number of rounds to keep (default: 10)
- `ROLLOUT_ARCHIVE_OLD`: 'True' or 'False' (default: False)
- `HUGGINGFACE_ACCESS_TOKEN`: For pushing trained models (optional)
- `WANDB_API_KEY`: Weights & Biases logging (optional)
- `WANDB_PROJECT`: W&B project name (optional)

**Removed Variables (No Longer Used):**
- ~~`IDENTITY_PATH`~~ (no peer identities needed)
- ~~`SWARM_CONTRACT`~~ (no blockchain)
- ~~`PRG_CONTRACT`~~ (no blockchain)
- ~~`CONNECT_TO_TESTNET`~~ (no blockchain)
- ~~`PRG_GAME`~~ (game removed)

## GenRL Integration

This codebase extends GenRL base classes:

**Google Drive Mode:**
- `Communication` → `GDriveCommunicationBackend`: File-based communication
  - `get_id()`: Returns node_id
  - `publish_state()`: Publishes rollouts to Google Drive
  - `get_swarm_states()`: Fetches rollouts from peers
  - `advance_stage()`: Hook for stage advancement
  - `advance_round()`: Hook for round advancement + cleanup

**Common (Both Modes):**
- `BaseGameManager` → `SwarmGameManager`: Orchestrates training
- `GRPOLanguageTrainerModule` → `GRPOTrainerModule`: GRPO training
- `LocalMemoryTextDataManager` → `ReasoningGymDataManager`: Dataset management

Key GenRL concepts:
- **GameState**: Tracks current round/stage
- **WorldState**: Synchronized state across peers (via Google Drive or DHT)
- **RewardManager**: Computes rewards using `RGRewards` (accuracy-based)
- **Communication**: Abstracted via `GDriveCommunicationBackend` or `HivemindBackend`

## Google Drive Mode Details

### Rollout Sharing

The `GDriveRolloutSharing` class handles all file operations:
- **Publish**: Writes rollouts to `/rollouts/round_X/stage_Y/{peer_id}.json`
- **Fetch**: Reads rollouts from other peers in same round/stage
- **Cleanup**: Deletes/archives old rollouts based on retention policy
- **Buffering**: Aggregates rollouts before writing (for stage/round frequencies)

### Communication Backend

The `GDriveCommunicationBackend` implements GenRL's `Communication` interface:
- Compatible with existing GenRL code (drop-in replacement)
- Local caching to reduce Google Drive API calls
- Retry logic with exponential backoff for API rate limits
- Hooks for stage/round advancement

### File Format

Rollout files are JSON:
```json
{
  "peer_id": "coordinator_0",
  "round": 5,
  "stage": 0,
  "timestamp": 1696800000.0,
  "rollouts": {
    "0": [{"prompt": "...", "response": "...", "reward": 0.85}],
    "1": [...]
  }
}
```

### Performance

- **API Calls**: ~16 per stage (4 nodes, frequency='stage')
- **Latency**: +1-2 seconds per stage vs Hivemind
- **Storage**: ~8 MB per 100 rounds (4 nodes, 2 stages/round)
- **Caching**: Reduces redundant API reads by ~60%

## Identity Management

**Google Drive Mode (Current):**
- **No peer identities needed** - nodes identified by `NODE_ID` config
- **No authentication** - just Google Drive access
- **Multi-node setup**: Use different `NODE_ID` for each node
- **Simple**: Just configure `NODE_ID` environment variable

**Original Mode (Removed):**
- ~~`swarm.pem` RSA keys~~ (no longer used)
- ~~Email-based authentication~~ (removed)
- ~~Alchemy Modal wallets~~ (removed)

## Testing

**Google Drive Mode Testing:**

See `GDRIVE_IMPLEMENTATION.md` for complete testing guide.

Quick tests:
1. Single node: Run coordinator only, verify rollout files created
2. Multi-node: Run coordinator + worker, verify rollout sharing
3. Retention: Enable cleanup, verify old rollouts deleted/archived
4. Resume: Stop and restart, verify checkpoint loading works

**Legacy Tests (Removed):**
- ~~`web/api/dht_pub_test.py`~~ (removed with web/)
- ~~`web/api/kinesis_test.py`~~ (removed with web/)

## Common Issues

**Google Drive Mode:**
- **No rollout files created**: Check `GDRIVE_PATH` and experiment name match
- **Rate limit errors**: Reduce publish frequency to 'round', enable caching
- **Out of storage**: Enable cleanup with `cleanup_enabled: true`
- **Worker can't find coordinator**: Verify `EXPERIMENT_NAME` matches exactly
- **Slow training**: Enable caching, reduce `fetch_max_peers`

**General:**
- **OOM on MacBook**: Set `export PYTORCH_MPS_HIGH_WATERMARK_RATIO=0.0`
- **Peer skips rounds**: Device too slow for swarm pace (normal behavior)
- **Protobuf warnings**: Can be ignored (expected)

**Removed Issues (No Longer Applicable):**
- ~~Port 3000 not accessible~~ (modal-login removed)
- ~~Viem package issues~~ (modal-login removed)
- ~~Blockchain connection issues~~ (blockchain removed)

## Documentation

**Primary Documentation:**
- `README.md`: Quick start guide for Google Drive mode
- `GDRIVE_IMPLEMENTATION.md`: Complete technical documentation
- `CLAUDE.md`: This file - architecture and development guide

**Working Examples:**
- `notebooks/colab_coordinator.ipynb`: Working Colab example for coordinator
- `notebooks/colab_worker.ipynb`: Working Colab example for worker
- `notebooks/colab_monitoring.ipynb`: Working Colab example for monitoring
- `rgym_exp/runner/swarm_launcher.py`: Simple entry point showing all components

**Removed Documentation:**
- ~~`CONTRIBUTING.md`~~ (removed)
- ~~`technical_report.pdf`~~ (removed)
- ~~Contract interaction guides~~ (blockchain removed)
- ~~Config file documentation~~ (no config files)

## Contributing

This is a fork of the original Gensyn RL Swarm project. Contributions should:
- Focus on Google Drive-only mode improvements
- Maintain simplicity (no config frameworks, direct Python)
- Include clear documentation
- Test on Google Colab
- Follow existing code style
- Update GDRIVE_IMPLEMENTATION.md for significant changes

For issues or feature requests, use GitHub issues:
https://github.com/Elrashid/rl-swarm/issues

## Migration from Original

If you have code using the original blockchain mode:

1. **Remove Hydra**: No config files, use environment variables
2. **Remove authentication**: No modal-login needed
3. **Remove Docker**: Run directly in Colab or locally
4. **Replace coordinator**: Use `GDriveSwarmCoordinator` instead of blockchain
4. **Remove peer identities**: Use `NODE_ID` environment variable
5. **Update communication**: Uses `GDriveCommunicationBackend` automatically

See `GDRIVE_IMPLEMENTATION.md` for complete migration guide.

---

# important-instruction-reminders

Do what has been asked; nothing more, nothing less.
NEVER create files unless they're absolutely necessary for achieving your goal.
ALWAYS prefer editing an existing file to creating a new one.
NEVER proactively create documentation files (*.md) or README files. Only create documentation files if explicitly requested by the User.
