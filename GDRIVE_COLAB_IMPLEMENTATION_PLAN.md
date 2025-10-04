# Google Drive + Colab Implementation Plan
**RL Swarm without Blockchain, Docker, or Login**

---

## 📊 Implementation Status

**Last Updated:** In Progress
**Completed:** 5/10 core files (50%)
**Status:** Phase 1 & 2 Complete ✅

---

## Files to Create and Modify

### Files to CREATE (8 new files)

| File Path | Purpose | Status | Why |
|-----------|---------|--------|-----|
| `rgym_exp/src/gdrive_coordinator.py` | Google Drive-based coordinator | ✅ **DONE** | Replace blockchain coordinator with file-based coordination |
| `rgym_exp/src/gdrive_logger.py` | Enhanced logging to Google Drive | ✅ **DONE** | Persist all logs, metrics, checkpoints to GDrive |
| `rgym_exp/src/gdrive_discovery.py` | Peer discovery via Google Drive | ✅ **DONE** | Enable nodes to find each other without hardcoded bootnodes |
| `rgym_exp/utils/experiment_manager.py` | Experiment management utilities | ✅ **DONE** | Initialize, list, and manage multiple experiments |
| `rgym_exp/runner/coordinator_node.py` | Coordinator manager daemon | ✅ **DONE** | Manage round/stage progression on coordinator node |
| `rgym_exp/config/colab-gdrive.yaml` | Colab-specific configuration | 🔲 Pending | Remove blockchain config, add GDrive paths |
| `notebooks/colab_coordinator.ipynb` | Coordinator Colab notebook | 🔲 Pending | Setup and run coordinator node in Colab |
| `notebooks/colab_worker.ipynb` | Worker Colab notebook | 🔲 Pending | Setup and run worker nodes in Colab |

### Files to MODIFY (2 existing files)

| File Path | Changes | Status | Why |
|-----------|---------|--------|-----|
| `rgym_exp/src/manager.py` | Make coordinator optional, add GDrive checkpoint/logging | 🔲 Pending | Support running without blockchain, enable checkpoint resume |
| `rgym_exp/runner/swarm_launcher.py` | Add GDrive mode flag, skip modal-login | 🔲 Pending | Enable launching without authentication |

---

## Detailed Implementation Plan

## Part 1: Core Google Drive Coordinator ✅ COMPLETE

### 1.1 Create `rgym_exp/src/gdrive_coordinator.py` ✅ IMPLEMENTED

**Purpose:** Replace blockchain-based `SwarmCoordinator` with file-based coordination using Google Drive.

**Implementation Status:** ✅ Complete - File created with full functionality

**Key Classes:**

