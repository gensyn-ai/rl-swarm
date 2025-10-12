# Testing Guide for RL Swarm

This document explains how to use TEST_MODE for quick validation of the RL Swarm system before running long training experiments.

## Overview

TEST_MODE notebooks provide quick validation of the RL Swarm system with 4 different configurations:
- **Duration**: 1-2 minutes each, ~8 minutes for all 4 configurations
- **Purpose**: Verify coordinator logic, rollout sharing, and logging work correctly
- **Nodes**: 5 (1 coordinator + 4 workers)
- **Rounds**: 3 (instead of 2000)
- **Configurations**: 4 test notebooks (Baseline, Config1, Config2, Config3)
- **Config**: Reduced batch size (4 samples, 4 generations)

## Test Configurations

There are 4 TEST_MODE notebooks, each testing different rollout sharing configurations:

| Notebook | Config | I (Local) | J (External) | Split | Tests |
|----------|--------|-----------|--------------|-------|-------|
| TEST_MODE_Baseline.ipynb | Baseline | 4 | 0 | 100%/0% | Core functionality only |
| TEST_MODE_Config1.ipynb | Config1 | 3 | 1 | 75%/25% | + Rollout sharing |
| TEST_MODE_Config2.ipynb | Config2 | 2 | 2 | 50%/50% | + Balanced sharing |
| TEST_MODE_Config3.ipynb | Config3 | 1 | 3 | 25%/75% | + Heavy sharing |

**Parameters:**
- **I (Local)**: Number of local training samples (`NUM_TRAIN_SAMPLES`)
- **J (External)**: Number of external rollouts to fetch (`NUM_TRANSPLANT_TREES`)
- **Split**: Percentage of local vs. external rollouts used in training

## Quick Start

### Option 1: Using TEST_MODE Notebooks

1. **Start with Baseline** (recommended for first-time validation):
   - Open `notebooks/TEST_MODE_Baseline.ipynb` in Google Colab
   - Run all cells
   - Wait 1-2 minutes for completion
   - Check the validation output at the end

2. **Test rollout sharing** (Config1-3):
   - Open `notebooks/TEST_MODE_Config1.ipynb` (or Config2/Config3)
   - Run all cells to validate rollout sharing works correctly
   - These test that workers can publish and fetch rollouts via GDrive

## Which Test Should I Run?

**When to use each configuration:**

- **Baseline**: For basic validation before full experiments
  - Use this to verify coordinator logic, state management, and worker submissions
  - No rollout sharing involved, so faster and simpler
  - Run this first if you're new to the system

- **Config1-3**: To test rollout sharing works correctly
  - Use these to validate that workers can publish and fetch rollouts via GDrive
  - Essential if you're planning experiments with `NUM_TRANSPLANT_TREES > 0`
  - Config3 (heavy sharing) is the most demanding test of the rollout system

**Recommendation**: If making changes to coordinator or sharing logic, run all 4 configurations to ensure full coverage.

### Option 2: Using Environment Variable

Set `TEST_MODE=True` when launching any experiment:

```bash
export TEST_MODE=True
python -m rgym_exp.runner.swarm_launcher
```

Or in a notebook cell:
```python
env['TEST_MODE'] = 'True'
```

## Real-Time Progress Monitoring

All TEST_MODE notebooks now include real-time progress monitoring that saves to Google Drive:

### Progress Tracking
- **Location**: `{gdrive_path}/experiments/{exp_name}/progress_{node_id}.jsonl`
- **Updates**: Every round completion
- **Content**: Round number, elapsed time, GPU memory, events
- **Access**: Can be viewed even after notebook disconnects

### Log Streaming
- **Location**: `{gdrive_path}/experiments/{exp_name}/logs/{node_id}/stdout.log` and `stderr.log`
- **Flush interval**: Every 30 seconds (configurable)
- **Content**: All console output (prints, errors, warnings)
- **Benefit**: Logs never lost, even if process crashes

