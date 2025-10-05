# SAPO Paper Explained: From Theory to Google Colab Implementation

## 📄 Original Paper Overview

**Title:** "Sharing is Caring: Efficient LM Post-Training with Collective RL Experience Sharing"

**Authors:** Gensyn AI Team (2025)

**arXiv:** 2509.08721v1

---

## 🧠 Core Ideas Combined in SAPO

The SAPO algorithm is a synthesis of three major research streams in AI:

### 1. **Reinforcement Learning for Language Model Fine-Tuning**

#### Background Concepts:

**A. RLHF (RL from Human Feedback)**
- Traditional approach: Train a reward model on human preference data
- Use the reward model to guide policy updates via PPO
- Examples: ChatGPT, Claude, GPT-4
- **Limitation:** Requires expensive human annotations

**B. RLVR (RL with Verifiable Rewards)**
- Alternative: Use programmatic, rule-based reward functions
- Works for tasks with objectively correct answers (math, code, logic)
- Examples: DeepSeek-R1-Zero, AlphaCode
- **Advantage:** No human labeling needed, infinite training data

**C. Policy Gradient Algorithms**
- **PPO (Proximal Policy Optimization):** Standard RL algorithm with KL penalty
- **GRPO (Group Relative Policy Optimization):** Extension for better reasoning
  - Compares multiple generations per prompt
  - Uses group-relative advantages instead of absolute values
  - More memory efficient than PPO
  - **SAPO uses GRPO** as its local update algorithm

#### SAPO's Contribution:
- Builds on RLVR + GRPO
- Adds decentralized experience sharing on top
- Each node still does standard RL, but samples from swarm rollouts

---

### 2. **Multi-Agent Methods**

#### Three Paradigms:

**A. Debate**
- Multiple LMs independently solve a problem
- They debate/discuss to refine answers
- Final answer chosen by voting or verifier
- Examples: AutoGen, Multi-Agent Debate

**B. Specialization (Role-Playing)**
- Different agents have different roles
- Example roles: Generator, Verifier, Critic, Refiner
- MALT: Separate agents for generation, verification, refinement
- Agents collaborate in pipeline

**C. Self-Improvement (Bootstrapping)**
- Models learn from their own outputs iteratively
- SPIN: Generate responses, learn to distinguish self-generated from human
- Self-play: Agents improve by competing/collaborating with themselves

#### SAPO's Contribution:
- **Not** structured multi-agent (no explicit roles)
- **Not** debate-based (no inter-agent communication during inference)
- **IS** collaborative self-improvement through experience sharing
- Bridges single-agent RL and multi-agent methods naturally
- Agents indirectly benefit from each other's exploration

---

### 3. **Distributed/Decentralized Training**

#### Traditional Distributed RL:

**Centralized Approaches:**
- Single coordinator orchestrates workers
- Gradient aggregation (AllReduce)
- Weight synchronization across GPUs
- Examples: DeepSpeed, Megatron-LM, LLaMA-RL

**Challenges:**
- High communication overhead
- Single point of failure
- Hardware homogeneity required
- Tight synchronization needed

#### SAPO's Contribution:
- **Fully decentralized:** No central coordinator
- **Asynchronous:** Nodes don't wait for each other
- **Heterogeneous:** Different models, hardware, latencies OK
- **Lightweight:** Share decoded text, not gradients/weights
- **Resilient:** Nodes can join/leave freely

---

## 🎯 What is Novel in SAPO?

### 1. **Decoded Rollout Sharing (Key Innovation)**

**Traditional Distributed RL:**
```
Node A: Gradients → Aggregate → Distribute
Node B: Gradients → Aggregate → Distribute
Problem: Requires same model architecture, synchronization
```

**SAPO:**
```
Node A: Generate text "2 + 2 = 4" → Share raw text
Node B: Re-encode "2 + 2 = 4" with its own model → Compute rewards/advantages
Benefit: Works across different models, no synchronization needed
```

**Why This Matters:**
- Different model sizes can collaborate (0.5B, 1.5B, 3B all in same swarm)
- Different architectures can collaborate (Qwen, Llama, Mistral)
- No need to send model weights or gradients (much smaller data transfer)
- Re-encoding allows each node to compute "as if" it generated that rollout

### 2. **Flexible Local/External Sampling**

**The I/J Split:**
- Each node samples **I local rollouts** (from its own generations)
- Each node samples **J external rollouts** (from swarm)
- Total training set size: I + J

**Key Finding from Paper:**
```
Configuration     Cumulative Reward    Improvement
──────────────────────────────────────────────────
8 local / 0 ext   561.79 (baseline)    -
6 local / 2 ext   854.43               +52%
4 local / 4 ext   1,093.31             +94% ⭐ BEST
2 local / 6 ext   945.87               +68% (unstable)
```

