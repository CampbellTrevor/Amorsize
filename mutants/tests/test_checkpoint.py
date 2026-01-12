"""
Tests for checkpoint/resume functionality.
"""

import json
import os
import pickle
import shutil
import tempfile
import time
from pathlib import Path

import pytest

from amorsize.checkpoint import (
    CheckpointManager,
    CheckpointPolicy,
    CheckpointState,
    get_pending_items,
    merge_results,
)


class TestCheckpointPolicy:
    """Tests for CheckpointPolicy configuration."""
    
    def test_default_policy(self):
        """Test default policy values."""
        policy = CheckpointPolicy()
        
        assert policy.checkpoint_dir == "./checkpoints"
        assert policy.checkpoint_interval == 100
        assert policy.checkpoint_name is None
        assert policy.save_format == "pickle"
        assert policy.keep_history == 2
        assert policy.auto_cleanup is True
    
    def test_custom_policy(self):
        """Test custom policy values."""
        policy = CheckpointPolicy(
            checkpoint_dir="/tmp/checkpoints",
            checkpoint_interval=50,
            checkpoint_name="my_checkpoint",
            save_format="json",
            keep_history=3,
            auto_cleanup=False
        )
        
        assert policy.checkpoint_dir == "/tmp/checkpoints"
        assert policy.checkpoint_interval == 50
        assert policy.checkpoint_name == "my_checkpoint"
        assert policy.save_format == "json"
        assert policy.keep_history == 3
        assert policy.auto_cleanup is False
    
    def test_invalid_checkpoint_interval(self):
        """Test that negative checkpoint_interval raises ValueError."""
        with pytest.raises(ValueError, match="checkpoint_interval must be >= 0"):
            CheckpointPolicy(checkpoint_interval=-1)
    
    def test_invalid_save_format(self):
        """Test that invalid save_format raises ValueError."""
        with pytest.raises(ValueError, match="save_format must be"):
            CheckpointPolicy(save_format="xml")
    
    def test_invalid_keep_history(self):
        """Test that invalid keep_history raises ValueError."""
        with pytest.raises(ValueError, match="keep_history must be >= 1"):
            CheckpointPolicy(keep_history=0)


class TestCheckpointState:
    """Tests for CheckpointState data class."""
    
    def test_state_creation(self):
        """Test creating checkpoint state."""
        state = CheckpointState(
            completed_indices=[0, 1, 2],
            results=["a", "b", "c"],
            total_items=10,
            checkpoint_time=time.time(),
            n_jobs=4,
            chunksize=10,
            metadata={"executor": "multiprocess"}
        )
        
        assert state.completed_indices == [0, 1, 2]
        assert state.results == ["a", "b", "c"]
        assert state.total_items == 10
        assert state.n_jobs == 4
        assert state.chunksize == 10
        assert state.metadata["executor"] == "multiprocess"
    
    def test_state_to_dict(self):
        """Test converting state to dictionary."""
        state = CheckpointState(
            completed_indices=[0, 1],
            results=["a", "b"],
            total_items=5,
            checkpoint_time=123.456,
            n_jobs=2,
            chunksize=5,
            metadata={"test": "value"}
        )
        
        data = state.to_dict()
        
        assert isinstance(data, dict)
        assert data["completed_indices"] == [0, 1]
        assert data["results"] == ["a", "b"]
        assert data["total_items"] == 5
        assert data["checkpoint_time"] == 123.456
        assert data["n_jobs"] == 2
        assert data["chunksize"] == 5
        assert data["metadata"] == {"test": "value"}
    
    def test_state_from_dict(self):
        """Test creating state from dictionary."""
        data = {
            "completed_indices": [0, 1],
            "results": ["a", "b"],
            "total_items": 5,
            "checkpoint_time": 123.456,
            "n_jobs": 2,
            "chunksize": 5,
            "metadata": {"test": "value"}
        }
        
        state = CheckpointState.from_dict(data)
        
        assert state.completed_indices == [0, 1]
        assert state.results == ["a", "b"]
        assert state.total_items == 5
        assert state.checkpoint_time == 123.456
        assert state.n_jobs == 2
        assert state.chunksize == 5
        assert state.metadata == {"test": "value"}


