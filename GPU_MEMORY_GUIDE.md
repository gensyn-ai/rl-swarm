# GPU Memory Guide for SAPO Experiments

Quick reference for running SAPO experiments on different GPU configurations.

## TL;DR

| Your GPU | What You Can Run | Notebook to Use | Notes |
|----------|------------------|-----------------|-------|
| **A100 80GB** | 8× gpt2 nodes | `EX12.14` | ✅ **Recommended** - Full swarm, all configs |
| **A100 40GB** | 6× gpt2 nodes | `EX12.14` (modify) | ⚠️ Reduce NUM_NODES=6 |
| **V100 32GB** | 4× gpt2 nodes | Not supported yet | Need to create custom notebook |
| **L4 24GB** | 3× gpt2 nodes | Not supported yet | Need to create custom notebook |
| **T4 15GB** | 1× gpt2 node | `EX12.10-13` (modify) | Change MODEL_NAME='gpt2' |
| **CPU** | Don't | N/A | Way too slow (200× slower) |

---

## Memory Requirements by Model & Config

### GPT-2 (124M parameters)

**Per node memory:**
- Model weights: 0.5 GB
- Forward pass (64 sequences): 4.0 GB
- Gradients + optimizer: 1.5 GB
- Working memory: 0.5 GB
- **Total: ~6.5 GB per node**

**Full swarm (8 nodes):**
```
8 nodes × 6.5 GB = 52 GB peak usage
```

### Qwen2.5-0.5B (500M parameters) - Paper's Model

**Per node memory:**
- Model weights: 1.0 GB
- Forward pass (64 sequences): 9.3 GB
- Gradients + optimizer: 3.0 GB
- Working memory: 2.0 GB
- **Total: ~16 GB per node**

**Full swarm (8 nodes):**
```
8 nodes × 16 GB = 128 GB total
Requires 8 separate GPUs with 16GB+ each
```

---

## Recommended Setups

### Setup 1: Google Colab Pro+ (A100 80GB) - $50/month

**Best for:** Full SAPO replication with gpt2

**Configuration:**
- Nodes: 8 (full swarm)
- Model: gpt2
- Config: I=8, J=0-6, G=8 (all paper configs)
- Memory: 52 GB / 80 GB (65% usage, safe)

**Cost:** $50/month (Colab Pro+ subscription)

**Timeline:** ~21 hours per experiment, 4 days for all 4 configs

**Notebook:** `notebooks/EX12.14.SAPO_8Node_SingleGPU_gpt2.ipynb`

**Steps:**
1. Open Colab, select Runtime > Change runtime type > A100 GPU
2. Open `EX12.14` notebook
3. Run all cells
4. For each experiment, change `NUM_TRAIN_SAMPLES` and `NUM_TRANSPLANT_TREES`

---

### Setup 2: Google Colab Free (T4 15GB) - Free

**Best for:** Single-node experiments or learning

**Limitations:**
- Cannot run full 8-node swarm
- Can run 1 node only
- Still demonstrates SAPO if you coordinate with friends (each runs 1 node)

**Configuration:**
- Nodes: 1
- Model: gpt2
- Config: I=8, J=0, G=8
- Memory: 6.5 GB / 15 GB (43% usage, very safe)

**Cost:** Free

**Timeline:** ~21 hours per experiment

**Notebook:** `notebooks/EX12.10.SAPO_Experiment_8loc0ext.ipynb` (modify)

**Changes needed:**
```python
# In Cell 2, change:
MODEL_NAME = 'gpt2'  # Instead of Qwen2.5-0.5B
```

---

### Setup 3: Cloud VM (Lambda Labs A100 80GB) - $1.29/hour

**Best for:** Uninterrupted training, no session limits

**Configuration:**
- Same as Setup 1
- Rent A100 80GB from Lambda Labs
- SSH access, no 24-hour timeout

**Cost:** $1.29/hour × 96 hours = **$124 for all 4 experiments**

**Advantages over Colab:**
- No session timeouts
- Can run all 4 experiments sequentially without manual restarts
- Full terminal access for debugging

