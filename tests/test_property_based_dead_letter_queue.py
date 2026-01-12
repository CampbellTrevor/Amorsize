"""
Property-based tests for the dead_letter_queue module using Hypothesis.

These tests automatically generate edge cases and verify invariant properties
of the dead letter queue logic across a wide range of inputs and configurations.
"""

import json
import os
import pickle
import tempfile
import threading
import time
from typing import Any, Dict

import pytest
from hypothesis import given, settings, strategies as st, HealthCheck, assume

from amorsize.dead_letter_queue import (
    DLQPolicy,
    DLQFormat,
    DLQEntry,
    DeadLetterQueue,
    replay_failed_items,
)


# Custom strategies for generating test data
@st.composite
def valid_dlq_policy(draw):
    """
    Generate valid DLQPolicy configurations.
    
    Generates policies with:
    - directory: Temporary directory path
    - format: JSON or PICKLE
    - max_entries: 0 to 10000 (0 = unlimited)
    - include_traceback: True or False
    - auto_persist: True or False
    
    Returns:
        DLQPolicy with randomized but valid parameters
    """
    # Use a temp directory that gets cleaned up
    directory = draw(st.just(tempfile.mkdtemp(prefix="dlq_test_")))
    format_val = draw(st.sampled_from([DLQFormat.JSON, DLQFormat.PICKLE]))
    max_entries = draw(st.integers(min_value=0, max_value=10000))
    include_traceback = draw(st.booleans())
    auto_persist = draw(st.booleans())
    
    return DLQPolicy(
        directory=directory,
        format=format_val,
        max_entries=max_entries,
        include_traceback=include_traceback,
        auto_persist=auto_persist
    )


@st.composite
def json_serializable_item(draw):
    """Generate JSON-serializable items for testing."""
    return draw(st.one_of(
        st.integers(),
        st.floats(allow_nan=False, allow_infinity=False),
        st.text(),
        st.booleans(),
        st.lists(st.integers(), max_size=10),
        st.dictionaries(st.text(min_size=1, max_size=10), st.integers(), max_size=5)
    ))


@st.composite
def dlq_entry_data(draw):
    """Generate DLQEntry test data."""
    item = draw(json_serializable_item())
    error_types = ["ValueError", "TypeError", "RuntimeError", "KeyError", "IndexError"]
    error_type = draw(st.sampled_from(error_types))
    error_message = draw(st.text(min_size=1, max_size=100))
    timestamp = draw(st.floats(min_value=1000000000, max_value=2000000000))
    traceback_str = draw(st.one_of(st.none(), st.text(min_size=10, max_size=200)))
    retry_count = draw(st.integers(min_value=0, max_value=100))
    metadata = draw(st.dictionaries(
        st.text(min_size=1, max_size=20),
        st.one_of(st.integers(), st.text(max_size=50)),
        max_size=5
    ))
    
    return {
        "item": item,
        "error_type": error_type,
        "error_message": error_message,
        "timestamp": timestamp,
        "traceback": traceback_str,
        "retry_count": retry_count,
        "metadata": metadata
    }