### Test Results
- **Location**: `{gdrive_path}/experiments/{exp_name}/test_results.json`
- **Content**: Pass/fail status, check details, configuration, timestamps
- **Purpose**: Easy comparison across multiple test runs

### Using Progress Monitoring

Run the progress viewer cell (Section 7.5) anytime:
```python
from rgym_exp.utils.progress_tracker import get_experiment_progress
progress = get_experiment_progress(GDRIVE_BASE_PATH, EXPERIMENT_NAME)
```

This shows:
- Current round for each node
- Elapsed time
- Latest event (round_start, round_complete, error)
- GPU memory usage

## What Gets Validated

After a TEST_MODE run, the following are automatically checked:

### 1. State File ✓
- **Location**: `{gdrive_path}/experiments/{exp_name}/state/current_state.json`
- **Check**: File exists and shows `round: 3`
- **Meaning**: Coordinator successfully advanced rounds

### 2. Worker Submissions ✓
- **Location**: `{gdrive_path}/experiments/{exp_name}/rewards/round_{0,1,2}/stage_0/`
- **Check**: JSON files present for each worker
- **Meaning**: Workers successfully submitted rewards

### 3. Logs ✓
- **Location**: `{gdrive_path}/experiments/{exp_name}/logs/node_{0-4}/`
- **Check**: `stdout.log` and `stderr.log` exist for all nodes
- **Meaning**: All nodes launched and logged properly

### 4. No OOM Errors ✓
- **Check**: `stderr.log` files don't contain "OutOfMemoryError"
- **Meaning**: Memory configuration is safe

### 5. Coordinator Functionality ✓
- **Check**: Coordinator log contains round advancement messages
- **Meaning**: Coordinator properly managed the swarm

### 6. Rollouts (Config1-3 only) ✓
- **Location**: `{gdrive_path}/experiments/{exp_name}/rollouts/round_{0-2}/stage_0/`
- **Check**: 4 JSON files per round (one per training worker) when `J > 0`
- **Meaning**: Workers successfully published rollouts for sharing
- **Note**: Baseline (J=0) skips this check as no rollouts are shared

## Using the Validation Script

Run the standalone validation script after your test. The script accepts different parameters for each configuration:

### Baseline (4 local, 0 external)
```bash
python rgym_exp/test/validate_test_run.py \
    --gdrive-path /content/drive/MyDrive/rl-swarm \
    --experiment test_baseline_4loc0ext \
    --rounds 3 \
    --nodes 5 \
    --transplants 0
```

### Config1 (3 local, 1 external)
```bash
python rgym_exp/test/validate_test_run.py \
    --gdrive-path /content/drive/MyDrive/rl-swarm \
    --experiment test_config1_3loc1ext \
    --rounds 3 \
    --nodes 5 \
    --transplants 1
```

### Config2 (2 local, 2 external)
```bash
python rgym_exp/test/validate_test_run.py \
    --gdrive-path /content/drive/MyDrive/rl-swarm \
    --experiment test_config2_2loc2ext \
    --rounds 3 \
    --nodes 5 \
    --transplants 2
```

### Config3 (1 local, 3 external)
```bash
python rgym_exp/test/validate_test_run.py \
    --gdrive-path /content/drive/MyDrive/rl-swarm \
    --experiment test_config3_1loc3ext \
    --rounds 3 \
    --nodes 5 \
    --transplants 3
```

### Example Output (Baseline)
```
==============================================================
🔍 TEST MODE VALIDATION
==============================================================
Experiment: test_baseline_4loc0ext
Path: /content/drive/MyDrive/rl-swarm/experiments/test_baseline_4loc0ext
==============================================================
✓ State file exists: Round 3
  ✓ Reached round 3 as expected
✓ Round 0: 4 worker submissions
✓ Round 1: 4 worker submissions
✓ Round 2: 4 worker submissions
✓ Node 0: stdout.log present
  ✓ Node 0: No OOM errors
✓ Node 1: stdout.log present
  ✓ Node 1: No OOM errors
...
✓ Coordinator: Coordinator loop started
✓ Coordinator: Round advancement
✓ Coordinator: Worker monitoring
==============================================================
📊 VALIDATION SUMMARY
==============================================================
✅ PASS: State file
✅ PASS: Submissions
✅ PASS: Logs
✅ PASS: Coordinator
==============================================================
✅ ALL CHECKS PASSED
==============================================================
```

