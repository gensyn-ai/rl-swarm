# RL Swarm - Google Drive Mode

> **Note:** This is a fork of [Gensyn RL Swarm](https://github.com/gensyn-ai/rl-swarm) modified to support **Google Drive-only mode** for simpler deployment on Google Colab without blockchain, Docker, or authentication requirements.

---

## Overview

RL Swarm is a system for decentralized reinforcement learning that implements the **SAPO (Swarm sAmpling Policy Optimization)** algorithm. This fork enables collaborative model training through Google Drive file-based coordination instead of blockchain and P2P networking.

**What makes SAPO special:**
- Nodes share decoded rollouts (text completions), not gradients
- Configurable I/J split: I local rollouts + J external (swarm) rollouts per round
- Paper shows **+94% improvement** with optimal 50/50 local/external balance

**Paper Reference:** [arXiv:2509.08721](https://arxiv.org/abs/2509.08721)

## Quick Start: Optimal SAPO Configuration

This repository includes one pre-configured notebook for the **optimal SAPO configuration** (Config 2: 2 local / 2 external rollouts).

### Run on Google Colab

**[🔗 Open EX12.14c - SAPO Config 2 (2/2) ⭐ BEST](https://colab.research.google.com/github/Elrashid/rl-swarm/blob/main/notebooks/EX12.14c.SAPO_gpt2_Config2_2loc2ext.ipynb)**

This notebook runs **5 nodes** (1 coordinator + 4 training workers) on a single A100 80GB GPU using GPT-2.

**Setup:**

1. Click the link above to open in Google Colab
2. Select: **Runtime > Change runtime type > A100 GPU**
3. Run all cells - training takes ~21 hours
4. Expected result: **+94-150% improvement** over baseline

**Requirements:**
- Google Colab Pro+ ($50/month) for A100 80GB access
- Or rent A100 80GB from cloud providers ($1.29/hour × 21 hours = $27 total)

**Configuration:**
```python
NUM_TRAIN_SAMPLES = 2        # I: Local rollouts per round
NUM_TRANSPLANT_TREES = 2     # J: External rollouts from swarm
NUM_GENERATIONS = 4          # G: Completions per question
MAX_ROUNDS = 2000            # Total training rounds
```

**Why GPT-2 instead of Qwen2.5?**
- GPT-2 (124M params) uses ~6.5 GB per node during training
- 5 nodes fit on single A100 80GB (~33 GB total)
- Paper's finding: **Weaker models benefit MORE from swarm collaboration**
- Expected: **>94% improvement** (vs paper's 94% with Qwen2.5-0.5B)
- **90% cost savings** vs running 8 separate Colab sessions

See `EXPERIMENTAL_DESIGN_JUSTIFICATION.md` for full scientific rationale.

## Features

**Simplified Architecture:**
- ✅ **No blockchain** - Uses Google Drive for coordination
- ✅ **No Docker** - Runs directly in Colab
- ✅ **No authentication** - Just mount Google Drive
- ✅ **No peer identities** - Simple NODE_ID configuration
- ✅ **Resumable** - Checkpoints saved automatically
- ✅ **Full logging** - All metrics saved to Google Drive

**Removed from Original:**
- ❌ Blockchain coordination
- ❌ Modal login authentication
- ❌ Docker containers
- ❌ P2P networking (Hivemind DHT)
- ❌ Configuration frameworks (Hydra/OmegaConf)

## Local Testing (Advanced)

For development and testing without Colab:

```bash
# Clone repository
git clone https://github.com/Elrashid/rl-swarm
cd rl-swarm

# Install dependencies
pip install -r requirements.txt

# Terminal 1 - Start Coordinator
export GDRIVE_PATH="/path/to/shared/folder"
export EXPERIMENT_NAME="test_experiment"
export NODE_ROLE="coordinator"
export NODE_ID="coordinator_0"
export MODEL_NAME="openai-community/gpt2"
export NUM_TRAIN_SAMPLES="2"
export NUM_TRANSPLANT_TREES="2"
export NUM_GENERATIONS="4"
export MAX_ROUNDS="2000"
export ROLLOUT_PUBLISH_FREQUENCY="stage"

python -m rgym_exp.runner.swarm_launcher

# Terminal 2 - Start Worker (optional)
export GDRIVE_PATH="/path/to/shared/folder"  # SAME path
export EXPERIMENT_NAME="test_experiment"      # SAME name
export NODE_ROLE="worker"
export NODE_ID="worker_1"                     # DIFFERENT ID
export MODEL_NAME="openai-community/gpt2"
export NUM_TRAIN_SAMPLES="2"
export NUM_TRANSPLANT_TREES="2"
export NUM_GENERATIONS="4"
export MAX_ROUNDS="2000"
export ROLLOUT_PUBLISH_FREQUENCY="stage"

python -m rgym_exp.runner.swarm_launcher
```

## Google Drive Structure

Your experiment data will be organized in Google Drive:

```
/MyDrive/rl-swarm/
├── experiments/
│   └── {EXPERIMENT_NAME}/
│       ├── state/current_state.json           # Current round/stage
│       ├── peers/*.json                       # Peer registrations
│       ├── rewards/round_X/stage_Y/*.json     # Reward submissions
│       ├── rollouts/round_X/stage_Y/*.json    # Rollout sharing
│       ├── checkpoints/round_X/*.pt           # Model checkpoints
│       ├── logs/{node_id}/
│       │   ├── stdout.log                     # Console output
│       │   ├── stderr.log                     # Error output
│       │   ├── metrics.jsonl                  # Training metrics
│       │   └── training_events.jsonl          # Events
│       └── progress_{node_id}.jsonl           # Per-node progress
└── archives/                                  # Archived rollouts (optional)
```

## Configuration Options

All configuration is done via **environment variables**:

**Core Settings:**
- `GDRIVE_PATH`: Path to Google Drive base folder
- `EXPERIMENT_NAME`: Unique experiment identifier
- `NODE_ROLE`: 'coordinator' or 'worker'
- `NODE_ID`: Unique node identifier
- `MODEL_NAME`: HuggingFace model ID

**SAPO Parameters:**
- `NUM_TRAIN_SAMPLES`: Number of local rollouts (I parameter)
- `NUM_TRANSPLANT_TREES`: Number of external rollouts (J parameter)
- `NUM_GENERATIONS`: Number of completions per question (G parameter)
- `MAX_ROUNDS`: Total training rounds

**Rollout Sharing:**
- `ROLLOUT_PUBLISH_FREQUENCY`: 'generation', 'stage', or 'round'
- `ROLLOUT_CLEANUP_ENABLED`: Enable/disable cleanup
- `ROLLOUT_KEEP_LAST_N_ROUNDS`: How many rounds to keep
- `ROLLOUT_ARCHIVE_OLD`: Archive instead of delete

## Expected Results

With the optimal configuration (Config 2: 2 local / 2 external):

| Metric | Paper (Qwen2.5) | Expected (GPT-2) |
|--------|-----------------|------------------|
| Baseline | 562 | 200-300 |
| Config 2 (2/2) | 1093 | 500-700 |
| **Improvement** | **+94%** | **+110-150%** ✅ |

## Monitoring Progress

The notebook includes a built-in progress viewer that displays:
- Current round and latest event for each node
- Elapsed time and GPU memory usage
- Training completion status

Run the progress viewer cell after reconnecting to check training status.

**Programmatic monitoring:**
```python
from rgym_exp.utils.progress_tracker import get_experiment_progress
progress = get_experiment_progress('/path/to/gdrive', 'experiment_name')
```

## Documentation

- **[GDRIVE_IMPLEMENTATION.md](GDRIVE_IMPLEMENTATION.md)** - Complete technical documentation
- **[CLAUDE.md](CLAUDE.md)** - Codebase structure and development guide
- **[SAPO_PAPER_EXPLAINED.md](SAPO_PAPER_EXPLAINED.md)** - Comprehensive SAPO algorithm explanation
- **[EXPERIMENTAL_DESIGN_JUSTIFICATION.md](EXPERIMENTAL_DESIGN_JUSTIFICATION.md)** - Scientific justification for GPT-2 approach
- **[GPU_MEMORY_GUIDE.md](GPU_MEMORY_GUIDE.md)** - GPU memory requirements and troubleshooting

## Troubleshooting

### Common Issues

**No rollout files created:**
- Check `GDRIVE_PATH` is correct
- Verify `EXPERIMENT_NAME` matches across all nodes
- Ensure training cell has run and is showing output
- Check permissions on Google Drive directory

**Out of GPU memory:**
- Reduce batch size: Lower `NUM_TRAIN_SAMPLES`
- Use smaller model: `openai-community/gpt2` (124M params)
- Reduce nodes: Run 3 training workers instead of 4

**Training seems slow:**
- Normal on first run (model download: 2-5 minutes)
- GPT-2 training: ~21 hours for 2000 rounds on A100
- Check GPU utilization in Colab: Runtime > View resources

**Worker can't find coordinator:**
- Ensure `EXPERIMENT_NAME` exactly matches coordinator
- Verify coordinator is still running
- Check using same Google Drive account
- Wait 1-2 minutes for coordinator initialization

For more troubleshooting, see `GDRIVE_IMPLEMENTATION.md`.

## Contributing

This is a research fork focused on Google Drive-only mode. Contributions should:
- Maintain simplicity (no config frameworks, direct Python)
- Test on Google Colab
- Update documentation for significant changes

For issues or feature requests:
https://github.com/Elrashid/rl-swarm/issues

## Citation

If you use this code in your research, please cite the original SAPO paper:

```bibtex
@article{sapo2025,
  title={SAPO: Swarm sAmpling Policy Optimization},
  journal={arXiv preprint arXiv:2509.08721},
  year={2025}
}
```

## License

This project inherits the license from the original [Gensyn RL Swarm](https://github.com/gensyn-ai/rl-swarm) repository.

---

**Original RL Swarm**: https://github.com/gensyn-ai/rl-swarm