```python
class GDriveSwarmCoordinator:
    """
    File-based coordinator that uses Google Drive for state management.
    Implements same interface as SwarmCoordinator for compatibility.
    """

    def __init__(self, gdrive_path, node_role='worker', round_check_interval=30):
        """
        Args:
            gdrive_path: Base path in Google Drive (e.g., /content/drive/MyDrive/rl-swarm/experiments/exp1)
            node_role: 'coordinator' or 'worker'
            round_check_interval: Seconds between state checks
        """
        self.gdrive_path = gdrive_path
        self.node_role = node_role
        self.round_check_interval = round_check_interval

        # Initialize directory structure
        self._init_directories()

    def _init_directories(self):
        """Create necessary directories in Google Drive"""
        dirs = ['state', 'peers', 'rewards', 'winners', 'checkpoints', 'logs']
        for d in dirs:
            os.makedirs(f"{self.gdrive_path}/{d}", exist_ok=True)

    def register_peer(self, peer_id):
        """Register peer to Google Drive"""
        peer_file = f"{self.gdrive_path}/peers/{peer_id}.json"
        data = {
            "peer_id": peer_id,
            "registered_at": time.time(),
            "node_role": self.node_role
        }
        self._write_json_with_retry(peer_file, data)
        logger.info(f"Registered peer {peer_id} to Google Drive")

    def get_round_and_stage(self):
        """Read current round and stage from Google Drive state file"""
        state_file = f"{self.gdrive_path}/state/current_state.json"
        state = self._read_json_with_retry(state_file)
        return state.get('round', 0), state.get('stage', 0)

    def submit_reward(self, round_num, stage_num, reward, peer_id):
        """Submit reward to Google Drive"""
        reward_dir = f"{self.gdrive_path}/rewards/round_{round_num}/stage_{stage_num}"
        os.makedirs(reward_dir, exist_ok=True)
        reward_file = f"{reward_dir}/{peer_id}.json"
        data = {
            "round": round_num,
            "stage": stage_num,
            "reward": reward,
            "peer_id": peer_id,
            "submitted_at": time.time()
        }
        self._write_json_with_retry(reward_file, data)

    def submit_winners(self, round_num, winners, peer_id):
        """Submit winner votes to Google Drive"""
        winner_dir = f"{self.gdrive_path}/winners/round_{round_num}"
        os.makedirs(winner_dir, exist_ok=True)
        winner_file = f"{winner_dir}/{peer_id}.json"
        data = {
            "round": round_num,
            "winners": winners,
            "peer_id": peer_id,
            "submitted_at": time.time()
        }
        self._write_json_with_retry(winner_file, data)

    def update_round_stage(self, new_round, new_stage):
        """
        Update global round/stage (coordinator only)
        Uses atomic write with temp file + rename
        """
        if self.node_role != 'coordinator':
            raise ValueError("Only coordinator can update round/stage")

        state_file = f"{self.gdrive_path}/state/current_state.json"
        temp_file = f"{state_file}.tmp"

        data = {
            "round": new_round,
            "stage": new_stage,
            "updated_at": time.time(),
            "updated_by": "coordinator"
        }

        # Atomic write: write to temp, then rename
        self._write_json_with_retry(temp_file, data)
        os.replace(temp_file, state_file)
        logger.info(f"Updated round={new_round}, stage={new_stage}")

    def _read_json_with_retry(self, filepath, max_retries=3):
        """Read JSON file with retry logic for GDrive API limits"""
        for attempt in range(max_retries):
            try:
                if not os.path.exists(filepath):
                    return {}
                with open(filepath, 'r') as f:
                    return json.load(f)
            except (json.JSONDecodeError, FileNotFoundError) as e:
                if attempt == max_retries - 1:
                    logger.error(f"Failed to read {filepath}: {e}")
                    return {}
                time.sleep(2 ** attempt)  # Exponential backoff
        return {}

    def _write_json_with_retry(self, filepath, data, max_retries=3):
        """Write JSON file with retry logic for GDrive API limits"""
        for attempt in range(max_retries):
            try:
                with open(filepath, 'w') as f:
                    json.dump(data, f, indent=2)
                return
            except Exception as e:
                if attempt == max_retries - 1:
                    logger.error(f"Failed to write {filepath}: {e}")
                    raise
                time.sleep(2 ** attempt)  # Exponential backoff
```

**Why this file:**
- Provides drop-in replacement for blockchain coordinator
- Implements same interface (`register_peer`, `get_round_and_stage`, etc.)
- Handles Google Drive API rate limits with retry logic
- Supports both coordinator and worker roles

---

### 1.2 Create `rgym_exp/runner/coordinator_node.py` ✅ IMPLEMENTED

**Purpose:** Manages round/stage progression on the coordinator node.

**Implementation Status:** ✅ Complete - File created with multiple advancement strategies

**Key Classes:**

```python
class CoordinatorManager:
    """
    Manages round progression for the coordinator node.
    Monitors worker submissions and advances rounds based on criteria.
    """

    def __init__(self, coordinator, config):
        self.coordinator = coordinator
        self.advancement_strategy = config.get('advancement_strategy', 'time_based')
        self.round_duration_minutes = config.get('round_duration_minutes', 10)
        self.min_submission_percent = config.get('min_submission_percent', 0.5)

        self.current_round = 0
        self.current_stage = 0
        self.round_start_time = time.time()

    def run(self):
        """Main loop for coordinator"""
        logger.info("Starting Coordinator Manager")

        while True:
            try:
                # Check if round should advance
                if self._should_advance_round():
                    self._advance_round()

                # Sleep before next check
                time.sleep(30)

            except KeyboardInterrupt:
                logger.info("Coordinator Manager stopped by user")
                break
            except Exception as e:
                logger.error(f"Error in coordinator loop: {e}")
                time.sleep(60)

    def _should_advance_round(self):
        """Determine if round should advance"""
        if self.advancement_strategy == 'time_based':
            elapsed_minutes = (time.time() - self.round_start_time) / 60
            return elapsed_minutes >= self.round_duration_minutes

        elif self.advancement_strategy == 'completion_based':
            submission_rate = self._get_submission_rate()
            return submission_rate >= self.min_submission_percent

        elif self.advancement_strategy == 'hybrid':
            elapsed_minutes = (time.time() - self.round_start_time) / 60
            submission_rate = self._get_submission_rate()

            # Advance if both conditions met OR max time exceeded
            min_met = submission_rate >= self.min_submission_percent
            time_met = elapsed_minutes >= self.round_duration_minutes
            max_time = elapsed_minutes >= self.round_duration_minutes * 2

            return (min_met and time_met) or max_time

        return False

    def _get_submission_rate(self):
        """Calculate percentage of active peers that submitted"""
        peers_dir = f"{self.coordinator.gdrive_path}/peers"
        rewards_dir = f"{self.coordinator.gdrive_path}/rewards/round_{self.current_round}/stage_{self.current_stage}"

        # Count active peers
        try:
            active_peers = len([f for f in os.listdir(peers_dir) if f.endswith('.json')])
            if active_peers == 0:
                return 0.0

            # Count submissions
            if not os.path.exists(rewards_dir):
                return 0.0
            submissions = len([f for f in os.listdir(rewards_dir) if f.endswith('.json')])

            return submissions / active_peers
        except Exception as e:
            logger.error(f"Error calculating submission rate: {e}")
            return 0.0

    def _advance_round(self):
        """Advance to next round"""
        self.current_round += 1
        self.current_stage = 0
        self.round_start_time = time.time()

        # Update state in Google Drive
        self.coordinator.update_round_stage(self.current_round, self.current_stage)

        logger.info(f"Advanced to round {self.current_round}")


def main():
    """Entry point for coordinator node"""
    import hydra
    from omegaconf import DictConfig
    from hydra.utils import instantiate

    @hydra.main(version_base=None, config_path="../config", config_name="colab-gdrive.yaml")
    def run_coordinator(cfg: DictConfig):
        # Create coordinator
        coordinator = instantiate(cfg.game_manager.coordinator)

        # Create and run manager
        manager = CoordinatorManager(coordinator, cfg.coordinator_manager)
        manager.run()

    run_coordinator()


if __name__ == "__main__":
    main()
```

