"""
Tests for Dead Letter Queue (DLQ) functionality.
"""

import json
import os
import pickle
import tempfile
import threading
import time
from unittest.mock import patch

import pytest

from amorsize.dead_letter_queue import (
    DLQEntry,
    DLQFormat,
    DLQPolicy,
    DeadLetterQueue,
    replay_failed_items,
)


# Global class for pickle testing (must be at module level to be picklable)
class CustomObject:
    """Test object for pickle serialization."""
    def __init__(self, value):
        self.value = value


class TestDLQPolicy:
    """Tests for DLQPolicy configuration validation."""
    
    def test_default_policy(self):
        """Test that default policy has sensible values."""
        policy = DLQPolicy()
        assert policy.directory == ".amorsize_dlq"
        assert policy.format == DLQFormat.JSON
        assert policy.max_entries == 10000
        assert policy.include_traceback is True
        assert policy.auto_persist is True
    
    def test_custom_policy(self):
        """Test creating policy with custom values."""
        policy = DLQPolicy(
            directory="/tmp/my_dlq",
            format=DLQFormat.PICKLE,
            max_entries=100,
            include_traceback=False,
            auto_persist=False
        )
        assert policy.directory == "/tmp/my_dlq"
        assert policy.format == DLQFormat.PICKLE
        assert policy.max_entries == 100
        assert policy.include_traceback is False
        assert policy.auto_persist is False
    
    def test_invalid_directory(self):
        """Test that empty directory is rejected."""
        with pytest.raises(ValueError, match="directory must be a non-empty string"):
            DLQPolicy(directory="")
    
    def test_invalid_format(self):
        """Test that invalid format is rejected."""
        with pytest.raises(ValueError, match="format must be a DLQFormat enum value"):
            DLQPolicy(format="invalid")
    
    def test_invalid_max_entries(self):
        """Test that negative max_entries is rejected."""
        with pytest.raises(ValueError, match="max_entries must be a non-negative integer"):
            DLQPolicy(max_entries=-1)
    
    def test_invalid_include_traceback(self):
        """Test that non-boolean include_traceback is rejected."""
        with pytest.raises(ValueError, match="include_traceback must be a boolean"):
            DLQPolicy(include_traceback="yes")
    
    def test_invalid_auto_persist(self):
        """Test that non-boolean auto_persist is rejected."""
        with pytest.raises(ValueError, match="auto_persist must be a boolean"):
            DLQPolicy(auto_persist=1)


class TestDLQEntry:
    """Tests for DLQEntry data structure."""
    
    def test_entry_creation(self):
        """Test creating a DLQ entry."""
        entry = DLQEntry(
            item={"id": 123},
            error_type="ValueError",
            error_message="Invalid value",
            timestamp=time.time(),
            retry_count=3,
            metadata={"worker": "w1"}
        )
        assert entry.item == {"id": 123}
        assert entry.error_type == "ValueError"
        assert entry.error_message == "Invalid value"
        assert entry.retry_count == 3
        assert entry.metadata["worker"] == "w1"
    
    def test_entry_to_dict(self):
        """Test converting entry to dictionary."""
        entry = DLQEntry(
            item=42,
            error_type="RuntimeError",
            error_message="Something went wrong",
            timestamp=1234567890.0,
            traceback="Traceback here",
            retry_count=2,
            metadata={"source": "test"}
        )
        data = entry.to_dict()
        assert data["item"] == 42
        assert data["error_type"] == "RuntimeError"
        assert data["error_message"] == "Something went wrong"
        assert data["timestamp"] == 1234567890.0
        assert data["traceback"] == "Traceback here"
        assert data["retry_count"] == 2
        assert data["metadata"]["source"] == "test"
    
    def test_entry_from_dict(self):
        """Test creating entry from dictionary."""
        data = {
            "item": "test_item",
            "error_type": "KeyError",
            "error_message": "key not found",
            "timestamp": 9999999.0,
            "traceback": None,
            "retry_count": 5,
            "metadata": {"category": "A"}
        }
        entry = DLQEntry.from_dict(data)
        assert entry.item == "test_item"
        assert entry.error_type == "KeyError"
        assert entry.error_message == "key not found"
        assert entry.timestamp == 9999999.0
        assert entry.traceback is None
        assert entry.retry_count == 5
        assert entry.metadata["category"] == "A"
    
    def test_entry_round_trip(self):
        """Test that to_dict/from_dict round-trip preserves data."""
        original = DLQEntry(
            item=[1, 2, 3],
            error_type="IndexError",
            error_message="list index out of range",
            timestamp=time.time(),
            retry_count=1
        )
        data = original.to_dict()
        restored = DLQEntry.from_dict(data)
        assert restored.item == original.item
        assert restored.error_type == original.error_type
        assert restored.error_message == original.error_message
        assert restored.timestamp == original.timestamp
        assert restored.retry_count == original.retry_count


