# Code Execution Flow - RL Swarm Training Pipeline

This document maps the complete execution flow of the RL Swarm training system, from notebook launch to rollout sharing.

## Overview

The training pipeline consists of 10 major components that orchestrate decentralized collaborative learning through Google Drive-based rollout sharing.

## Execution Flow Diagram

```
┌─────────────────────────────────────────────────────────────────────┐
│ 1. NOTEBOOK (e.g., EX12.14a.SAPO_gpt2_Baseline_4loc0ext.ipynb)     │
│    Cell 1: Mount Google Drive                                       │
│    Cell 2: Set environment variables (GDRIVE_PATH, NODE_ROLE, etc.)│
│    Cell 3: Install dependencies (!pip install gensyn-genrl==0.1.9)  │
│    Cell 4: Launch training                                          │
└────────────────────────┬────────────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────────────┐
│ 2. LAUNCHER: rgym_exp/runner/swarm_launcher.py::main()             │
│    - Read env vars (GDRIVE_PATH, NODE_ROLE, MODEL_NAME, etc.)      │
│    - Setup log streaming (gdrive_log_stream.py)                    │
│    - Setup progress tracker (progress_tracker.py)                  │
│    - Create GDriveRolloutSharing                                    │
│    - Create GDriveCommunicationBackend                              │
│    - Create GameState                                               │
│    - Create RewardManager                                           │
│    - Load model (AutoModelForCausalLM)                              │
│    - Create GRPOTrainerModule                                       │
│    - Create ReasoningGymDataManager                                 │
│    - Create GDriveSwarmCoordinator                                  │
│    - Create SwarmGameManager (line 252-266)                         │
│    - Call: game_manager.run_game() (line 283) ◄─────┐              │
└────────────────────────┬────────────────────────────┘              │
                         │                                            │
                         ▼                                            │
┌─────────────────────────────────────────────────────────────────────┐
│ 3. GENRL: genrl.game.game_manager.BaseGameManager.run_game()       │
│    (Inherited by SwarmGameManager)                                  │
│                                                                     │
│    world_state_pruners, game_tree_brancher = ...                   │
│    self.state._init_game(...)  # Initialize game trees             │
│                                                                     │
│    try:                                                             │
│        while not self.end_of_game():  # Loop until max_round       │
│            get_logger().info(f"Starting round: {round}")            │
│            self.run_game_round() ◄───────────────┐                 │
│    except:                                       │                 │
│        get_logger().exception(...)               │                 │
│    finally:                                      │                 │
│        self._hook_after_game() ──────┐           │                 │
│        self.trainer.cleanup()        │           │                 │
└──────────────────────────────────────┼───────────┼─────────────────┘
                                       │           │
                                       │           ▼
┌──────────────────────────────────────┼───────────────────────────────┐
│ 4. GENRL: BaseGameManager.run_game_round()      │                   │
│                                                  │                   │
│    # STAGE LOOP                                 │                   │
│    while not self.end_of_round():  # max_stage times               │
│        self.run_game_stage()  # Generate rollouts ◄─────────┐      │
│        swarm_payloads = self.communication.all_gather_object(...)   │
│        world_states = self.data_manager.prepare_states(...) ─┐      │
│        self.state.advance_stage(world_states)                │      │
│                                                              │      │
│    # AFTER ALL STAGES COMPLETE                              │      │
│    self.rewards.update_rewards(self.state)                  │      │
│    self._hook_after_rewards_updated() ◄──────────────┐      │      │
│                                                       │      │      │
│    # TRAINING                                        │      │      │
│    if self.mode in [Train, TrainAndEvaluate]:       │      │      │
│        self.trainer.train(self.state, ...)          │      │      │
│    if self.mode in [Evaluate, TrainAndEvaluate]:    │      │      │
│        self.trainer.evaluate(self.state, ...)       │      │      │
│                                                      │      │      │
│    # ADVANCE ROUND                                   │      │      │
│    self.state.advance_round(...)                    │      │      │
│    self.rewards.reset()                             │      │      │
│    self._hook_after_round_advanced() ◄──────────┐   │      │      │
└─────────────────────────────────────────────────┼───┼──────┼──────┼─┘
                                                  │   │      │      │
                         ┌────────────────────────┘   │      │      │
                         │  ┌─────────────────────────┘      │      │
                         │  │  ┌──────────────────────────────┘      │
                         │  │  │  ┌───────────────────────────────────┘
                         │  │  │  │
                         ▼  ▼  ▼  ▼
┌─────────────────────────────────────────────────────────────────────┐
│ 5. YOUR CODE: rgym_exp/src/manager.py::SwarmGameManager            │
│                                                                     │
│ ┌─────────────────────────────────────────────────────────────┐   │
│ │ _hook_after_rewards_updated() (line 181)                    │   │
│ │   signal_by_agent = self._get_total_rewards_by_agent()      │   │
│ │   self.batched_signals += self._get_my_rewards(...)         │   │
│ │   self._try_submit_to_chain(signal_by_agent)                │   │
│ │                                                              │   │
│ │   # PUBLISH ROLLOUTS TO GDRIVE                              │   │
│ │   if isinstance(self.communication, GDriveCommunicationBackend): │
│ │       local_rollouts = self.state.trees.get(self.peer_id, {})    │
│ │       if local_rollouts:                                     │   │
│ │           self.communication.publish_state(...)  ◄───────────────┼──┐
│ │           get_logger().debug("Published local rollouts...")  │   │  │
│ └─────────────────────────────────────────────────────────────┘   │  │
│                                                                     │  │
│ ┌─────────────────────────────────────────────────────────────┐   │  │
│ │ _hook_after_round_advanced() (line 204)                     │   │  │
│ │   self._save_to_hf()  # Push to HuggingFace                 │   │  │
│ │   self._try_submit_to_chain(...)  # Submit to blockchain    │   │  │
│ │                                                              │   │  │
│ │   # NOTIFY COMMUNICATION BACKEND                            │   │  │
│ │   if isinstance(self.communication, GDriveCommunicationBackend): │  │
│ │       self.communication.advance_round() ◄───────────────────────┼──┼──┐
│ │                                                              │   │  │  │
│ │   # BLOCK UNTIL SWARM ADVANCES                              │   │  │  │
│ │   self.agent_block() ◄───────────────────────────────────────────┼──┼──┼──┐
│ └─────────────────────────────────────────────────────────────┘   │  │  │  │
│                                                                     │  │  │  │
│ ┌─────────────────────────────────────────────────────────────┐   │  │  │  │
│ │ _hook_after_game() (line 222)                               │   │  │  │  │
│ │   self._save_to_hf()  # Final HuggingFace push              │   │  │  │  │
│ │   if checkpoint_interval > 0:                                │   │  │  │  │
│ │       self.gdrive_logger.log_checkpoint(...)                │   │  │  │  │
│ └─────────────────────────────────────────────────────────────┘   │  │  │  │
└─────────────────────────────────────────────────────────────────────┘  │  │  │
                                                                          │  │  │
                         ┌────────────────────────────────────────────────┘  │  │
                         │  ┌───────────────────────────────────────────────┘  │
                         │  │  ┌────────────────────────────────────────────────┘
                         ▼  ▼  ▼
┌─────────────────────────────────────────────────────────────────────┐
│ 6. GDRIVE BACKEND: rgym_exp/communication/gdrive_backend.py         │
│                                                                     │
│ ┌─────────────────────────────────────────────────────────────┐   │
│ │ publish_state() (line 121)                                  │   │
│ │   # Buffer rollouts in memory                               │   │
│ │   if self.publish_frequency == 'stage':                     │   │
│ │       self.rollout_sharing.buffer_stage_rollout(...)        │   │
│ │   elif self.publish_frequency == 'round':                   │   │
│ │       self.rollout_sharing.buffer_round_rollout(...)        │   │
│ └─────────────────────────────────────────────────────────────┘   │
│                                                                     │
│ ┌─────────────────────────────────────────────────────────────┐   │
│ │ advance_round() (line 208)                                  │   │
│ │   old_round = self.current_round                            │   │
│ │   old_stage = self.current_stage                            │   │
│ │                                                              │   │
│ │   # FLUSH BUFFERED ROLLOUTS TO DISK                         │   │
│ │   if old_round >= 0:                                        │   │
│ │       if self.publish_frequency == 'round':                 │   │
│ │           self.rollout_sharing.flush_buffer(node_id, old_round) ──┐
│ │       elif self.publish_frequency == 'stage':               │   │ │
│ │           self.rollout_sharing.flush_buffer(                │   │ │
│ │               node_id, old_round, old_stage) ───────────────────┼──┐
│ │                                                              │   │ │ │
│ │   self.current_round += 1                                   │   │ │ │
│ │   self.current_stage = 0                                    │   │ │ │
│ │   self.rollout_sharing.cleanup_old_rollouts(current_round)  │   │ │ │
│ └─────────────────────────────────────────────────────────────┘   │ │ │
└─────────────────────────────────────────────────────────────────────┘ │ │
                                                                        │ │
                         ┌──────────────────────────────────────────────┘ │
                         │  ┌───────────────────────────────────────────────┘
                         ▼  ▼
┌─────────────────────────────────────────────────────────────────────┐
│ 7. ROLLOUT SHARING: rgym_exp/src/gdrive_rollout_sharing.py         │
│                                                                     │
│ ┌─────────────────────────────────────────────────────────────┐   │
│ │ flush_buffer() (line 85)                                    │   │
│ │   # Write buffered rollouts to GDrive                       │   │
│ │   rollout_dir = gdrive_path/experiments/exp_name/rollouts/  │   │
│ │                 round_{round}/stage_{stage}/{node_id}/      │   │
│ │                                                              │   │
│ │   for batch_id, payloads in buffer.items():                 │   │
│ │       file = f"{rollout_dir}/batch_{batch_id}.json"         │   │
│ │       json.dump(payloads, file)  # Write to disk ◄────────────────┐
│ │                                                              │   │ │
│ │   buffer.clear()  # Clear memory buffer                     │   │ │
│ └─────────────────────────────────────────────────────────────┘   │ │
└─────────────────────────────────────────────────────────────────────┘ │
                                                                        │
                              WRITES TO GDRIVE                          │
                                     │                                  │
                                     ▼                                  │
┌─────────────────────────────────────────────────────────────────────┐ │
│ GOOGLE DRIVE FILE STRUCTURE                                         │ │
│                                                                     │ │
│ /content/drive/MyDrive/rl-swarm/                                   │ │
│   experiments/                                                      │ │
│     sapo_gpt2_config2_2loc2ext/                                    │ │
│       rollouts/                                                     │ │
│         round_0/                                                    │ │
│           stage_0/                                                  │ │
│             node_abc123/                                            │ │
│               batch_12345.json  ◄───────────────────────────────────┘
│               batch_67890.json                                      │
│             node_def456/                                            │
│               batch_12345.json                                      │
│         round_1/                                                    │
│           stage_0/                                                  │
│             node_abc123/                                            │
│               batch_98765.json                                      │
└─────────────────────────────────────────────────────────────────────┘
                                     │
                                     │ READS FROM GDRIVE
                                     ▼
┌─────────────────────────────────────────────────────────────────────┐
│ 8. DATA MANAGER: rgym_exp/src/data.py::ReasoningGymDataManager     │
│                                                                     │
│ ┌─────────────────────────────────────────────────────────────┐   │
│ │ prepare_states() (line 251)                                 │   │
│ │   # Called from GenRL's run_game_round() before each stage  │   │
│ │                                                              │   │
│ │   # FETCH SWARM ROLLOUTS FROM PREVIOUS ROUND                │   │
│ │   if swarm_states is None and self.communication is not None:   │
│ │       fetch_round = max(0, current_state.round - 1)  ◄────────────┐
│ │       if fetch_round >= 0 and current_state.round > 0:      │   │ │
│ │           swarm_states = self.communication.get_swarm_states(    │ │
│ │               round_num=fetch_round,  # ◄ FIX: Use round-1! │   │ │
│ │               stage=current_state.stage                      │   │ │
│ │           )                                                  │   │ │
│ │                                                              │   │ │
│ │   # TRANSPLANT EXTERNAL ROLLOUTS                            │   │ │
│ │   if self.num_transplant_trees > 0:  # J > 0               │   │ │
│ │       transplants = self.transplant_trees(                  │   │ │
│ │           current_state, swarm_states, num_transplant_trees │   │ │
│ │       )                                                      │   │ │
│ │       # Add external rollouts to local game trees           │   │ │
│ └─────────────────────────────────────────────────────────────┘   │ │
└─────────────────────────────────────────────────────────────────────┘ │
                                                                        │
                         ┌──────────────────────────────────────────────┘
                         ▼
┌─────────────────────────────────────────────────────────────────────┐
│ 9. GDRIVE BACKEND: gdrive_backend.py::get_swarm_states()           │
│                                                                     │
│ ┌─────────────────────────────────────────────────────────────┐   │
│ │ get_swarm_states() (line 167)                               │   │
│ │   # Read rollouts from GDrive for specified round           │   │
│ │   swarm_states = self.rollout_sharing.fetch_rollouts(       │   │
│ │       round_num=round_num,  # Uses round-1 from caller      │   │
│ │       stage=stage,                                          │   │
│ │       max_peers=self.fetch_max_peers  # Default 10          │   │
│ │   )                                                          │   │
│ │   return swarm_states  # Dict[peer_id -> rollouts]          │   │
│ └─────────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────┘
                                     │
                                     ▼
┌─────────────────────────────────────────────────────────────────────┐
│ 10. ROLLOUT SHARING: gdrive_rollout_sharing.py::fetch_rollouts()   │
│                                                                     │
│ ┌─────────────────────────────────────────────────────────────┐   │
│ │ fetch_rollouts() (line 122)                                 │   │
│ │   rollout_dir = gdrive_path/experiments/exp_name/rollouts/  │   │
│ │                 round_{round_num}/stage_{stage}/            │   │
│ │                                                              │   │
│ │   # Read from all peer directories                          │   │
│ │   for peer_dir in os.listdir(rollout_dir):                  │   │
│ │       if peer_dir == current_node_id:                       │   │
│ │           continue  # Skip self                             │   │
│ │                                                              │   │
│ │       for json_file in glob(f"{peer_dir}/*.json"):          │   │
│ │           with open(json_file) as f:                        │   │
│ │               payload = json.load(f)                        │   │
│ │               rollouts[peer_id][batch_id].append(payload)   │   │
│ │                                                              │   │
│ │   return rollouts  # External rollouts from other nodes     │   │
│ └─────────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────┘
                                     │
                                     │ Returns to data.py
                                     ▼
┌─────────────────────────────────────────────────────────────────────┐
│ TRAINING: Now has I local + J external rollouts                    │
│                                                                     │
│ Example for Config2 (I=2, J=2):                                    │
│   - 2 local rollouts (from this node's generation)                 │
│   - 2 external rollouts (fetched from other nodes' round-1)        │
│   - Total: 4 rollouts for training                                 │
│                                                                     │
│ GenRL calls: trainer.train(state, data_manager, rewards)           │
│   → GRPOTrainerModule computes policy gradients on all rollouts    │
│   → Updates model weights                                          │
│   → Publishes new rollouts for next round                          │
└─────────────────────────────────────────────────────────────────────┘
```

