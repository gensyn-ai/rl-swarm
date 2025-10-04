# Implementation Plan: Remove Hivemind and Use Google Drive Only

**Date:** 2025-10-04
**Status:** Planning Phase
**Goal:** Replace Hivemind P2P communication with Google Drive file-based rollout sharing

---

## Executive Summary

This plan removes the Hivemind DHT (Distributed Hash Table) P2P communication layer and replaces it entirely with Google Drive file-based rollout sharing. This eliminates dependencies on libp2p, peer identity files, and external P2P servers while making the system simpler and more private.

### Current Architecture
- **Coordinator**: Google Drive (file-based state management) ✅ Already implemented
- **Communication**: Hivemind DHT (P2P rollout sharing via libp2p) ⬅ To be removed
- **Discovery**: Google Drive (publishes peer multiaddrs for P2P connections) ⬅ To be removed

### Target Architecture
- **Coordinator**: Google Drive (file-based state management) ✅ Already implemented
- **Communication**: Google Drive (file-based rollout sharing) ⬅ NEW
- **Discovery**: Not needed (no P2P connections required) ✅ Simplified

---

## Motivation

### Why Remove Hivemind?

**Current situation:**
- Hivemind requires peer identity (swarm.pem) for cryptographic authentication
- Requires libp2p networking stack (complex, firewall issues on Colab)
- Uses external DHT servers for peer discovery
- Not needed since we already use Google Drive for coordination

**Benefits of Google Drive-only approach:**
1. **Simplicity**: No networking stack, no crypto key management
2. **Privacy**: All data stays in user's Google Drive
3. **Debugging**: All rollouts visible as plain JSON files
4. **Colab-friendly**: No firewall/NAT traversal issues
5. **Consistency**: Everything uses same storage mechanism
6. **Flexibility**: Configurable rollout sharing frequency and retention

**Trade-offs:**
- **Slower**: Google Drive API has latency (1-5 seconds vs milliseconds for DHT)
- **Rate limits**: Drive API has quotas (15 QPM read, 10 QPM write)
- **Storage**: Uses more Drive storage (rollouts stored as files vs DHT references)

**Mitigation strategies:**
- Local caching to reduce Drive API calls
- Configurable publish frequency (generation/stage/round)
- Configurable retention policy (keep all, keep N rounds, archive)
- Automatic cleanup of old rollout files

---

## Technical Background

### What is SAPO?

The codebase implements SAPO (Swarm sAmpling Policy Optimization) from the research paper arXiv-2509.08721v1. The key algorithm components:

1. **Local Rollouts (I^n)**: Each node generates `num_generations` rollouts locally
2. **External Rollouts (J^n)**: Each node samples `num_transplant_trees` rollouts from other peers
3. **Training**: Combines local + external rollouts for GRPO training

### How Hivemind Currently Works

```python
# In manager.py - Training loop
self.communication.step_ = self.state.round

# Hivemind automatically:
# 1. Publishes local rollouts to DHT
# 2. Fetches peer rollouts from DHT
# 3. Returns as swarm_states dict

# In data.py - SAPO sampling
swarm_states = communication.get_swarm_states()  # From Hivemind DHT
transplants = self.transplant_trees(
    current_state,
    swarm_states,  # Contains rollouts from other peers
    num_transplants=self.num_transplant_trees  # J^n parameter
)
```

**Data format:**
```python
swarm_states = {
    "peer_id_1": {
        0: [payload1, payload2, ...],  # batch_id 0
        1: [payload3, payload4, ...],  # batch_id 1
    },
    "peer_id_2": {
        0: [payload5, payload6, ...],
    }
}
```

Each `payload` contains:
- `question`: The prompt from reasoning-gym
- `actions`: Model's generated text response
- `values`: (optional) value estimates
- Other metadata

### How Google Drive Will Work

```python
# In gdrive_backend.py - New communication backend
class GDriveCommunicationBackend(Communication):
    def publish_state(self, state_dict):
        # Write to: {experiment}/rollouts/round_X/stage_Y/{node_id}.json
        # Frequency configurable: per generation, stage, or round

    def get_swarm_states(self):
        # Read from: {experiment}/rollouts/round_X/stage_Y/*.json
        # Return same format as Hivemind for compatibility
```

**Key insight:** We just need to implement the same interface Hivemind provides, but use Google Drive files instead of DHT.

---

## Configuration Options

### Rollout Sharing Frequency

Users can configure **when** rollouts are published to Google Drive:

```yaml
# In colab-gdrive.yaml
communication:
  rollout_publish_frequency: 'stage'  # Options: 'generation', 'stage', 'round'
```

**Option 1: Per Generation (Most Frequent)**
- Publishes after each generation within a stage
- If `num_generations = 2`, publishes 2 times per stage
- **Pros:** Most up-to-date rollouts, fastest peer learning
- **Cons:** Most Drive API calls (may hit rate limits with many nodes)

**Option 2: Per Stage (Recommended Default)**
- Publishes once at the end of each stage
- Aggregates all generations from that stage
- **Pros:** Balanced API usage, still fresh rollouts
- **Cons:** Slightly less frequent updates than per-generation

**Option 3: Per Round**
- Publishes once at the end of each round
- Aggregates all stages from that round
- **Pros:** Minimal API calls, lowest rate limit risk
- **Cons:** Peers see older rollouts, slower convergence

### Rollout Retention Policy

Users can configure **how long** to keep rollout files:

```yaml
# In colab-gdrive.yaml
communication:
  rollout_retention:
    cleanup_enabled: true              # Enable automatic cleanup
    keep_last_n_rounds: 10             # Keep 10 most recent rounds
    archive_old_rollouts: false        # Archive instead of delete
    archive_path: ${gdrive.base_path}/archives/${experiment_name}/
```

**Option 1: Keep All Rollouts Forever**
```yaml
rollout_retention:
  cleanup_enabled: false
```
- **Pros:** Complete history for analysis, debugging, replay
- **Cons:** Storage grows indefinitely (~8 MB per 100 rounds with 4 nodes)
- **Use case:** Short experiments, research analysis, debugging

**Option 2: Keep Last N Rounds**
```yaml
rollout_retention:
  cleanup_enabled: true
  keep_last_n_rounds: 10
  archive_old_rollouts: false
```
- **Pros:** Bounded storage, keeps recent history
- **Cons:** Loses old rollouts permanently
- **Use case:** Long-running experiments, production training

**Option 3: Archive Old Rollouts**
```yaml
rollout_retention:
  cleanup_enabled: true
  keep_last_n_rounds: 5
  archive_old_rollouts: true
  archive_path: ${gdrive.base_path}/archives/${experiment_name}/
```
- **Pros:** Keep everything but organized, bounded active storage
- **Cons:** Uses more total storage
- **Use case:** Best of both worlds - cleanup active dir but keep history