**Why this file:**
- Automates round progression without manual intervention
- Supports multiple advancement strategies (time-based, completion-based, hybrid)
- Monitors worker activity via Google Drive files
- Runs independently from training process

---

## Part 2: Enhanced Logging and Metrics ✅ COMPLETE

### 2.1 Create `rgym_exp/src/gdrive_logger.py` ✅ IMPLEMENTED

**Purpose:** Comprehensive logging to Google Drive for persistence and multi-experiment tracking.

**Implementation Status:** ✅ Complete - Full logging, checkpointing, and wandb sync

```python
class GDriveLogger:
    """
    Handles all logging to Google Drive including:
    - Training metrics (JSONL format)
    - Checkpoints
    - Training events
    - Wandb sync
    """

    def __init__(self, gdrive_log_path, node_id, experiment_name):
        """
        Args:
            gdrive_log_path: Path to experiment logs (e.g., /drive/.../experiments/exp1/logs/worker_1/)
            node_id: Unique node identifier (e.g., 'worker_1')
            experiment_name: Name of experiment
        """
        self.gdrive_log_path = gdrive_log_path
        self.node_id = node_id
        self.experiment_name = experiment_name

        os.makedirs(gdrive_log_path, exist_ok=True)

        self.metrics_file = f"{gdrive_log_path}/metrics.jsonl"
        self.events_file = f"{gdrive_log_path}/training_events.jsonl"
        self.checkpoint_dir = f"{gdrive_log_path}/../checkpoints"

    def log_metrics(self, round_num, stage_num, metrics_dict):
        """
        Log metrics in JSONL format (newline-delimited JSON)
        Allows streaming aggregation and analysis
        """
        entry = {
            "timestamp": time.time(),
            "round": round_num,
            "stage": stage_num,
            "node_id": self.node_id,
            "experiment": self.experiment_name,
            **metrics_dict
        }

        with open(self.metrics_file, 'a') as f:
            f.write(json.dumps(entry) + '\n')

    def log_checkpoint(self, round_num, model, optimizer=None):
        """Save model checkpoint to Google Drive"""
        checkpoint_round_dir = f"{self.checkpoint_dir}/round_{round_num}"
        os.makedirs(checkpoint_round_dir, exist_ok=True)

        checkpoint_path = f"{checkpoint_round_dir}/{self.node_id}.pt"

        checkpoint = {
            "round": round_num,
            "node_id": self.node_id,
            "model_state_dict": model.state_dict(),
            "timestamp": time.time()
        }

        if optimizer:
            checkpoint["optimizer_state_dict"] = optimizer.state_dict()

        torch.save(checkpoint, checkpoint_path)
        logger.info(f"Saved checkpoint to {checkpoint_path}")

    def load_checkpoint(self, round_num, model, optimizer=None):
        """Load checkpoint from Google Drive"""
        checkpoint_path = f"{self.checkpoint_dir}/round_{round_num}/{self.node_id}.pt"

        if not os.path.exists(checkpoint_path):
            logger.warning(f"No checkpoint found at {checkpoint_path}")
            return None

        checkpoint = torch.load(checkpoint_path)
        model.load_state_dict(checkpoint["model_state_dict"])

        if optimizer and "optimizer_state_dict" in checkpoint:
            optimizer.load_state_dict(checkpoint["optimizer_state_dict"])

        logger.info(f"Loaded checkpoint from round {round_num}")
        return checkpoint

    def log_event(self, event_type, data):
        """Log training events (errors, warnings, state changes)"""
        entry = {
            "timestamp": time.time(),
            "event_type": event_type,
            "node_id": self.node_id,
            "data": data
        }

        with open(self.events_file, 'a') as f:
            f.write(json.dumps(entry) + '\n')

    def sync_wandb_to_gdrive(self, wandb_dir):
        """
        Copy wandb logs to Google Drive for persistence
        (Colab sessions are temporary)
        """
        if not os.path.exists(wandb_dir):
            return

        wandb_backup_dir = f"{self.gdrive_log_path}/wandb"
        shutil.copytree(wandb_dir, wandb_backup_dir, dirs_exist_ok=True)
        logger.info(f"Synced wandb logs to {wandb_backup_dir}")
```