class TestDLQPolicyInvariants:
    """Test invariant properties of DLQPolicy."""

    @given(
        directory=st.text(min_size=1, max_size=100),
        format_val=st.sampled_from([DLQFormat.JSON, DLQFormat.PICKLE]),
        max_entries=st.integers(min_value=0, max_value=100000),
        include_traceback=st.booleans(),
        auto_persist=st.booleans()
    )
    @settings(max_examples=100, deadline=1000)
    def test_policy_initialization_valid_params(self, directory, format_val, max_entries, include_traceback, auto_persist):
        """Test that valid parameters create a policy without errors."""
        policy = DLQPolicy(
            directory=directory,
            format=format_val,
            max_entries=max_entries,
            include_traceback=include_traceback,
            auto_persist=auto_persist
        )
        
        assert policy.directory == directory
        assert policy.format == format_val
        assert policy.max_entries == max_entries
        assert policy.include_traceback == include_traceback
        assert policy.auto_persist == auto_persist

    @given(directory=st.just("") | st.none())
    @settings(max_examples=10, deadline=1000)
    def test_policy_rejects_empty_directory(self, directory):
        """Test that empty or None directory raises ValueError."""
        with pytest.raises(ValueError, match="directory must be a non-empty string"):
            DLQPolicy(directory=directory)

    @given(format_val=st.text())
    @settings(max_examples=50, deadline=1000, suppress_health_check=[HealthCheck.filter_too_much])
    def test_policy_rejects_invalid_format(self, format_val):
        """Test that invalid format raises ValueError."""
        assume(format_val not in [DLQFormat.JSON.value, DLQFormat.PICKLE.value])
        assume(not isinstance(format_val, DLQFormat))
        with pytest.raises(ValueError, match="format must be a DLQFormat enum value"):
            DLQPolicy(format=format_val)

    @given(max_entries=st.integers(max_value=-1))
    @settings(max_examples=50, deadline=1000)
    def test_policy_rejects_negative_max_entries(self, max_entries):
        """Test that negative max_entries raises ValueError."""
        with pytest.raises(ValueError, match="max_entries must be a non-negative integer"):
            DLQPolicy(max_entries=max_entries)

    @given(include_traceback=st.one_of(st.integers(), st.text(), st.lists(st.integers())))
    @settings(max_examples=50, deadline=1000)
    def test_policy_rejects_non_boolean_include_traceback(self, include_traceback):
        """Test that non-boolean include_traceback raises ValueError."""
        assume(not isinstance(include_traceback, bool))
        with pytest.raises(ValueError, match="include_traceback must be a boolean"):
            DLQPolicy(include_traceback=include_traceback)

    @given(auto_persist=st.one_of(st.integers(), st.text(), st.lists(st.integers())))
    @settings(max_examples=50, deadline=1000)
    def test_policy_rejects_non_boolean_auto_persist(self, auto_persist):
        """Test that non-boolean auto_persist raises ValueError."""
        assume(not isinstance(auto_persist, bool))
        with pytest.raises(ValueError, match="auto_persist must be a boolean"):
            DLQPolicy(auto_persist=auto_persist)


class TestDLQEntryInvariants:
    """Test invariant properties of DLQEntry."""

    @given(entry_data=dlq_entry_data())
    @settings(max_examples=100, deadline=1000)
    def test_entry_stores_all_fields(self, entry_data):
        """Test that DLQEntry stores all provided fields correctly."""
        entry = DLQEntry(**entry_data)
        
        assert entry.item == entry_data["item"]
        assert entry.error_type == entry_data["error_type"]
        assert entry.error_message == entry_data["error_message"]
        assert entry.timestamp == entry_data["timestamp"]
        assert entry.traceback == entry_data["traceback"]
        assert entry.retry_count == entry_data["retry_count"]
        assert entry.metadata == entry_data["metadata"]

    @given(entry_data=dlq_entry_data())
    @settings(max_examples=100, deadline=1000)
    def test_entry_to_dict_roundtrip(self, entry_data):
        """Test that to_dict() and from_dict() are inverse operations."""
        entry = DLQEntry(**entry_data)
        dict_repr = entry.to_dict()
        recovered_entry = DLQEntry.from_dict(dict_repr)
        
        assert recovered_entry.item == entry.item
        assert recovered_entry.error_type == entry.error_type
        assert recovered_entry.error_message == entry.error_message
        assert recovered_entry.timestamp == entry.timestamp
        assert recovered_entry.traceback == entry.traceback
        assert recovered_entry.retry_count == entry.retry_count
        assert recovered_entry.metadata == entry.metadata

    @given(entry_data=dlq_entry_data())
    @settings(max_examples=50, deadline=1000)
    def test_entry_to_dict_has_all_keys(self, entry_data):
        """Test that to_dict() includes all required keys."""
        entry = DLQEntry(**entry_data)
        dict_repr = entry.to_dict()
        
        required_keys = {"item", "error_type", "error_message", "timestamp", "traceback", "retry_count", "metadata"}
        assert set(dict_repr.keys()) == required_keys

    @given(entry_data=dlq_entry_data())
    @settings(max_examples=50, deadline=1000)
    def test_entry_retry_count_non_negative(self, entry_data):
        """Test that retry_count is always non-negative."""
        entry = DLQEntry(**entry_data)
        assert entry.retry_count >= 0