class TestDeadLetterQueue:
    """Tests for DeadLetterQueue core functionality."""
    
    def test_queue_initialization(self):
        """Test creating a DLQ with default policy."""
        with tempfile.TemporaryDirectory() as tmpdir:
            policy = DLQPolicy(directory=tmpdir, auto_persist=False)
            dlq = DeadLetterQueue(policy)
            assert dlq.size() == 0
            assert dlq.get_entries() == []
    
    def test_add_entry(self):
        """Test adding a failed item to the queue."""
        with tempfile.TemporaryDirectory() as tmpdir:
            policy = DLQPolicy(directory=tmpdir, auto_persist=False)
            dlq = DeadLetterQueue(policy)
            
            error = ValueError("test error")
            dlq.add(item=123, error=error, retry_count=2)
            
            assert dlq.size() == 1
            entries = dlq.get_entries()
            assert len(entries) == 1
            assert entries[0].item == 123
            assert entries[0].error_type == "ValueError"
            assert entries[0].error_message == "test error"
            assert entries[0].retry_count == 2
    
    def test_add_multiple_entries(self):
        """Test adding multiple failed items."""
        with tempfile.TemporaryDirectory() as tmpdir:
            policy = DLQPolicy(directory=tmpdir, auto_persist=False)
            dlq = DeadLetterQueue(policy)
            
            for i in range(5):
                dlq.add(item=i, error=RuntimeError(f"error {i}"))
            
            assert dlq.size() == 5
            entries = dlq.get_entries()
            assert [e.item for e in entries] == [0, 1, 2, 3, 4]
    
    def test_add_with_metadata(self):
        """Test adding entry with custom metadata."""
        with tempfile.TemporaryDirectory() as tmpdir:
            policy = DLQPolicy(directory=tmpdir, auto_persist=False)
            dlq = DeadLetterQueue(policy)
            
            metadata = {"function": "process_image", "worker_id": "w7"}
            dlq.add(item="image.jpg", error=IOError("file not found"), metadata=metadata)
            
            entries = dlq.get_entries()
            assert entries[0].metadata["function"] == "process_image"
            assert entries[0].metadata["worker_id"] == "w7"
    
    def test_clear_queue(self):
        """Test clearing all entries from the queue."""
        with tempfile.TemporaryDirectory() as tmpdir:
            policy = DLQPolicy(directory=tmpdir, auto_persist=False)
            dlq = DeadLetterQueue(policy)
            
            # Add some entries
            for i in range(3):
                dlq.add(item=i, error=Exception(f"error {i}"))
            
            assert dlq.size() == 3
            
            # Clear the queue
            cleared_count = dlq.clear()
            assert cleared_count == 3
            assert dlq.size() == 0
            assert dlq.get_entries() == []
    
    def test_max_entries_limit(self):
        """Test that queue respects max_entries limit."""
        with tempfile.TemporaryDirectory() as tmpdir:
            policy = DLQPolicy(directory=tmpdir, max_entries=10, auto_persist=False)
            dlq = DeadLetterQueue(policy)
            
            # Add 15 entries (exceeds limit of 10)
            for i in range(15):
                dlq.add(item=i, error=Exception(f"error {i}"))
            
            # Should only keep the last 10
            assert dlq.size() == 10
            entries = dlq.get_entries()
            # Oldest entries (0-4) should be removed
            assert entries[0].item == 5
            assert entries[-1].item == 14
    
    def test_get_entries_returns_copy(self):
        """Test that get_entries returns a copy, not reference."""
        with tempfile.TemporaryDirectory() as tmpdir:
            policy = DLQPolicy(directory=tmpdir, auto_persist=False)
            dlq = DeadLetterQueue(policy)
            
            dlq.add(item=1, error=Exception("error"))
            entries1 = dlq.get_entries()
            entries2 = dlq.get_entries()
            
            # Should be equal but not same object
            assert entries1 == entries2
            assert entries1 is not entries2
    
    def test_get_summary_empty(self):
        """Test summary for empty queue."""
        with tempfile.TemporaryDirectory() as tmpdir:
            policy = DLQPolicy(directory=tmpdir, auto_persist=False)
            dlq = DeadLetterQueue(policy)
            
            summary = dlq.get_summary()
            assert summary["total_entries"] == 0
            assert summary["error_types"] == {}
            assert summary["avg_retry_count"] == 0.0
            assert summary["oldest_timestamp"] is None
            assert summary["newest_timestamp"] is None
    
    def test_get_summary_with_entries(self):
        """Test summary with multiple entries."""
        with tempfile.TemporaryDirectory() as tmpdir:
            policy = DLQPolicy(directory=tmpdir, auto_persist=False)
            dlq = DeadLetterQueue(policy)
            
            # Add entries with different error types and retry counts
            dlq.add(item=1, error=ValueError("err1"), retry_count=1)
            dlq.add(item=2, error=ValueError("err2"), retry_count=2)
            dlq.add(item=3, error=RuntimeError("err3"), retry_count=3)
            
            summary = dlq.get_summary()
            assert summary["total_entries"] == 3
            assert summary["error_types"]["ValueError"] == 2
            assert summary["error_types"]["RuntimeError"] == 1
            assert summary["avg_retry_count"] == 2.0  # (1+2+3)/3
            assert summary["oldest_timestamp"] is not None
            assert summary["newest_timestamp"] is not None
            assert summary["oldest_timestamp"] <= summary["newest_timestamp"]