**Why this file:**
- Persists all training data to Google Drive (Colab sessions are temporary)
- JSONL format allows streaming analysis and aggregation
- Checkpoint saving/loading enables experiment resumption
- Wandb sync ensures metrics survive Colab disconnects

---

### 2.2 Create `rgym_exp/src/gdrive_discovery.py` ✅ IMPLEMENTED

**Purpose:** Enable peer discovery without hardcoded bootnodes.

**Implementation Status:** ✅ Complete - Dynamic peer discovery with heartbeat mechanism

```python
class GDrivePeerDiscovery:
    """
    Peer discovery mechanism using Google Drive.
    Nodes publish their multiaddrs to shared directory.
    """

    def __init__(self, discovery_path, stale_threshold_seconds=3600):
        """
        Args:
            discovery_path: Path to discovery directory in Google Drive
            stale_threshold_seconds: Time before entry considered stale (default 1 hour)
        """
        self.discovery_path = discovery_path
        self.stale_threshold = stale_threshold_seconds
        os.makedirs(discovery_path, exist_ok=True)

    def publish_multiaddr(self, peer_id, multiaddr, node_role='worker'):
        """Publish this node's multiaddr for others to discover"""
        discovery_file = f"{self.discovery_path}/{peer_id}.json"
        data = {
            "peer_id": peer_id,
            "multiaddr": multiaddr,
            "node_role": node_role,
            "published_at": time.time(),
            "last_heartbeat": time.time()
        }

        with open(discovery_file, 'w') as f:
            json.dump(data, f, indent=2)

    def update_heartbeat(self, peer_id):
        """Update heartbeat timestamp to show node is still alive"""
        discovery_file = f"{self.discovery_path}/{peer_id}.json"

        if not os.path.exists(discovery_file):
            return

        with open(discovery_file, 'r') as f:
            data = json.load(f)

        data['last_heartbeat'] = time.time()

        with open(discovery_file, 'w') as f:
            json.dump(data, f, indent=2)

    def discover_peers(self, exclude_self=None, max_peers=10):
        """
        Discover active peers from Google Drive

        Returns:
            List of multiaddrs from active peers
        """
        peers = []
        current_time = time.time()

        try:
            for filename in os.listdir(self.discovery_path):
                if not filename.endswith('.json'):
                    continue

                filepath = f"{self.discovery_path}/{filename}"

                with open(filepath, 'r') as f:
                    data = json.load(f)

                # Skip self
                if exclude_self and data['peer_id'] == exclude_self:
                    continue

                # Skip stale entries
                if current_time - data.get('last_heartbeat', 0) > self.stale_threshold:
                    logger.debug(f"Skipping stale peer: {data['peer_id']}")
                    continue

                peers.append(data['multiaddr'])

                if len(peers) >= max_peers:
                    break

        except Exception as e:
            logger.error(f"Error discovering peers: {e}")

        return peers

    def cleanup_stale_entries(self):
        """Remove stale discovery entries (optional maintenance)"""
        current_time = time.time()

        for filename in os.listdir(self.discovery_path):
            if not filename.endswith('.json'):
                continue

            filepath = f"{self.discovery_path}/{filename}"

            try:
                with open(filepath, 'r') as f:
                    data = json.load(f)

                if current_time - data.get('last_heartbeat', 0) > self.stale_threshold:
                    os.remove(filepath)
                    logger.info(f"Removed stale discovery entry: {filename}")

            except Exception as e:
                logger.error(f"Error cleaning {filename}: {e}")
```