class TestDeadLetterQueueBasicOperations:
    """Test basic operations of DeadLetterQueue."""

    @given(policy=valid_dlq_policy())
    @settings(max_examples=50, deadline=2000)
    def test_dlq_initialization(self, policy):
        """Test that DLQ initializes correctly with a policy."""
        dlq = DeadLetterQueue(policy=policy)
        
        assert dlq.policy == policy
        assert dlq.size() == 0
        assert dlq.get_entries() == []

    @given(
        items=st.lists(json_serializable_item(), min_size=1, max_size=20),
        include_traceback=st.booleans()
    )
    @settings(max_examples=50, deadline=2000, suppress_health_check=[HealthCheck.function_scoped_fixture])
    def test_dlq_add_increases_size(self, items, include_traceback):
        """Test that adding items increases queue size."""
        with tempfile.TemporaryDirectory() as tmpdir:
            policy = DLQPolicy(directory=tmpdir, auto_persist=False, include_traceback=include_traceback)
            dlq = DeadLetterQueue(policy=policy)
            
            for i, item in enumerate(items):
                error = ValueError(f"Error {i}")
                dlq.add(item, error, retry_count=i)
                assert dlq.size() == i + 1

    @given(
        items=st.lists(json_serializable_item(), min_size=1, max_size=10)
    )
    @settings(max_examples=30, deadline=2000)
    def test_dlq_get_entries_returns_copy(self, items):
        """Test that get_entries() returns a copy, not reference."""
        with tempfile.TemporaryDirectory() as tmpdir:
            policy = DLQPolicy(directory=tmpdir, auto_persist=False)
            dlq = DeadLetterQueue(policy=policy)
            
            for item in items:
                dlq.add(item, ValueError("test"), retry_count=0)
            
            entries1 = dlq.get_entries()
            entries2 = dlq.get_entries()
            
            # Should return different list instances
            assert entries1 is not entries2
            # But with same content
            assert len(entries1) == len(entries2) == len(items)

    @given(
        items=st.lists(json_serializable_item(), min_size=1, max_size=10)
    )
    @settings(max_examples=30, deadline=2000)
    def test_dlq_clear_empties_queue(self, items):
        """Test that clear() removes all entries."""
        with tempfile.TemporaryDirectory() as tmpdir:
            policy = DLQPolicy(directory=tmpdir, auto_persist=False)
            dlq = DeadLetterQueue(policy=policy)
            
            for item in items:
                dlq.add(item, ValueError("test"), retry_count=0)
            
            cleared_count = dlq.clear()
            
            assert cleared_count == len(items)
            assert dlq.size() == 0
            assert dlq.get_entries() == []

    @given(
        items=st.lists(json_serializable_item(), min_size=1, max_size=10),
        retry_counts=st.lists(st.integers(min_value=0, max_value=50), min_size=1, max_size=10)
    )
    @settings(max_examples=30, deadline=2000)
    def test_dlq_entries_preserve_retry_count(self, items, retry_counts):
        """Test that retry counts are preserved in entries."""
        assume(len(items) == len(retry_counts))
        
        with tempfile.TemporaryDirectory() as tmpdir:
            policy = DLQPolicy(directory=tmpdir, auto_persist=False)
            dlq = DeadLetterQueue(policy=policy)
            
            for item, retry_count in zip(items, retry_counts):
                dlq.add(item, ValueError("test"), retry_count=retry_count)
            
            entries = dlq.get_entries()
            for entry, expected_count in zip(entries, retry_counts):
                assert entry.retry_count == expected_count