**Steps:**
1. Rent A100 80GB from [lambdalabs.com](https://lambdalabs.com/)
2. SSH into instance
3. Clone repo: `git clone https://github.com/Elrashid/rl-swarm.git`
4. Install dependencies: `pip install -r requirements.txt`
5. Run experiments manually or use notebook via Jupyter

---

## Quick Setup Guide (Colab Pro+ A100 80GB)

### Step 1: Open Notebook
1. Go to Google Colab: [colab.research.google.com](https://colab.research.google.com/)
2. Upload `EX12.14.SAPO_8Node_SingleGPU_gpt2.ipynb`
3. Runtime > Change runtime type > Hardware accelerator: **A100 GPU**

### Step 2: Verify GPU
Run Cell 3 to verify you have A100 80GB:
```
✓ GPU: NVIDIA A100-SXM4-80GB
✓ Total VRAM: 80.0 GB
```

If you see A100 40GB instead:
- You got the smaller A100 (40GB VRAM)
- Reduce `NUM_NODES = 6` in Cell 1
- Still works, just fewer nodes

### Step 3: Run Baseline First
In Cell 1, set:
```python
EXPERIMENT_NAME = 'sapo_gpt2_baseline_8loc0ext'
NUM_TRAIN_SAMPLES = 8
NUM_TRANSPLANT_TREES = 0
```

Run all cells. Training will take ~21 hours.

### Step 4: Run Other Configs
After baseline completes, change Cell 1 for each config:

**Config 1 (6/2):**
```python
EXPERIMENT_NAME = 'sapo_gpt2_config1_6loc2ext'
NUM_TRAIN_SAMPLES = 6
NUM_TRANSPLANT_TREES = 2
```

**Config 2 (4/4) - BEST:**
```python
EXPERIMENT_NAME = 'sapo_gpt2_config2_4loc4ext'
NUM_TRAIN_SAMPLES = 4
NUM_TRANSPLANT_TREES = 4
```

**Config 3 (2/6):**
```python
EXPERIMENT_NAME = 'sapo_gpt2_config3_2loc6ext'
NUM_TRAIN_SAMPLES = 2
NUM_TRANSPLANT_TREES = 6
```

---

## Expected Results

### GPT-2 vs Paper (Qwen2.5-0.5B)

| Config | Paper Reward | GPT-2 Reward (Est.) | Paper Improvement | GPT-2 Improvement (Est.) |
|--------|--------------|---------------------|-------------------|--------------------------|
| Baseline (8/0) | 562 | 200-300 | — | — |
| Config 1 (6/2) | 854 | 350-500 | +52% | **+60-80%** |
| Config 2 (4/4) | 1093 | 500-700 | **+94%** | **+110-150%** ✅ |
| Config 3 (2/6) | 946 | 450-650 | +68% | **+100-130%** |

**Key Insight:** Relative improvements should be **higher** with GPT-2 than with Qwen2.5, confirming the paper's finding that weaker models benefit more from swarm collaboration.

---

## Troubleshooting

### Problem: Out of Memory (OOM)

**Error:** `torch.OutOfMemoryError: CUDA out of memory`

**Solution 1:** Reduce number of nodes
```python
NUM_NODES = 6  # Instead of 8
```

**Solution 2:** Enable gradient checkpointing
Edit `rgym_exp/runner/swarm_launcher.py` around line 140:
```python
if torch.cuda.is_available():
    model = model.to('cuda:0')
    model.gradient_checkpointing_enable()  # Add this line
```

**Solution 3:** Use smaller model (already using gpt2, can't go smaller)

---

### Problem: Colab Session Disconnects

**Symptom:** After 12-24 hours, Colab disconnects

**Solution:** Training continues in background. To monitor:
1. Reconnect to runtime
2. Re-run Cell 7 (Monitor cell)
3. Check Google Drive for checkpoints

**Prevention:**
- Keep browser tab active
- Use browser extension to prevent sleep
- Or use cloud VM instead (no timeouts)

---

### Problem: Protobuf Version Warnings

**Error:**
```
AttributeError: 'MessageFactory' object has no attribute 'GetPrototype'
```

**Solution:** Already fixed in `requirements.txt`
```
protobuf>=3.20.0,<5.0
```

Reinstall if needed:
```bash
pip install 'protobuf>=3.20.0,<5.0'
```

---

### Problem: Processes Won't Start

**Symptom:** Cell 6 launches processes but they crash immediately

**Check logs:**
```bash
cat /content/rl-swarm/logs/node_0/stderr.log
```

**Common causes:**
1. Google Drive not mounted → Re-run Cell 2
2. Repo not cloned → Re-run Cell 4
3. Dependencies missing → Re-run Cell 4
4. GPU not available → Check Cell 3

---

## Memory Monitoring

### Real-time GPU Usage

Run this in a separate cell anytime:
```python
import torch

allocated = torch.cuda.memory_allocated(0) / 1e9
reserved = torch.cuda.memory_reserved(0) / 1e9
total = torch.cuda.get_device_properties(0).total_memory / 1e9

print(f"Allocated: {allocated:.1f} GB")
print(f"Reserved:  {reserved:.1f} GB / {total:.1f} GB")
print(f"Free:      {total - reserved:.1f} GB")
```

### Expected Usage Over Time

**Startup (loading models):**
```
Round 0: 10-20 GB (loading 8 models)
```

**Early training:**
```
Round 1-100: 45-55 GB (stable)
```

**Mid training:**
```
Round 500-1500: 50-60 GB (gradual increase due to optimizer state)
```

**Late training:**
```
Round 1500-2000: 50-60 GB (stable plateau)
```

**If you see >70 GB:** Potential OOM risk, reduce nodes

---

## Comparison to Paper's Setup

### Original Paper (Qwen2.5-0.5B)
- GPUs: 8× separate (1 per node)
- Model: Qwen2.5-0.5B (500M params)
- VRAM per GPU: ~16 GB
- Total VRAM: 128 GB across 8 GPUs
- Cost: ~$400-500 (8× cloud VMs or Colab accounts)

### Our Setup (GPT-2)
- GPUs: 1× shared (all nodes)
- Model: GPT-2 (124M params)
- VRAM per GPU: ~52 GB total
- Total VRAM: 52 GB on 1 GPU
- Cost: **$50** (Colab Pro+) or **$124** (Lambda Labs for all 4 experiments)

**Savings:** 85-90% cost reduction

**Trade-off:** Lower absolute rewards (GPT-2 weaker than Qwen2.5), but **higher relative improvements** (tests hypothesis that weaker models benefit more)

---

## FAQ

### Q: Can I use FP16 to save memory?

**A:** Not recommended. GenRL uses FP32 for numerical stability. FP16 can cause:
- Gradient underflow/overflow
- NaN losses
- GRPO instability

### Q: Can I run multiple experiments in parallel?

**A:** No - each experiment uses all 8 nodes. Run sequentially.

### Q: What if I have A100 40GB instead of 80GB?

**A:** Reduce to 6 nodes:
```python
NUM_NODES = 6  # In Cell 1
```

Still demonstrates SAPO, just slightly less swarm diversity.

### Q: Can I use this on local hardware?

**A:** Yes, if you have:
- NVIDIA GPU with 80+ GB VRAM (RTX 6000 Ada, A100, H100)
- CUDA drivers installed
- Same steps as cloud VM

### Q: How do I know if training is working?

**Check:**
1. Cell 7 shows nodes running
2. GPU memory is 50-60 GB
3. Round number increases every ~35 seconds
4. Google Drive has metrics file: `experiments/{EXPERIMENT_NAME}/metrics/metrics.csv`

### Q: Can I run with friends (each person 1 node)?

**A:** Yes! Coordinate via shared Google Drive:
1. Everyone uses same `EXPERIMENT_NAME`
2. Everyone mounts same Google Drive folder
3. Person 1: `NODE_ROLE='coordinator'`, `NODE_ID='node_0'`
4. Person 2: `NODE_ROLE='worker'`, `NODE_ID='node_1'`
5. ...and so on

This is the **most cost-effective** approach for free tier users!

---

## Next Steps

1. **Run Baseline First:** Start with `EX12.14` notebook, baseline config (8/0)
2. **Validate Results:** After baseline completes, check if cumulative reward is 200-300
3. **Run Collaborative Configs:** If baseline works, run configs 6/2, 4/4, 2/6
4. **Analyze Results:** Use Cell 8 to compare against paper
5. **Write Paper:** Use `EXPERIMENTAL_DESIGN_JUSTIFICATION.md` for Methods section

Good luck! 🚀

---

**For detailed scientific justification of this setup, see:**
- `EXPERIMENTAL_DESIGN_JUSTIFICATION.md` - Why GPT-2 and single GPU
- `SAPO_PAPER_EXPLAINED.md` - Deep dive into SAPO algorithm
- Original paper: arXiv:2509.08721 (Gensyn AI Team, 2025)