**Why this file:**
- Eliminates need for hardcoded bootnode addresses
- Nodes can dynamically discover each other
- Heartbeat mechanism filters out dead nodes
- Supports dynamic scaling (add/remove nodes)

---

## Part 3: Experiment Management ✅ COMPLETE

### 3.1 Create `rgym_exp/utils/experiment_manager.py` ✅ IMPLEMENTED

**Purpose:** Utilities for managing multiple experiments.

**Implementation Status:** ✅ Complete - Full experiment lifecycle management

```python
def init_experiment(gdrive_base_path, experiment_name, config_overrides=None):
    """
    Initialize a new experiment in Google Drive

    Args:
        gdrive_base_path: Base path (e.g., /content/drive/MyDrive/rl-swarm)
        experiment_name: Unique experiment identifier
        config_overrides: Dict of config overrides (e.g., {'training.seed': 42})

    Returns:
        Experiment path
    """
    exp_path = f"{gdrive_base_path}/experiments/{experiment_name}"

    # Create directory structure
    directories = [
        'state',
        'peers',
        'rewards',
        'winners',
        'checkpoints',
        'logs'
    ]

    for d in directories:
        os.makedirs(f"{exp_path}/{d}", exist_ok=True)

    # Initialize state
    state = {
        "round": 0,
        "stage": 0,
        "created_at": time.time(),
        "experiment_name": experiment_name,
        "config_overrides": config_overrides or {}
    }

    state_file = f"{exp_path}/state/current_state.json"
    with open(state_file, 'w') as f:
        json.dump(state, f, indent=2)

    # Save config overrides
    if config_overrides:
        config_file = f"{exp_path}/config.yaml"
        with open(config_file, 'w') as f:
            yaml.dump(config_overrides, f)

    logger.info(f"Initialized experiment: {experiment_name} at {exp_path}")
    return exp_path


def list_experiments(gdrive_base_path):
    """
    List all experiments with metadata

    Returns:
        List of dicts with experiment info
    """
    experiments_dir = f"{gdrive_base_path}/experiments"

    if not os.path.exists(experiments_dir):
        return []

    experiments = []

    for exp_name in os.listdir(experiments_dir):
        exp_path = f"{experiments_dir}/{exp_name}"

        if not os.path.isdir(exp_path):
            continue

        state_file = f"{exp_path}/state/current_state.json"

        if not os.path.exists(state_file):
            continue

        with open(state_file, 'r') as f:
            state = json.load(f)

        # Count active peers
        peers_dir = f"{exp_path}/peers"
        num_peers = len([f for f in os.listdir(peers_dir) if f.endswith('.json')]) if os.path.exists(peers_dir) else 0

        experiments.append({
            "name": exp_name,
            "path": exp_path,
            "round": state.get('round', 0),
            "stage": state.get('stage', 0),
            "created_at": state.get('created_at'),
            "num_peers": num_peers
        })

    return experiments


def get_experiment_metrics(gdrive_base_path, experiment_name):
    """
    Aggregate metrics from all nodes in an experiment

    Returns:
        DataFrame with metrics from all nodes
    """
    import pandas as pd

    exp_path = f"{gdrive_base_path}/experiments/{experiment_name}"
    logs_dir = f"{exp_path}/logs"

    if not os.path.exists(logs_dir):
        return pd.DataFrame()

    all_metrics = []

    # Read metrics from each node
    for node_dir in os.listdir(logs_dir):
        metrics_file = f"{logs_dir}/{node_dir}/metrics.jsonl"

        if not os.path.exists(metrics_file):
            continue

        # Read JSONL file
        with open(metrics_file, 'r') as f:
            for line in f:
                try:
                    entry = json.loads(line)
                    all_metrics.append(entry)
                except json.JSONDecodeError:
                    continue

    return pd.DataFrame(all_metrics)


def export_experiment_summary(gdrive_base_path, experiment_name, output_path=None):
    """
    Export experiment summary including:
    - Config
    - Final metrics
    - Peer participation
    - Round progression
    """
    exp_path = f"{gdrive_base_path}/experiments/{experiment_name}"

    summary = {
        "experiment_name": experiment_name,
        "generated_at": time.time()
    }

    # Load state
    state_file = f"{exp_path}/state/current_state.json"
    if os.path.exists(state_file):
        with open(state_file, 'r') as f:
            summary['final_state'] = json.load(f)

    # Load config
    config_file = f"{exp_path}/config.yaml"
    if os.path.exists(config_file):
        with open(config_file, 'r') as f:
            summary['config'] = yaml.safe_load(f)

    # Aggregate metrics
    metrics_df = get_experiment_metrics(gdrive_base_path, experiment_name)
    if not metrics_df.empty:
        summary['metrics_summary'] = {
            "total_rounds": metrics_df['round'].max(),
            "total_entries": len(metrics_df),
            "nodes": metrics_df['node_id'].unique().tolist()
        }

    # Save summary
    if output_path is None:
        output_path = f"{exp_path}/summary.json"

    with open(output_path, 'w') as f:
        json.dump(summary, f, indent=2)

    return summary
```