class TestDeadLetterQueueSizeLimiting:
    """Test size limiting and pruning behavior."""

    @given(
        num_items=st.integers(min_value=5, max_value=20),
        max_entries=st.integers(min_value=1, max_value=10)
    )
    @settings(max_examples=30, deadline=2000)
    def test_dlq_enforces_max_entries(self, num_items, max_entries):
        """Test that DLQ enforces max_entries limit by pruning oldest."""
        assume(num_items > max_entries)
        
        with tempfile.TemporaryDirectory() as tmpdir:
            policy = DLQPolicy(directory=tmpdir, max_entries=max_entries, auto_persist=False)
            dlq = DeadLetterQueue(policy=policy)
            
            for i in range(num_items):
                dlq.add(i, ValueError(f"Error {i}"), retry_count=0)
            
            # Should only keep max_entries
            assert dlq.size() == max_entries
            
            # Should keep the newest entries (last max_entries items)
            entries = dlq.get_entries()
            kept_items = [entry.item for entry in entries]
            expected_items = list(range(num_items - max_entries, num_items))
            assert kept_items == expected_items

    @given(num_items=st.integers(min_value=1, max_value=20))
    @settings(max_examples=30, deadline=2000)
    def test_dlq_unlimited_when_max_entries_zero(self, num_items):
        """Test that max_entries=0 means unlimited."""
        with tempfile.TemporaryDirectory() as tmpdir:
            policy = DLQPolicy(directory=tmpdir, max_entries=0, auto_persist=False)
            dlq = DeadLetterQueue(policy=policy)
            
            for i in range(num_items):
                dlq.add(i, ValueError(f"Error {i}"), retry_count=0)
            
            # Should keep all items
            assert dlq.size() == num_items


class TestDeadLetterQueuePersistence:
    """Test persistence to disk (JSON and Pickle formats)."""

    @given(
        items=st.lists(json_serializable_item(), min_size=1, max_size=10),
        format_val=st.sampled_from([DLQFormat.JSON, DLQFormat.PICKLE])
    )
    @settings(max_examples=30, deadline=3000)
    def test_dlq_save_and_load_preserves_entries(self, items, format_val):
        """Test that save() and load() preserve all entries."""
        with tempfile.TemporaryDirectory() as tmpdir:
            policy = DLQPolicy(directory=tmpdir, format=format_val, auto_persist=False)
            dlq1 = DeadLetterQueue(policy=policy)
            
            for item in items:
                dlq1.add(item, ValueError("test"), retry_count=0)
            
            # Save to disk
            filepath = dlq1.save()
            
            # Load into new DLQ
            dlq2 = DeadLetterQueue(policy=policy)
            loaded_count = dlq2.load(filepath)
            
            assert loaded_count == len(items)
            assert dlq2.size() == len(items)
            
            # Verify items match
            original_items = [e.item for e in dlq1.get_entries()]
            loaded_items = [e.item for e in dlq2.get_entries()]
            assert original_items == loaded_items

    @given(items=st.lists(json_serializable_item(), min_size=1, max_size=10))
    @settings(max_examples=20, deadline=3000)
    def test_dlq_auto_persist_saves_on_add(self, items):
        """Test that auto_persist=True saves entries on add()."""
        with tempfile.TemporaryDirectory() as tmpdir:
            policy = DLQPolicy(directory=tmpdir, format=DLQFormat.JSON, auto_persist=True)
            dlq = DeadLetterQueue(policy=policy)
            
            for item in items:
                dlq.add(item, ValueError("test"), retry_count=0)
            
            # File should exist
            filepath = os.path.join(tmpdir, "dlq.json")
            assert os.path.exists(filepath)
            
            # Load and verify
            with open(filepath, 'r') as f:
                data = json.load(f)
            
            assert len(data) == len(items)

    @given(items=st.lists(json_serializable_item(), min_size=1, max_size=10))
    @settings(max_examples=20, deadline=3000)
    def test_dlq_json_format_is_human_readable(self, items):
        """Test that JSON format creates readable files."""
        with tempfile.TemporaryDirectory() as tmpdir:
            policy = DLQPolicy(directory=tmpdir, format=DLQFormat.JSON, auto_persist=False)
            dlq = DeadLetterQueue(policy=policy)
            
            for item in items:
                dlq.add(item, ValueError("test"), retry_count=0)
            
            filepath = dlq.save()
            
            # Should be valid JSON
            with open(filepath, 'r') as f:
                data = json.load(f)
            
            assert isinstance(data, list)
            assert len(data) == len(items)