**Option 4: Time-Based Retention**
```yaml
rollout_retention:
  cleanup_enabled: true
  keep_last_n_hours: 24  # Keep 24 hours of rollouts
```
- **Pros:** Time-based policy, intuitive
- **Cons:** Variable storage usage depending on training speed
- **Use case:** Time-bounded experiments

### Storage Implications

**Rollout size estimation:**
- Per rollout: ~1 KB (question + answer + metadata)
- Per stage: 10 rollouts × 4 nodes = 40 KB
- Per round: 2 stages × 40 KB = 80 KB
- 100 rounds: ~8 MB
- 1000 rounds: ~80 MB

**Google Drive free tier:** 15 GB
- Can store ~187,500 rounds worth of rollouts
- For most experiments, keeping all rollouts is feasible

**Recommended configurations:**

```yaml
# For development/debugging (keep everything)
communication:
  rollout_publish_frequency: 'stage'
  rollout_retention:
    cleanup_enabled: false

# For production/long experiments (cleanup with archive)
communication:
  rollout_publish_frequency: 'stage'
  rollout_retention:
    cleanup_enabled: true
    keep_last_n_rounds: 10
    archive_old_rollouts: true

# For resource-constrained (aggressive cleanup)
communication:
  rollout_publish_frequency: 'round'
  rollout_retention:
    cleanup_enabled: true
    keep_last_n_rounds: 3
    archive_old_rollouts: false
```

---

## Implementation Plan

### Phase 1: Core Communication Backend

#### Task 1.1: Create `rgym_exp/src/gdrive_rollout_sharing.py`

**Purpose:** Low-level file operations for rollout publishing/fetching

**Estimated time:** 3-4 hours
**Lines of code:** ~300 (increased for retention features)

**Key classes/methods:**
```python
class GDriveRolloutSharing:
    """
    Manages rollout file operations on Google Drive.
    """

    def __init__(
        self,
        gdrive_path: str,
        experiment_name: str,
        publish_frequency: str = 'stage',  # 'generation', 'stage', 'round'
        retention_config: Dict = None
    ):
        """
        Args:
            gdrive_path: Base Google Drive path
            experiment_name: Name of experiment
            publish_frequency: When to publish rollouts
            retention_config: Cleanup/archive settings
        """
        self.rollouts_path = f"{gdrive_path}/experiments/{experiment_name}/rollouts"
        self.archive_path = retention_config.get('archive_path') if retention_config else None
        self.publish_frequency = publish_frequency
        self.retention_config = retention_config or {'cleanup_enabled': False}

        # Local buffer for batching
        self._rollout_buffer = {}

    def publish_rollouts(
        self,
        peer_id: str,
        round_num: int,
        stage: int,
        generation: int,
        rollouts_dict: Dict[int, List[Any]]
    ) -> bool:
        """
        Publish rollouts to Google Drive based on configured frequency.

        Args:
            peer_id: Node identifier
            round_num: Current round number
            stage: Current stage number
            generation: Current generation number
            rollouts_dict: {batch_id: [payloads]} from trainer

        Returns:
            True if published, False if buffered for later

        Behavior:
            - If frequency='generation': Publish immediately
            - If frequency='stage': Buffer until stage ends, then publish
            - If frequency='round': Buffer until round ends, then publish
        """

    def _write_rollouts_to_drive(
        self,
        peer_id: str,
        round_num: int,
        stage: int,
        rollouts_dict: Dict[int, List[Any]]
    ):
        """
        Internal method to write rollouts to Drive.
        Uses retry logic with exponential backoff.
        """

    def fetch_rollouts(
        self,
        round_num: int,
        stage: int,
        max_peers: int = 10,
        exclude_peer_ids: List[str] = None,
        timeout_seconds: int = 30
    ) -> Dict[str, Dict[int, List[Any]]]:
        """
        Fetch rollouts from other peers.

        Args:
            round_num: Current round number
            stage: Current stage number
            max_peers: Maximum number of peers to fetch from
            exclude_peer_ids: Peers to exclude (e.g., self)
            timeout_seconds: Max time to wait for Drive API

        Returns:
            {peer_id: {batch_id: [payloads]}} - same format as Hivemind
        """

    def cleanup_old_rollouts(self, current_round: int):
        """
        Clean up old rollouts based on retention policy.

        Args:
            current_round: Current round number

        Behavior:
            - If cleanup_enabled=False: Do nothing
            - If keep_last_n_rounds set: Delete rounds older than (current - N)
            - If archive_old_rollouts=True: Move to archive instead of delete
        """
        if not self.retention_config.get('cleanup_enabled', False):
            return

        keep_n = self.retention_config.get('keep_last_n_rounds', 5)
        archive = self.retention_config.get('archive_old_rollouts', False)

        cutoff_round = current_round - keep_n

        for round_dir in self._list_round_directories():
            round_num = self._extract_round_num(round_dir)
            if round_num < cutoff_round:
                if archive:
                    self._archive_round(round_num)
                else:
                    self._delete_round(round_num)

    def _archive_round(self, round_num: int):
        """Move rollouts from active dir to archive."""

    def _delete_round(self, round_num: int):
        """Permanently delete rollouts for a round."""
```

**Implementation details:**
- Use JSON serialization for rollouts (human-readable, debuggable)
- Retry logic for Google Drive API rate limits (exponential backoff)
- Local cache to reduce Drive API calls
- Atomic writes to prevent corrupted files
- Buffering for batched publish modes