**Why this file:**
- Simplifies multi-experiment workflow
- Provides utilities for experiment initialization, listing, analysis
- Enables experiment comparison and tracking
- Exports summaries for reporting

---

## Part 4: Configuration Files

### 4.1 Create `rgym_exp/config/colab-gdrive.yaml`

**Purpose:** Configuration specifically for Google Colab + Google Drive setup.

```yaml
# Google Drive Configuration
gdrive:
  base_path: ${oc.env:GDRIVE_PATH,/content/drive/MyDrive/rl-swarm}
  experiment_name: ${oc.env:EXPERIMENT_NAME,default_experiment}
  node_role: ${oc.env:NODE_ROLE,worker}  # 'coordinator' or 'worker'
  node_id: ${oc.env:NODE_ID,node_0}

# Logs go to Google Drive (persistent across Colab sessions)
log_dir: ${gdrive.base_path}/experiments/${gdrive.experiment_name}/logs/${gdrive.node_id}

# Hydra configuration
hydra:
  run:
    dir: ${log_dir}
  job_logging:
    handlers:
      console:
        level: INFO
    root:
      level: DEBUG

# Training configuration
training:
  max_round: 1000000
  max_stage: 1
  num_generations: 2
  num_transplant_trees: 2
  seed: ${oc.env:SEED,42}
  dtype: 'float32'
  checkpoint_frequency: 10  # Save checkpoint every N rounds

# Evaluation configuration
eval:
  judge_base_url: "https://swarm-judge.internal-apps-central1.clusters.gensyn.ai"

# Communication configuration (Hivemind P2P)
communications:
  use_gdrive_discovery: true
  discovery_path: ${gdrive.base_path}/discovery
  initial_peers: []  # Will be discovered via Google Drive

# Coordinator Manager (for coordinator node only)
coordinator_manager:
  advancement_strategy: hybrid  # 'time_based', 'completion_based', or 'hybrid'
  round_duration_minutes: 10
  min_submission_percent: 0.5
  max_round_duration_minutes: 20

# Game Manager configuration
game_manager:
  _target_: rgym_exp.src.manager.SwarmGameManager
  max_stage: ${training.max_stage}
  max_round: ${training.max_round}
  log_dir: ${log_dir}
  hf_token: ${oc.env:HUGGINGFACE_ACCESS_TOKEN,null}
  hf_push_frequency: 20
  run_mode: "train_and_evaluate"
  bootnodes: ${communications.initial_peers}

  # Game state
  game_state:
    _target_: genrl.state.game_state.GameState
    round: 0
    stage: 0

  # Reward manager
  reward_manager:
    _target_: genrl.rewards.DefaultRewardManager
    reward_fn_store:
      _target_: genrl.rewards.reward_store.RewardFnStore
      max_rounds: ${training.max_round}
      reward_fn_stores:
        - _target_: genrl.rewards.reward_store.RoundRewardFnStore
          num_stages: ${training.max_stage}
          reward_fns:
            - _target_: rgym_exp.src.rewards.RGRewards

  # Trainer configuration
  trainer:
    _target_: rgym_exp.src.trainer.GRPOTrainerModule
    models:
      - _target_: transformers.AutoModelForCausalLM.from_pretrained
        pretrained_model_name_or_path: ${oc.env:MODEL_NAME,Gensyn/Qwen2.5-0.5B-Instruct}
    config:
      _target_: genrl.trainer.grpo_trainer.GRPOTrainerConfig
      dtype: ${training.dtype}
      epsilon: 0.2
      epsilon_high: 0.28
      num_generations: ${training.num_generations}
    log_with: wandb
    log_dir: ${log_dir}
    judge_base_url: ${eval.judge_base_url}

  # Data manager
  data_manager:
    _target_: rgym_exp.src.data.ReasoningGymDataManager
    yaml_config_path: "rgym_exp/src/datasets.yaml"
    num_train_samples: 2
    num_evaluation_samples: 0
    num_generations: ${training.num_generations}
    system_prompt_id: 'default'
    seed: ${training.seed}
    num_transplant_trees: ${training.num_transplant_trees}

  # Communication (Hivemind)
  communication:
    _target_: genrl.communication.hivemind.hivemind_backend.HivemindBackend
    initial_peers: ${communications.initial_peers}
    identity_path: ${oc.env:IDENTITY_PATH,/tmp/swarm.pem}
    startup_timeout: 120
    beam_size: 50

  # Google Drive Coordinator
  coordinator:
    _target_: rgym_exp.src.gdrive_coordinator.GDriveSwarmCoordinator
    gdrive_path: ${gdrive.base_path}/experiments/${gdrive.experiment_name}
    node_role: ${gdrive.node_role}
    round_check_interval: 30

# Model pools
default_large_model_pool:
  - nvidia/AceInstruct-1.5B
  - dnotitia/Smoothie-Qwen3-1.7B
  - Gensyn/Qwen2.5-1.5B-Instruct

default_small_model_pool:
  - Gensyn/Qwen2.5-0.5B-Instruct
  - Qwen/Qwen3-0.6B
```