## Detailed Component Descriptions

### 1. Notebook Entry Point
Notebooks like `EX12.14a.SAPO_gpt2_Baseline_4loc0ext.ipynb` set up the environment:
- Mount Google Drive
- Set environment variables (GDRIVE_PATH, EXPERIMENT_NAME, NODE_ROLE, NODE_ID, etc.)
- Install dependencies (gensyn-genrl==0.1.9)
- Launch training via `python -m rgym_exp.runner.swarm_launcher`

### 2. Launcher (`swarm_launcher.py`)
Main entry point that instantiates all components:
- Reads environment variables
- Sets up logging and progress tracking
- Creates communication backend (GDriveCommunicationBackend)
- Loads model and creates trainer (GRPOTrainerModule)
- Creates data manager (ReasoningGymDataManager)
- Creates coordinator (GDriveSwarmCoordinator)
- Creates game manager (SwarmGameManager)
- Calls `game_manager.run_game()` to start training

### 3. GenRL BaseGameManager.run_game()
Main training loop from GenRL library:
```python
def run_game(self):
    self.state._init_game(...)
    try:
        while not self.end_of_game():  # Loop until max_round
            self.run_game_round()
    except:
        get_logger().exception(...)
    finally:
        self._hook_after_game()  # ← Hook call
        self.trainer.cleanup()
```

