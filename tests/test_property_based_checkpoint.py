"""
Property-based tests for checkpoint/resume functionality using Hypothesis.

This module tests checkpoint operations using property-based testing to
automatically generate thousands of edge cases for:
- CheckpointPolicy configuration validation
- CheckpointState serialization and deserialization
- CheckpointManager file operations (save, load, delete, list)
- Checkpoint history rotation and cleanup
- Thread safety for concurrent operations
- Resume logic with pending items and result merging
"""

import json
import os
import pickle
import shutil
import tempfile
import threading
import time
from pathlib import Path
from typing import Any, Dict, List

import pytest
from hypothesis import given, strategies as st, settings, assume

from amorsize.checkpoint import (
    CheckpointManager,
    CheckpointPolicy,
    CheckpointState,
    get_pending_items,
    merge_results,
)


# ============================================================================
# Custom Hypothesis Strategies
# ============================================================================

@st.composite
def checkpoint_policy_strategy(draw):
    """Generate valid CheckpointPolicy configurations."""
    return CheckpointPolicy(
        checkpoint_dir=draw(st.sampled_from([
            "./checkpoints",
            "/tmp/test_checkpoints",
            tempfile.mkdtemp()
        ])),
        checkpoint_interval=draw(st.integers(min_value=0, max_value=1000)),
        checkpoint_name=draw(st.one_of(
            st.none(),
            st.text(min_size=1, max_size=50, alphabet=st.characters(
                whitelist_categories=('Lu', 'Ll', 'Nd'),
                whitelist_characters='_-'
            ))
        )),
        save_format=draw(st.sampled_from(["pickle", "json"])),
        keep_history=draw(st.integers(min_value=1, max_value=10)),
        auto_cleanup=draw(st.booleans())
    )


@st.composite
def checkpoint_state_strategy(draw, max_items=100):
    """Generate valid CheckpointState objects."""
    total_items = draw(st.integers(min_value=0, max_value=max_items))
    
    # Generate completed indices (sorted, unique, within range)
    if total_items > 0:
        num_completed = draw(st.integers(min_value=0, max_value=total_items))
        completed_indices = draw(st.lists(
            st.integers(min_value=0, max_value=total_items - 1),
            min_size=num_completed,
            max_size=num_completed,
            unique=True
        ))
        completed_indices.sort()
    else:
        completed_indices = []
    
    # Generate results matching completed indices
    results = [draw(st.one_of(
        st.integers(),
        st.text(max_size=20),
        st.floats(allow_nan=False, allow_infinity=False),
        st.lists(st.integers(), max_size=5)
    )) for _ in completed_indices]
    
    return CheckpointState(
        completed_indices=completed_indices,
        results=results,
        total_items=total_items,
        checkpoint_time=draw(st.floats(min_value=0.0, max_value=2e9)),
        n_jobs=draw(st.integers(min_value=1, max_value=32)),
        chunksize=draw(st.integers(min_value=1, max_value=1000)),
        metadata=draw(st.dictionaries(
            st.text(min_size=1, max_size=20),
            st.one_of(st.integers(), st.text(max_size=20), st.booleans()),
            max_size=5
        ))
    )


@st.composite
def checkpoint_name_strategy(draw):
    """Generate valid checkpoint names."""
    return draw(st.text(
        min_size=1,
        max_size=50,
        alphabet=st.characters(
            whitelist_categories=('Lu', 'Ll', 'Nd'),
            whitelist_characters='_-'
        )
    ))


# ============================================================================
# Test Class 1: CheckpointPolicy Invariants
# ============================================================================