**Why this file:**
- Removes all blockchain dependencies
- Configures Google Drive paths
- Sets up coordinator manager parameters
- Enables GDrive-based peer discovery
- Configures checkpoint frequency for Colab environment

---

## Part 5: Colab Notebooks

### 5.1 Create `notebooks/colab_coordinator.ipynb`

**Purpose:** Jupyter notebook for running coordinator node on Google Colab.

**(Content too long - see task list for structure)**

**Why this file:**
- Provides easy-to-use interface for Colab users
- Handles Google Drive mounting
- Installs all dependencies
- Sets up environment variables
- Starts coordinator manager and training

### 5.2 Create `notebooks/colab_worker.ipynb`

**Purpose:** Jupyter notebook for running worker nodes on Google Colab.

**(Content too long - see task list for structure)**

**Why this file:**
- Simplified worker setup (no coordinator manager)
- Can run multiple workers concurrently
- Same experiment connection via environment variables

---

## Part 6: Modifications to Existing Files

### 6.1 Modify `rgym_exp/src/manager.py`

**Changes needed:**

1. **Make coordinator optional** (lines 28, 65-68):
```python
def __init__(
    self,
    coordinator: SwarmCoordinator | None = None,  # Make optional
    ...
):
    ...

    # Register peer_id and get current round from the chain
    if coordinator is not None:
        self.coordinator = coordinator
        self.coordinator.register_peer(self.peer_id)
        round, _ = self.coordinator.get_round_and_stage()
        self.state.round = round
    else:
        self.coordinator = None
        self.state.round = 0
        logger.info("Running without coordinator (standalone mode)")
```

2. **Add GDrive logger integration** (line 60):
```python
from rgym_exp.src.gdrive_logger import GDriveLogger

# In __init__
self.gdrive_logger = None
if log_dir.startswith('/content/drive/'):
    self.gdrive_logger = GDriveLogger(
        gdrive_log_path=log_dir,
        node_id=os.environ.get('NODE_ID', 'unknown'),
        experiment_name=os.environ.get('EXPERIMENT_NAME', 'default')
    )
```

3. **Add checkpoint saving** (after line 185):
```python
def _hook_after_stage(self):
    super()._hook_after_stage()

    # Save checkpoint to Google Drive
    if self.gdrive_logger and self.state.round % 10 == 0:
        self.gdrive_logger.log_checkpoint(
            self.state.round,
            self.trainer.model,
            self.trainer.optimizer if hasattr(self.trainer, 'optimizer') else None
        )
```

4. **Add metrics logging** (in training loop):
```python
# After computing rewards/metrics
if self.gdrive_logger:
    metrics = {
        'rewards': signal_by_agent,
        'my_reward': my_signal,
        # ... other metrics
    }
    self.gdrive_logger.log_metrics(self.state.round, self.state.stage, metrics)
```

5. **Handle coordinator errors gracefully** (lines 120-140):
```python
def _try_submit_to_chain(self, signal_by_agent):
    if self.coordinator is None:
        return  # Skip if no coordinator

    elapsed_time_hours = (time.time() - self.time_since_submit) / 3600
    if elapsed_time_hours > self.submit_period:
        try:
            self.coordinator.submit_reward(...)
            self.coordinator.submit_winners(...)
            ...
        except Exception as e:
            logger.error(f"Failed to submit to coordinator: {e}")
            # Continue training even if submission fails
```

**Why these changes:**
- Enables running without blockchain coordinator
- Adds persistent checkpoint/logging to Google Drive
- Graceful degradation when coordinator unavailable
- Supports resumption from checkpoints

---