class TestCheckpointManager:
    """Tests for CheckpointManager."""
    
    @pytest.fixture
    def temp_dir(self):
        """Create temporary directory for checkpoints."""
        temp_dir = tempfile.mkdtemp()
        yield temp_dir
        # Cleanup
        shutil.rmtree(temp_dir, ignore_errors=True)
    
    @pytest.fixture
    def policy(self, temp_dir):
        """Create policy with temporary directory."""
        return CheckpointPolicy(checkpoint_dir=temp_dir)
    
    @pytest.fixture
    def manager(self, policy):
        """Create checkpoint manager."""
        return CheckpointManager(policy)
    
    def test_manager_creation(self, manager, temp_dir):
        """Test creating checkpoint manager."""
        assert manager.policy.checkpoint_dir == temp_dir
        assert os.path.exists(temp_dir)
    
    def test_generate_checkpoint_name(self, manager):
        """Test generating checkpoint name from function."""
        def test_func(x):
            return x * 2
        
        name = manager._generate_checkpoint_name(test_func)
        
        assert "test_func" in name
        assert "_" in name  # Should have timestamp
    
    def test_save_and_load_checkpoint_pickle(self, manager, temp_dir):
        """Test saving and loading checkpoint with pickle format."""
        state = CheckpointState(
            completed_indices=[0, 1, 2, 3],
            results=[0, 2, 4, 6],
            total_items=10,
            checkpoint_time=time.time(),
            n_jobs=4,
            chunksize=10,
            metadata={"format": "pickle"}
        )
        
        # Save checkpoint
        checkpoint_path = manager.save_checkpoint("test_checkpoint", state)
        
        assert checkpoint_path.exists()
        assert checkpoint_path.suffix == ".pkl"
        
        # Load checkpoint
        loaded_state = manager.load_checkpoint("test_checkpoint")
        
        assert loaded_state is not None
        assert loaded_state.completed_indices == [0, 1, 2, 3]
        assert loaded_state.results == [0, 2, 4, 6]
        assert loaded_state.total_items == 10
        assert loaded_state.n_jobs == 4
        assert loaded_state.chunksize == 10
        assert loaded_state.metadata == {"format": "pickle"}
    
    def test_save_and_load_checkpoint_json(self, temp_dir):
        """Test saving and loading checkpoint with JSON format."""
        policy = CheckpointPolicy(checkpoint_dir=temp_dir, save_format="json")
        manager = CheckpointManager(policy)
        
        state = CheckpointState(
            completed_indices=[0, 1, 2],
            results=["a", "b", "c"],
            total_items=5,
            checkpoint_time=123.456,
            n_jobs=2,
            chunksize=5,
            metadata={"format": "json"}
        )
        
        # Save checkpoint
        checkpoint_path = manager.save_checkpoint("test_json", state)
        
        assert checkpoint_path.exists()
        assert checkpoint_path.suffix == ".json"
        
        # Verify JSON is human-readable
        with open(checkpoint_path, 'r') as f:
            data = json.load(f)
            assert data["completed_indices"] == [0, 1, 2]
            assert data["results"] == ["a", "b", "c"]
        
        # Load checkpoint
        loaded_state = manager.load_checkpoint("test_json")
        
        assert loaded_state is not None
        assert loaded_state.completed_indices == [0, 1, 2]
        assert loaded_state.results == ["a", "b", "c"]
    
    def test_checkpoint_versioning(self, manager, temp_dir):
        """Test that old checkpoints are versioned."""
        state1 = CheckpointState(
            completed_indices=[0, 1],
            results=["a", "b"],
            total_items=5,
            checkpoint_time=time.time(),
            n_jobs=2,
            chunksize=5,
            metadata={"version": 1}
        )
        
        state2 = CheckpointState(
            completed_indices=[0, 1, 2, 3],
            results=["a", "b", "c", "d"],
            total_items=5,
            checkpoint_time=time.time(),
            n_jobs=2,
            chunksize=5,
            metadata={"version": 2}
        )
        
        # Save first checkpoint
        manager.save_checkpoint("versioned", state1)
        
        # Save second checkpoint (should version the first)
        manager.save_checkpoint("versioned", state2)
        
        # Latest checkpoint should be version 2
        latest = manager.load_checkpoint("versioned")
        assert latest.metadata["version"] == 2
        
        # Version 1 should exist
        v1_path = manager._get_checkpoint_path("versioned", 1)
        assert v1_path.exists()
    
    def test_checkpoint_history_limit(self, temp_dir):
        """Test that old checkpoint versions are cleaned up."""
        policy = CheckpointPolicy(checkpoint_dir=temp_dir, keep_history=2)
        manager = CheckpointManager(policy)
        
        # Create 4 checkpoints
        for i in range(4):
            state = CheckpointState(
                completed_indices=list(range(i + 1)),
                results=list(range(i + 1)),
                total_items=10,
                checkpoint_time=time.time(),
                n_jobs=2,
                chunksize=5,
                metadata={"version": i}
            )
            manager.save_checkpoint("limited", state)
            time.sleep(0.01)  # Ensure different timestamps
        
        # Should have: current + keep_history versions
        # With keep_history=2, we keep current + 2 old versions = 3 total
        assert manager._get_checkpoint_path("limited", 0).exists()  # current
        assert manager._get_checkpoint_path("limited", 1).exists()  # v1
        assert manager._get_checkpoint_path("limited", 2).exists()  # v2
        assert not manager._get_checkpoint_path("limited", 3).exists()  # v3 (should be deleted)
    
    def test_load_nonexistent_checkpoint(self, manager):
        """Test loading checkpoint that doesn't exist."""
        loaded = manager.load_checkpoint("nonexistent")
        assert loaded is None
    
    def test_delete_checkpoint(self, manager):
        """Test deleting checkpoint."""
        state = CheckpointState(
            completed_indices=[0, 1],
            results=["a", "b"],
            total_items=5,
            checkpoint_time=time.time(),
            n_jobs=2,
            chunksize=5,
            metadata={}
        )
        
        # Save checkpoint
        manager.save_checkpoint("to_delete", state)
        
        # Verify it exists
        assert manager.load_checkpoint("to_delete") is not None
        
        # Delete it
        deleted_count = manager.delete_checkpoint("to_delete")
        
        assert deleted_count >= 1
        assert manager.load_checkpoint("to_delete") is None
    
    def test_delete_checkpoint_with_versions(self, manager):
        """Test deleting checkpoint with multiple versions."""
        # Create multiple versions
        for i in range(3):
            state = CheckpointState(
                completed_indices=list(range(i + 1)),
                results=list(range(i + 1)),
                total_items=10,
                checkpoint_time=time.time(),
                n_jobs=2,
                chunksize=5,
                metadata={"version": i}
            )
            manager.save_checkpoint("multi_version", state)
        
        # Delete all versions
        deleted_count = manager.delete_checkpoint("multi_version")
        
        assert deleted_count >= 2  # At least current + v1
        assert manager.load_checkpoint("multi_version") is None
    
    def test_list_checkpoints(self, manager):
        """Test listing available checkpoints."""
        # Create several checkpoints
        for name in ["checkpoint1", "checkpoint2", "checkpoint3"]:
            state = CheckpointState(
                completed_indices=[0],
                results=["a"],
                total_items=5,
                checkpoint_time=time.time(),
                n_jobs=2,
                chunksize=5,
                metadata={}
            )
            manager.save_checkpoint(name, state)
        
        checkpoints = manager.list_checkpoints()
        
        assert "checkpoint1" in checkpoints
        assert "checkpoint2" in checkpoints
        assert "checkpoint3" in checkpoints
    
    def test_list_checkpoints_empty(self, temp_dir):
        """Test listing checkpoints when directory is empty."""
        policy = CheckpointPolicy(checkpoint_dir=temp_dir)
        manager = CheckpointManager(policy)
        
        checkpoints = manager.list_checkpoints()
        
        assert checkpoints == []
    
    def test_thread_safety(self, manager):
        """Test thread-safe checkpoint operations."""
        import threading
        
        def save_checkpoint(thread_id):
            for i in range(5):
                state = CheckpointState(
                    completed_indices=[thread_id * 10 + i],
                    results=[thread_id * 10 + i],
                    total_items=100,
                    checkpoint_time=time.time(),
                    n_jobs=2,
                    chunksize=5,
                    metadata={"thread": thread_id}
                )
                manager.save_checkpoint(f"thread_{thread_id}", state)
        
        # Create multiple threads
        threads = [threading.Thread(target=save_checkpoint, args=(i,)) for i in range(3)]
        
        # Start all threads
        for t in threads:
            t.start()
        
        # Wait for completion
        for t in threads:
            t.join()
        
        # Verify all checkpoints exist
        for i in range(3):
            state = manager.load_checkpoint(f"thread_{i}")
            assert state is not None


