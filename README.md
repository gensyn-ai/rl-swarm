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

**Added:**
- ✅ Google Drive-based rollout sharing
- ✅ Configurable publish frequency (generation/stage/round)
- ✅ Configurable retention policies
- ✅ Automatic cleanup/archiving
- ✅ Local caching for performance
- ✅ Simplified Colab notebooks

### Quick Start on Google Colab

#### 1. Open Coordinator Notebook

**[Open Coordinator Notebook](https://colab.research.google.com/github/Elrashid/rl-swarm/blob/main/notebooks/colab_coordinator.ipynb)**

Or manually:
1. Go to [Google Colab](https://colab.research.google.com/)
2. File > Open notebook > GitHub tab
3. Enter: `Elrashid/rl-swarm`
4. Select: `notebooks/colab_coordinator.ipynb`

#### 2. Configure Your Experiment

```python
# In the first cell of colab_coordinator.ipynb
EXPERIMENT_NAME = 'my_experiment'  # Choose a unique name
NODE_ID = 'coordinator_0'
MODEL_NAME = 'Gensyn/Qwen2.5-0.5B-Instruct'
SEED = 42

# Rollout Configuration
ROLLOUT_PUBLISH_FREQUENCY = 'stage'  # 'generation', 'stage', or 'round'
ROLLOUT_CLEANUP_ENABLED = False      # Set True to enable cleanup
```

#### 3. Run All Cells

Click **Runtime > Run all** and wait for training to start.

### Add Worker Nodes (Optional)

**[Open Worker Notebook](https://colab.research.google.com/github/Elrashid/rl-swarm/blob/main/notebooks/colab_worker.ipynb)**

Configure with **same EXPERIMENT_NAME** but unique NODE_ID:

```python
EXPERIMENT_NAME = 'my_experiment'  # MUST MATCH coordinator
NODE_ID = 'worker_1'               # MUST BE UNIQUE
MODEL_NAME = 'Gensyn/Qwen2.5-0.5B-Instruct'
SEED = 42
```

Run all cells. Repeat for additional workers (worker_2, worker_3, etc.)

### Google Drive Structure

Your experiment data will be organized in Google Drive:

```
/MyDrive/rl-swarm/
├── experiments/
│   └── my_experiment/
│       ├── state/current_state.json           # Current round/stage
│       ├── peers/*.json                       # Peer registrations
│       ├── rollouts/round_X/stage_Y/*.json    # Rollout sharing
│       ├── checkpoints/round_X/*.pt           # Model checkpoints
│       └── logs/{node_id}/
│           ├── metrics.jsonl                  # Training metrics
│           └── training_events.jsonl          # Events
└── archives/                                  # Archived rollouts
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

### Google Drive Mode Issues

#### No rollout files created
- Check `GDRIVE_PATH` is correct
- Verify `EXPERIMENT_NAME` matches across all nodes
- Check permissions on Google Drive directory
- Look for errors in logs

#### Worker can't find coordinator rollouts
- Ensure `EXPERIMENT_NAME` is identical
- Check rollout files exist: `/rollouts/round_X/stage_Y/coordinator_*.json`
- Verify no typos in experiment name
- Check Google Drive sync status

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
    - If you're using a consumer device (e.g. a MacBook), it is likely just running slowly - check back in 20 minutes.

- **OOM errors on MacBook?**
    - Try this (experimental) fix to increase memory:
        ```
        export PYTORCH_MPS_HIGH_WATERMARK_RATIO=0.0
        ```

- **I want to use a bigger and/or different model, can I do that?**: Yes - just change the `MODEL_NAME` configuration variable to any HuggingFace model.

- **I am running a model on my CPU and training seems frozen**: Wait longer than a single training iteration has previously taken. If actually frozen, try:
    - Set: `export PYTORCH_MPS_HIGH_WATERMARK_RATIO=0.0`

For more troubleshooting, see [`GDRIVE_IMPLEMENTATION.md`](GDRIVE_IMPLEMENTATION.md).
