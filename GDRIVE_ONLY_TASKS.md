# Task List: Remove Hivemind and Use Google Drive Only

**Related Document:** `GDRIVE_ONLY_IMPLEMENTATION_PLAN.md`
**Status:** Not Started
**Last Updated:** 2025-10-04

---

## Phase 1: Core Communication Backend

### Task 1.1: Create `rgym_exp/src/gdrive_rollout_sharing.py`
- [ ] Create file structure and class definition
- [ ] Implement `__init__` with retention config
- [ ] Implement `publish_rollouts` with frequency logic
- [ ] Implement `_write_rollouts_to_drive` with retry logic
- [ ] Implement `fetch_rollouts` with timeout and caching
- [ ] Implement `cleanup_old_rollouts`
- [ ] Implement `_archive_round` for archiving
- [ ] Implement `_delete_round` for cleanup
- [ ] Implement buffering for 'stage' and 'round' frequencies
- [ ] Add error handling and logging
- [ ] Test locally with mock Drive directory

**Estimated time:** 3-4 hours
**Lines of code:** ~300

---

### Task 1.2: Create `rgym_exp/communication/gdrive_backend.py`
- [ ] Create file and import GenRL Communication base class
- [ ] Implement `GDriveCommunicationBackend` class
- [ ] Implement `__init__` with config parameters
- [ ] Implement `get_id()` method
- [ ] Implement `step_` property getter/setter
- [ ] Implement `publish_state()` with frequency awareness
- [ ] Implement `get_swarm_states()` with caching
- [ ] Implement `advance_stage()` hook
- [ ] Implement `advance_round()` hook with cleanup trigger
- [ ] Implement `_invalidate_cache()` method
- [ ] Create `MockDHT` class for compatibility
- [ ] Add comprehensive error handling
- [ ] Add logging for debugging
- [ ] Test with mock GDriveRolloutSharing

**Estimated time:** 3-4 hours
**Lines of code:** ~350

---

## Phase 2: Integration with Existing Code

### Task 2.1: Modify `rgym_exp/src/manager.py`
- [ ] Add import for `GDriveCommunicationBackend`
- [ ] Update backend assertion (line 56) to accept both backends
- [ ] Make DHT call conditional (line 273)
- [ ] Add `advance_stage()` hook after stage completion
- [ ] Add `advance_round()` hook after round completion
- [ ] Verify existing GDrive logger integration still works
- [ ] Test with both Hivemind and GDrive backends

**Estimated time:** 1-2 hours
**Lines changed:** ~10

---

### Task 2.2: Modify `rgym_exp/runner/swarm_launcher.py`
- [ ] Add missing imports (`uuid`, `get_logger`)
- [ ] Detect GDrive mode from config
- [ ] Extract retention config from yaml
- [ ] Create `GDriveRolloutSharing` instance in GDrive mode
- [ ] Set `Communication.set_backend()` appropriately
- [ ] Inject rollout sharing into config
- [ ] Log configuration details
- [ ] Keep Hivemind mode working for backward compatibility
- [ ] Test both modes (Hivemind and GDrive)

**Estimated time:** 1 hour
**Lines changed:** ~15

---

### Task 2.3: Update `rgym_exp/config/colab-gdrive.yaml`
- [ ] Replace `communication` section target with `GDriveCommunicationBackend`
- [ ] Add `rollout_publish_frequency` parameter
- [ ] Add `fetch_max_peers` parameter
- [ ] Add `fetch_timeout_seconds` parameter
- [ ] Add `cache_rollouts` parameter
- [ ] Add `rollout_retention` section with all options
- [ ] Add configuration comments/documentation
- [ ] Remove old `communications` section (discovery-related)
- [ ] Test config parsing with Hydra

**Estimated time:** 30 minutes
**Lines changed:** ~20

---

## Phase 3: Notebook Updates

### Task 3.1: Update `notebooks/colab_coordinator.ipynb`
- [ ] Add retention config variables to cell 2
- [ ] Delete cell 4 (Generate Peer Identity)
- [ ] Update cell 6 (Set Environment Variables)
  - [ ] Remove `IDENTITY_PATH`
  - [ ] Add UUID generation for `NODE_ID`
  - [ ] Add retention env vars
- [ ] Update cell 7 (Initialize Experiment)
  - [ ] Add retention config to overrides
- [ ] Update markdown cells to remove peer identity mentions
- [ ] Add retention configuration guide in markdown
- [ ] Test notebook end-to-end on Colab

