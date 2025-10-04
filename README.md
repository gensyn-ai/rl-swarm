# RL Swarm

> **Note:** This is a fork of the original [Gensyn RL Swarm](https://github.com/gensyn-ai/rl-swarm) project, modified to support **Google Drive-only mode** for simpler deployment on Google Colab without blockchain or Docker requirements.

---

## 🆕 Google Drive-Only Mode (Recommended)

**NEW**: Run RL Swarm on Google Colab without blockchain, Docker, or authentication!

This fork adds a **Google Drive-only mode** that uses Google Drive for all coordination instead of blockchain and P2P networking, making it perfect for:
- Testing and experimentation
- Running on free Google Colab GPUs
- Multi-node training without infrastructure setup
- Checkpoint persistence across Colab sessions
- Privacy (all data stays in your Google Drive)

### ✨ What's Different in This Fork

**Removed:**
- ❌ Blockchain coordination
- ❌ Modal login authentication
- ❌ Docker containers
- ❌ P2P networking (Hivemind DHT)
- ❌ Peer identity files (swarm.pem)
- ❌ Web server/API
- ❌ Configuration frameworks (Hydra/OmegaConf)
- ❌ Config files (all config via environment variables)

**Added:**
- ✅ Google Drive-based rollout sharing
- ✅ Configurable publish frequency (generation/stage/round)
- ✅ Configurable retention policies
- ✅ Automatic cleanup/archiving
- ✅ Local caching for performance
- ✅ Simplified Colab notebooks

### Quick Start on Google Colab (Recommended)

#### Option A: Single-Node Training (Easiest)

Perfect for testing and learning. Runs one training node on a free Colab GPU.

1. **Open the Coordinator Notebook**

   Click here: **[Open Coordinator Notebook](https://colab.research.google.com/github/Elrashid/rl-swarm/blob/main/notebooks/colab_coordinator.ipynb)**

   Or manually:
   - Go to [Google Colab](https://colab.research.google.com/)
   - File > Open notebook > GitHub tab
   - Enter: `Elrashid/rl-swarm`
   - Select: `notebooks/colab_coordinator.ipynb`

2. **Configure Your Experiment**

   In Cell 2, set your configuration:
   ```python
   # Experiment Configuration
   EXPERIMENT_NAME = 'my_first_experiment'  # Choose any unique name
   NODE_ID = 'coordinator_0'                 # Keep as-is for single node
   MODEL_NAME = 'Gensyn/Qwen2.5-0.5B-Instruct'
   SEED = 42

   # Rollout Configuration (optional, defaults work fine)
   ROLLOUT_PUBLISH_FREQUENCY = 'stage'      # How often to save rollouts
   ROLLOUT_CLEANUP_ENABLED = False          # Keep all rollouts
   ```

3. **Run the Notebook**

   Click **Runtime > Run all** (or Ctrl+F9)

   The notebook will:
   - ✓ Mount your Google Drive (requires permission)
   - ✓ Install dependencies (~3-5 minutes)
   - ✓ Initialize the experiment in `/MyDrive/rl-swarm/`
   - ✓ Start training

   You'll see training progress in the output. Training runs until you stop it or reach max rounds.

4. **Monitor Progress**

   While training, you can run Cell 17 (Monitor Progress) to see:
   - Current round/stage
   - Number of active peers
   - Recent rewards

#### Option B: Multi-Node Training (Advanced)

Run multiple nodes to simulate swarm training. Each node learns from the others.

**Prerequisites:**
- Complete Option A (coordinator running)
- Multiple browser tabs or Google accounts

**Steps:**

1. **Keep Coordinator Running**

   From Option A above, keep the coordinator notebook running in one tab.

2. **Open Worker Notebook**

   In a **new tab/window**: **[Open Worker Notebook](https://colab.research.google.com/github/Elrashid/rl-swarm/blob/main/notebooks/colab_worker.ipynb)**

3. **Configure Worker**

   In Cell 2, use **SAME experiment name** but **DIFFERENT node ID**:
   ```python
   EXPERIMENT_NAME = 'my_first_experiment'  # MUST MATCH coordinator
   NODE_ID = 'worker_1'                     # MUST BE UNIQUE
   MODEL_NAME = 'Gensyn/Qwen2.5-0.5B-Instruct'  # Same model
   SEED = 42                                # Same seed
   ```

4. **Run Worker Notebook**

   Click **Runtime > Run all**

   The worker will:
   - ✓ Mount Google Drive (same account as coordinator)
   - ✓ Verify experiment exists
   - ✓ Install dependencies
   - ✓ Join the experiment and start training

5. **Add More Workers (Optional)**

   Repeat steps 2-4 with different `NODE_ID`:
   - Worker 2: `NODE_ID = 'worker_2'`
   - Worker 3: `NODE_ID = 'worker_3'`
   - etc.

   Each worker will share rollouts with all other nodes!

### Local Testing (Advanced)

For development and testing without Colab:

```bash
# Clone repository
git clone https://github.com/Elrashid/rl-swarm
cd rl-swarm

# Install dependencies
pip install -r requirements.txt
pip install gensyn-genrl==0.1.9

# Terminal 1 - Start Coordinator
export GDRIVE_PATH="/path/to/shared/folder"
export EXPERIMENT_NAME="test_experiment"
export NODE_ROLE="coordinator"
export NODE_ID="coordinator_0"
export MODEL_NAME="Gensyn/Qwen2.5-0.5B-Instruct"
export ROLLOUT_PUBLISH_FREQUENCY="stage"
export ROLLOUT_CLEANUP_ENABLED="False"

python -m rgym_exp.runner.swarm_launcher

# Terminal 2 - Start Worker (optional)
export GDRIVE_PATH="/path/to/shared/folder"  # SAME path
export EXPERIMENT_NAME="test_experiment"      # SAME name
export NODE_ROLE="worker"
export NODE_ID="worker_1"                     # DIFFERENT ID
export MODEL_NAME="Gensyn/Qwen2.5-0.5B-Instruct"
export ROLLOUT_PUBLISH_FREQUENCY="stage"
export ROLLOUT_CLEANUP_ENABLED="False"

python -m rgym_exp.runner.swarm_launcher
```

**Note:** Use a shared folder (network drive, Dropbox, etc.) for `GDRIVE_PATH` to test multi-node locally.

### Google Drive Structure

Your experiment data will be organized in Google Drive:

```
/MyDrive/rl-swarm/
├── experiments/
│   └── my_experiment/
│       ├── state/current_state.json           # Current round/stage
│       ├── peers/*.json                       # Peer registrations
│       ├── rewards/round_X/stage_Y/*.json     # Reward submissions
│       ├── winners/round_X/*.json             # Winner votes
│       ├── rollouts/round_X/stage_Y/*.json    # Rollout sharing
│       ├── checkpoints/round_X/*.pt           # Model checkpoints
│       └── logs/{node_id}/
│           ├── metrics.jsonl                  # Training metrics
│           └── training_events.jsonl          # Events
└── archives/                                  # Archived rollouts (optional)
    └── my_experiment/rollouts/
```

### Features

- ✅ **No blockchain** - Uses Google Drive for coordination
- ✅ **No Docker** - Runs directly in Colab
- ✅ **No authentication** - Just mount Google Drive
- ✅ **No peer identities** - Simple NODE_ID configuration
- ✅ **Resumable** - Checkpoints saved automatically
- ✅ **Multi-experiment** - Run different experiments simultaneously
- ✅ **Full logging** - All metrics in Google Drive
- ✅ **Configurable retention** - Control storage usage

### Configuration Options

#### Publish Frequency

Controls when rollouts are shared:

```yaml
rollout_publish_frequency: 'stage'  # Options: generation, stage, round
```

- `generation`: Most frequent, highest API usage
- `stage`: **Recommended** - balanced
- `round`: Least frequent, lowest API usage

#### Retention Policy

Controls how long to keep rollouts:

```yaml
rollout_retention:
  cleanup_enabled: false           # Enable cleanup
  keep_last_n_rounds: 10          # Keep last N rounds
  archive_old_rollouts: false     # Archive instead of delete
```

### Documentation

- **Complete Guide**: [`GDRIVE_IMPLEMENTATION.md`](GDRIVE_IMPLEMENTATION.md) - Full documentation with architecture, configuration, testing, and troubleshooting
- **Architecture**: [`CLAUDE.md`](CLAUDE.md) - Codebase structure and technical details

---

## Original RL Swarm (Blockchain Mode)

The sections below describe the original RL Swarm implementation with blockchain coordination. **This fork focuses on Google Drive-only mode**, but the original mode is still available for reference.

---

RL Swarm is a peer-to-peer system for reinforcement learning. It allows you to train models collaboratively with others in the swarm, leveraging their collective intelligence. It is open source and permissionless, meaning you can run it on a consumer laptop at home or on a powerful GPU in the cloud. You can also connect your model to the Gensyn Testnet to receive an on-chain identity that tracks your progress over time.

Currently, we are running the [reasoning-gym](https://github.com/open-thought/reasoning-gym/tree/main) swarm on the Testnet. This swarm is designed to train models to solve a diverse set of reasoning tasks using the reasoning-gym dataset. The current list of default models includes:

Models:
   - Gensyn/Qwen2.5-0.5B-Instruct
   - Qwen/Qwen3-0.6B
   - nvidia/AceInstruct-1.5B
   - dnotitia/Smoothie-Qwen3-1.7B
   - Gensyn/Qwen2.5-1.5B-Instruct

This iteration of rl-swarm is powered by the [GenRL](https://github.com/gensyn-ai/genrl) library. It is a fully composable framework for decentralized reinforcement learning which enables users to create and customize their own swarms for reinforcement learning with multi-agent multi-stage environments.

## Requirements

Your hardware requirements will vary depending on a number of factors including model size and the accelerator platform you use. Users running a large NVIDIA GPU will be assigned a model from the large model pool, while users running less powerful hardware will be assigned a model from the small model pool. This design decision is intended to allow users to advance at a similar rate regardless of the hardware they use, maximizing their utility to the swarm.

**Supported Hardware**

- arm64 or x86 CPU with a minimum of 32GB RAM (note that if you run other applications during training it might crash the training).

OR

- CUDA devices (officially supported):
    - RTX 3090
    - RTX 4090
    - RTX 5090
    - A100
    - H100

With either configuration, you will need Python >=3.10 (for Mac, you will likely need to upgrade).

## ⚠️ Please read before continuing ⚠️

This software is **experimental** and provided as-is for users who are interested in using (or helping to develop) an early version of the Gensyn Protocol for training models.

If you encounter issues, please first check [Troubleshooting](#troubleshooting). If you cannot find a solution there, please check if there is an open (or closed) [Issue](../../issues). If there is no relevant issue, please file one and include 1) all relevant logs, 2) information about your device (e.g. which GPU, if relevant), and 3) your operating system information.

## Monitor Progress

Add a monitoring cell to any notebook:

```python
from rgym_exp.utils.experiment_manager import get_experiment_status

status = get_experiment_status(
    '/content/drive/MyDrive/rl-swarm',
    'my_experiment'
)

print(f"Round: {status['current_round']}")
print(f"Active Peers: {status['num_active_peers']}")
```

### Analyze Results

Aggregate and visualize metrics across all nodes:

```python
from rgym_exp.utils.experiment_manager import get_experiment_metrics
import matplotlib.pyplot as plt

# Load metrics
df = get_experiment_metrics(
    '/content/drive/MyDrive/rl-swarm',
    'my_experiment'
)

# Plot average reward per round
df.groupby('round')['my_reward'].mean().plot(
    title='Average Reward per Round'
)
plt.xlabel('Round')
plt.ylabel('Reward')
plt.show()

# Compare performance across nodes
df.groupby('node_id')['my_reward'].mean().plot(
    kind='bar',
    title='Average Reward by Node'
)
plt.show()
```

## Troubleshooting

### Common Colab Issues

#### "Current Round: 0, Active Peers: 0" - Training not starting

**Symptoms:** All cells run successfully, folders created, but training never starts.

**Cause:** The training cell is missing or didn't run.

**Solution:**
1. Make sure you're using the **latest notebooks** from GitHub
2. **Coordinator**: Run cell 15 "Start Training & Coordination"
3. **Worker**: Run cell 14 "Start Training"
4. Wait 2-5 minutes for model download on first run
5. Check cell output for error messages

**Verify training started:**
```python
import os
exp_path = "/content/drive/MyDrive/rl-swarm/experiments/YOUR_EXPERIMENT_NAME"
print("Peers:", os.listdir(f"{exp_path}/peers") if os.path.exists(f"{exp_path}/peers") else "None")
print("Logs:", os.listdir(f"{exp_path}/logs") if os.path.exists(f"{exp_path}/logs") else "None")
```

#### "requirements.txt not found" during install

**Cause:** Repository clone failed or directory is corrupted.

**Solution:**
1. The notebook now **automatically removes old directory** before cloning
2. If error persists, manually run:
   ```python
   !rm -rf /content/rl-swarm
   !git clone https://github.com/Elrashid/rl-swarm.git /content/rl-swarm
   %cd /content/rl-swarm
   ```

#### "KeyError: 'active_peers'" in monitor cell

**Cause:** Old version of notebook trying to access missing dict keys.

**Solution:**
- Use the latest notebooks from GitHub (updated to use `.get()` method)
- Or manually change `status['active_peers']` to `status.get('active_peers', 0)`

#### Model download taking forever

**Normal:** First run downloads ~500MB model (2-5 minutes on Colab)

**If stuck >10 minutes:**
1. Check Colab GPU allocation (Runtime > Change runtime type)
2. Restart runtime and try again
3. Try a smaller model: `MODEL_NAME = 'Qwen/Qwen3-0.6B'`

#### Worker can't find coordinator

**Checklist:**
- [ ] `EXPERIMENT_NAME` **exactly** matches coordinator (check for typos, spaces)
- [ ] Coordinator notebook is **still running** (didn't disconnect)
- [ ] Coordinator reached cell 15 (training cell)
- [ ] Using **same Google Drive account**

**Verify coordinator is running:**
```python
import os
exp_path = "/content/drive/MyDrive/rl-swarm/experiments/YOUR_EXPERIMENT_NAME"
state_file = f"{exp_path}/state/current_state.json"

if os.path.exists(state_file):
    import json
    with open(state_file) as f:
        state = json.load(f)
    print(f"Coordinator status: Round {state['round']}, Stage {state['stage']}")
else:
    print("❌ Coordinator not initialized!")
```

### Google Drive Mode Issues

#### No rollout files created
- Check `GDRIVE_PATH` is correct
- Verify `EXPERIMENT_NAME` matches across all nodes
- Training must actually start (check cell 15 output)
- Check permissions on Google Drive directory

#### Rate limit errors
- Reduce publish frequency: `'stage'` → `'round'`
- Enable caching: `cache_rollouts: true`
- Reduce number of peers: `fetch_max_peers: 5`
- Increase timeout: `fetch_timeout_seconds: 60`

#### Out of storage
- Enable cleanup: `cleanup_enabled: true`
- Reduce retention: `keep_last_n_rounds: 5`
- Enable archiving to external location
- Manually delete old experiments

### General Issues

- **How do I find my logs?**
    - Google Drive mode: Check `/MyDrive/rl-swarm/experiments/{EXPERIMENT_NAME}/logs/{NODE_ID}/`
    - Files: `metrics.jsonl`, `training_events.jsonl`

- **My peer 'skipped a round'**: This occurs when your device isn't fast enough to keep up with the pace of the swarm. This is normal behavior.

- **My model doesn't seem to be training?**
    - First run takes 2-5 minutes for model download
    - Check training cell output for progress
    - Consumer devices (MacBook) are slow - wait 20 minutes

- **OOM errors on MacBook?**
    - Try this (experimental) fix to increase memory:
        ```
        export PYTORCH_MPS_HIGH_WATERMARK_RATIO=0.0
        ```

- **I want to use a bigger and/or different model**: Change `MODEL_NAME` to any HuggingFace model ID

For more troubleshooting, see [`GDRIVE_IMPLEMENTATION.md`](GDRIVE_IMPLEMENTATION.md).