### Example Output (Config2 with rollouts)
```
==============================================================
🔍 TEST MODE VALIDATION
==============================================================
Experiment: test_config2_2loc2ext
Transplants: 2
==============================================================
✓ State file exists: Round 3
✓ Round 0: 4 worker submissions
✓ Round 0: 4 rollout files published
✓ Round 1: 4 worker submissions
✓ Round 1: 4 rollout files published
✓ Round 2: 4 worker submissions
✓ Round 2: 4 rollout files published
...
✅ PASS: Rollouts (12 files across 3 rounds)
✅ ALL CHECKS PASSED
==============================================================
```

## TEST_MODE Configuration

When `TEST_MODE=True`, the following parameters are automatically set:

| Parameter | Normal | TEST_MODE |
|-----------|--------|-----------|
| `MAX_ROUNDS` | 2000 | **3** |
| `NUM_TRAIN_SAMPLES` | 8 | **4** |
| `NUM_GENERATIONS` | 8 | **4** |
| Duration | Hours | **1-2 min** |

All other parameters (model, coordinator logic, rollout sharing) remain identical to production runs.

## Interpreting Results

### ✅ All Checks Pass
Your system is ready for full training runs. Proceed with:
- **Baseline passed**: Core coordinator/worker logic is working
- **Config1-3 passed**: Rollout sharing via GDrive is functional
- You can now run full experiment notebooks:
  - `notebooks/EX12.14a.SAPO_gpt2_Baseline_4loc0ext.ipynb`
  - `notebooks/EX12.14b.SAPO_gpt2_Config1_3loc1ext.ipynb`
  - Or other experiment notebooks

### ❌ State File Check Failed
**Problem**: Coordinator didn't advance rounds
**Possible causes**:
- Coordinator node crashed
- GDrive state file not writable
- Check `logs/node_0/stderr.log` for errors

**Fix**: Verify GDrive is mounted and writable

### ❌ Submissions Check Failed
**Problem**: Workers didn't submit rewards
**Possible causes**:
- Workers crashed during training
- OOM errors (check memory)
- Data loading issues

**Fix**: Check worker logs in `logs/node_{1-4}/stderr.log`

### ❌ Logs Check Failed
**Problem**: Some nodes didn't start
**Possible causes**:
- Process spawn errors
- Python environment issues
- Missing dependencies

**Fix**: Check the monitoring cell output for process status

### ❌ OOM Errors Detected
**Problem**: GPU memory exceeded
**Possible causes**:
- Too many nodes for available VRAM
- Model too large
- Batch size too high

**Fix**: Reduce number of nodes or use CPU-only mode

### ❌ Coordinator Check Failed
**Problem**: Coordinator didn't run properly
**Possible causes**:
- `NODE_ROLE` not set to 'coordinator' for node_0
- Coordinator crashed before advancing rounds
- Logic error in coordinator loop

**Fix**: Check `logs/node_0/stdout.log` for coordinator messages

### ❌ Rollouts Check Failed (Config1-3 only)
**Problem**: Rollout files not found or incomplete
**Possible causes**:
- Workers didn't complete training steps
- `NUM_TRANSPLANT_TREES` (J) set to 0 by mistake
- GDrive write permissions issue
- Rollout publishing disabled in config

**Fix**:
- Check worker logs for training completion
- Verify `J > 0` in the config cell of the notebook
- Ensure GDrive is mounted and writable
- Check for "Publishing rollout" messages in worker logs