class TestDLQPersistence:
    """Tests for saving and loading DLQ to/from disk."""
    
    def test_save_and_load_json(self):
        """Test saving and loading DLQ in JSON format."""
        with tempfile.TemporaryDirectory() as tmpdir:
            policy = DLQPolicy(directory=tmpdir, format=DLQFormat.JSON, auto_persist=False)
            dlq = DeadLetterQueue(policy)
            
            # Add some entries
            dlq.add(item={"id": 1}, error=ValueError("test"))
            dlq.add(item={"id": 2}, error=RuntimeError("test2"))
            
            # Save to disk
            filepath = dlq.save()
            assert os.path.exists(filepath)
            
            # Create new DLQ and load
            dlq2 = DeadLetterQueue(policy)
            count = dlq2.load(filepath)
            
            assert count == 2
            assert dlq2.size() == 2
            entries = dlq2.get_entries()
            assert entries[0].item == {"id": 1}
            assert entries[0].error_type == "ValueError"
    
    def test_save_and_load_pickle(self):
        """Test saving and loading DLQ in Pickle format."""
        with tempfile.TemporaryDirectory() as tmpdir:
            policy = DLQPolicy(directory=tmpdir, format=DLQFormat.PICKLE, auto_persist=False)
            dlq = DeadLetterQueue(policy)
            
            # Add entries with complex objects (using module-level class)
            dlq.add(item=CustomObject(42), error=Exception("test"))
            
            # Save and load
            filepath = dlq.save()
            dlq2 = DeadLetterQueue(policy)
            dlq2.load(filepath)
            
            entries = dlq2.get_entries()
            assert entries[0].item.value == 42
    
    def test_auto_persist_on_add(self):
        """Test that entries are auto-persisted when auto_persist=True."""
        with tempfile.TemporaryDirectory() as tmpdir:
            policy = DLQPolicy(directory=tmpdir, format=DLQFormat.JSON, auto_persist=True)
            dlq = DeadLetterQueue(policy)
            
            # Add entry (should auto-persist)
            dlq.add(item=123, error=ValueError("test"))
            
            # Check that file was created
            filepath = os.path.join(tmpdir, "dlq.json")
            assert os.path.exists(filepath)
            
            # Load from file to verify
            with open(filepath, 'r') as f:
                data = json.load(f)
            assert len(data) == 1
            assert data[0]["item"] == 123
    
    def test_auto_persist_on_clear(self):
        """Test that clear is persisted when auto_persist=True."""
        with tempfile.TemporaryDirectory() as tmpdir:
            policy = DLQPolicy(directory=tmpdir, format=DLQFormat.JSON, auto_persist=True)
            dlq = DeadLetterQueue(policy)
            
            # Add and clear
            dlq.add(item=1, error=Exception("test"))
            dlq.clear()
            
            # File should exist and be empty
            filepath = os.path.join(tmpdir, "dlq.json")
            assert os.path.exists(filepath)
            with open(filepath, 'r') as f:
                data = json.load(f)
            assert len(data) == 0
    
    def test_load_nonexistent_file(self):
        """Test loading from nonexistent file raises error."""
        with tempfile.TemporaryDirectory() as tmpdir:
            policy = DLQPolicy(directory=tmpdir, auto_persist=False)
            dlq = DeadLetterQueue(policy)
            
            with pytest.raises(IOError, match="DLQ file not found"):
                dlq.load("/nonexistent/path/dlq.json")
    
    def test_custom_filepath(self):
        """Test saving and loading with custom filepath."""
        with tempfile.TemporaryDirectory() as tmpdir:
            policy = DLQPolicy(directory=tmpdir, auto_persist=False)
            dlq = DeadLetterQueue(policy)
            
            dlq.add(item="test", error=Exception("err"))
            
            custom_path = os.path.join(tmpdir, "my_custom_dlq.json")
            dlq.save(custom_path)
            assert os.path.exists(custom_path)
            
            dlq2 = DeadLetterQueue(policy)
            dlq2.load(custom_path)
            assert dlq2.size() == 1