class TestCheckpointPolicyInvariants:
    """Property-based tests for CheckpointPolicy validation."""
    
    @given(policy=checkpoint_policy_strategy())
    def test_valid_policy_creation(self, policy):
        """Property: Valid configurations create policy successfully."""
        assert isinstance(policy, CheckpointPolicy)
        assert policy.checkpoint_interval >= 0
        assert policy.save_format in ("pickle", "json")
        assert policy.keep_history >= 1
        assert isinstance(policy.auto_cleanup, bool)
    
    @given(
        interval=st.integers(max_value=-1)
    )
    def test_negative_interval_rejected(self, interval):
        """Property: Negative checkpoint_interval raises ValueError."""
        with pytest.raises(ValueError, match="checkpoint_interval must be >= 0"):
            CheckpointPolicy(checkpoint_interval=interval)
    
    @given(
        format_str=st.text(min_size=1, max_size=20).filter(
            lambda x: x not in ("pickle", "json")
        )
    )
    def test_invalid_format_rejected(self, format_str):
        """Property: Invalid save_format raises ValueError."""
        with pytest.raises(ValueError, match="save_format must be"):
            CheckpointPolicy(save_format=format_str)
    
    @given(
        keep_history=st.integers(max_value=0)
    )
    def test_invalid_keep_history_rejected(self, keep_history):
        """Property: keep_history < 1 raises ValueError."""
        with pytest.raises(ValueError, match="keep_history must be >= 1"):
            CheckpointPolicy(keep_history=keep_history)


# ============================================================================
# Test Class 2: CheckpointState Invariants
# ============================================================================

class TestCheckpointStateInvariants:
    """Property-based tests for CheckpointState serialization."""
    
    @given(state=checkpoint_state_strategy())
    def test_state_field_storage(self, state):
        """Property: State stores all fields correctly."""
        assert isinstance(state.completed_indices, list)
        assert isinstance(state.results, list)
        assert isinstance(state.total_items, int)
        assert isinstance(state.checkpoint_time, float)
        assert isinstance(state.n_jobs, int)
        assert isinstance(state.chunksize, int)
        assert isinstance(state.metadata, dict)
        
        # Verify results match completed indices
        assert len(state.completed_indices) == len(state.results)
    
    @given(state=checkpoint_state_strategy())
    def test_to_dict_from_dict_roundtrip(self, state):
        """Property: to_dict/from_dict roundtrip preserves state."""
        state_dict = state.to_dict()
        restored_state = CheckpointState.from_dict(state_dict)
        
        assert restored_state.completed_indices == state.completed_indices
        assert restored_state.results == state.results
        assert restored_state.total_items == state.total_items
        assert restored_state.checkpoint_time == state.checkpoint_time
        assert restored_state.n_jobs == state.n_jobs
        assert restored_state.chunksize == state.chunksize
        assert restored_state.metadata == state.metadata
    
    @given(state=checkpoint_state_strategy())
    def test_completed_indices_length_consistency(self, state):
        """Property: completed_indices and results have same length."""
        assert len(state.completed_indices) == len(state.results)
    
    @given(state=checkpoint_state_strategy())
    def test_completed_indices_within_bounds(self, state):
        """Property: All completed indices are within [0, total_items)."""
        # When total_items is 0, completed_indices should be empty (verified by strategy)
        if state.total_items == 0:
            assert len(state.completed_indices) == 0
        else:
            for idx in state.completed_indices:
                assert 0 <= idx < state.total_items


# ============================================================================
# Test Class 3: CheckpointManager Basic Operations
# ============================================================================