## Advanced Usage

### Custom Test Configuration

You can override TEST_MODE defaults:

```python
env['TEST_MODE'] = 'True'
env['MAX_ROUNDS'] = '5'  # Override: test with 5 rounds
env['NUM_TRAIN_SAMPLES'] = '2'  # Override: smaller batch
```

### Testing Specific Configurations

Use TEST_MODE with any SAPO config:

```python
# Test Config2 (balanced collaboration) in test mode
env['TEST_MODE'] = 'True'
env['NUM_TRANSPLANT_TREES'] = '2'  # Enable rollout sharing
env['NUM_TRAIN_SAMPLES'] = '2'
```

### Coordinator-Only Testing

Test coordinator logic without training:

```python
# Launch only coordinator node
env['NODE_ROLE'] = 'coordinator'
env['TEST_MODE'] = 'True'
env['COORDINATOR_ROUND_INTERVAL'] = '30'  # Advance every 30s
```

## Troubleshooting

### Test Hangs at Round 0
**Symptom**: Training starts but never advances past round 0
**Cause**: Coordinator not advancing rounds
**Solution**: Check coordinator logs for errors

### Test Completes but Validation Fails
**Symptom**: Notebook finishes but checks fail
**Cause**: Processes crashed silently
**Solution**: Check stderr logs for each node

### OOM During Test Mode
**Symptom**: Memory errors even with reduced config
**Cause**: Too many training nodes for available VRAM
**Solution**: Run with 3 nodes instead of 5:
```python
# In notebook, change process loop
for node_id in range(3):  # Reduced from 5
```

### Rollouts Not Published (Config1-3)
**Symptom**: Validation shows no rollout files in `rollouts/` directory
**Causes**:
1. Workers didn't complete training steps before coordinator advanced rounds
2. `NUM_TRANSPLANT_TREES` (J) set to 0 by mistake in config cell
3. GDrive write permissions issue
4. Rollout publishing logic not triggered

**Fixes**:
1. Check worker logs (`logs/node_{1-4}/stdout.log`) for "Publishing rollout" messages
2. Verify the config cell has correct J value:
   - Config1: `env['NUM_TRANSPLANT_TREES'] = '1'`
   - Config2: `env['NUM_TRANSPLANT_TREES'] = '2'`
   - Config3: `env['NUM_TRANSPLANT_TREES'] = '3'`
3. Ensure GDrive is mounted properly: `ls /content/drive/MyDrive/rl-swarm`
4. Check that workers have write permissions to the experiment directory

### Rollouts Published but Not Fetched
**Symptom**: Rollout files exist but workers report "No external rollouts found"
**Causes**:
1. Round timing: Workers tried to fetch before rollouts were published
2. Directory structure mismatch
3. JSON parsing errors in rollout files

**Fixes**:
1. Check that rollout files are in correct location: `{exp_path}/rollouts/round_{N}/stage_0/`
2. Verify rollout JSON files are valid (not empty or corrupted)
3. Look for "Fetching external rollouts" messages in worker logs
4. Increase `COORDINATOR_ROUND_INTERVAL` to give workers more time

## Next Steps

After successful TEST_MODE validation:

1. **Review outputs**: Check that logs make sense
2. **Verify GDrive sync**: Ensure rollouts are being shared (Config1-3)
3. **Start full training**: Run one of the experiment notebooks:
   - Baseline experiments: `EX12.14a.SAPO_gpt2_Baseline_4loc0ext.ipynb`
   - Config1 experiments: `EX12.14b.SAPO_gpt2_Config1_3loc1ext.ipynb`
   - Config2 experiments: `EX12.14c.SAPO_gpt2_Config2_2loc2ext.ipynb`
   - Config3 experiments: `EX12.14d.SAPO_gpt2_Config3_1loc3ext.ipynb`
4. **Monitor progress**: Use the monitoring cell to track training

## Files Created by TEST_MODE

