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
- ✅ Simplified Colab notebooks with live output streaming
- ✅ Comprehensive monitoring dashboard

### Quick Start on Google Colab (Recommended)

#### Option A: Single-Node Training (Easiest)

Perfect for testing and learning. Runs one training node on a free Colab GPU.

1. **Open the Coordinator Notebook**

   Click here: **[Open Coordinator Notebook](https://colab.research.google.com/github/Elrashid/rl-swarm/blob/main/notebooks/EX12.00.RL_Swarm_Coordinator.ipynb)**

   Or manually:
   - Go to [Google Colab](https://colab.research.google.com/)
   - File > Open notebook > GitHub tab
   - Enter: `Elrashid/rl-swarm`
   - Select: `notebooks/EX12.00.RL_Swarm_Coordinator.ipynb`

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
   - ✓ Start training with **live output streaming**

   You'll see training logs appear in **real-time** as training progresses. Training runs until you stop it (press ■ stop button) or reach max rounds.

4. **Monitor Progress** (Optional)

   While training is running, open a **new browser tab** and use the monitoring notebook:

   **[🔗 Open Monitoring Notebook](https://colab.research.google.com/github/Elrashid/rl-swarm/blob/main/notebooks/EX12.02.RL_Swarm_Monitoring.ipynb)**

   Quick monitoring steps:
   - Mount Google Drive (same account)
   - Set `EXPERIMENT_NAME = 'my_first_experiment'` (match your experiment)
   - Run all cells to see charts and metrics

   Or use Cell 17 in the coordinator notebook for quick status:
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

   In a **new tab/window**: **[Open Worker Notebook](https://colab.research.google.com/github/Elrashid/rl-swarm/blob/main/notebooks/EX12.01.RL_Swarm_Worker.ipynb)**

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
   - ✓ Join the experiment and start training with **live output**

5. **Add More Workers (Optional)**

   Repeat steps 2-4 with different `NODE_ID`:
   - Worker 2: `NODE_ID = 'worker_2'`
   - Worker 3: `NODE_ID = 'worker_3'`
   - etc.

   Each worker will share rollouts with all other nodes!

6. **Monitor Multi-Node Training**

   Use the monitoring notebook to see all nodes working together:

   **[🔗 Open Monitoring Notebook](https://colab.research.google.com/github/Elrashid/rl-swarm/blob/main/notebooks/EX12.02.RL_Swarm_Monitoring.ipynb)**

   The dashboard will show:
   - All registered peers (coordinator + workers)
   - Reward comparison across nodes
   - Per-node training metrics
   - Rollout sharing activity

   **Tip:** Keep the monitoring notebook open in a separate tab for real-time updates!

### 🧪 SAPO Paper Replication (Research)

Want to replicate the **SAPO (Swarm sAmpling Policy Optimization)** paper results? This fork includes complete experiment notebooks that reproduce the paper's findings on swarm collaboration benefits.

**Paper Reference:** [arXiv:2509.08721](https://arxiv.org/abs/2509.08721) - SAPO: Decentralized RL with decoded rollout sharing

**What is SAPO?**
- Novel algorithm combining GRPO (policy optimization) with swarm experience sharing
- Nodes share decoded rollouts (text completions), not gradients
- Configurable I/J split: I local rollouts + J external (swarm) rollouts per round
- Paper shows +94% improvement with optimal 50/50 local/external balance

#### Available Experiment Notebooks

We provide multiple notebooks for different use cases:

| Notebook | Config | I / J | Model | Nodes/GPU | Why This Notebook? |
|----------|--------|-------|-------|-----------|-------------------|
| **[EX12.10](https://colab.research.google.com/github/Elrashid/rl-swarm/blob/main/notebooks/EX12.10.SAPO_Experiment_8loc0ext.ipynb)** | Baseline | 8 / 0 | Qwen2.5 | 1 node/session | **Original approach**: Run 1 node per Colab session. Need 8 sessions for full swarm (~$400) |
| **[EX12.11](https://colab.research.google.com/github/Elrashid/rl-swarm/blob/main/notebooks/EX12.11.SAPO_Experiment_6loc2ext.ipynb)** | Config 1 | 6 / 2 | Qwen2.5 | 1 node/session | **Original approach**: Run 1 node per Colab session. Need 8 sessions for full swarm (~$400) |
| **[EX12.12](https://colab.research.google.com/github/Elrashid/rl-swarm/blob/main/notebooks/EX12.12.SAPO_Experiment_4loc4ext.ipynb)** | Config 2 ⭐ | 4 / 4 | Qwen2.5 | 1 node/session | **Original approach**: Run 1 node per Colab session. Need 8 sessions for full swarm (~$400) |
| **[EX12.13](https://colab.research.google.com/github/Elrashid/rl-swarm/blob/main/notebooks/EX12.13.SAPO_Experiment_2loc6ext.ipynb)** | Config 3 | 2 / 6 | Qwen2.5 | 1 node/session | **Original approach**: Run 1 node per Colab session. Need 8 sessions for full swarm (~$400) |
| **[EX12.14](https://colab.research.google.com/github/Elrashid/rl-swarm/blob/main/notebooks/EX12.14.SAPO_8Node_SingleGPU_gpt2.ipynb)** | Template | Custom | GPT-2 | **8 nodes/1 GPU** | **For experimentation**: Manually set I/J values to test custom configurations |
| **[EX12.14a](https://colab.research.google.com/github/Elrashid/rl-swarm/blob/main/notebooks/EX12.14a.SAPO_gpt2_Baseline_8loc0ext.ipynb)** 🆕 | Baseline | 4 / 0 | GPT-2 | **5 nodes/1 GPU** | **Recommended**: Pre-configured baseline. Just click & run! (~$50) |
| **[EX12.14b](https://colab.research.google.com/github/Elrashid/rl-swarm/blob/main/notebooks/EX12.14b.SAPO_gpt2_Config1_6loc2ext.ipynb)** 🆕 | Config 1 | 3 / 1 | GPT-2 | **5 nodes/1 GPU** | **Recommended**: Pre-configured Config 1. Just click & run! (~$50) |
| **[EX12.14c](https://colab.research.google.com/github/Elrashid/rl-swarm/blob/main/notebooks/EX12.14c.SAPO_gpt2_Config2_4loc4ext.ipynb)** 🆕⭐ | Config 2 | 2 / 2 | GPT-2 | **5 nodes/1 GPU** | **Recommended BEST**: Pre-configured optimal config. Just click & run! (~$50) |
| **[EX12.14d](https://colab.research.google.com/github/Elrashid/rl-swarm/blob/main/notebooks/EX12.14d.SAPO_gpt2_Config3_2loc6ext.ipynb)** 🆕 | Config 3 | 1 / 3 | GPT-2 | **5 nodes/1 GPU** | **Recommended**: Pre-configured Config 3. Just click & run! (~$50) |
| **[TEST_MODE](https://colab.research.google.com/github/Elrashid/rl-swarm/blob/main/notebooks/TEST_MODE.ipynb)** 🧪 | Test | 4 / 0 | GPT-2 | **5 nodes/1 GPU** | **Quick validation**: 1-2 min test run to verify setup before full training |
| **[EX12.20](https://colab.research.google.com/github/Elrashid/rl-swarm/blob/main/notebooks/EX12.20.SAPO_Results_Analysis.ipynb)** | Analysis | - | - | - | **Post-training**: Load and compare results from all experiments |

**Key Differences:**
- **EX12.10-13**: Original single-node approach (expensive - needs 8 Colab Pro+ sessions = ~$400/month)
- **EX12.14**: Template for custom I/J values (manual configuration required)
- **EX12.14a-d**: ⭐ **Recommended** - Pre-configured for each config, just click and run (only ~$50/month for Colab Pro+)
- **TEST_MODE**: 🧪 Quick validation run (1-2 minutes) to verify coordinator, rollouts, and logs before full training
- **EX12.20**: Analysis notebook to visualize and compare results

#### 🆕 NEW: Full Swarm on Single GPU (Recommended for Colab Pro+)

**The most cost-effective way to run the complete SAPO swarm!**

Instead of running 8 separate Colab sessions (8× $50/month = $400), you can now run **5 nodes** (1 coordinator + 4 training workers) on a single A100 80GB GPU using GPT-2.

**Pre-configured notebooks (just click and run!):**
- **[EX12.14a - Baseline (4/0)](https://colab.research.google.com/github/Elrashid/rl-swarm/blob/main/notebooks/EX12.14a.SAPO_gpt2_Baseline_4loc0ext.ipynb)** - No swarm sharing
- **[EX12.14b - Config 1 (3/1)](https://colab.research.google.com/github/Elrashid/rl-swarm/blob/main/notebooks/EX12.14b.SAPO_gpt2_Config1_3loc1ext.ipynb)** - Light collaboration (25%)
- **[EX12.14c - Config 2 (2/2)](https://colab.research.google.com/github/Elrashid/rl-swarm/blob/main/notebooks/EX12.14c.SAPO_gpt2_Config2_2loc2ext.ipynb)** ⭐ - **BEST** (50%)
- **[EX12.14d - Config 3 (1/3)](https://colab.research.google.com/github/Elrashid/rl-swarm/blob/main/notebooks/EX12.14d.SAPO_gpt2_Config3_1loc3ext.ipynb)** - Heavy collaboration (75%)
- **[TEST_MODE](https://colab.research.google.com/github/Elrashid/rl-swarm/blob/main/notebooks/TEST_MODE.ipynb)** 🧪 - Quick validation (1-2 min) before full training

Or use the **[template notebook (EX12.14)](https://colab.research.google.com/github/Elrashid/rl-swarm/blob/main/notebooks/EX12.14.SAPO_8Node_SingleGPU_gpt2.ipynb)** to manually configure parameters.

**Why this works:**
- **GPT-2 (124M params)** uses ~8-10 GB per training node during backprop
- **4 training nodes + 1 coordinator** = **~33 GB peak** (safe on A100 80GB)
- **Coordinator doesn't train** - only manages state, saves GPU memory
- Paper's finding: **Weaker models benefit MORE from swarm** (Section 5.2)
- Expected: **>94% improvement** (vs paper's 94% with Qwen2.5-0.5B)

**Requirements:**
- Google Colab Pro+ ($50/month) for A100 80GB access
- Or rent A100 80GB from Lambda Labs ($1.29/hour × 96 hours = $124 total)

**Setup:**
1. **First run TEST_MODE** to verify everything works (~1-2 min)
2. Open one of the experiment notebooks above
3. Select Runtime > Change runtime type > **A100 GPU**
4. Verify GPU: Cell 3 should show "NVIDIA A100-SXM4-80GB"
5. Run all cells - training takes ~21 hours per experiment

**Cost comparison:**
- Original (8× Qwen2.5 nodes, 8 GPUs): ~$400-500
- This approach (5× GPT-2 nodes, 1 GPU): **$50** (90% savings!)

**Scientific justification:**
This isn't just a cost compromise—it's a valid research extension testing the paper's hypothesis that weaker models show stronger swarm effects. See `EXPERIMENTAL_DESIGN_JUSTIFICATION.md` for full rationale.

**Expected results with GPT-2:**

| Config | Paper (Qwen2.5) | Expected (GPT-2) | Improvement |
|--------|-----------------|------------------|-------------|
| Baseline (8/0) | 562 | 200-300 | — |
| Config 2 (4/4) | 1093 (+94%) | 500-700 | **+110-150%** ✅ |

See `GPU_MEMORY_GUIDE.md` for detailed setup instructions and troubleshooting.

#### Quick Start: Run Baseline Experiment

**[🔗 Open Baseline Notebook](https://colab.research.google.com/github/Elrashid/rl-swarm/blob/main/notebooks/EX12.10.SAPO_Experiment_8loc0ext.ipynb)**

1. Click link above to open in Colab
2. Run all cells (this will train for 2000 rounds)
3. Expected result: ~562 cumulative reward (baseline)
4. Training time: ~24-48 hours on free Colab GPU

#### Run Collaborative Experiments (Recommended)

For best results, run **Config 2 (4/4)** with multiple nodes:

**[🔗 Open Config 2 Notebook](https://colab.research.google.com/github/Elrashid/rl-swarm/blob/main/notebooks/EX12.12.SAPO_Experiment_4loc4ext.ipynb)**

**Setup (8 nodes recommended):**

1. **First Tab - Coordinator:**
   - Open Config 2 notebook
   - Keep `NODE_ROLE = 'coordinator'`
   - Set `NODE_ID = 'node_0'`
   - Run all cells

2. **Additional Tabs - Workers (7 more):**
   - Open same Config 2 notebook in new tabs
   - Change `NODE_ROLE = 'worker'`
   - Use unique IDs: `node_1`, `node_2`, ..., `node_7`
   - Use **SAME** `EXPERIMENT_NAME` across all nodes
   - Run all cells

3. **Monitor Progress:**
   - Open [Monitoring Notebook](https://colab.research.google.com/github/Elrashid/rl-swarm/blob/main/notebooks/EX12.02.RL_Swarm_Monitoring.ipynb)
   - Set `EXPERIMENT_NAME = 'sapo_config2_4loc4ext'`
   - Watch all 8 nodes training together!

**Expected Results (after 2000 rounds):**
- Cumulative reward: ~1093
- **+94% improvement** over baseline (562)
- **Best configuration** from the paper

#### Analyze All Results

After running multiple configurations, compare them:

**[🔗 Open Analysis Notebook](https://colab.research.google.com/github/Elrashid/rl-swarm/blob/main/notebooks/EX12.20.SAPO_Results_Analysis.ipynb)**

The analysis notebook will:
- ✓ Load metrics from all experiments
- ✓ Calculate cumulative rewards
- ✓ Generate comparison plots (replicating paper figures)
- ✓ Perform statistical significance tests
- ✓ Export results to Google Drive

**Key Findings You'll Replicate:**

1. **Swarm collaboration works** - All configs beat baseline significantly
2. **Balance is critical** - 4/4 (50% external) performs best
3. **Diminishing returns** - More external ≠ better (2/6 worse than 4/4)
4. **Local diversity matters** - Each node needs sufficient local exploration

#### Configuration Parameters

All SAPO experiments use these environment variables:

```python
# Example: Config 2 (4/4) - BEST
NUM_TRAIN_SAMPLES = 4        # I: Local rollouts per round
NUM_TRANSPLANT_TREES = 4     # J: External rollouts per round
NUM_GENERATIONS = 8          # G: Completions per question
MAX_ROUNDS = 2000            # Total training rounds (same as paper)
```

#### Time and Resource Requirements

- **Single experiment:** ~24-48 hours on free Colab GPU (T4)
- **All 4 configs:** Run in parallel using 4 Google accounts
- **Storage:** ~2-5 GB per experiment in Google Drive
- **Recommended:** Enable cleanup (`ROLLOUT_CLEANUP_ENABLED = True`)

#### Detailed Documentation

For algorithm details and implementation notes:
- **[SAPO_PAPER_EXPLAINED.md](SAPO_PAPER_EXPLAINED.md)** - Comprehensive 25-page guide explaining the SAPO algorithm, paper contributions, and Google Colab implementation plan

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

### Option A: Monitoring Notebook (Recommended)

The monitoring notebook provides a comprehensive dashboard to track your experiment's progress with visualizations and diagnostics.

**[🔗 Open Monitoring Notebook](https://colab.research.google.com/github/Elrashid/rl-swarm/blob/main/notebooks/EX12.02.RL_Swarm_Monitoring.ipynb)**

**Quick Start:**

1. **Open the notebook** using the link above
2. **Mount Google Drive** (run Cell 1)
3. **Install dependencies** (run Cell 2)
4. **Configure experiment name** (Cell 3):
   ```python
   EXPERIMENT_NAME = 'my_first_experiment'  # Must match your running experiment
   ```
5. **Run all monitoring cells** (Cell 4 onwards)

**Available Dashboards:**

- **📊 Experiment Status** (Cell 4)
  - Current round and stage
  - Number of active peers
  - Last activity timestamp
  - List of registered nodes

- **📈 Training Metrics** (Cells 5-6)
  - Average reward per round (line plot with std dev)
  - Reward comparison by node (bar chart)
  - Active agents over time
  - Reward distribution histogram
  - Per-node reward trends

- **📁 Rollout Inspection** (Cell 7-8)
  - Rollout file counts by round
  - View latest rollout content
  - Batch and generation breakdown

- **⚠️ Health Checks** (Cell 9)
  - Automatic issue detection
  - Missing files warnings
  - Stale activity alerts

- **📉 Summary Statistics** (Cell 10)
  - Training duration
  - Per-node statistics
  - Overall reward metrics

- **🔄 Auto-Refresh Mode** (Cell 11)
  - Live status updates every 30 seconds
  - Real-time round progression
  - Press ■ (stop button) to exit

**Example Output:**

After running the status cell, you'll see:
```
===========================================================
📊 EXPERIMENT STATUS: my_first_experiment
===========================================================
Current Round:  15
Current Stage:  0
Active Peers:   3
Last Updated:   2025-10-05 14:23:45

👥 Registered Peers:
  - coordinator_0 (registered: 2025-10-05 12:00:15)
  - worker_1 (registered: 2025-10-05 12:05:32)
  - worker_2 (registered: 2025-10-05 12:10:48)
===========================================================
```

**Tips:**
- Run Cell 4 periodically to check current status
- Cell 11 (auto-refresh) is useful for monitoring long training runs
- Use Cell 9 to diagnose if training appears stuck
- Charts in Cells 5-6 update as you re-run them

### Option B: Quick Status Check

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