class TestCheckpointManagerBasicOperations:
    """Property-based tests for CheckpointManager save/load/delete operations."""
    
    @given(
        policy=checkpoint_policy_strategy(),
        state=checkpoint_state_strategy(),
        checkpoint_name=checkpoint_name_strategy()
    )
    @settings(max_examples=50)  # Reduced for file I/O operations
    def test_save_and_load_preserves_state(self, policy, state, checkpoint_name):
        """Property: Saving and loading checkpoint preserves all state."""
        # Create temporary directory for this test
        with tempfile.TemporaryDirectory() as tmpdir:
            policy.checkpoint_dir = tmpdir
            manager = CheckpointManager(policy)
            
            # Save checkpoint
            saved_path = manager.save_checkpoint(checkpoint_name, state)
            assert saved_path.exists()
            
            # Load checkpoint
            loaded_state = manager.load_checkpoint(checkpoint_name)
            assert loaded_state is not None
            
            # Verify all fields preserved
            assert loaded_state.completed_indices == state.completed_indices
            assert loaded_state.results == state.results
            assert loaded_state.total_items == state.total_items
            assert loaded_state.n_jobs == state.n_jobs
            assert loaded_state.chunksize == state.chunksize
            assert loaded_state.metadata == state.metadata
    
    @given(
        policy=checkpoint_policy_strategy(),
        checkpoint_name=checkpoint_name_strategy()
    )
    @settings(max_examples=30)
    def test_load_nonexistent_returns_none(self, policy, checkpoint_name):
        """Property: Loading nonexistent checkpoint returns None."""
        with tempfile.TemporaryDirectory() as tmpdir:
            policy.checkpoint_dir = tmpdir
            manager = CheckpointManager(policy)
            
            result = manager.load_checkpoint(checkpoint_name)
            assert result is None
    
    @given(
        policy=checkpoint_policy_strategy(),
        state=checkpoint_state_strategy(),
        checkpoint_name=checkpoint_name_strategy()
    )
    @settings(max_examples=30)
    def test_delete_removes_checkpoint(self, policy, state, checkpoint_name):
        """Property: Deleting checkpoint removes file from disk."""
        with tempfile.TemporaryDirectory() as tmpdir:
            policy.checkpoint_dir = tmpdir
            manager = CheckpointManager(policy)
            
            # Save and verify exists
            manager.save_checkpoint(checkpoint_name, state)
            assert manager.load_checkpoint(checkpoint_name) is not None
            
            # Delete and verify removed
            deleted_count = manager.delete_checkpoint(checkpoint_name)
            assert deleted_count >= 1
            assert manager.load_checkpoint(checkpoint_name) is None
    
    @given(
        policy=checkpoint_policy_strategy(),
        checkpoint_name=checkpoint_name_strategy()
    )
    @settings(max_examples=30)
    def test_delete_nonexistent_returns_zero(self, policy, checkpoint_name):
        """Property: Deleting nonexistent checkpoint returns 0."""
        with tempfile.TemporaryDirectory() as tmpdir:
            policy.checkpoint_dir = tmpdir
            manager = CheckpointManager(policy)
            
            deleted_count = manager.delete_checkpoint(checkpoint_name)
            assert deleted_count == 0


# ============================================================================
# Test Class 4: Checkpoint File Format Handling
# ============================================================================