class TestDeadLetterQueueThreadSafety:
    """Test thread safety of concurrent operations."""

    @given(
        num_threads=st.integers(min_value=2, max_value=5),
        items_per_thread=st.integers(min_value=5, max_value=10)
    )
    @settings(max_examples=10, deadline=5000)
    def test_dlq_concurrent_add_is_thread_safe(self, num_threads, items_per_thread):
        """Test that concurrent add() operations don't corrupt the queue."""
        with tempfile.TemporaryDirectory() as tmpdir:
            policy = DLQPolicy(directory=tmpdir, auto_persist=False)
            dlq = DeadLetterQueue(policy=policy)
            
            def add_items(thread_id):
                for i in range(items_per_thread):
                    item = f"thread{thread_id}_item{i}"
                    dlq.add(item, ValueError("test"), retry_count=0)
            
            threads = [
                threading.Thread(target=add_items, args=(tid,))
                for tid in range(num_threads)
            ]
            
            for t in threads:
                t.start()
            for t in threads:
                t.join()
            
            # Should have all items
            expected_total = num_threads * items_per_thread
            assert dlq.size() == expected_total


class TestDeadLetterQueueSummary:
    """Test summary statistics functionality."""

    @given(
        items=st.lists(json_serializable_item(), min_size=1, max_size=20),
        error_types=st.lists(st.sampled_from(["ValueError", "TypeError", "RuntimeError"]), min_size=1, max_size=20)
    )
    @settings(max_examples=30, deadline=2000, suppress_health_check=[HealthCheck.filter_too_much])
    def test_dlq_summary_counts_error_types(self, items, error_types):
        """Test that get_summary() correctly counts error types."""
        assume(len(items) == len(error_types))
        
        with tempfile.TemporaryDirectory() as tmpdir:
            policy = DLQPolicy(directory=tmpdir, auto_persist=False)
            dlq = DeadLetterQueue(policy=policy)
            
            for item, error_type in zip(items, error_types):
                if error_type == "ValueError":
                    error = ValueError("test")
                elif error_type == "TypeError":
                    error = TypeError("test")
                else:
                    error = RuntimeError("test")
                dlq.add(item, error, retry_count=0)
            
            summary = dlq.get_summary()
            
            assert summary["total_entries"] == len(items)
            # Error types count should match
            expected_counts = {}
            for et in error_types:
                expected_counts[et] = expected_counts.get(et, 0) + 1
            assert summary["error_types"] == expected_counts

    @given(retry_counts=st.lists(st.integers(min_value=0, max_value=10), min_size=1, max_size=20))
    @settings(max_examples=30, deadline=2000)
    def test_dlq_summary_computes_avg_retry_count(self, retry_counts):
        """Test that get_summary() computes average retry count."""
        with tempfile.TemporaryDirectory() as tmpdir:
            policy = DLQPolicy(directory=tmpdir, auto_persist=False)
            dlq = DeadLetterQueue(policy=policy)
            
            for i, retry_count in enumerate(retry_counts):
                dlq.add(i, ValueError("test"), retry_count=retry_count)
            
            summary = dlq.get_summary()
            
            expected_avg = sum(retry_counts) / len(retry_counts)
            assert abs(summary["avg_retry_count"] - expected_avg) < 0.001

    def test_dlq_summary_empty_queue(self):
        """Test that get_summary() handles empty queue."""
        with tempfile.TemporaryDirectory() as tmpdir:
            policy = DLQPolicy(directory=tmpdir, auto_persist=False)
            dlq = DeadLetterQueue(policy=policy)
            
            summary = dlq.get_summary()
            
            assert summary["total_entries"] == 0
            assert summary["error_types"] == {}
            assert summary["avg_retry_count"] == 0.0
            assert summary["oldest_timestamp"] is None
            assert summary["newest_timestamp"] is None