**Estimated time:** 30 minutes
**Cells modified:** Remove 1, update 3

---

### Task 3.2: Update `notebooks/colab_worker.ipynb`
- [ ] Add retention config variables to cell 2
- [ ] Delete cell 4 (Generate Peer Identity)
- [ ] Delete cell 7 (Check Peer Discovery)
- [ ] Update cell 6 (Set Environment Variables)
  - [ ] Remove `IDENTITY_PATH`
  - [ ] Add UUID generation for `NODE_ID`
  - [ ] Add retention env vars
- [ ] Update markdown cells to remove identity/discovery mentions
- [ ] Simplify troubleshooting guide
- [ ] Test notebook end-to-end on Colab

**Estimated time:** 30 minutes
**Cells modified:** Remove 2, update 2

---

## Phase 4: Enhanced Logging (Optional)

### Task 4.1: Add Rollout Text Logging to `gdrive_logger.py`
- [ ] Add `log_rollouts()` method
- [ ] Add `log_transplanted_rollouts()` method
- [ ] Update file paths for rollouts.jsonl
- [ ] Add JSONL formatting for rollout entries
- [ ] Include source tracking (local vs transplant)
- [ ] Add peer tracking for transplanted rollouts
- [ ] Integrate with data.py `prepare_states()`
- [ ] Test logging output format
- [ ] Verify JSONL is valid and parseable

**Estimated time:** 1-2 hours
**Lines added:** ~70

---

## Testing Phase

### Test 1: Publish Frequency Variations
- [ ] Test frequency='generation'
  - [ ] Single node, verify files created per generation
  - [ ] Check file timestamps
- [ ] Test frequency='stage'
  - [ ] Single node, verify files created per stage
  - [ ] Check aggregation of generations
- [ ] Test frequency='round'
  - [ ] Single node, verify files created per round
  - [ ] Check aggregation of stages

**Estimated time:** 1 hour

---

### Test 2: Retention Policy Testing
- [ ] Test cleanup_enabled=false
  - [ ] Run for 10 rounds
  - [ ] Verify all rollout files exist
- [ ] Test cleanup with delete
  - [ ] Set keep_last_n_rounds=5
  - [ ] Run for 10 rounds
  - [ ] Verify only rounds 5-9 exist
- [ ] Test cleanup with archive
  - [ ] Set archive_old_rollouts=true
  - [ ] Run for 10 rounds
  - [ ] Verify old rollouts in archive directory
  - [ ] Verify active directory bounded

**Estimated time:** 1-2 hours

---

### Test 3: Multi-Node Rollout Sharing
- [ ] Start coordinator node
  - [ ] Verify rollouts published correctly
- [ ] Start worker node
  - [ ] Verify worker fetches coordinator rollouts
  - [ ] Verify coordinator fetches worker rollouts
- [ ] Check logs for fetch confirmations
- [ ] Verify swarm_states format matches Hivemind
- [ ] Check SAPO transplant_trees receives correct data

**Estimated time:** 1 hour

---

### Test 4: SAPO Transplant Trees Verification
- [ ] Set NUM_TRANSPLANT_TREES > 0
- [ ] Run multi-node training
- [ ] Check logs for transplant messages
- [ ] Verify rollouts.jsonl contains 'transplant' entries
- [ ] Verify source_peer matches other nodes
- [ ] Verify training uses external rollouts
- [ ] Compare rewards with/without transplants

**Estimated time:** 30 minutes

---

### Test 5: Resume After Disconnect
- [ ] Start coordinator
- [ ] Run for 5 rounds
- [ ] Verify rollout files created
- [ ] Stop coordinator (simulate disconnect)
- [ ] Restart with same NODE_ID and EXPERIMENT_NAME
- [ ] Verify old rollout files still accessible
- [ ] Verify training resumes from checkpoint
- [ ] Check that fetching works with old rollouts

**Estimated time:** 1 hour

---

### Test 6: Rate Limit Handling
- [ ] Configure aggressive settings (frequency='generation', many peers)
- [ ] Monitor for rate limit errors in logs
- [ ] Verify exponential backoff occurs
- [ ] Verify training continues despite rate limits
- [ ] Check graceful degradation (local-only training)
- [ ] Test timeout handling

**Estimated time:** 30 minutes

---

### Test 7: Performance Comparison
- [ ] Baseline: Run Hivemind mode
  - [ ] Track time per round
  - [ ] Track reward progression
  - [ ] Track final model quality