**Insights:**
- Balanced sharing (4/4) works best
- Too much external reliance (2/6) causes instability
- "Aha moments" propagate through swarm
- But over-reliance on others hurts learning

### 3. **Smart Filtering Mechanism**

**How Nodes Sample from Swarm:**
1. Receive all shared rollouts from other nodes
2. **Filter out rollouts with zero advantage** (no learning signal)
3. Sample J rollouts uniformly from remaining pool
4. Re-encode with local model
5. Compute advantages as if locally generated
6. Use for policy update

**Why This Works:**
- Nodes automatically ignore "useless" rollouts
- Each node tailors samples to its own learning needs
- High-quality rollouts get reused across swarm
- Bad rollouts are filtered out quickly

### 4. **No Trust Assumptions**

**Traditional Distributed Training:**
- Assumes all nodes are honest
- Byzantine failures can corrupt entire system
- Needs verification/validation layers

**SAPO:**
- Each node independently verifies rollouts with reward model
- Malicious/low-quality rollouts get zero advantage → filtered out
- Natural robustness through local verification
- Can add sophisticated filtering strategies

---

## 🔬 Paper's Experimental Setup

### Hardware
- **8 nodes** (agents)
- **Qwen2.5-0.5B** models (500M parameters each)
- **Docker containers** with one GPU per node
- **NCCL** for communication

### Dataset: ReasoningGYM
9 task types:
1. `base_conversion` - Number base conversion
2. `basic_arithmetic` - Elementary math
3. `arc_1d` - Abstract reasoning sequences
4. `bf` - Brainf*ck programs
5. `propositional_logic` - Logic puzzles
6. `fraction_simplification` - Simplify fractions
7. `decimal_arithmetic` - Decimal operations
8. `calendar_arithmetic` - Date puzzles
9. `binary_matrix` - Matrix reasoning

**Key Properties:**
- Procedurally generated (infinite data)
- Verifiable rewards (programmatic checking)
- Multi-domain (diverse reasoning)

### Training Configuration
```python
# Model
model = "Qwen2.5-0.5B"

# Training
max_rounds = 2000
num_generations = 8  # Completions per question
batch_size = 8       # Questions per round

# GRPO hyperparameters
epsilon_low = 0.2
epsilon_high = 0.28
kl_weight = 0.0      # No KL penalty

# Optimizer
optimizer = "Adam"
learning_rate = 0.001  # Default Adam LR
```

### 4 Experimental Configurations

Each node processes **8 questions per round**:

**1. Baseline: 8 local / 0 external**
- Sample 8 tasks
- Generate 8 completions per task
- Use all 64 rollouts for training
- Standard RL fine-tuning (no sharing)

**2. Config 1: 6 local / 2 external**
- Sample 6 tasks locally
- Generate 8 completions per task = 48 local rollouts
- Share all 48 with swarm
- Sample 2 rollouts from swarm (after filtering zero-advantage)
- Train on 6 local + 2 external = 8 total rollouts

**3. Config 2: 4 local / 4 external** ⭐
- Sample 4 tasks locally
- Generate 8 completions per task = 32 local rollouts
- Share all 32 with swarm
- Sample 4 rollouts from swarm
- Train on 4 local + 4 external = 8 total rollouts
- **BEST PERFORMANCE**

**4. Config 3: 2 local / 6 external**
- Sample 2 tasks locally
- Generate 8 completions per task = 16 local rollouts
- Share all 16 with swarm
- Sample 6 rollouts from swarm
- Train on 2 local + 6 external = 8 total rollouts
- Good performance but unstable

---

## 🚀 Our Google Colab Implementation Plan

### Architecture Differences

| Paper Implementation | Our Google Colab Implementation |
|---------------------|--------------------------------|
| Docker + NCCL | Google Drive file sharing |
| Single machine, 8 GPUs | 8 separate Colab notebooks |
| Synchronous communication | Asynchronous via file polling |
| Local filesystem | Cloud storage (Google Drive) |
| ~5 min per round | ~10-15 min per round |
| All nodes start together | Nodes can join anytime |

### Implementation Components

#### 1. **Rollout Sharing via Google Drive**

**How it works:**
```
Round N:
├── Node 1: Generates 8 questions × 8 completions = 64 rollouts
│   └── Writes: /rollouts/round_N/stage_0/node_1.json
│
├── Node 2: Generates rollouts
│   └── Writes: /rollouts/round_N/stage_0/node_2.json
│
└── All nodes:
    ├── Read all .json files in /rollouts/round_N/stage_0/
    ├── Filter rollouts with advantage > 0
    ├── Sample I local + J external rollouts
    └── Update policy with GRPO
```