class TestReplayFailedItems:
    """Test replay_failed_items helper function."""

    @given(
        items=st.lists(st.integers(min_value=0, max_value=100), min_size=5, max_size=20),
        failure_threshold=st.integers(min_value=0, max_value=50)
    )
    @settings(max_examples=20, deadline=3000)
    def test_replay_recovers_successful_items(self, items, failure_threshold):
        """Test that replay_failed_items correctly separates successes from failures."""
        with tempfile.TemporaryDirectory() as tmpdir:
            policy = DLQPolicy(directory=tmpdir, auto_persist=False)
            dlq = DeadLetterQueue(policy=policy)
            
            # Add all items as failed
            for item in items:
                dlq.add(item, ValueError("test"), retry_count=0)
            
            # Function that succeeds for items below threshold
            def process(item):
                if item < failure_threshold:
                    return item * 2
                else:
                    raise ValueError(f"Still failing: {item}")
            
            results, still_failed = replay_failed_items(dlq, process, clear_on_success=True)
            
            # Count expected successes
            expected_successes = sum(1 for item in items if item < failure_threshold)
            expected_failures = len(items) - expected_successes
            
            assert len(results) == expected_successes
            assert len(still_failed) == expected_failures
            
            # After clear_on_success, DLQ should only contain failures
            assert dlq.size() == expected_failures

    @given(items=st.lists(st.integers(), min_size=1, max_size=10))
    @settings(max_examples=20, deadline=2000)
    def test_replay_increments_retry_count(self, items):
        """Test that replay increments retry_count for items that fail again."""
        with tempfile.TemporaryDirectory() as tmpdir:
            policy = DLQPolicy(directory=tmpdir, auto_persist=False)
            dlq = DeadLetterQueue(policy=policy)
            
            # Add all items with retry_count=1
            for item in items:
                dlq.add(item, ValueError("test"), retry_count=1)
            
            # Function that always fails
            def always_fail(item):
                raise ValueError("Still failing")
            
            results, still_failed = replay_failed_items(dlq, always_fail, clear_on_success=True)
            
            # All should still fail
            assert len(results) == 0
            assert len(still_failed) == len(items)
            
            # Retry counts should be incremented
            for entry in still_failed:
                assert entry.retry_count == 2