class TestDLQThreadSafety:
    """Tests for thread safety of DLQ operations."""
    
    def test_concurrent_add(self):
        """Test that concurrent adds are thread-safe."""
        with tempfile.TemporaryDirectory() as tmpdir:
            policy = DLQPolicy(directory=tmpdir, auto_persist=False)
            dlq = DeadLetterQueue(policy)
            
            def add_items(start, count):
                for i in range(start, start + count):
                    dlq.add(item=i, error=Exception(f"error {i}"))
            
            # Start multiple threads adding items
            threads = []
            for i in range(5):
                t = threading.Thread(target=add_items, args=(i * 10, 10))
                threads.append(t)
                t.start()
            
            # Wait for all threads
            for t in threads:
                t.join()
            
            # Should have all 50 items
            assert dlq.size() == 50
    
    def test_concurrent_get_entries(self):
        """Test that concurrent reads are safe."""
        with tempfile.TemporaryDirectory() as tmpdir:
            policy = DLQPolicy(directory=tmpdir, auto_persist=False)
            dlq = DeadLetterQueue(policy)
            
            # Add some entries
            for i in range(10):
                dlq.add(item=i, error=Exception(f"error {i}"))
            
            results = []
            
            def read_entries():
                entries = dlq.get_entries()
                results.append(len(entries))
            
            # Multiple threads reading simultaneously
            threads = [threading.Thread(target=read_entries) for _ in range(10)]
            for t in threads:
                t.start()
            for t in threads:
                t.join()
            
            # All reads should see same size
            assert all(r == 10 for r in results)