**Error handling:**
- Graceful degradation if Drive API fails (train with local rollouts only)
- Warning logs for partial fetches (some peers' files missing)
- Timeout handling for slow Drive API responses

---

#### Task 1.2: Create `rgym_exp/communication/gdrive_backend.py`

**Purpose:** GenRL-compatible Communication backend using Google Drive

**Estimated time:** 3-4 hours
**Lines of code:** ~350

**Key classes/methods:**
```python
from genrl.communication.communication import Communication

class GDriveCommunicationBackend(Communication):
    """
    Communication backend that uses Google Drive for rollout sharing.
    Replaces HivemindBackend with file-based approach.
    """

    def __init__(
        self,
        gdrive_rollout_sharing: GDriveRolloutSharing,
        node_id: str,
        experiment_name: str,
        rollout_publish_frequency: str = 'stage',
        fetch_max_peers: int = 10,
        fetch_timeout_seconds: int = 30,
        cache_rollouts: bool = True,
        **kwargs
    ):
        """
        Args:
            gdrive_rollout_sharing: Instance of GDriveRolloutSharing
            node_id: Unique node identifier (UUID, no crypto needed)
            experiment_name: Name of current experiment
            rollout_publish_frequency: 'generation', 'stage', or 'round'
            fetch_max_peers: Max peers to fetch rollouts from
            fetch_timeout_seconds: Timeout for Drive API
            cache_rollouts: Enable local caching
        """
        super().__init__()
        self.rollout_sharing = gdrive_rollout_sharing
        self.node_id = node_id
        self.experiment_name = experiment_name
        self.publish_frequency = rollout_publish_frequency
        self.fetch_max_peers = fetch_max_peers
        self.fetch_timeout = fetch_timeout_seconds

        self.current_round = 0
        self.current_stage = 0
        self.current_generation = 0

        # Local cache: {(round, stage): {peer_id: rollouts}}
        self.cache_enabled = cache_rollouts
        self.rollout_cache = {}

    def get_id(self) -> str:
        """Return node identifier."""
        return self.node_id

    @property
    def step_(self) -> int:
        """Get current step (round number)."""
        return self.current_round

    @step_.setter
    def step_(self, value: int):
        """
        Set current step (round number).
        Triggers cache invalidation if round changed.
        """
        if value != self.current_round:
            self.current_round = value
            self._invalidate_cache()

    def publish_state(
        self,
        state_dict: Dict[Any, Any],
        stage: int = None,
        generation: int = None
    ):
        """
        Publish local rollouts to Google Drive.

        Args:
            state_dict: Contains rollouts in format {batch_id: [payloads]}
            stage: Current stage number (optional, uses self.current_stage if None)
            generation: Current generation (optional, uses self.current_generation if None)

        Behavior depends on rollout_publish_frequency:
            - 'generation': Publishes immediately
            - 'stage': Buffers until end of stage
            - 'round': Buffers until end of round
        """
        stage = stage or self.current_stage
        generation = generation or self.current_generation

        published = self.rollout_sharing.publish_rollouts(
            peer_id=self.node_id,
            round_num=self.current_round,
            stage=stage,
            generation=generation,
            rollouts_dict=state_dict
        )

        if published:
            get_logger().info(
                f"Published rollouts for round {self.current_round}, "
                f"stage {stage}, generation {generation}"
            )
        else:
            get_logger().debug(
                f"Buffered rollouts (will publish at end of {self.publish_frequency})"
            )

    def get_swarm_states(
        self,
        round_num: int = None,
        stage: int = None
    ) -> Dict[str, Dict[int, List[Any]]]:
        """
        Fetch rollouts from all peers via Google Drive.

        Args:
            round_num: Round to fetch (uses self.current_round if None)
            stage: Stage to fetch (uses self.current_stage if None)

        Returns:
            {peer_id: {batch_id: [payloads]}} - same format as Hivemind

        Uses local cache to minimize Drive API calls.
        """
        round_num = round_num or self.current_round
        stage = stage or self.current_stage

        cache_key = (round_num, stage)

        # Check cache first
        if self.cache_enabled and cache_key in self.rollout_cache:
            get_logger().debug(f"Using cached rollouts for {cache_key}")
            return self.rollout_cache[cache_key]

        # Fetch from Drive
        get_logger().info(f"Fetching rollouts from Drive for round {round_num}, stage {stage}")

        swarm_states = self.rollout_sharing.fetch_rollouts(
            round_num=round_num,
            stage=stage,
            max_peers=self.fetch_max_peers,
            exclude_peer_ids=[self.node_id],
            timeout_seconds=self.fetch_timeout
        )

        # Cache the result
        if self.cache_enabled:
            self.rollout_cache[cache_key] = swarm_states

        get_logger().info(f"Fetched rollouts from {len(swarm_states)} peers")
        return swarm_states

    def advance_stage(self):
        """Notify backend that stage has advanced."""
        self.current_stage += 1

        # Trigger buffered publish if frequency='stage'
        if self.publish_frequency == 'stage':
            self.rollout_sharing.flush_buffer(
                self.node_id, self.current_round, self.current_stage - 1
            )

    def advance_round(self):
        """Notify backend that round has advanced."""
        self.current_round += 1
        self.current_stage = 0
        self.current_generation = 0

        # Trigger buffered publish if frequency='round'
        if self.publish_frequency == 'round':
            self.rollout_sharing.flush_buffer(
                self.node_id, self.current_round - 1
            )

        # Trigger cleanup based on retention policy
        self.rollout_sharing.cleanup_old_rollouts(self.current_round)

        # Invalidate cache
        self._invalidate_cache()

    def _invalidate_cache(self):
        """Clear cached rollouts when round advances."""
        if self.cache_enabled:
            old_size = len(self.rollout_cache)
            self.rollout_cache.clear()
            get_logger().debug(f"Invalidated cache ({old_size} entries)")

    # Compatibility methods (Hivemind interface)
    @property
    def dht(self):
        """Return mock DHT object for compatibility."""
        return MockDHT()

class MockDHT:
    """Mock DHT object to maintain compatibility with existing code."""
    def get_visible_maddrs(self, latest=True):
        return []  # No multiaddrs needed
```

**Implementation details:**
- Maintain same interface as HivemindBackend for drop-in replacement
- Implement caching strategy to minimize Drive API calls
- Thread-safe operations (multiple stages may run concurrently)
- Automatic retry on API failures
- Hooks for stage/round advancement to trigger buffered publishes

---

### Phase 2: Integration with Existing Code

#### Task 2.1: Modify `rgym_exp/src/manager.py`

**Purpose:** Make manager compatible with both backends, add stage/round hooks

**Estimated time:** 1-2 hours
**Lines of code:** ~10 changes

**Changes:**

1. **Line 7** - Add import:
```python
from rgym_exp.communication.gdrive_backend import GDriveCommunicationBackend
```

2. **Line 56** - Update backend assertion:
```python
# BEFORE
assert isinstance(self.communication, HivemindBackend)

# AFTER
# Support both HivemindBackend and GDriveCommunicationBackend
assert isinstance(self.communication, (HivemindBackend, GDriveCommunicationBackend))
```

3. **Line 273** - Make DHT call conditional:
```python
# BEFORE
_ = self.communication.dht.get_visible_maddrs(latest=True)

# AFTER
# Only call if backend is Hivemind
if isinstance(self.communication, HivemindBackend):
    _ = self.communication.dht.get_visible_maddrs(latest=True)
```

4. **After stage completion** - Add hook to notify backend:
```python
# In _hook_after_stage() or wherever stage advances
if isinstance(self.communication, GDriveCommunicationBackend):
    self.communication.advance_stage()
```

5. **After round completion** - Add hook to notify backend:
```python
# In _hook_after_round() or wherever round advances
if isinstance(self.communication, GDriveCommunicationBackend):
    self.communication.advance_round()
```

6. **Keep all existing GDrive logger code** (lines 84-96) - no changes needed

---

#### Task 2.2: Modify `rgym_exp/runner/swarm_launcher.py`

**Purpose:** Set correct backend for GDrive mode, fix missing import

**Estimated time:** 1 hour
**Lines of code:** ~15 changes

**Changes:**

1. **Add missing import** at top of file (line 1):
```python
import uuid
from genrl.logging_utils.global_defs import get_logger
```

2. **Replace lines 19-54** with backend selection logic:
```python
@hydra.main(version_base=None)
def main(cfg: DictConfig):
    # Check if running in GDrive mode
    gdrive_mode = cfg.get('gdrive', {}).get('base_path') is not None

    if gdrive_mode:
        get_logger().info("Running in Google Drive mode (no Hivemind)")

        # Initialize GDrive communication backend
        from rgym_exp.src.gdrive_rollout_sharing import GDriveRolloutSharing
        from rgym_exp.communication.gdrive_backend import GDriveCommunicationBackend
        import os

        gdrive_base_path = cfg.gdrive.base_path
        experiment_name = os.environ.get('EXPERIMENT_NAME', 'default')
        node_id = os.environ.get('NODE_ID', str(uuid.uuid4())[:8])

        # Get retention config from config file
        retention_config = {
            'cleanup_enabled': cfg.communication.get('rollout_retention', {}).get('cleanup_enabled', False),
            'keep_last_n_rounds': cfg.communication.get('rollout_retention', {}).get('keep_last_n_rounds', 5),
            'archive_old_rollouts': cfg.communication.get('rollout_retention', {}).get('archive_old_rollouts', False),
            'archive_path': cfg.communication.get('rollout_retention', {}).get('archive_path',
                f"{gdrive_base_path}/archives/{experiment_name}/")
        }

        # Create rollout sharing instance
        rollout_sharing = GDriveRolloutSharing(
            gdrive_path=gdrive_base_path,
            experiment_name=experiment_name,
            publish_frequency=cfg.communication.get('rollout_publish_frequency', 'stage'),
            retention_config=retention_config
        )

        # Set communication backend to GDrive
        Communication.set_backend(GDriveCommunicationBackend)

        # Store in config for game_manager initialization
        cfg.communication.gdrive_rollout_sharing = rollout_sharing
        cfg.communication.node_id = node_id
        cfg.communication.experiment_name = experiment_name

        get_logger().info(f"Rollout publish frequency: {cfg.communication.get('rollout_publish_frequency', 'stage')}")
        get_logger().info(f"Rollout retention: {retention_config}")

    else:
        # Original Hivemind mode
        get_logger().info("Running in Hivemind mode")
        Communication.set_backend(HivemindBackend)
        is_master = False
        HivemindRendezvouz.init(is_master=is_master)

    game_manager = instantiate(cfg.game_manager)
    game_manager.run_game()
```

---

#### Task 2.3: Update `rgym_exp/config/colab-gdrive.yaml`

**Purpose:** Configure GDrive communication backend with retention options

**Estimated time:** 30 minutes
**Lines of code:** ~20 changes

**Changes:**

Replace `communication` section (currently lines 87-94):

```yaml
# BEFORE
communication:
  _target_: genrl.communication.hivemind.hivemind_backend.HivemindBackend
  initial_peers: ${communications.initial_peers}
  identity_path: ${oc.env:IDENTITY_PATH,/tmp/swarm.pem}
  beam_size: 50

# AFTER
communication:
  _target_: rgym_exp.communication.gdrive_backend.GDriveCommunicationBackend
  gdrive_rollout_sharing: null  # Will be injected by swarm_launcher
  node_id: null  # Will be injected by swarm_launcher
  experiment_name: ${oc.env:EXPERIMENT_NAME,default}

  # Rollout sharing configuration
  rollout_publish_frequency: 'stage'  # Options: 'generation', 'stage', 'round'

  # Fetching behavior
  fetch_max_peers: 10                 # How many peers to fetch from
  fetch_timeout_seconds: 30           # How long to wait for Drive API
  cache_rollouts: true                # Enable local caching

  # Retention policy
  rollout_retention:
    cleanup_enabled: false            # Set to true to enable cleanup
    keep_last_n_rounds: 10            # Keep 10 most recent rounds
    archive_old_rollouts: false       # Set to true to archive instead of delete
    archive_path: ${gdrive.base_path}/archives/${oc.env:EXPERIMENT_NAME,default}/
```

Remove `communications` section (no longer needed):

```yaml
# DELETE these lines
communications:
  use_gdrive_discovery: true
  discovery_path: ${gdrive.base_path}/discovery
  initial_peers: []
```

Add comments explaining configuration:

```yaml
# Rollout Sharing Configuration Guide:
#
# rollout_publish_frequency:
#   - 'generation': Publish after each generation (most frequent, highest API usage)
#   - 'stage': Publish after each stage (recommended, balanced)
#   - 'round': Publish after each round (least frequent, lowest API usage)
#
# rollout_retention:
#   cleanup_enabled: false = Keep all rollouts forever (good for debugging)
#   cleanup_enabled: true = Enable automatic cleanup
#     keep_last_n_rounds: N = Keep only last N rounds
#     archive_old_rollouts: true = Move old rollouts to archive instead of deleting
#
# Storage estimates (4 nodes, 2 stages/round):
#   - 100 rounds: ~8 MB
#   - 1000 rounds: ~80 MB
#   - Google Drive free tier: 15 GB (can store ~187,500 rounds)
```

---

### Phase 3: Notebook Updates

#### Task 3.1: Update `notebooks/colab_coordinator.ipynb`

**Purpose:** Remove peer identity generation, add retention config

**Estimated time:** 30 minutes

**Changes:**

1. **Cell 2 (Configuration)** - Add retention options:
```python
# Experiment Configuration
EXPERIMENT_NAME = 'qwen_0.6b_seed42'
NODE_ROLE = 'coordinator'
NODE_ID = 'coordinator_0'

# Model Configuration
MODEL_NAME = 'Gensyn/Qwen2.5-0.5B-Instruct'
SEED = 42

# Training Configuration
MAX_ROUNDS = 1000
NUM_GENERATIONS = 2
NUM_TRANSPLANT_TREES = 2

# Rollout Sharing Configuration
ROLLOUT_PUBLISH_FREQUENCY = 'stage'  # 'generation', 'stage', or 'round'
ROLLOUT_CLEANUP_ENABLED = False      # Set to True to enable cleanup
ROLLOUT_KEEP_LAST_N_ROUNDS = 10      # Only used if cleanup enabled
ROLLOUT_ARCHIVE_OLD = False          # Archive instead of delete

# Optional: HuggingFace Token
HUGGINGFACE_TOKEN = None

# Optional: Wandb Configuration
WANDB_API_KEY = None
WANDB_PROJECT = 'rl-swarm-colab'
```

2. **Delete cell 4** (Generate Peer Identity) - entire cell removed

3. **Update cell 6** (Set Environment Variables) - Remove identity, add NODE_ID generation:
```python
import os
import uuid

# Set environment variables
os.environ['GDRIVE_PATH'] = GDRIVE_BASE_PATH
os.environ['EXPERIMENT_NAME'] = EXPERIMENT_NAME
os.environ['NODE_ROLE'] = NODE_ROLE
os.environ['NODE_ID'] = NODE_ID or f"coord_{uuid.uuid4().hex[:8]}"
os.environ['MODEL_NAME'] = MODEL_NAME
os.environ['SEED'] = str(SEED)

# Rollout configuration
os.environ['ROLLOUT_PUBLISH_FREQUENCY'] = ROLLOUT_PUBLISH_FREQUENCY
os.environ['ROLLOUT_CLEANUP_ENABLED'] = str(ROLLOUT_CLEANUP_ENABLED)
os.environ['ROLLOUT_KEEP_LAST_N_ROUNDS'] = str(ROLLOUT_KEEP_LAST_N_ROUNDS)
os.environ['ROLLOUT_ARCHIVE_OLD'] = str(ROLLOUT_ARCHIVE_OLD)

if HUGGINGFACE_TOKEN:
    os.environ['HUGGINGFACE_ACCESS_TOKEN'] = HUGGINGFACE_TOKEN

if WANDB_API_KEY:
    os.environ['WANDB_API_KEY'] = WANDB_API_KEY
    os.environ['WANDB_PROJECT'] = WANDB_PROJECT

print("✓ Environment variables set")
```

4. **Update cell 7** (Initialize Experiment) - Add retention config:
```python
from rgym_exp.utils.experiment_manager import init_experiment

config_overrides = {
    'training.max_round': MAX_ROUNDS,
    'training.num_generations': NUM_GENERATIONS,
    'training.num_transplant_trees': NUM_TRANSPLANT_TREES,
    'training.seed': SEED,
    'coordinator_manager.advancement_strategy': ADVANCEMENT_STRATEGY,
    'coordinator_manager.round_duration_minutes': ROUND_DURATION_MINUTES,
    'coordinator_manager.min_submission_percent': MIN_SUBMISSION_PERCENT,
    'coordinator_manager.max_round_duration_minutes': MAX_ROUND_DURATION_MINUTES,
    'communication.rollout_publish_frequency': ROLLOUT_PUBLISH_FREQUENCY,
    'communication.rollout_retention.cleanup_enabled': ROLLOUT_CLEANUP_ENABLED,
    'communication.rollout_retention.keep_last_n_rounds': ROLLOUT_KEEP_LAST_N_ROUNDS,
    'communication.rollout_retention.archive_old_rollouts': ROLLOUT_ARCHIVE_OLD,
}

init_experiment(
    gdrive_base_path=GDRIVE_BASE_PATH,
    experiment_name=EXPERIMENT_NAME,
    config_overrides=config_overrides
)

print(f"✓ Experiment initialized: {EXPERIMENT_NAME}")
print(f"  Rollout frequency: {ROLLOUT_PUBLISH_FREQUENCY}")
print(f"  Cleanup enabled: {ROLLOUT_CLEANUP_ENABLED}")
```

5. **Update markdown cells** to reflect simplified setup (no peer identity)

---

#### Task 3.2: Update `notebooks/colab_worker.ipynb`

**Purpose:** Remove peer identity and discovery check, add retention config

**Estimated time:** 30 minutes

**Changes:**

1. **Cell 2 (Configuration)** - Add same retention options as coordinator

2. **Delete cell 4** (Generate Peer Identity) - entire cell removed

3. **Delete cell 7** (Check Peer Discovery) - no longer needed without P2P

4. **Update cell 6** (Set Environment Variables) - Same as coordinator changes

5. **Update markdown cells** to remove mentions of peer discovery and identity

---

### Phase 4: Enhanced Logging (Optional)

#### Task 4.1: Add Rollout Text Logging to `gdrive_logger.py`

**Purpose:** Enable viewing decoded rollout text for debugging

**Estimated time:** 1 hour
**Lines of code:** ~70 additions

**Changes:**

Add new method to `GDriveLogger` class:

```python
def log_rollouts(
    self,
    round_num: int,
    stage: int,
    generation: int,
    rollouts: List[Dict[str, Any]],
    source: str = 'local'
):
    """
    Log decoded rollout text (question + answer pairs).

    Args:
        round_num: Current round
        stage: Current stage
        generation: Current generation
        rollouts: List of rollout payloads
        source: 'local' or 'external' (from peers)
    """
    rollouts_file = os.path.join(self.log_dir, 'rollouts.jsonl')

    for i, rollout in enumerate(rollouts):
        entry = {
            "timestamp": time.time(),
            "round": round_num,
            "stage": stage,
            "generation": generation,
            "rollout_id": i,
            "source": source,
            "question": rollout.get('question', ''),
            "answer": rollout.get('actions', ''),
            "values": rollout.get('values', None),
            "metadata": rollout.get('metadata', {})
        }

        with open(rollouts_file, 'a') as f:
            f.write(json.dumps(entry) + '\n')

    get_logger().debug(f"Logged {len(rollouts)} {source} rollouts to {rollouts_file}")

def log_transplanted_rollouts(
    self,
    round_num: int,
    stage: int,
    transplants: Dict[Tuple[str, int], Any]
):
    """
    Log rollouts that were sampled from external peers (transplants).

    Args:
        round_num: Current round
        stage: Current stage
        transplants: {(peer_id, batch_id): payload} from transplant_trees()
    """
    rollouts_file = os.path.join(self.log_dir, 'rollouts.jsonl')

    for (peer_id, batch_id), payload in transplants.items():
        entry = {
            "timestamp": time.time(),
            "round": round_num,
            "stage": stage,
            "source": "transplant",
            "source_peer": peer_id,
            "source_batch": batch_id,
            "question": payload.get('question', ''),
            "answer": payload.get('actions', ''),
            "values": payload.get('values', None)
        }

        with open(rollouts_file, 'a') as f:
            f.write(json.dumps(entry) + '\n')

    get_logger().info(f"Logged {len(transplants)} transplanted rollouts from {len(set(p for p, _ in transplants.keys()))} peers")
```

**Usage in data.py:**
```python
# In prepare_states() after transplanting
if self.gdrive_logger:
    self.gdrive_logger.log_transplanted_rollouts(
        current_state.round,
        current_state.stage,
        transplants
    )
```

---

## Google Drive Directory Structure

```
/content/drive/MyDrive/rl-swarm/
├── experiments/
│   └── qwen_0.6b_seed42/
│       ├── state/
│       │   └── current_state.json           # Coordinator state (round/stage)
│       │
│       ├── peers/
│       │   ├── coordinator_0.json           # Peer registrations
│       │   ├── worker_1.json
│       │   └── worker_2.json
│       │
│       ├── rewards/
│       │   └── round_0/
│       │       └── stage_0/
│       │           ├── coordinator_0.json   # Reward submissions
│       │           ├── worker_1.json
│       │           └── worker_2.json
│       │
│       ├── rollouts/                        # 🆕 NEW DIRECTORY
│       │   ├── round_0/
│       │   │   └── stage_0/
│       │   │       ├── coordinator_0.json   # Published rollouts
│       │   │       ├── worker_1.json
│       │   │       └── worker_2.json
│       │   ├── round_1/
│       │   │   └── stage_0/
│       │   └── ...
│       │
│       ├── checkpoints/
│       │   └── round_10/
│       │       ├── coordinator_0.pt
│       │       ├── worker_1.pt
│       │       └── worker_2.pt
│       │
│       └── logs/
│           ├── coordinator_0/
│           │   ├── metrics.jsonl            # Training metrics
│           │   ├── rollouts.jsonl           # 🆕 Decoded rollout text
│           │   └── training_events.jsonl
│           ├── worker_1/
│           └── worker_2/
│
├── archives/                                # 🆕 ARCHIVE DIRECTORY
│   └── qwen_0.6b_seed42/
│       └── rollouts/
│           ├── round_0/                     # Old rollouts moved here
│           ├── round_1/
│           └── ...
```

---

## Rollout File Format

**File:** `rollouts/round_0/stage_0/worker_1.json`

```json
{
  "peer_id": "worker_1",
  "round": 0,
  "stage": 0,
  "generation": 1,
  "timestamp": 1728000000.123,
  "publish_frequency": "stage",
  "rollouts": {
    "0": [
      {
        "question": "What is 2+2?",
        "actions": "The answer is 4.",
        "values": [0.95],
        "metadata": {
          "model": "Qwen2.5-0.5B-Instruct",
          "temperature": 0.7
        }
      },
      {
        "question": "What is the capital of France?",
        "actions": "The capital of France is Paris.",
        "values": [0.88],
        "metadata": {}
      }
    ],
    "1": [
      {
        "question": "Solve: 5*3",
        "actions": "5*3 = 15",
        "values": [0.92],
        "metadata": {}
      }
    ]
  }
}
```

**Rollout log file:** `logs/worker_1/rollouts.jsonl`

```jsonl
{"timestamp": 1728000000.123, "round": 0, "stage": 0, "generation": 0, "rollout_id": 0, "source": "local", "question": "What is 2+2?", "answer": "The answer is 4.", "values": [0.95]}
{"timestamp": 1728000000.456, "round": 0, "stage": 0, "generation": 0, "rollout_id": 1, "source": "local", "question": "What is the capital of France?", "answer": "The capital of France is Paris.", "values": [0.88]}
{"timestamp": 1728000001.789, "round": 0, "stage": 0, "source": "transplant", "source_peer": "coordinator_0", "source_batch": 0, "question": "Solve: 5*3", "answer": "5*3 = 15", "values": [0.92]}
```

---

## Performance Considerations

### Google Drive API Rate Limits

**Read operations:** 15 queries per minute (QPM) per user
**Write operations:** 10 queries per minute (QPM) per user

**Impact analysis by configuration:**

**Config 1: frequency='generation', 4 nodes, 2 generations/stage, 2 stages/round**
- Per stage: 8 writes (4 nodes × 2 generations) + 24 reads (each node fetches 3 others × 2 gens)
- Total: 32 API calls per stage
- **Risk:** Very high, would hit write limit (16 writes/min > 10 QPM)

**Config 2: frequency='stage', 4 nodes, 2 stages/round** (Recommended)
- Per stage: 4 writes + 12 reads
- Total: 16 API calls per stage
- **Risk:** Low at <1 stage/minute, medium at >1 stage/minute

**Config 3: frequency='round', 4 nodes**
- Per round: 4 writes + 12 reads
- Total: 16 API calls per round
- **Risk:** Very low unless rounds are <1 minute

**Mitigation strategies:**

1. **Local caching** (implemented):
```python
# Cache rollouts for current round
# Only fetch from Drive if cache miss
self.cache[(round, stage)] = fetched_rollouts
```

2. **Exponential backoff** (implemented):
```python
# Retry with increasing delays on rate limit errors
# 1s, 2s, 4s, 8s, 16s...
```

3. **Graceful degradation** (implemented):
```python
# If fetch fails, train with local rollouts only
# Training continues, just no external rollouts for this stage
```

4. **Batched writes** (implemented):
```python
# Publish all batches in one file write
# Instead of one file per batch
```

### Storage Usage

**Per node per stage:**
- ~10 rollouts × 500 chars/rollout × 2 bytes/char = ~10 KB
- With 4 nodes × 2 stages/round = ~80 KB/round

**Retention scenarios:**

| Configuration | Rounds | Storage |
|---------------|--------|---------|
| Keep all | 100 | ~8 MB |
| Keep all | 1000 | ~80 MB |
| Keep all | 10000 | ~800 MB |
| Keep last 10 rounds | ∞ | ~800 KB |
| Keep last 50 rounds | ∞ | ~4 MB |

**Google Drive free tier:** 15 GB
- Can store ~187,500 rounds with all rollouts
- For most experiments, storage is not a concern

**Recommendation:**
- Development: Keep all rollouts (cleanup_enabled=false)
- Production: Keep last 10-20 rounds with archiving

### Latency

**Hivemind DHT:** ~10-100ms to fetch peer rollouts
**Google Drive API:** ~500-2000ms to fetch peer rollouts

**Impact on training time:**

| Training speed | Fetch overhead | % overhead |
|----------------|----------------|------------|
| 5 min/round | 1-2 sec | <1% |
| 1 min/round | 1-2 sec | 2-3% |
| 10 sec/round | 1-2 sec | 10-20% |

**Conclusion:** For typical training (5-10 min/round), latency is negligible

---

## Testing Plan

### Test 1: Single Node with Different Frequencies
**Goal:** Verify all publish frequencies work

```bash
# Test 1a: frequency='generation'
EXPERIMENT_NAME = 'test_freq_gen'
ROLLOUT_PUBLISH_FREQUENCY = 'generation'
NUM_GENERATIONS = 2

# Test 1b: frequency='stage'
EXPERIMENT_NAME = 'test_freq_stage'
ROLLOUT_PUBLISH_FREQUENCY = 'stage'

# Test 1c: frequency='round'
EXPERIMENT_NAME = 'test_freq_round'
ROLLOUT_PUBLISH_FREQUENCY = 'round'
```

**Success criteria:**
- ✅ Rollout files created at correct frequency
- ✅ File timestamps match expected publish times
- ✅ No errors about missing rollouts

---

### Test 2: Retention Policies
**Goal:** Verify cleanup and archiving work correctly

```bash
# Test 2a: Keep all
ROLLOUT_CLEANUP_ENABLED = False
# Run for 10 rounds, verify all rollout files exist

# Test 2b: Keep last 5 rounds
ROLLOUT_CLEANUP_ENABLED = True
ROLLOUT_KEEP_LAST_N_ROUNDS = 5
ROLLOUT_ARCHIVE_OLD = False
# Run for 10 rounds, verify only rounds 5-9 exist

# Test 2c: Archive old rollouts
ROLLOUT_CLEANUP_ENABLED = True
ROLLOUT_KEEP_LAST_N_ROUNDS = 3
ROLLOUT_ARCHIVE_OLD = True
# Run for 10 rounds, verify rounds 0-6 in archive, 7-9 in active
```

**Success criteria:**
- ✅ Cleanup happens at correct round boundaries
- ✅ Archived files moved to correct location
- ✅ Active rollouts count stays bounded

---

### Test 3: Multi-Node Rollout Sharing
**Goal:** Verify rollout sharing between nodes

```bash
# Coordinator
EXPERIMENT_NAME = 'test_sharing'
NODE_ID = 'coordinator_0'
NUM_TRANSPLANT_TREES = 2

# Worker
EXPERIMENT_NAME = 'test_sharing'  # SAME
NODE_ID = 'worker_1'
NUM_TRANSPLANT_TREES = 2

# Expected: Both fetch each other's rollouts
```

**Success criteria:**
- ✅ Both nodes create rollout files
- ✅ Logs show "fetched rollouts from {peer}"
- ✅ Transplanted rollouts logged correctly

---

### Test 4: SAPO Transplant Trees
**Goal:** Verify external rollout sampling works

```python
# In data.py, verify transplants include external rollouts
# Check rollouts.jsonl for entries with source='transplant'
```

**Success criteria:**
- ✅ Transplants come from different peers
- ✅ Number of transplants = NUM_TRANSPLANT_TREES
- ✅ Training uses both local and external rollouts

---

### Test 5: Resume After Disconnect
**Goal:** Verify rollouts persist across sessions

```bash
# 1. Start coordinator
# 2. Run for 5 rounds
# 3. Stop coordinator
# 4. Restart with same EXPERIMENT_NAME and NODE_ID
# 5. Verify old rollouts still accessible
```

**Success criteria:**
- ✅ Rollout files from rounds 0-5 still exist
- ✅ Can fetch old rollouts if needed
- ✅ Training continues from checkpoint

---

### Test 6: Rate Limit Handling
**Goal:** Verify graceful handling of API limits

```python
# Simulate rate limit by making many rapid requests
# Verify exponential backoff works
```

**Success criteria:**
- ✅ Retries with increasing delays
- ✅ Eventually succeeds or times out gracefully
- ✅ Training continues even if some fetches fail

---

### Test 7: Performance Comparison
**Goal:** Compare Hivemind vs GDrive mode

**Metrics:**
- Time per round
- Reward progression
- Final model quality
- API call count

**Success criteria:**
- ✅ GDrive mode <20% slower than Hivemind
- ✅ Final rewards within 5% of Hivemind
- ✅ No rate limit errors in normal usage

---

## Error Handling

### Scenario 1: Google Drive API Rate Limit
```python
# In gdrive_rollout_sharing.py
def _retry_with_backoff(func, max_retries=5):
    for attempt in range(max_retries):
        try:
            return func()
        except HttpError as e:
            if e.resp.status == 429:  # Rate limit
                wait = 2 ** attempt  # Exponential backoff
                get_logger().warning(f"Rate limit hit, retrying in {wait}s...")
                time.sleep(wait)
            else:
                raise
    get_logger().error("Max retries exceeded, giving up")
    return None
```

**Fallback:** Train with local rollouts only if fetching fails

---

### Scenario 2: Corrupted Rollout File
```python
def fetch_rollouts(self, round_num, stage):
    rollouts = {}
    for file in rollout_files:
        try:
            with open(file, 'r') as f:
                data = json.load(f)
            rollouts[data['peer_id']] = data['rollouts']
        except json.JSONDecodeError:
            get_logger().warning(f"Corrupted file {file}, skipping...")
            continue
        except KeyError as e:
            get_logger().warning(f"Invalid format in {file}: {e}, skipping...")
            continue
    return rollouts
```

**Fallback:** Skip corrupted files, use available rollouts

---

### Scenario 3: No Peer Rollouts Available
```python
# In transplant_trees() - data.py
swarm_states = communication.get_swarm_states()
if not swarm_states:
    get_logger().warning("No external rollouts available, using local only")
    return {}  # Empty transplants
```

**Fallback:** Train with local rollouts only (I^n mode, J^n=0)

---

### Scenario 4: Drive Disconnected
```python
def publish_state(self, state_dict):
    try:
        self.rollout_sharing.publish_rollouts(...)
    except Exception as e:
        get_logger().error(f"Failed to publish rollouts: {e}")
        # Continue training without publishing
        # Will retry next publish cycle
```

**Fallback:** Local training continues, rollouts published when connection restored

---

### Scenario 5: Archive Directory Creation Fails
```python
def _archive_round(self, round_num):
    try:
        os.makedirs(self.archive_path, exist_ok=True)
        shutil.move(source, dest)
    except Exception as e:
        get_logger().error(f"Archiving failed: {e}, deleting instead")
        self._delete_round(round_num)
```

**Fallback:** Delete instead of archive if archiving fails

---

## Migration Path

### For Existing Users

**Option 1: Full migration (recommended for new experiments)**
- Start new experiment with updated `colab-gdrive.yaml`
- Configure retention policy as needed
- No backward compatibility concerns

**Option 2: Hybrid mode (for ongoing experiments)**
- Keep Hivemind for existing experiments
- Use GDrive for new experiments
- Both modes supported in same codebase

**Code supports both:**
```python
# In manager.py
assert isinstance(self.communication, (HivemindBackend, GDriveCommunicationBackend))
```

### Config Selection

**Hivemind mode (original):**
```bash
python -m rgym_exp.runner.swarm_launcher --config-name rg-swarm
```

**GDrive mode (new):**
```bash
python -m rgym_exp.runner.swarm_launcher --config-name colab-gdrive
```

### Gradual Rollout

1. **Phase 1:** Deploy with cleanup_enabled=false (keep all rollouts)
2. **Phase 2:** Monitor storage usage for 1 week
3. **Phase 3:** Enable cleanup with conservative policy (keep_last_n_rounds=20)
4. **Phase 4:** Adjust based on usage patterns

---

## Dependencies

### No New Dependencies Required

**Already in requirements.txt:**
- `google-colab` (for Drive mounting)
- `hydra-core` (for config management)

**Standard library only:**
- `json` (for rollout serialization)
- `os`, `time`, `uuid`, `shutil` (for file operations)

**No additional packages needed** ✅

---

## Success Metrics

### Implementation Success
- [ ] All 8 tasks completed
- [ ] Code passes type checking (mypy)
- [ ] No breaking changes to existing Hivemind mode
- [ ] All tests pass (7/7)

### Performance Success
- [ ] Training completes without errors
- [ ] Rollout sharing works across nodes
- [ ] Performance within 20% of Hivemind mode
- [ ] No Drive API rate limit errors in normal usage
- [ ] Retention policies work as configured

### User Experience Success
- [ ] Notebooks simplified (fewer setup steps)
- [ ] No manual peer identity management needed
- [ ] Clear error messages for Drive issues
- [ ] Documentation is clear and complete
- [ ] Configurable retention meets user needs

---

## Timeline

### Development Phase (10-14 hours)
- **Day 1:** Phase 1 - Core communication backend (6-8 hours)
  - Task 1.1: GDriveRolloutSharing with retention (3-4 hours)
  - Task 1.2: GDriveCommunicationBackend (3-4 hours)

- **Day 2:** Phase 2 & 3 - Integration (3-4 hours)
  - Task 2.1: Modify manager.py (1-2 hours)
  - Task 2.2: Modify swarm_launcher.py (1 hour)
  - Task 2.3: Update config (30 min)
  - Task 3.1: Update coordinator notebook (30 min)
  - Task 3.2: Update worker notebook (30 min)

- **Day 3:** Phase 4 - Enhanced logging (1-2 hours)
  - Task 4.1: Add rollout logging (1-2 hours)

### Testing Phase (5-7 hours)
- **Day 4:** Testing (5-7 hours)
  - Test 1: Publish frequencies (1 hour)
  - Test 2: Retention policies (1-2 hours)
  - Test 3: Multi-node sharing (1 hour)
  - Test 4: SAPO verification (30 min)
  - Test 5: Resume test (1 hour)
  - Test 6: Rate limit handling (30 min)
  - Test 7: Performance comparison (1-2 hours)

### Total Estimated Time: 15-21 hours

---

## Appendix A: File Checklist

### New Files
- [ ] `rgym_exp/src/gdrive_rollout_sharing.py` (~300 lines)
- [ ] `rgym_exp/communication/gdrive_backend.py` (~350 lines)

### Modified Files
- [ ] `rgym_exp/src/manager.py` (~10 changes)
- [ ] `rgym_exp/runner/swarm_launcher.py` (~15 changes)
- [ ] `rgym_exp/config/colab-gdrive.yaml` (~20 changes)
- [ ] `notebooks/colab_coordinator.ipynb` (remove 1 cell, update 3 cells)
- [ ] `notebooks/colab_worker.ipynb` (remove 2 cells, update 2 cells)
- [ ] `rgym_exp/src/gdrive_logger.py` (+70 lines, optional)

### Documentation Files
- [x] `GDRIVE_ONLY_IMPLEMENTATION_PLAN.md` (this file)
- [ ] `GDRIVE_ONLY_TASKS.md` (task list with checkboxes)
- [ ] Update `IMPLEMENTATION_SUMMARY.md`
- [ ] Update `README.md`

---

## Appendix B: Configuration Examples

### Example 1: Development (Keep Everything)
```yaml
communication:
  rollout_publish_frequency: 'stage'
  rollout_retention:
    cleanup_enabled: false
```
**Use case:** Debugging, analysis, short experiments
**Storage:** ~8 MB per 100 rounds

### Example 2: Production (Cleanup with Archive)
```yaml
communication:
  rollout_publish_frequency: 'stage'
  rollout_retention:
    cleanup_enabled: true
    keep_last_n_rounds: 10
    archive_old_rollouts: true
```
**Use case:** Long-running experiments, want history
**Storage:** ~800 KB active + archive grows

### Example 3: Resource-Constrained (Aggressive Cleanup)
```yaml
communication:
  rollout_publish_frequency: 'round'
  rollout_retention:
    cleanup_enabled: true
    keep_last_n_rounds: 3
    archive_old_rollouts: false
```
**Use case:** Limited storage, very long experiments
**Storage:** ~240 KB constant

### Example 4: Research (Maximum Frequency)
```yaml
communication:
  rollout_publish_frequency: 'generation'
  rollout_retention:
    cleanup_enabled: false
  fetch_max_peers: 20
```
**Use case:** Research on swarm dynamics, need all data
**Storage:** Grows continuously, highest API usage

---

## Appendix C: Troubleshooting Guide

### Problem: "Rate limit exceeded" errors
**Solution:**
- Reduce `rollout_publish_frequency` (use 'round' instead of 'generation')
- Enable caching (`cache_rollouts: true`)
- Increase `fetch_timeout_seconds` to allow more retry time

### Problem: Drive storage full
**Solution:**
- Enable cleanup (`cleanup_enabled: true`)
- Reduce `keep_last_n_rounds`
- Enable archiving and periodically delete archive

### Problem: Rollouts not being shared
**Check:**
- Same `EXPERIMENT_NAME` across all nodes
- Rollout files exist in `rollouts/round_X/stage_Y/`
- Correct permissions on Google Drive folder
- Check logs for publish/fetch errors

### Problem: Training slower than expected
**Solution:**
- Check if hitting rate limits (logs will show retries)
- Reduce `fetch_max_peers` to minimize API calls
- Use 'round' frequency instead of 'stage'

---

**Document version:** 2.0
**Last updated:** 2025-10-04
**Status:** Ready for implementation with configurable retention