class TestDLQEdgeCases:
    """Test edge cases and boundary conditions."""

    def test_dlq_with_empty_metadata(self):
        """Test that DLQ handles empty metadata correctly."""
        with tempfile.TemporaryDirectory() as tmpdir:
            policy = DLQPolicy(directory=tmpdir, auto_persist=False)
            dlq = DeadLetterQueue(policy=policy)
            
            dlq.add(123, ValueError("test"), retry_count=0, metadata=None)
            
            entries = dlq.get_entries()
            assert len(entries) == 1
            assert entries[0].metadata == {}

    @given(include_traceback=st.booleans())
    @settings(max_examples=20, deadline=1000)
    def test_dlq_traceback_inclusion_respects_policy(self, include_traceback):
        """Test that traceback is included/excluded based on policy."""
        with tempfile.TemporaryDirectory() as tmpdir:
            policy = DLQPolicy(directory=tmpdir, include_traceback=include_traceback, auto_persist=False)
            dlq = DeadLetterQueue(policy=policy)
            
            try:
                raise ValueError("test error")
            except ValueError as e:
                dlq.add(123, e, retry_count=0)
            
            entries = dlq.get_entries()
            assert len(entries) == 1
            
            if include_traceback:
                assert entries[0].traceback is not None
                assert "ValueError" in entries[0].traceback
            else:
                assert entries[0].traceback is None

    @given(max_entries=st.integers(min_value=1, max_value=5))
    @settings(max_examples=10, deadline=2000)
    def test_dlq_pruning_keeps_newest_entries(self, max_entries):
        """Test that pruning keeps newest entries, not oldest."""
        with tempfile.TemporaryDirectory() as tmpdir:
            policy = DLQPolicy(directory=tmpdir, max_entries=max_entries, auto_persist=False)
            dlq = DeadLetterQueue(policy=policy)
            
            # Add items with unique values
            num_items = max_entries + 3
            for i in range(num_items):
                dlq.add(f"item_{i}", ValueError(f"error {i}"), retry_count=0)
                time.sleep(0.01)  # Ensure distinct timestamps
            
            entries = dlq.get_entries()
            assert len(entries) == max_entries
            
            # Should have the last max_entries items
            kept_items = [entry.item for entry in entries]
            expected_items = [f"item_{i}" for i in range(num_items - max_entries, num_items)]
            assert kept_items == expected_items


class TestDLQIntegration:
    """Test integrated scenarios combining multiple features."""

    @given(
        items=st.lists(st.integers(), min_size=5, max_size=15),
        max_entries=st.integers(min_value=3, max_value=10)
    )
    @settings(max_examples=15, deadline=3000)
    def test_dlq_full_lifecycle_with_persistence(self, items, max_entries):
        """Test full DLQ lifecycle: add, prune, save, load, clear."""
        assume(len(items) > max_entries)
        
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create DLQ, add items
            policy = DLQPolicy(directory=tmpdir, max_entries=max_entries, auto_persist=False)
            dlq1 = DeadLetterQueue(policy=policy)
            
            for item in items:
                dlq1.add(item, ValueError("test"), retry_count=0)
            
            # Should be pruned to max_entries
            assert dlq1.size() == max_entries
            
            # Save
            filepath = dlq1.save()
            assert os.path.exists(filepath)
            
            # Load into new DLQ
            dlq2 = DeadLetterQueue(policy=policy)
            loaded_count = dlq2.load(filepath)
            assert loaded_count == max_entries
            assert dlq2.size() == max_entries
            
            # Clear
            cleared = dlq2.clear()
            assert cleared == max_entries
            assert dlq2.size() == 0

    @given(
        items=st.lists(st.integers(min_value=0, max_value=100), min_size=10, max_size=20)
    )
    @settings(max_examples=10, deadline=3000)
    def test_dlq_with_replay_and_summary(self, items):
        """Test DLQ integration with replay and summary statistics."""
        with tempfile.TemporaryDirectory() as tmpdir:
            policy = DLQPolicy(directory=tmpdir, auto_persist=False)
            dlq = DeadLetterQueue(policy=policy)
            
            # Add items
            for item in items:
                dlq.add(item, ValueError("test"), retry_count=1)
            
            # Get summary before replay
            summary_before = dlq.get_summary()
            assert summary_before["total_entries"] == len(items)
            assert summary_before["avg_retry_count"] == 1.0
            
            # Replay with partial success
            def process(item):
                if item % 2 == 0:
                    return item * 2
                else:
                    raise ValueError(f"Still failing: {item}")
            
            results, still_failed = replay_failed_items(dlq, process, clear_on_success=True)
            
            # Summary after replay
            summary_after = dlq.get_summary()
            assert summary_after["total_entries"] == len(still_failed)
            # Retry count should have incremented for failed items
            if still_failed:
                assert summary_after["avg_retry_count"] == 2.0