**File Format:**
```json
{
  "peer_id": "node_1",
  "round": 5,
  "stage": 0,
  "timestamp": 1696800000.0,
  "rollouts": {
    "0": [
      {"prompt": "What is 2+2?", "response": "4", "reward": 1.0},
      {"prompt": "What is 2+2?", "response": "5", "reward": 0.0}
    ]
  }
}
```

#### 2. **Configuration Parameters**

**Environment Variables:**
```bash
# Experiment configuration
EXPERIMENT_NAME="sapo_4loc4ext_run1"
NODE_ID="node_1"  # node_1 through node_8

# SAPO parameters
NUM_TRAIN_SAMPLES=4      # I: local rollouts
NUM_TRANSPLANT_TREES=4   # J: external rollouts
NUM_GENERATIONS=8        # Completions per question

# Training
MAX_ROUNDS=2000
MODEL_NAME="Qwen/Qwen2.5-0.5B-Instruct"
SEED=42

# Google Drive
GDRIVE_PATH="/content/drive/MyDrive/rl-swarm"
ROLLOUT_PUBLISH_FREQUENCY="stage"
```

#### 3. **Four Experiment Notebooks**

**EX12.10.SAPO_Experiment_8loc0ext.ipynb** (Baseline)
```python
EXPERIMENT_NAME = 'sapo_baseline_8loc0ext'
NUM_TRAIN_SAMPLES = 8
NUM_TRANSPLANT_TREES = 0
```

**EX12.11.SAPO_Experiment_6loc2ext.ipynb**
```python
EXPERIMENT_NAME = 'sapo_config1_6loc2ext'
NUM_TRAIN_SAMPLES = 6
NUM_TRANSPLANT_TREES = 2
```

**EX12.12.SAPO_Experiment_4loc4ext.ipynb** ⭐ Best
```python
EXPERIMENT_NAME = 'sapo_config2_4loc4ext'
NUM_TRAIN_SAMPLES = 4
NUM_TRANSPLANT_TREES = 4
```

**EX12.13.SAPO_Experiment_2loc6ext.ipynb**
```python
EXPERIMENT_NAME = 'sapo_config3_2loc6ext'
NUM_TRAIN_SAMPLES = 2
NUM_TRANSPLANT_TREES = 6
```

### Execution Plan

#### Phase 1: Small-Scale Test (1 day)
```
Goal: Verify implementation works
Nodes: 2 nodes
Rounds: 10 rounds
Config: 4 local / 4 external
Expected: ~30 minutes total
```

#### Phase 2: Full Experiment (10 days)
```
For each configuration (4 total):
  - Launch 8 Colab notebooks
  - Run 2000 rounds
  - Expected: ~2.6 days per config (parallel)
  - Total: ~10 days for all 4 configs

Total data generated: ~32 GB
```

#### Phase 3: Analysis
```
Notebook: EX12.20.SAPO_Results_Analysis.ipynb

Metrics to compare:
1. Cumulative reward per configuration
2. Average reward trajectory (with confidence intervals)
3. Per-node learning curves
4. Oscillation patterns (for 2/6 config)
5. Statistical significance tests
```

### Expected Results

Based on paper, we expect:

**Cumulative Rewards (2000 rounds, 8 nodes):**
- 8/0 baseline: ~562
- 6/2 config: ~854 (+52%)
- 4/4 config: ~1093 (+94%) ⭐
- 2/6 config: ~946 (+68%, unstable)

**Key Observations:**
1. Balanced sharing (4/4) significantly outperforms baseline
2. "Aha moments" propagate through swarm
3. Over-reliance on external rollouts causes oscillations
4. Google Drive adds latency but doesn't change core dynamics

---

## 📊 How to Measure Success

### Quantitative Metrics

**1. Cumulative Reward**
```python
total_reward = sum(all rewards across all nodes and rounds)
improvement = (total_reward - baseline) / baseline * 100
```

**2. Moving Average Rewards**
```python
# Window size: 100 rounds
smoothed_reward = moving_average(rewards, window=100)
```

**3. Peak Performance**
```python
max_reward = max(smoothed_rewards across all nodes)
```

**4. Stability**
```python
std_dev = std(rewards_per_round)
oscillation_metric = count(steep_drops > threshold)
```

### Qualitative Observations

**1. Aha Moment Propagation**
- Track when one node suddenly improves
- Measure how quickly other nodes catch up
- Identify which task types spread fastest

**2. Network Effects**
- Do high-performing nodes help low-performing ones?
- What happens when strong node relies too much on weak swarm?

**3. Failure Modes**
- Forgetting behavior in 2/6 config
- Quality degradation when swarm has too few good samples