class TestReplayFailedItems:
    """Tests for replay_failed_items helper function."""
    
    def test_replay_all_succeed(self):
        """Test replay where all items succeed."""
        with tempfile.TemporaryDirectory() as tmpdir:
            policy = DLQPolicy(directory=tmpdir, auto_persist=False)
            dlq = DeadLetterQueue(policy)
            
            # Add failed items
            dlq.add(item=1, error=Exception("err"))
            dlq.add(item=2, error=Exception("err"))
            dlq.add(item=3, error=Exception("err"))
            
            # Replay with function that succeeds
            def process(x):
                return x * 2
            
            results, still_failed = replay_failed_items(dlq, process)
            
            assert results == [2, 4, 6]
            assert still_failed == []
            assert dlq.size() == 0  # Should be cleared on success
    
    def test_replay_all_fail(self):
        """Test replay where all items fail again."""
        with tempfile.TemporaryDirectory() as tmpdir:
            policy = DLQPolicy(directory=tmpdir, auto_persist=False)
            dlq = DeadLetterQueue(policy)
            
            # Add failed items
            dlq.add(item=1, error=ValueError("err1"))
            dlq.add(item=2, error=ValueError("err2"))
            
            # Replay with function that always fails
            def process(x):
                raise RuntimeError(f"still failing {x}")
            
            results, still_failed = replay_failed_items(dlq, process)
            
            assert results == []
            assert len(still_failed) == 2
            assert dlq.size() == 2  # Items re-added to queue
            
            # Check retry count was incremented
            entries = dlq.get_entries()
            assert all(e.retry_count == 1 for e in entries)
    
    def test_replay_mixed_results(self):
        """Test replay where some items succeed and some fail."""
        with tempfile.TemporaryDirectory() as tmpdir:
            policy = DLQPolicy(directory=tmpdir, auto_persist=False)
            dlq = DeadLetterQueue(policy)
            
            # Add items
            for i in range(1, 6):
                dlq.add(item=i, error=Exception(f"err{i}"))
            
            # Function that fails on even numbers
            def process(x):
                if x % 2 == 0:
                    raise ValueError(f"even number {x}")
                return x * 10
            
            results, still_failed = replay_failed_items(dlq, process)
            
            assert sorted(results) == [10, 30, 50]  # 1, 3, 5
            assert len(still_failed) == 2  # 2, 4
            assert dlq.size() == 2
    
    def test_replay_no_clear_on_success(self):
        """Test replay with clear_on_success=False."""
        with tempfile.TemporaryDirectory() as tmpdir:
            policy = DLQPolicy(directory=tmpdir, auto_persist=False)
            dlq = DeadLetterQueue(policy)
            
            dlq.add(item=1, error=Exception("err"))
            
            def process(x):
                return x * 2
            
            results, still_failed = replay_failed_items(dlq, process, clear_on_success=False)
            
            assert results == [2]
            assert still_failed == []
            # DLQ should still have original entry since clear_on_success=False
            assert dlq.size() == 1


class TestDLQWithTraceback:
    """Tests for traceback capture functionality."""
    
    def test_traceback_included(self):
        """Test that traceback is captured when include_traceback=True."""
        with tempfile.TemporaryDirectory() as tmpdir:
            policy = DLQPolicy(directory=tmpdir, include_traceback=True, auto_persist=False)
            dlq = DeadLetterQueue(policy)
            
            try:
                raise ValueError("test error")
            except ValueError as e:
                dlq.add(item=123, error=e)
            
            entries = dlq.get_entries()
            assert entries[0].traceback is not None
            assert "ValueError: test error" in entries[0].traceback
            assert "Traceback" in entries[0].traceback
    
    def test_traceback_excluded(self):
        """Test that traceback is not captured when include_traceback=False."""
        with tempfile.TemporaryDirectory() as tmpdir:
            policy = DLQPolicy(directory=tmpdir, include_traceback=False, auto_persist=False)
            dlq = DeadLetterQueue(policy)
            
            try:
                raise RuntimeError("test error")
            except RuntimeError as e:
                dlq.add(item=456, error=e)
            
            entries = dlq.get_entries()
            assert entries[0].traceback is None