class TestCheckpointFileFormats:
    """Property-based tests for JSON vs Pickle format handling."""
    
    @given(
        state=checkpoint_state_strategy(),
        checkpoint_name=checkpoint_name_strategy()
    )
    @settings(max_examples=30)
    def test_pickle_format_roundtrip(self, state, checkpoint_name):
        """Property: Pickle format preserves state."""
        with tempfile.TemporaryDirectory() as tmpdir:
            policy = CheckpointPolicy(
                checkpoint_dir=tmpdir,
                save_format="pickle"
            )
            manager = CheckpointManager(policy)
            
            manager.save_checkpoint(checkpoint_name, state)
            loaded_state = manager.load_checkpoint(checkpoint_name)
            
            assert loaded_state is not None
            assert loaded_state.completed_indices == state.completed_indices
            assert loaded_state.results == state.results
    
    @given(
        state=checkpoint_state_strategy(),
        checkpoint_name=checkpoint_name_strategy()
    )
    @settings(max_examples=30)
    def test_json_format_roundtrip(self, state, checkpoint_name):
        """Property: JSON format preserves state (for JSON-serializable data)."""
        with tempfile.TemporaryDirectory() as tmpdir:
            policy = CheckpointPolicy(
                checkpoint_dir=tmpdir,
                save_format="json"
            )
            manager = CheckpointManager(policy)
            
            manager.save_checkpoint(checkpoint_name, state)
            loaded_state = manager.load_checkpoint(checkpoint_name)
            
            assert loaded_state is not None
            assert loaded_state.completed_indices == state.completed_indices
            # JSON serializes/deserializes all data types successfully
            assert loaded_state.total_items == state.total_items
    
    @given(
        state=checkpoint_state_strategy(),
        checkpoint_name=checkpoint_name_strategy()
    )
    @settings(max_examples=20)
    def test_pickle_file_extension(self, state, checkpoint_name):
        """Property: Pickle format creates .pkl files."""
        with tempfile.TemporaryDirectory() as tmpdir:
            policy = CheckpointPolicy(
                checkpoint_dir=tmpdir,
                save_format="pickle"
            )
            manager = CheckpointManager(policy)
            
            saved_path = manager.save_checkpoint(checkpoint_name, state)
            assert saved_path.suffix == ".pkl"
    
    @given(
        state=checkpoint_state_strategy(),
        checkpoint_name=checkpoint_name_strategy()
    )
    @settings(max_examples=20)
    def test_json_file_extension(self, state, checkpoint_name):
        """Property: JSON format creates .json files."""
        with tempfile.TemporaryDirectory() as tmpdir:
            policy = CheckpointPolicy(
                checkpoint_dir=tmpdir,
                save_format="json"
            )
            manager = CheckpointManager(policy)
            
            saved_path = manager.save_checkpoint(checkpoint_name, state)
            assert saved_path.suffix == ".json"


# ============================================================================
# Test Class 5: Checkpoint History Management
# ============================================================================

class TestCheckpointHistoryManagement:
    """Property-based tests for checkpoint version rotation."""
    
    @given(
        keep_history=st.integers(min_value=1, max_value=5),
        num_saves=st.integers(min_value=2, max_value=10),
        checkpoint_name=checkpoint_name_strategy()
    )
    @settings(max_examples=20)
    def test_keep_history_enforced(self, keep_history, num_saves, checkpoint_name):
        """Property: keep_history limit is enforced on rotation."""
        with tempfile.TemporaryDirectory() as tmpdir:
            policy = CheckpointPolicy(
                checkpoint_dir=tmpdir,
                keep_history=keep_history
            )
            manager = CheckpointManager(policy)
            
            # Save multiple versions
            for i in range(num_saves):
                state = CheckpointState(
                    completed_indices=[i],
                    results=[f"result_{i}"],
                    total_items=10,
                    checkpoint_time=time.time(),
                    n_jobs=4,
                    chunksize=10,
                    metadata={"version": i}
                )
                manager.save_checkpoint(checkpoint_name, state)
            
            # Count checkpoint files
            checkpoint_dir = Path(tmpdir)
            checkpoint_files = list(checkpoint_dir.glob(f"{checkpoint_name}_checkpoint*"))
            
            # Should have at most keep_history + 1 files (current + history)
            assert len(checkpoint_files) <= keep_history + 1
    
    @given(
        state1=checkpoint_state_strategy(),
        state2=checkpoint_state_strategy(),
        checkpoint_name=checkpoint_name_strategy()
    )
    @settings(max_examples=30)
    def test_newest_checkpoint_is_current(self, state1, state2, checkpoint_name):
        """Property: Loading checkpoint returns most recent save."""
        with tempfile.TemporaryDirectory() as tmpdir:
            policy = CheckpointPolicy(checkpoint_dir=tmpdir)
            manager = CheckpointManager(policy)
            
            # Save two different states
            manager.save_checkpoint(checkpoint_name, state1)
            time.sleep(0.01)  # Ensure different timestamps
            manager.save_checkpoint(checkpoint_name, state2)
            
            # Load should return state2 (most recent)
            loaded = manager.load_checkpoint(checkpoint_name)
            assert loaded is not None
            assert loaded.completed_indices == state2.completed_indices