### 6.2 Modify `rgym_exp/runner/swarm_launcher.py`

**Changes needed:**

1. **Add GDrive mode detection** (line 17):
```python
@hydra.main(version_base=None)
def main(cfg: DictConfig):
    # Check if running in GDrive mode
    gdrive_mode = cfg.get('gdrive', {}).get('base_path') is not None

    if gdrive_mode:
        logger.info("Running in Google Drive mode (no blockchain)")

    is_master = False
    HivemindRendezvouz.init(is_master=is_master)

    # Initialize GDrive discovery if enabled
    if gdrive_mode and cfg.communications.use_gdrive_discovery:
        from rgym_exp.src.gdrive_discovery import GDrivePeerDiscovery
        discovery = GDrivePeerDiscovery(cfg.communications.discovery_path)

        # Discover peers and update config
        discovered_peers = discovery.discover_peers()
        if discovered_peers:
            cfg.communications.initial_peers = discovered_peers

    game_manager = instantiate(cfg.game_manager)
    game_manager.run_game()
```

**Why these changes:**
- Detects GDrive mode from config
- Skips blockchain/modal-login when in GDrive mode
- Enables peer discovery via Google Drive
- Maintains compatibility with original blockchain mode

---

## Google Drive Directory Structure

```
/content/drive/MyDrive/rl-swarm/
│
├── experiments/
│   ├── qwen_0.6b_seed42/                 # Experiment 1
│   │   ├── config.yaml                   # Experiment config
│   │   ├── state/
│   │   │   └── current_state.json        # {round: 5, stage: 0, updated_at: ...}
│   │   ├── peers/
│   │   │   ├── QmAbc123.json             # Peer 1 registration
│   │   │   ├── QmDef456.json             # Peer 2 registration
│   │   │   └── QmGhi789.json             # Peer 3 registration
│   │   ├── rewards/
│   │   │   ├── round_1/stage_0/
│   │   │   │   ├── QmAbc123.json
│   │   │   │   └── QmDef456.json
│   │   │   └── round_2/stage_0/
│   │   ├── winners/
│   │   │   ├── round_1/
│   │   │   │   ├── QmAbc123.json
│   │   │   │   └── QmDef456.json
│   │   │   └── round_2/
│   │   ├── checkpoints/
│   │   │   ├── round_10/
│   │   │   │   ├── coordinator_0.pt       # Coordinator checkpoint
│   │   │   │   ├── worker_1.pt            # Worker 1 checkpoint
│   │   │   │   └── worker_2.pt            # Worker 2 checkpoint
│   │   │   └── round_20/
│   │   ├── logs/
│   │   │   ├── coordinator_0/
│   │   │   │   ├── swarm.log              # Text logs
│   │   │   │   ├── metrics.jsonl          # Metrics (newline-delimited JSON)
│   │   │   │   ├── training_events.jsonl  # Events log
│   │   │   │   └── wandb/                 # Weights & Biases data
│   │   │   ├── worker_1/
│   │   │   │   ├── swarm.log
│   │   │   │   ├── metrics.jsonl
│   │   │   │   └── ...
│   │   │   └── worker_2/
│   │   └── summary.json                   # Experiment summary
│   │
│   ├── ace_1.5b_seed123/                  # Experiment 2 (different model/seed)
│   │   └── ...
│   │
│   └── custom_experiment/                 # Experiment 3
│       └── ...
│
├── discovery/                              # Peer discovery
│   ├── QmAbc123.json                      # {multiaddr: ..., last_heartbeat: ...}
│   ├── QmDef456.json
│   └── QmGhi789.json
│
├── coordinator.pem                         # Coordinator peer identity
├── worker_1.pem                            # Worker peer identities
├── worker_2.pem
└── worker_3.pem
```

---

## Summary

**Files to CREATE: 8**
1. `rgym_exp/src/gdrive_coordinator.py` - GDrive coordinator
2. `rgym_exp/src/gdrive_logger.py` - Enhanced logging
3. `rgym_exp/src/gdrive_discovery.py` - Peer discovery
4. `rgym_exp/utils/experiment_manager.py` - Experiment utilities
5. `rgym_exp/runner/coordinator_node.py` - Coordinator manager
6. `rgym_exp/config/colab-gdrive.yaml` - Colab configuration
7. `notebooks/colab_coordinator.ipynb` - Coordinator notebook
8. `notebooks/colab_worker.ipynb` - Worker notebook

**Files to MODIFY: 2**
1. `rgym_exp/src/manager.py` - Make coordinator optional, add checkpointing
2. `rgym_exp/runner/swarm_launcher.py` - Add GDrive mode support

**Total changes: 10 files**