class TestCheckpointHelpers:
    """Tests for checkpoint helper functions."""
    
    def test_get_pending_items_no_checkpoint(self):
        """Test getting pending items when no checkpoint exists."""
        data = [1, 2, 3, 4, 5]
        
        pending_indices, pending_items = get_pending_items(data, None)
        
        assert pending_indices == [0, 1, 2, 3, 4]
        assert pending_items == [1, 2, 3, 4, 5]
    
    def test_get_pending_items_with_checkpoint(self):
        """Test getting pending items with existing checkpoint."""
        data = [1, 2, 3, 4, 5]
        
        state = CheckpointState(
            completed_indices=[0, 1, 3],
            results=[1, 2, 4],
            total_items=5,
            checkpoint_time=time.time(),
            n_jobs=2,
            chunksize=5,
            metadata={}
        )
        
        pending_indices, pending_items = get_pending_items(data, state)
        
        assert pending_indices == [2, 4]
        assert pending_items == [3, 5]
    
    def test_get_pending_items_all_complete(self):
        """Test getting pending items when all items are complete."""
        data = [1, 2, 3]
        
        state = CheckpointState(
            completed_indices=[0, 1, 2],
            results=[1, 2, 3],
            total_items=3,
            checkpoint_time=time.time(),
            n_jobs=2,
            chunksize=5,
            metadata={}
        )
        
        pending_indices, pending_items = get_pending_items(data, state)
        
        assert pending_indices == []
        assert pending_items == []
    
    def test_merge_results_no_checkpoint(self):
        """Test merging results when no checkpoint exists."""
        new_results = [1, 2, 3, 4, 5]
        pending_indices = [0, 1, 2, 3, 4]
        
        final_results = merge_results(new_results, pending_indices, None, 5)
        
        assert final_results == [1, 2, 3, 4, 5]
    
    def test_merge_results_with_checkpoint(self):
        """Test merging results with existing checkpoint."""
        state = CheckpointState(
            completed_indices=[0, 1, 3],
            results=[10, 20, 40],
            total_items=5,
            checkpoint_time=time.time(),
            n_jobs=2,
            chunksize=5,
            metadata={}
        )
        
        new_results = [30, 50]
        pending_indices = [2, 4]
        
        final_results = merge_results(new_results, pending_indices, state, 5)
        
        assert final_results == [10, 20, 30, 40, 50]
    
    def test_merge_results_preserves_order(self):
        """Test that merge preserves original data order."""
        state = CheckpointState(
            completed_indices=[1, 3, 5],
            results=["b", "d", "f"],
            total_items=6,
            checkpoint_time=time.time(),
            n_jobs=2,
            chunksize=5,
            metadata={}
        )
        
        new_results = ["a", "c", "e"]
        pending_indices = [0, 2, 4]
        
        final_results = merge_results(new_results, pending_indices, state, 6)
        
        assert final_results == ["a", "b", "c", "d", "e", "f"]