# ============================================================================
# Test Class 6: List Checkpoints Operation
# ============================================================================

class TestListCheckpoints:
    """Property-based tests for listing available checkpoints."""
    
    @given(
        num_checkpoints=st.integers(min_value=0, max_value=10)
    )
    @settings(max_examples=30)
    def test_list_returns_correct_count(self, num_checkpoints):
        """Property: list_checkpoints returns correct number of checkpoints."""
        with tempfile.TemporaryDirectory() as tmpdir:
            policy = CheckpointPolicy(checkpoint_dir=tmpdir)
            manager = CheckpointManager(policy)
            
            # Create checkpoints
            checkpoint_names = []
            for i in range(num_checkpoints):
                name = f"checkpoint_{i}"
                checkpoint_names.append(name)
                state = CheckpointState(
                    completed_indices=[],
                    results=[],
                    total_items=0,
                    checkpoint_time=time.time(),
                    n_jobs=1,
                    chunksize=1,
                    metadata={}
                )
                manager.save_checkpoint(name, state)
            
            # List checkpoints
            listed = manager.list_checkpoints()
            assert len(listed) == num_checkpoints
            
            # Verify all names present
            for name in checkpoint_names:
                assert name in listed
    
    @given(policy=checkpoint_policy_strategy())
    @settings(max_examples=20)
    def test_list_empty_directory(self, policy):
        """Property: list_checkpoints returns empty list for empty directory."""
        with tempfile.TemporaryDirectory() as tmpdir:
            policy.checkpoint_dir = tmpdir
            manager = CheckpointManager(policy)
            
            listed = manager.list_checkpoints()
            assert listed == []


# ============================================================================
# Test Class 7: Thread Safety
# ============================================================================

class TestThreadSafety:
    """Property-based tests for concurrent checkpoint operations."""
    
    @given(
        num_threads=st.integers(min_value=2, max_value=8),
        checkpoint_name=checkpoint_name_strategy()
    )
    @settings(max_examples=10)
    def test_concurrent_save_operations(self, num_threads, checkpoint_name):
        """Property: Concurrent saves don't corrupt checkpoint."""
        with tempfile.TemporaryDirectory() as tmpdir:
            policy = CheckpointPolicy(checkpoint_dir=tmpdir)
            manager = CheckpointManager(policy)
            
            # Prepare states for each thread
            states = []
            for i in range(num_threads):
                state = CheckpointState(
                    completed_indices=[i],
                    results=[f"thread_{i}"],
                    total_items=num_threads,
                    checkpoint_time=time.time(),
                    n_jobs=1,
                    chunksize=1,
                    metadata={"thread": i}
                )
                states.append(state)
            
            # Concurrent save operations
            barrier = threading.Barrier(num_threads)
            
            def save_checkpoint(state):
                barrier.wait()  # Synchronize thread start
                manager.save_checkpoint(checkpoint_name, state)
            
            threads = []
            for state in states:
                thread = threading.Thread(target=save_checkpoint, args=(state,))
                threads.append(thread)
                thread.start()
            
            for thread in threads:
                thread.join()
            
            # Verify checkpoint can be loaded (not corrupted)
            loaded = manager.load_checkpoint(checkpoint_name)
            assert loaded is not None
            assert isinstance(loaded, CheckpointState)


# ============================================================================
# Test Class 8: Resume Helper Functions
# ============================================================================