### 4. GenRL BaseGameManager.run_game_round()
Per-round execution from GenRL library:
```python
def run_game_round(self):
    # STAGE LOOP
    while not self.end_of_round():
        self.run_game_stage()
        swarm_payloads = self.communication.all_gather_object(...)
        world_states = self.data_manager.prepare_states(...)
        self.state.advance_stage(world_states)

    # REWARDS & TRAINING
    self.rewards.update_rewards(self.state)
    self._hook_after_rewards_updated()  # ← Hook call

    self.trainer.train(self.state, self.data_manager, self.rewards)

    # ADVANCE ROUND
    self.state.advance_round(...)
    self.rewards.reset()
    self._hook_after_round_advanced()  # ← Hook call
```

### 5. SwarmGameManager Hooks (Your Code)
Three hooks override GenRL's base implementation:

**`_hook_after_rewards_updated()` (line 181)**:
- Calculates reward signals by agent
- Submits rewards to blockchain (if coordinator configured)
- **Publishes local rollouts to GDrive** via `communication.publish_state()`

**`_hook_after_round_advanced()` (line 204)**:
- Saves model to HuggingFace
- Submits final rewards to blockchain
- **Notifies communication backend** via `communication.advance_round()` (flushes rollouts)
- **Blocks until swarm advances** via `agent_block()` (polls coordinator)