- [ ] Comparison: Run GDrive mode
  - [ ] Same model, same config
  - [ ] Track time per round
  - [ ] Track reward progression
  - [ ] Track final model quality
- [ ] Compare results
  - [ ] Time overhead <20%?
  - [ ] Rewards within 5%?
  - [ ] Model quality comparable?
- [ ] Monitor API call counts

**Estimated time:** 2-3 hours

---

## Documentation

### Update Existing Documentation
- [ ] Update `IMPLEMENTATION_SUMMARY.md`
  - [ ] Mark GDrive communication as complete
  - [ ] Update file count and status
- [ ] Update `README.md`
  - [ ] Add section on GDrive-only mode
  - [ ] Document retention configuration
  - [ ] Add troubleshooting section
- [ ] Update `CLAUDE.md`
  - [ ] Update architecture section
  - [ ] Document new communication backend

**Estimated time:** 1 hour

---

### Create New Documentation
- [ ] Create `GDRIVE_MODE_GUIDE.md`
  - [ ] User guide for GDrive-only mode
  - [ ] Configuration examples
  - [ ] Best practices
  - [ ] Troubleshooting
- [ ] Create `ROLLOUT_SHARING.md`
  - [ ] Technical details on rollout format
  - [ ] File structure documentation
  - [ ] API documentation

**Estimated time:** 1-2 hours

---

## Summary Checklist

### Implementation Tasks
- [ ] Phase 1: Core backend (Tasks 1.1, 1.2) - 6-8 hours
- [ ] Phase 2: Integration (Tasks 2.1, 2.2, 2.3) - 2-3 hours
- [ ] Phase 3: Notebooks (Tasks 3.1, 3.2) - 1 hour
- [ ] Phase 4: Logging (Task 4.1) - 1-2 hours

**Total Development:** 10-14 hours

### Testing Tasks
- [ ] Test 1: Publish frequencies - 1 hour
- [ ] Test 2: Retention policies - 1-2 hours
- [ ] Test 3: Multi-node sharing - 1 hour
- [ ] Test 4: SAPO verification - 30 min
- [ ] Test 5: Resume test - 1 hour
- [ ] Test 6: Rate limits - 30 min
- [ ] Test 7: Performance - 2-3 hours

**Total Testing:** 5-7 hours

### Documentation Tasks
- [ ] Update existing docs - 1 hour
- [ ] Create new docs - 1-2 hours

**Total Documentation:** 2-3 hours

---

## Total Estimated Time: 17-24 hours

---

## Dependencies
- [ ] Verify no new Python packages needed
- [ ] Confirm Google Drive API access working
- [ ] Ensure Colab environment setup correct

---

## Risks and Mitigation

### Risk 1: Rate Limiting
**Mitigation:**
- Implement caching ✓
- Exponential backoff ✓
- Graceful degradation ✓

### Risk 2: Storage Overflow
**Mitigation:**
- Configurable retention ✓
- Archiving option ✓
- Storage monitoring ✓

### Risk 3: Compatibility Break
**Mitigation:**
- Keep Hivemind mode working ✓
- Backward compatible ✓
- Gradual rollout option ✓

---

## Success Criteria

### Must Have
- [ ] All code tasks completed
- [ ] All tests pass
- [ ] No breaking changes to Hivemind mode
- [ ] Training works end-to-end
- [ ] Rollout sharing works correctly

### Should Have
- [ ] Performance within 20% of Hivemind
- [ ] Documentation complete
- [ ] Retention policies work
- [ ] Error handling robust

### Nice to Have
- [ ] Rollout text logging
- [ ] Performance optimizations
- [ ] Advanced monitoring

---

## Progress Tracking

**Development:** 0% (0/10-14 hours)
**Testing:** 0% (0/5-7 hours)
**Documentation:** 6% (1/2-3 hours) - Plan document created ✓

**Overall:** 3% (1/17-24 hours)

---

## Next Steps

1. **Start with Task 1.1** - Create `gdrive_rollout_sharing.py`
2. **Then Task 1.2** - Create `gdrive_backend.py`
3. **Integration** - Tasks 2.1, 2.2, 2.3
4. **Quick test** - Verify basic functionality
5. **Notebooks** - Tasks 3.1, 3.2
6. **Full testing** - All test scenarios
7. **Documentation** - Update and create docs

---

**Ready to begin implementation!** 🚀