class TestDLQEdgeCases:
    """Tests for edge cases and error conditions."""
    
    def test_empty_queue_operations(self):
        """Test operations on empty queue."""
        with tempfile.TemporaryDirectory() as tmpdir:
            policy = DLQPolicy(directory=tmpdir, auto_persist=False)
            dlq = DeadLetterQueue(policy)
            
            assert dlq.size() == 0
            assert dlq.get_entries() == []
            assert dlq.clear() == 0
            summary = dlq.get_summary()
            assert summary["total_entries"] == 0
    
    def test_zero_max_entries(self):
        """Test that max_entries=0 means unlimited."""
        with tempfile.TemporaryDirectory() as tmpdir:
            policy = DLQPolicy(directory=tmpdir, max_entries=0, auto_persist=False)
            dlq = DeadLetterQueue(policy)
            
            # Add many entries
            for i in range(100):
                dlq.add(item=i, error=Exception(f"error {i}"))
            
            # All should be kept (no limit)
            assert dlq.size() == 100
    
    def test_add_complex_error_types(self):
        """Test adding entries with various exception types."""
        with tempfile.TemporaryDirectory() as tmpdir:
            policy = DLQPolicy(directory=tmpdir, auto_persist=False)
            dlq = DeadLetterQueue(policy)
            
            # Test different exception types
            errors = [
                ValueError("value error"),
                RuntimeError("runtime error"),
                KeyError("key error"),
                TypeError("type error"),
                IOError("io error"),
            ]
            
            for i, error in enumerate(errors):
                dlq.add(item=i, error=error)
            
            entries = dlq.get_entries()
            assert len(entries) == 5
            assert entries[0].error_type == "ValueError"
            assert entries[1].error_type == "RuntimeError"
            assert entries[2].error_type == "KeyError"
            assert entries[3].error_type == "TypeError"
            assert entries[4].error_type == "OSError"  # IOError is alias for OSError
    
    def test_persistence_error_handling(self):
        """Test that persistence errors don't crash the add operation."""
        with tempfile.TemporaryDirectory() as tmpdir:
            policy = DLQPolicy(directory=tmpdir, auto_persist=True)
            dlq = DeadLetterQueue(policy)
            
            # Mock _write_to_file_unsafe to raise an error
            with patch.object(dlq, '_write_to_file_unsafe', side_effect=IOError("disk full")):
                # Add should succeed even though persist fails
                dlq.add(item=123, error=Exception("test"))
            
            # Item should still be in memory
            assert dlq.size() == 1


class TestDLQIntegration:
    """Integration tests showing real-world usage patterns."""
    
    def test_with_retry_pattern(self):
        """Test DLQ integration with retry logic."""
        with tempfile.TemporaryDirectory() as tmpdir:
            policy = DLQPolicy(directory=tmpdir, auto_persist=False)
            dlq = DeadLetterQueue(policy)
            
            def process_with_retry(item, max_retries=3):
                """Simulate processing with retry logic."""
                for attempt in range(max_retries):
                    try:
                        # Simulate function that fails intermittently
                        if item % 5 == 0:  # Items divisible by 5 always fail
                            raise ValueError(f"Item {item} cannot be processed")
                        return item * 2
                    except Exception as e:
                        if attempt == max_retries - 1:
                            # Final retry failed - add to DLQ
                            dlq.add(item, e, retry_count=max_retries)
                            raise
                        # Otherwise retry
                        time.sleep(0.01)
            
            # Process items
            items = list(range(10))
            results = []
            for item in items:
                try:
                    result = process_with_retry(item)
                    results.append(result)
                except Exception:
                    pass  # Already added to DLQ
            
            # Check that failing items (0, 5) are in DLQ
            assert dlq.size() == 2
            entries = dlq.get_entries()
            failed_items = [e.item for e in entries]
            assert 0 in failed_items
            assert 5 in failed_items
            
            # Check successful results
            assert len(results) == 8
    
    def test_monitoring_workflow(self):
        """Test monitoring and inspection workflow."""
        with tempfile.TemporaryDirectory() as tmpdir:
            policy = DLQPolicy(directory=tmpdir, auto_persist=False)
            dlq = DeadLetterQueue(policy)
            
            # Simulate various failures
            dlq.add(item="file1.txt", error=FileNotFoundError("not found"), retry_count=3)
            dlq.add(item="file2.txt", error=FileNotFoundError("not found"), retry_count=3)
            dlq.add(item="data.json", error=json.JSONDecodeError("invalid", "", 0), retry_count=2)
            dlq.add(item="image.jpg", error=ValueError("corrupted"), retry_count=1)
            
            # Inspect summary
            summary = dlq.get_summary()
            assert summary["total_entries"] == 4
            assert summary["error_types"]["FileNotFoundError"] == 2
            assert summary["error_types"]["JSONDecodeError"] == 1
            assert summary["error_types"]["ValueError"] == 1
            assert summary["avg_retry_count"] == 2.25  # (3+3+2+1)/4
            
            # Filter entries by error type
            entries = dlq.get_entries()
            file_not_found = [e for e in entries if e.error_type == "FileNotFoundError"]
            assert len(file_not_found) == 2