**`_hook_after_game()` (line 222)**:
- Final HuggingFace save
- Saves checkpoint to GDrive (if CHECKPOINT_INTERVAL > 0)

### 6. GDriveCommunicationBackend
Implements GenRL's Communication interface for GDrive-based sharing:

**`publish_state()` (line 121)**:
- Buffers rollouts in memory (doesn't write immediately)
- Waits for flush signal

**`advance_round()` (line 208)**:
- **Flushes buffered rollouts to disk** based on publish_frequency
- Increments round counter
- Triggers cleanup of old rollouts
- Invalidates cache

### 7. GDriveRolloutSharing
Handles actual file I/O for rollouts:

**`flush_buffer()` (line 85)**:
- Creates directory structure: `{gdrive_path}/experiments/{exp_name}/rollouts/round_{R}/stage_{S}/{node_id}/`
- Writes each batch as separate JSON file: `batch_{batch_id}.json`
- Clears memory buffer

### 8. ReasoningGymDataManager
Manages dataset and rollout transplanting:

**`prepare_states()` (line 251)** - **THE CRITICAL FIX**:
```python
# OLD (BROKEN): fetch_round = current_state.round
# NEW (FIXED):  fetch_round = max(0, current_state.round - 1)
```
- Fetches rollouts from **previous round** (round-1)
- Handles round 0 edge case (can't fetch from round -1)
- Transplants J external rollouts into local game trees
- Returns combined state for training

**Why the fix was needed**:
- Round 0: Train → publish to `/rollouts/round_0/`
- Round 1 starts: Old code tried to fetch from `/rollouts/round_1/` (doesn't exist!)
- New code fetches from `/rollouts/round_0/` (exists!)

### 9. GDriveCommunicationBackend.get_swarm_states()
Bridge between data manager and rollout sharing:

**`get_swarm_states()` (line 167)**:
- Receives `round_num` from data manager (now round-1)
- Calls rollout_sharing.fetch_rollouts()
- Returns Dict[peer_id -> Dict[batch_id -> List[Payload]]]

### 10. GDriveRolloutSharing.fetch_rollouts()
Reads rollouts from disk:

**`fetch_rollouts()` (line 122)**:
- Lists all peer directories in `/rollouts/round_{R}/stage_{S}/`
- Skips current node's directory (no self-training)
- Reads all JSON files from each peer
- Parses and returns rollouts
- Respects `max_peers` limit (default 10)

## Key Timing Sequence

### Round 0
1. Generate I local rollouts
2. Hook: Buffer rollouts
3. Hook: Flush to `/rollouts/round_0/stage_0/{node_id}/`
4. No external rollouts (round 0 has no previous round)
5. Train on I local rollouts only

### Round 1
1. Generate I local rollouts
2. Fetch from `/rollouts/round_0/stage_0/` (previous round)
3. Transplant J external rollouts
4. Train on I local + J external = I+J total rollouts
5. Hook: Flush new rollouts to `/rollouts/round_1/stage_0/{node_id}/`

### Round 2+
Same as Round 1, fetching from previous round

## Configuration Impact

### I (num_train_samples) - Local Rollouts
Number of questions sampled for local generation each round.

### J (num_transplant_trees) - External Rollouts
Number of external rollouts fetched from other nodes.

### Example Configs
- **Baseline (I=4, J=0)**: 4 local, 0 external = 4 total (no collaboration)
- **Config1 (I=3, J=1)**: 3 local, 1 external = 4 total
- **Config2 (I=2, J=2)**: 2 local, 2 external = 4 total
- **Config3 (I=1, J=3)**: 1 local, 3 external = 4 total (maximum collaboration)

## Critical Fixes Timeline

### Commit `20d9435` - Stage Buffer Flushing
**Problem**: With `ROLLOUT_PUBLISH_FREQUENCY='stage'`, rollouts buffered but never flushed.
**Fix**: Modified `advance_round()` to flush stage buffers.

### Commit `510c0de` - Hook Integration
**Problem**: `publish_state()` and `get_swarm_states()` methods existed but never called.
**Fix**:
- Wired `publish_state()` call into `_hook_after_rewards_updated()`
- Wired `get_swarm_states()` call into `prepare_states()`
- Passed communication backend to data_manager

### Commit `724106c` - Round Mismatch Fix (CRITICAL)
**Problem**: Fetching rollouts from current round, but they're published in previous round.
**Fix**: Changed `prepare_states()` to fetch from `round-1` instead of `round`.

This final fix enables proper swarm collaboration by ensuring nodes can actually find each other's rollouts.

## Verification

To verify the system is working, check logs for:

### Round 0
- ✅ `"Round 0: No previous rollouts to fetch"`
- ✅ `"Published local rollouts: round=0, stage=0, batches=N"`

### Round 1+
- ✅ `"Fetched swarm states from round N: X peers"`
- ✅ `"Published local rollouts: round=N, stage=0, batches=M"`
- ✅ Metrics show `total_agents: 5` (not 1)

### GDrive Structure
```
/content/drive/MyDrive/rl-swarm/experiments/{experiment_name}/
├── rollouts/
│   ├── round_0/
│   │   └── stage_0/
│   │       ├── node_abc123/
│   │       │   ├── batch_12345.json
│   │       │   └── batch_67890.json
│   │       ├── node_def456/
│   │       └── node_ghi789/
│   └── round_1/
│       └── stage_0/
│           ├── node_abc123/
│           ├── node_def456/
│           └── node_ghi789/
└── logs/
    ├── node_abc123/
    └── node_def456/
```

## Summary

The execution flow demonstrates a **Template Method pattern** where:
1. GenRL provides the algorithm skeleton (`run_game()`, `run_game_round()`)
2. GenRL calls hooks at specific points (`_hook_after_rewards_updated()`, etc.)
3. Your code (SwarmGameManager) overrides hooks with custom behavior (GDrive publishing)
4. Communication backend handles buffering and flushing
5. Data manager fetches from previous round (the critical fix!)

The system achieves decentralized collaborative learning without P2P networking by using Google Drive as a shared filesystem for rollout exchange.
