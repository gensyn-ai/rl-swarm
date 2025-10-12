# Testing Guide for RL Swarm

This document explains how to use TEST_MODE for quick validation of the RL Swarm system before running long training experiments.

## Overview

TEST_MODE is a quick validation run that:
- **Duration**: 1-2 minutes
- **Purpose**: Verify coordinator logic, rollout sharing, and logging work correctly
- **Nodes**: 5 (1 coordinator + 4 workers)
- **Rounds**: 3 (instead of 2000)
- **Config**: Reduced batch size (4 samples, 4 generations)

## Quick Start

### Option 1: Using TEST_MODE Notebook

1. Open `notebooks/TEST_MODE.ipynb` in Google Colab
2. Run all cells
3. Wait 1-2 minutes for completion
4. Check the validation output at the end

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

## Using the Validation Script

Run the standalone validation script after your test:

```bash
python rgym_exp/test/validate_test_run.py \
    --gdrive-path /content/drive/MyDrive/rl-swarm \
    --experiment test_mode_validation \
    --rounds 3 \
    --nodes 5
```

**Output:**
```
==============================================================
🔍 TEST MODE VALIDATION
==============================================================
Experiment: test_mode_validation
Path: /content/drive/MyDrive/rl-swarm/experiments/test_mode_validation
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
- `notebooks/EX12.14a.SAPO_gpt2_Baseline_4loc0ext.ipynb`
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

## Next Steps

After successful TEST_MODE validation:

1. **Review outputs**: Check that logs make sense
2. **Verify GDrive sync**: Ensure rollouts are being shared
3. **Start full training**: Run one of the SAPO experiment notebooks
4. **Monitor progress**: Use the monitoring cell to track training

## Files Created by TEST_MODE

```
{gdrive_path}/experiments/test_mode_validation/
├── state/
│   └── current_state.json          # Round/stage tracker
├── rewards/
│   ├── round_0/stage_0/            # Worker submissions
│   ├── round_1/stage_0/
│   └── round_2/stage_0/
├── peers/
│   └── *.json                      # Registered peer IDs
├── logs/
│   ├── node_0/                     # Coordinator logs
│   ├── node_1/                     # Worker logs
│   ├── node_2/
│   ├── node_3/
│   └── node_4/
└── rollouts/                       # Shared rollouts (if enabled)
    └── node_*/
```

## Environment Variables Reference

| Variable | Default | TEST_MODE | Description |
|----------|---------|-----------|-------------|
| `TEST_MODE` | False | **True** | Enable test mode |
| `MAX_ROUNDS` | 2000 | **3** | Number of training rounds |
| `NUM_TRAIN_SAMPLES` | 8 | **4** | Batch size (I) |
| `NUM_GENERATIONS` | 8 | **4** | Generations per sample (G) |
| `NUM_TRANSPLANT_TREES` | 0 | 0 | External rollouts (J) |
| `COORDINATOR_ROUND_INTERVAL` | 60 | 60 | Seconds between round advances |
| `NODE_ROLE` | worker | coordinator/worker | Node's role |
| `EXPERIMENT_NAME` | - | test_mode_validation | Experiment identifier |

## FAQ

**Q: How long should TEST_MODE take?**
A: 1-2 minutes on a GPU, 3-5 minutes on CPU

**Q: Can I run TEST_MODE without GDrive?**
A: No, GDrive is required for state management and rollout sharing

**Q: Does TEST_MODE require all 5 nodes?**
A: Yes, to properly test coordinator/worker interaction

**Q: Can I use TEST_MODE with custom models?**
A: Yes, set `MODEL_NAME` environment variable as usual

**Q: What if my test passes but full training fails?**
A: Check for OOM errors after multiple rounds. Test mode is short, so memory may accumulate over time.

## Support

If TEST_MODE validation fails:
1. Check logs in `{exp_path}/logs/node_*/stderr.log`
2. Run validation script for detailed diagnostics
3. Review this guide's troubleshooting section
4. Check CLAUDE.md for architecture details