class TestCheckpointEdgeCases:
    """Tests for edge cases and error conditions."""
    
    def test_checkpoint_with_complex_objects(self):
        """Test checkpointing with complex Python objects."""
        temp_dir = tempfile.mkdtemp()
        try:
            policy = CheckpointPolicy(checkpoint_dir=temp_dir, save_format="pickle")
            manager = CheckpointManager(policy)
            
            # Create state with complex objects
            state = CheckpointState(
                completed_indices=[0, 1],
                results=[{"key": "value"}, [1, 2, 3]],
                total_items=5,
                checkpoint_time=time.time(),
                n_jobs=2,
                chunksize=5,
                metadata={"nested": {"data": [1, 2, 3]}}
            )
            
            # Save and load
            manager.save_checkpoint("complex", state)
            loaded = manager.load_checkpoint("complex")
            
            assert loaded.results[0] == {"key": "value"}
            assert loaded.results[1] == [1, 2, 3]
            assert loaded.metadata["nested"]["data"] == [1, 2, 3]
        
        finally:
            shutil.rmtree(temp_dir, ignore_errors=True)
    
    def test_checkpoint_with_empty_results(self):
        """Test checkpointing with empty results."""
        temp_dir = tempfile.mkdtemp()
        try:
            policy = CheckpointPolicy(checkpoint_dir=temp_dir)
            manager = CheckpointManager(policy)
            
            state = CheckpointState(
                completed_indices=[],
                results=[],
                total_items=10,
                checkpoint_time=time.time(),
                n_jobs=2,
                chunksize=5,
                metadata={}
            )
            
            manager.save_checkpoint("empty", state)
            loaded = manager.load_checkpoint("empty")
            
            assert loaded.completed_indices == []
            assert loaded.results == []
            assert loaded.total_items == 10
        
        finally:
            shutil.rmtree(temp_dir, ignore_errors=True)
    
    def test_checkpoint_with_zero_interval(self):
        """Test policy with checkpoint_interval=0 (disabled)."""
        policy = CheckpointPolicy(checkpoint_interval=0)
        
        assert policy.checkpoint_interval == 0