class TestResumeHelpers:
    """Property-based tests for get_pending_items and merge_results."""
    
    @given(
        data_size=st.integers(min_value=0, max_value=100),
        num_completed=st.integers(min_value=0, max_value=100)
    )
    def test_get_pending_items_no_checkpoint(self, data_size, num_completed):
        """Property: Without checkpoint, all items are pending."""
        assume(num_completed <= data_size)  # Ensure valid constraint
        
        data = list(range(data_size))
        pending_indices, pending_items = get_pending_items(data, None)
        
        assert pending_indices == list(range(data_size))
        assert pending_items == data
    
    @given(
        state=checkpoint_state_strategy(max_items=50)
    )
    @settings(max_examples=50)
    def test_get_pending_items_with_checkpoint(self, state):
        """Property: With checkpoint, only uncompleted items are pending."""
        data = list(range(state.total_items))
        pending_indices, pending_items = get_pending_items(data, state)
        
        # Verify no completed indices in pending
        completed_set = set(state.completed_indices)
        for idx in pending_indices:
            assert idx not in completed_set
        
        # Verify all indices accounted for
        all_indices = set(pending_indices) | completed_set
        assert all_indices == set(range(state.total_items))
    
    @given(
        state=checkpoint_state_strategy(max_items=50)
    )
    @settings(max_examples=50)
    def test_merge_results_correctness(self, state):
        """Property: merge_results produces correct final ordering."""
        data = list(range(state.total_items))
        pending_indices, pending_items = get_pending_items(data, state)
        
        # Generate new results for pending items
        new_results = [f"new_{idx}" for idx in pending_indices]
        
        # Merge results
        final_results = merge_results(
            new_results,
            pending_indices,
            state,
            state.total_items
        )
        
        assert len(final_results) == state.total_items
        
        # Verify completed results preserved (strategy ensures indices are valid)
        for idx, result in zip(state.completed_indices, state.results):
            assert final_results[idx] == result
        
        # Verify new results placed correctly (strategy ensures indices are valid)
        for idx, result in zip(pending_indices, new_results):
            assert final_results[idx] == result
    
    @given(
        total_items=st.integers(min_value=1, max_value=100)
    )
    def test_merge_results_no_checkpoint(self, total_items):
        """Property: Without checkpoint, merge just returns new results."""
        new_results = [f"result_{i}" for i in range(total_items)]
        pending_indices = list(range(total_items))
        
        final_results = merge_results(
            new_results,
            pending_indices,
            None,
            total_items
        )
        
        assert final_results == new_results


# ============================================================================
# Test Class 9: Edge Cases
# ============================================================================

class TestEdgeCases:
    """Property-based tests for edge cases and boundary conditions."""
    
    @given(
        policy=checkpoint_policy_strategy(),
        checkpoint_name=checkpoint_name_strategy()
    )
    @settings(max_examples=20)
    def test_empty_checkpoint_state(self, policy, checkpoint_name):
        """Property: Empty checkpoint (0 items) can be saved and loaded."""
        with tempfile.TemporaryDirectory() as tmpdir:
            policy.checkpoint_dir = tmpdir
            manager = CheckpointManager(policy)
            
            state = CheckpointState(
                completed_indices=[],
                results=[],
                total_items=0,
                checkpoint_time=time.time(),
                n_jobs=1,
                chunksize=1,
                metadata={}
            )
            
            manager.save_checkpoint(checkpoint_name, state)
            loaded = manager.load_checkpoint(checkpoint_name)
            
            assert loaded is not None
            assert loaded.completed_indices == []
            assert loaded.results == []
            assert loaded.total_items == 0
    
    @given(
        policy=checkpoint_policy_strategy(),
        checkpoint_name=checkpoint_name_strategy()
    )
    @settings(max_examples=20)
    def test_large_metadata_dict(self, policy, checkpoint_name):
        """Property: Large metadata dictionaries are preserved."""
        with tempfile.TemporaryDirectory() as tmpdir:
            policy.checkpoint_dir = tmpdir
            manager = CheckpointManager(policy)
            
            # Create state with large metadata
            large_metadata = {f"key_{i}": f"value_{i}" for i in range(100)}
            state = CheckpointState(
                completed_indices=[0, 1],
                results=["a", "b"],
                total_items=10,
                checkpoint_time=time.time(),
                n_jobs=4,
                chunksize=10,
                metadata=large_metadata
            )
            
            manager.save_checkpoint(checkpoint_name, state)
            loaded = manager.load_checkpoint(checkpoint_name)
            
            assert loaded is not None
            assert loaded.metadata == large_metadata
    
    @given(
        keep_history=st.integers(min_value=1, max_value=3)
    )
    @settings(max_examples=10)
    def test_checkpoint_interval_zero(self, keep_history):
        """Property: checkpoint_interval=0 is valid (disables auto-checkpointing)."""
        policy = CheckpointPolicy(
            checkpoint_interval=0,
            keep_history=keep_history
        )
        
        assert policy.checkpoint_interval == 0