### Baseline (test_baseline_4loc0ext)
```
{gdrive_path}/experiments/test_baseline_4loc0ext/
├── state/
│   └── current_state.json          # Round/stage tracker
├── rewards/
│   ├── round_0/stage_0/            # Worker submissions
│   ├── round_1/stage_0/
│   └── round_2/stage_0/
├── peers/
│   └── *.json                      # Registered peer IDs
└── logs/
    ├── node_0/                     # Coordinator logs
    ├── node_1/                     # Worker logs
    ├── node_2/
    ├── node_3/
    └── node_4/
```

### Config1-3 (with rollout sharing)
```
{gdrive_path}/experiments/test_config{1,2,3}_*/
├── state/
│   └── current_state.json          # Round/stage tracker
├── rewards/
│   ├── round_0/stage_0/            # Worker submissions
│   ├── round_1/stage_0/
│   └── round_2/stage_0/
├── rollouts/                       # Shared rollouts (J > 0)
│   ├── round_0/stage_0/
│   │   ├── worker_1.json           # 4 files per round
│   │   ├── worker_2.json
│   │   ├── worker_3.json
│   │   └── worker_4.json
│   ├── round_1/stage_0/
│   └── round_2/stage_0/
├── peers/
│   └── *.json                      # Registered peer IDs
└── logs/
    ├── node_0/                     # Coordinator logs
    ├── node_1/                     # Worker logs
    ├── node_2/
    ├── node_3/
    └── node_4/
```

## Environment Variables Reference

| Variable | Default | TEST_MODE | Description |
|----------|---------|-----------|-------------|
| `TEST_MODE` | False | **True** | Enable test mode |
| `MAX_ROUNDS` | 2000 | **3** | Number of training rounds |
| `NUM_TRAIN_SAMPLES` | 8 | **4** | Batch size (I) |
| `NUM_GENERATIONS` | 8 | **4** | Generations per sample (G) |
| `NUM_TRANSPLANT_TREES` | 0 | 0/1/2/3 | External rollouts (J), varies by test config |
| `COORDINATOR_ROUND_INTERVAL` | 60 | 60 | Seconds between round advances |
| `NODE_ROLE` | worker | coordinator/worker | Node's role |
| `EXPERIMENT_NAME` | - | test_baseline_4loc0ext / test_config{1,2,3}_* | Experiment identifier |

## FAQ

**Q: How long should TEST_MODE take?**
A: 1-2 minutes per notebook on a GPU, 3-5 minutes on CPU. All 4 notebooks take ~8 minutes total.

**Q: Should I run all 4 test notebooks?**
A: Start with Baseline to validate core functionality. Run Config1-3 if you plan to use rollout sharing (`J > 0`) in your experiments.

**Q: What's the difference between the 4 test configs?**
A: They test different ratios of local (I) vs. external (J) rollouts:
- Baseline: 4 local, 0 external (no sharing)
- Config1: 3 local, 1 external (25% sharing)
- Config2: 2 local, 2 external (50% sharing)
- Config3: 1 local, 3 external (75% sharing)

**Q: Can I run TEST_MODE without GDrive?**
A: No, GDrive is required for state management and rollout sharing

**Q: Does TEST_MODE require all 5 nodes?**
A: Yes, to properly test coordinator/worker interaction

**Q: Can I use TEST_MODE with custom models?**
A: Yes, set `MODEL_NAME` environment variable as usual

**Q: Why are there no rollouts in Baseline test?**
A: Baseline has `J=0` (no external rollouts), so no rollout sharing occurs. This is expected behavior.

**Q: What if my test passes but full training fails?**
A: Check for OOM errors after multiple rounds. Test mode is short, so memory may accumulate over time.

## Support

If TEST_MODE validation fails:
1. Check logs in `{exp_path}/logs/node_*/stderr.log`
2. Run validation script for detailed diagnostics
3. Review this guide's troubleshooting section
4. Check CLAUDE.md for architecture details