---

## 🛠️ Implementation Checklist

### Code Changes Required

- [ ] **swarm_launcher.py**: Add environment variables for I/J split
  - `NUM_TRAIN_SAMPLES` (I: local rollouts)
  - `NUM_TRANSPLANT_TREES` (J: external rollouts)
  - `NUM_GENERATIONS` (completions per question)
  - `MAX_ROUNDS` (should be 2000)

- [ ] **Four experiment notebooks**: One per config (8/0, 6/2, 4/4, 2/6)
  - Cell 1: Mount Google Drive
  - Cell 2: Configuration (set I, J, experiment name)
  - Cell 3: Clone repo & install dependencies
  - Cell 4: Initialize experiment folders
  - Cell 5: Start training with live output

- [ ] **Analysis notebook**: Visualize results
  - Load metrics from all 4 experiments
  - Plot per-agent trajectories
  - Plot moving averages with confidence intervals
  - Compute cumulative rewards
  - Statistical tests (t-test, ANOVA)

### Testing Strategy

**Test 1: Single Node (10 min)**
```bash
# Verify basic training works
NUM_TRAIN_SAMPLES=8
NUM_TRANSPLANT_TREES=0
MAX_ROUNDS=5
```

**Test 2: Two Nodes, Sharing (30 min)**
```bash
# Verify rollout sharing works
Node 1: NUM_TRAIN_SAMPLES=4, NUM_TRANSPLANT_TREES=4
Node 2: NUM_TRAIN_SAMPLES=4, NUM_TRANSPLANT_TREES=4
MAX_ROUNDS=10
```

**Test 3: Eight Nodes, Small Scale (2 hours)**
```bash
# Verify full swarm works
8 nodes × (NUM_TRAIN_SAMPLES=4, NUM_TRANSPLANT_TREES=4)
MAX_ROUNDS=50
```

**Test 4: Full Experiment (10 days)**
```bash
# Replicate paper
8 nodes × 2000 rounds × 4 configs
```

---

## 📈 Visualization Examples

### Figure 1: Raw Rewards (Paper Figure 2)
```
4 subplots (one per config)
X-axis: Training round (0-2000)
Y-axis: Reward (0-1)
Lines: 8 agents (one per node)
Shows: Individual learning trajectories
```

### Figure 2: Smoothed Average (Paper Figure 3)
```
Single plot with 4 lines
X-axis: Training round (0-2000)
Y-axis: Average reward (moving avg, window=100)
Lines: 4 configs (8/0, 6/2, 4/4, 2/6)
Shaded: Confidence interval (min/max across agents)
Shows: Overall performance comparison
```

### Figure 3: Cumulative Rewards (Our Addition)
```
Bar chart
X-axis: Configuration
Y-axis: Total cumulative reward
Bars: 4 configs with % improvement labels
Shows: Which config accumulated most reward
```

---

## 🎓 Key Takeaways

### For Researchers
1. **SAPO bridges single-agent RL and multi-agent methods**
   - Gets multi-agent benefits without explicit coordination
   - More flexible than traditional distributed RL

2. **Experience sharing is powerful but needs balance**
   - 50/50 local/external is optimal
   - Too much external causes instability

3. **Decentralization enables new possibilities**
   - Heterogeneous models can collaborate
   - No infrastructure lock-in
   - Resilient to node failures

### For Practitioners
1. **Google Colab + Drive makes SAPO accessible**
   - No need for GPU cluster
   - Free or low-cost experimentation
   - Easy to scale up/down

2. **Filtering is crucial**
   - Remove zero-advantage samples
   - Can add task-difficulty filtering
   - Can add model-capability filtering

3. **Start with balanced sharing**
   - 4 local / 4 external is safe default
   - Monitor for oscillations if going higher external ratio
   - Can adapt I/J ratio dynamically

---

## 🔗 References

**Original Paper:**
- Gensyn AI Team (2025). "Sharing is Caring: Efficient LM Post-Training with Collective RL Experience Sharing." arXiv:2509.08721v1

**Key Dependencies:**
- ReasoningGYM: https://github.com/open-thought/reasoning-gym
- GenRL: https://github.com/gensyn-ai/genrl
- Qwen2.5: https://huggingface.co/Qwen/Qwen2.5-0.5B-Instruct

**Related Work:**
- GRPO: Shao et al. (2024) "DeepSeekMath"
- RLHF: Ziegler et al. (2020)
- DeepSeek-R1: DeepSeek AI (2025)
- Multi-agent debate: Du et al. (2023)

---

**Document Version:** 1.0
**Created:** 2025-01-05
**Author:** Claude (Anthropic)
**Repository:** https://github.com/Elrashid/rl-swarm