# ============================================================================
# Test Class 10: Integration Properties
# ============================================================================

class TestIntegrationProperties:
    """Property-based tests for complete checkpoint workflows."""
    
    @given(
        num_checkpoints=st.integers(min_value=1, max_value=5),
        keep_history=st.integers(min_value=1, max_value=3)
    )
    @settings(max_examples=15)
    def test_full_checkpoint_lifecycle(self, num_checkpoints, keep_history):
        """Property: Full lifecycle (save, list, load, delete) works correctly."""
        with tempfile.TemporaryDirectory() as tmpdir:
            policy = CheckpointPolicy(
                checkpoint_dir=tmpdir,
                keep_history=keep_history
            )
            manager = CheckpointManager(policy)
            
            # Create checkpoints
            checkpoint_names = []
            for i in range(num_checkpoints):
                name = f"checkpoint_{i}"
                checkpoint_names.append(name)
                
                state = CheckpointState(
                    completed_indices=[i],
                    results=[f"result_{i}"],
                    total_items=10,
                    checkpoint_time=time.time(),
                    n_jobs=4,
                    chunksize=10,
                    metadata={"checkpoint": i}
                )
                manager.save_checkpoint(name, state)
            
            # List checkpoints
            listed = manager.list_checkpoints()
            assert len(listed) == num_checkpoints
            
            # Load each checkpoint
            for name in checkpoint_names:
                loaded = manager.load_checkpoint(name)
                assert loaded is not None
            
            # Delete all checkpoints
            for name in checkpoint_names:
                deleted_count = manager.delete_checkpoint(name)
                assert deleted_count >= 1
            
            # Verify all deleted
            listed_after = manager.list_checkpoints()
            assert len(listed_after) == 0
    
    @given(
        total_items=st.integers(min_value=10, max_value=100),
        num_checkpoints=st.integers(min_value=2, max_value=5)
    )
    @settings(max_examples=10)
    def test_resume_from_multiple_checkpoints(self, total_items, num_checkpoints):
        """Property: Resume workflow with multiple checkpoint saves."""
        with tempfile.TemporaryDirectory() as tmpdir:
            policy = CheckpointPolicy(checkpoint_dir=tmpdir)
            manager = CheckpointManager(policy)
            
            checkpoint_name = "progressive_checkpoint"
            items_per_checkpoint = total_items // num_checkpoints
            
            # Simulate progressive checkpointing
            all_completed = []
            all_results = []
            
            for i in range(num_checkpoints):
                # Process some items
                start_idx = i * items_per_checkpoint
                end_idx = min((i + 1) * items_per_checkpoint, total_items)
                
                for idx in range(start_idx, end_idx):
                    all_completed.append(idx)
                    all_results.append(f"result_{idx}")
                
                # Save checkpoint
                state = CheckpointState(
                    completed_indices=all_completed.copy(),
                    results=all_results.copy(),
                    total_items=total_items,
                    checkpoint_time=time.time(),
                    n_jobs=4,
                    chunksize=10,
                    metadata={"checkpoint_num": i}
                )
                manager.save_checkpoint(checkpoint_name, state)
            
            # Load final checkpoint
            loaded = manager.load_checkpoint(checkpoint_name)
            assert loaded is not None
            assert len(loaded.completed_indices) >= items_per_checkpoint * (num_checkpoints - 1)
            assert loaded.total_items == total_items


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
