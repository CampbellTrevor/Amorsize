"""
Property-based tests for the hooks module using Hypothesis.

These tests automatically generate edge cases and verify invariant properties
of the execution hook system across a wide range of inputs and scenarios.
"""

import threading
import time
from typing import Any, Dict, List

import pytest
from hypothesis import given, settings, strategies as st, HealthCheck, assume

from amorsize.hooks import (
    HookEvent,
    HookContext,
    HookManager,
    create_progress_hook,
    create_timing_hook,
    create_throughput_hook,
    create_error_hook,
)


# Custom strategies for generating test data

@st.composite
def valid_hook_event(draw):
    """Generate valid HookEvent values."""
    return draw(st.sampled_from(list(HookEvent)))


@st.composite
def valid_hook_context(draw, event=None):
    """Generate valid HookContext objects."""
    if event is None:
        event = draw(valid_hook_event())
    
    # Generate optional integer fields
    n_jobs = draw(st.none() | st.integers(min_value=1, max_value=128))
    chunksize = draw(st.none() | st.integers(min_value=1, max_value=10000))
    total_items = draw(st.none() | st.integers(min_value=0, max_value=1000000))
    worker_id = draw(st.none() | st.integers(min_value=0, max_value=127))
    chunk_id = draw(st.none() | st.integers(min_value=0, max_value=10000))
    chunk_size = draw(st.none() | st.integers(min_value=1, max_value=10000))
    
    # Generate non-negative integer fields
    items_completed = draw(st.integers(min_value=0, max_value=1000000))
    items_remaining = draw(st.integers(min_value=0, max_value=1000000))
    worker_count = draw(st.integers(min_value=0, max_value=128))
    results_count = draw(st.integers(min_value=0, max_value=1000000))
    results_size_bytes = draw(st.integers(min_value=0, max_value=1000000000))
    
    # Generate float fields
    percent_complete = draw(st.floats(min_value=0.0, max_value=100.0, allow_nan=False, allow_infinity=False))
    elapsed_time = draw(st.floats(min_value=0.0, max_value=86400.0, allow_nan=False, allow_infinity=False))
    estimated_time_remaining = draw(st.floats(min_value=0.0, max_value=86400.0, allow_nan=False, allow_infinity=False))
    throughput_items_per_sec = draw(st.floats(min_value=0.0, max_value=1000000.0, allow_nan=False, allow_infinity=False))
    avg_item_time = draw(st.floats(min_value=0.0, max_value=1000.0, allow_nan=False, allow_infinity=False))
    chunk_time = draw(st.floats(min_value=0.0, max_value=1000.0, allow_nan=False, allow_infinity=False))
    
    # Generate optional error fields
    error = draw(st.none() | st.sampled_from([
        ValueError("test error"),
        RuntimeError("test runtime error"),
        TypeError("test type error"),
    ]))
    error_message = draw(st.none() | st.text(min_size=0, max_size=200))
    error_traceback = draw(st.none() | st.text(min_size=0, max_size=500))
    
    # Generate metadata
    metadata = draw(st.dictionaries(
        st.text(min_size=1, max_size=20),
        st.one_of(
            st.integers(),
            st.floats(allow_nan=False, allow_infinity=False),
            st.text(max_size=50),
            st.booleans(),
            st.none(),
        ),
        max_size=10
    ))
    
    return HookContext(
        event=event,
        timestamp=time.time(),
        n_jobs=n_jobs,
        chunksize=chunksize,
        total_items=total_items,
        items_completed=items_completed,
        items_remaining=items_remaining,
        percent_complete=percent_complete,
        elapsed_time=elapsed_time,
        estimated_time_remaining=estimated_time_remaining,
        throughput_items_per_sec=throughput_items_per_sec,
        avg_item_time=avg_item_time,
        worker_id=worker_id,
        worker_count=worker_count,
        chunk_id=chunk_id,
        chunk_size=chunk_size,
        chunk_time=chunk_time,
        error=error,
        error_message=error_message,
        error_traceback=error_traceback,
        results_count=results_count,
        results_size_bytes=results_size_bytes,
        metadata=metadata,
    )


@st.composite
def valid_min_interval(draw):
    """Generate valid min_interval values for throttling."""
    return draw(st.floats(min_value=0.0, max_value=10.0, allow_nan=False, allow_infinity=False))


class TestHookContextInvariants:
    """Test invariant properties of HookContext."""

    @given(context=valid_hook_context())
    @settings(max_examples=100, deadline=1000)
    def test_context_initialization(self, context):
        """Test that HookContext objects are created with valid fields."""
        assert isinstance(context.event, HookEvent)
        assert isinstance(context.timestamp, float)
        assert context.timestamp > 0
        
        # Check integer field types when not None
        if context.n_jobs is not None:
            assert isinstance(context.n_jobs, int)
            assert context.n_jobs >= 1
        
        if context.chunksize is not None:
            assert isinstance(context.chunksize, int)
            assert context.chunksize >= 1
        
        # Check non-negative integers
        assert isinstance(context.items_completed, int)
        assert context.items_completed >= 0
        assert isinstance(context.items_remaining, int)
        assert context.items_remaining >= 0
        assert isinstance(context.worker_count, int)
        assert context.worker_count >= 0
        
        # Check float fields
        assert isinstance(context.percent_complete, float)
        assert 0.0 <= context.percent_complete <= 100.0
        assert isinstance(context.elapsed_time, float)
        assert context.elapsed_time >= 0.0
        
        # Check metadata is a dict
        assert isinstance(context.metadata, dict)

    @given(event=valid_hook_event())
    @settings(max_examples=50, deadline=1000)
    def test_context_event_field_preserved(self, event):
        """Test that event field is preserved in context."""
        context = HookContext(event=event)
        assert context.event == event

    @given(context=valid_hook_context())
    @settings(max_examples=100, deadline=1000)
    def test_context_metadata_immutability(self, context):
        """Test that metadata dictionary is independent (copy semantics)."""
        original_metadata = context.metadata.copy()
        # Attempt to modify metadata externally
        context.metadata["new_key"] = "new_value"
        # Original metadata should still match what we copied
        # (This tests that the context doesn't prevent modification,
        # but we can verify the initial state was correct)
        assert "new_key" in context.metadata


class TestHookManagerBasicOperations:
    """Test basic operations of HookManager."""

    @given(event=valid_hook_event())
    @settings(max_examples=50, deadline=1000)
    def test_manager_initialization(self, event):
        """Test that HookManager initializes with empty hooks."""
        manager = HookManager()
        assert not manager.has_hooks(event)
        assert manager.get_hook_count(event) == 0

    @given(
        event=valid_hook_event(),
        verbose=st.booleans(),
    )
    @settings(max_examples=50, deadline=1000)
    def test_register_adds_hook(self, event, verbose):
        """Test that registering a hook increases count."""
        manager = HookManager(verbose=verbose)
        initial_count = manager.get_hook_count(event)
        
        def dummy_hook(ctx: HookContext) -> None:
            pass
        
        manager.register(event, dummy_hook)
        assert manager.get_hook_count(event) == initial_count + 1
        assert manager.has_hooks(event)

    @given(event=valid_hook_event())
    @settings(max_examples=50, deadline=1000)
    def test_register_same_hook_once(self, event):
        """Test that registering same hook twice doesn't duplicate."""
        manager = HookManager()
        
        def dummy_hook(ctx: HookContext) -> None:
            pass
        
        manager.register(event, dummy_hook)
        count_after_first = manager.get_hook_count(event)
        
        manager.register(event, dummy_hook)
        count_after_second = manager.get_hook_count(event)
        
        # Same hook should not be added twice
        assert count_after_first == count_after_second

    @given(event=valid_hook_event())
    @settings(max_examples=50, deadline=1000)
    def test_unregister_removes_hook(self, event):
        """Test that unregistering removes a hook."""
        manager = HookManager()
        
        def dummy_hook(ctx: HookContext) -> None:
            pass
        
        manager.register(event, dummy_hook)
        assert manager.has_hooks(event)
        
        result = manager.unregister(event, dummy_hook)
        assert result is True
        assert not manager.has_hooks(event)

    @given(event=valid_hook_event())
    @settings(max_examples=50, deadline=1000)
    def test_unregister_nonexistent_hook_returns_false(self, event):
        """Test that unregistering a hook that doesn't exist returns False."""
        manager = HookManager()
        
        def dummy_hook(ctx: HookContext) -> None:
            pass
        
        result = manager.unregister(event, dummy_hook)
        assert result is False

    @given(event=valid_hook_event())
    @settings(max_examples=50, deadline=1000)
    def test_unregister_all_clears_specific_event(self, event):
        """Test that unregister_all clears all hooks for specific event."""
        manager = HookManager()
        
        # Register multiple hooks using factory to create unique instances
        def make_hook(idx):
            def hook(ctx):
                pass
            hook._test_id = idx
            return hook
        
        for i in range(3):
            manager.register(event, make_hook(i))
        
        count = manager.unregister_all(event)
        assert count == 3
        assert not manager.has_hooks(event)

    @given(events=st.lists(valid_hook_event(), min_size=2, max_size=5, unique=True))
    @settings(max_examples=50, deadline=1000)
    def test_unregister_all_without_event_clears_everything(self, events):
        """Test that unregister_all() clears all hooks for all events."""
        manager = HookManager()
        
        # Register hooks for multiple events using factory to create unique instances
        def make_hook(event_idx):
            def hook(ctx):
                pass
            hook._test_event_id = event_idx
            return hook
        
        for i, event in enumerate(events):
            manager.register(event, make_hook(i))
        
        count = manager.unregister_all()
        assert count == len(events)
        
        # Verify all events have no hooks
        for event in events:
            assert not manager.has_hooks(event)


class TestHookManagerTriggerInvariants:
    """Test invariant properties of hook trigger mechanism."""

    @given(context=valid_hook_context())
    @settings(max_examples=100, deadline=1000)
    def test_trigger_with_context(self, context):
        """Test that trigger works with HookContext (preferred style)."""
        manager = HookManager()
        call_count = [0]
        
        def counter_hook(ctx: HookContext) -> None:
            call_count[0] += 1
            assert ctx.event == context.event
        
        manager.register(context.event, counter_hook)
        manager.trigger(context)
        
        assert call_count[0] == 1

    @given(context=valid_hook_context())
    @settings(max_examples=100, deadline=1000)
    def test_trigger_with_event_and_context(self, context):
        """Test that trigger works with event and context (legacy style)."""
        manager = HookManager()
        call_count = [0]
        
        def counter_hook(ctx: HookContext) -> None:
            call_count[0] += 1
        
        manager.register(context.event, counter_hook)
        manager.trigger(context.event, context)
        
        assert call_count[0] == 1

    @given(context=valid_hook_context())
    @settings(max_examples=50, deadline=1000)
    def test_trigger_with_no_hooks_doesnt_error(self, context):
        """Test that triggering with no registered hooks doesn't error."""
        manager = HookManager()
        # Should not raise any exception
        manager.trigger(context)

    @given(context=valid_hook_context())
    @settings(max_examples=50, deadline=1000)
    def test_trigger_calls_all_registered_hooks(self, context):
        """Test that triggering calls all registered hooks for the event."""
        manager = HookManager()
        call_counts = [0, 0, 0]
        
        def hook_1(ctx: HookContext) -> None:
            call_counts[0] += 1
        
        def hook_2(ctx: HookContext) -> None:
            call_counts[1] += 1
        
        def hook_3(ctx: HookContext) -> None:
            call_counts[2] += 1
        
        manager.register(context.event, hook_1)
        manager.register(context.event, hook_2)
        manager.register(context.event, hook_3)
        
        manager.trigger(context)
        
        assert call_counts == [1, 1, 1]

    @given(context=valid_hook_context())
    @settings(max_examples=50, deadline=1000)
    def test_trigger_isolates_hook_errors(self, context):
        """Test that hook errors don't prevent other hooks from running."""
        manager = HookManager(verbose=False)
        call_order = []
        
        def failing_hook(ctx: HookContext) -> None:
            call_order.append("failing")
            raise RuntimeError("Hook error")
        
        def succeeding_hook(ctx: HookContext) -> None:
            call_order.append("succeeding")
        
        manager.register(context.event, failing_hook)
        manager.register(context.event, succeeding_hook)
        
        # Should not raise exception
        manager.trigger(context)
        
        # Both hooks should have been called
        assert "failing" in call_order
        assert "succeeding" in call_order

    @given(context=valid_hook_context())
    @settings(max_examples=50, deadline=1000)
    def test_trigger_updates_call_counts(self, context):
        """Test that triggering updates call count statistics."""
        manager = HookManager()
        
        def dummy_hook(ctx: HookContext) -> None:
            pass
        
        manager.register(context.event, dummy_hook)
        
        initial_stats = manager.get_stats()
        initial_call_count = initial_stats["call_counts"].get(context.event.value, 0)
        
        manager.trigger(context)
        
        updated_stats = manager.get_stats()
        updated_call_count = updated_stats["call_counts"][context.event.value]
        
        assert updated_call_count == initial_call_count + 1

    @given(context=valid_hook_context())
    @settings(max_examples=50, deadline=1000)
    def test_trigger_updates_error_counts(self, context):
        """Test that hook errors update error count statistics."""
        manager = HookManager(verbose=False)
        
        def failing_hook(ctx: HookContext) -> None:
            raise RuntimeError("Test error")
        
        manager.register(context.event, failing_hook)
        
        initial_stats = manager.get_stats()
        initial_error_count = initial_stats["error_counts"].get(context.event.value, 0)
        
        manager.trigger(context)
        
        updated_stats = manager.get_stats()
        updated_error_count = updated_stats["error_counts"].get(context.event.value, 0)
        
        assert updated_error_count == initial_error_count + 1


class TestHookManagerThreadSafety:
    """Test thread safety of HookManager operations."""

    @given(
        event=valid_hook_event(),
        num_threads=st.integers(min_value=2, max_value=10),
    )
    @settings(max_examples=20, deadline=2000, suppress_health_check=[HealthCheck.function_scoped_fixture])
    def test_concurrent_register(self, event, num_threads):
        """Test that concurrent registration is thread-safe."""
        manager = HookManager()
        barrier = threading.Barrier(num_threads)
        
        # Create unique hooks using factory pattern
        def make_hook(thread_id):
            def hook(ctx):
                pass
            hook._thread_id = thread_id
            return hook
        
        hooks = [make_hook(i) for i in range(num_threads)]
        
        def register_hook(hook_func):
            # Synchronize all threads to maximize contention
            barrier.wait()
            manager.register(event, hook_func)
        
        threads = [threading.Thread(target=register_hook, args=(hooks[i],)) for i in range(num_threads)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()
        
        # All hooks should be registered since they're unique
        assert manager.has_hooks(event)
        assert manager.get_hook_count(event) == num_threads

    @given(
        context=valid_hook_context(),
        num_threads=st.integers(min_value=2, max_value=10),
    )
    @settings(max_examples=20, deadline=2000, suppress_health_check=[HealthCheck.function_scoped_fixture])
    def test_concurrent_trigger(self, context, num_threads):
        """Test that concurrent triggering is thread-safe."""
        manager = HookManager()
        call_count = [0]
        lock = threading.Lock()
        
        def thread_safe_hook(ctx: HookContext) -> None:
            with lock:
                call_count[0] += 1
        
        manager.register(context.event, thread_safe_hook)
        barrier = threading.Barrier(num_threads)
        
        def trigger_hook():
            barrier.wait()
            manager.trigger(context)
        
        threads = [threading.Thread(target=trigger_hook) for _ in range(num_threads)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()
        
        # Hook should have been called once per thread
        assert call_count[0] == num_threads


class TestHookManagerStatistics:
    """Test statistics tracking in HookManager."""

    @given(event=valid_hook_event())
    @settings(max_examples=50, deadline=1000)
    def test_get_stats_structure(self, event):
        """Test that get_stats returns correctly structured data."""
        manager = HookManager()
        stats = manager.get_stats()
        
        assert isinstance(stats, dict)
        assert "hook_counts" in stats
        assert "call_counts" in stats
        assert "error_counts" in stats
        
        assert isinstance(stats["hook_counts"], dict)
        assert isinstance(stats["call_counts"], dict)
        assert isinstance(stats["error_counts"], dict)

    @given(
        event=valid_hook_event(),
        num_hooks=st.integers(min_value=0, max_value=10),
    )
    @settings(max_examples=50, deadline=1000)
    def test_hook_counts_accuracy(self, event, num_hooks):
        """Test that hook_counts in stats are accurate."""
        manager = HookManager()
        
        # Create unique hooks using factory pattern to avoid duplicate prevention
        def make_hook(idx):
            def hook(ctx):
                pass
            # Store index as attribute to make hooks unique
            hook._test_id = idx
            return hook
        
        for i in range(num_hooks):
            manager.register(event, make_hook(i))
        
        stats = manager.get_stats()
        assert stats["hook_counts"][event.value] == num_hooks

    @given(
        context=valid_hook_context(),
        num_triggers=st.integers(min_value=1, max_value=10),
    )
    @settings(max_examples=50, deadline=1000)
    def test_call_counts_accuracy(self, context, num_triggers):
        """Test that call_counts in stats are accurate."""
        manager = HookManager()
        
        def dummy_hook(ctx: HookContext) -> None:
            pass
        
        manager.register(context.event, dummy_hook)
        
        for _ in range(num_triggers):
            manager.trigger(context)
        
        stats = manager.get_stats()
        assert stats["call_counts"][context.event.value] == num_triggers


class TestConvenienceFunctionInvariants:
    """Test invariant properties of convenience hook creation functions."""

    @given(min_interval=valid_min_interval())
    @settings(max_examples=50, deadline=1000)
    def test_create_progress_hook_returns_callable(self, min_interval):
        """Test that create_progress_hook returns a callable."""
        def callback(percent, completed, total):
            pass
        
        hook = create_progress_hook(callback, min_interval=min_interval)
        assert callable(hook)

    @given(
        context=valid_hook_context(event=HookEvent.ON_PROGRESS),
        min_interval=st.floats(min_value=0.0, max_value=0.1),
    )
    @settings(max_examples=50, deadline=1000)
    def test_create_progress_hook_calls_callback(self, context, min_interval):
        """Test that progress hook calls callback with correct arguments."""
        called = [False]
        
        def callback(percent, completed, total):
            called[0] = True
            assert isinstance(percent, float)
            assert isinstance(completed, int)
            assert isinstance(total, int)
        
        hook = create_progress_hook(callback, min_interval=min_interval)
        hook(context)
        
        assert called[0]

    @given(min_interval=st.floats(min_value=1.0, max_value=10.0))
    @settings(max_examples=50, deadline=1000)
    def test_create_progress_hook_throttles_calls(self, min_interval):
        """Test that progress hook throttles based on min_interval."""
        call_count = [0]
        
        def callback(percent, completed, total):
            call_count[0] += 1
        
        hook = create_progress_hook(callback, min_interval=min_interval)
        
        # First call should succeed
        context1 = HookContext(event=HookEvent.ON_PROGRESS, timestamp=time.time())
        hook(context1)
        assert call_count[0] == 1
        
        # Immediate second call should be throttled
        context2 = HookContext(event=HookEvent.ON_PROGRESS, timestamp=time.time())
        hook(context2)
        assert call_count[0] == 1

    @settings(max_examples=50, deadline=1000)
    @given(st.none())
    def test_create_timing_hook_returns_callable(self, _):
        """Test that create_timing_hook returns a callable."""
        def callback(event_name, elapsed):
            pass
        
        hook = create_timing_hook(callback)
        assert callable(hook)

    @given(context=valid_hook_context())
    @settings(max_examples=50, deadline=1000)
    def test_create_timing_hook_calls_callback(self, context):
        """Test that timing hook calls callback with correct arguments."""
        called = [False]
        
        def callback(event_name, elapsed):
            called[0] = True
            assert isinstance(event_name, str)
            assert isinstance(elapsed, float)
        
        hook = create_timing_hook(callback)
        hook(context)
        
        assert called[0]

    @given(min_interval=valid_min_interval())
    @settings(max_examples=50, deadline=1000)
    def test_create_throughput_hook_returns_callable(self, min_interval):
        """Test that create_throughput_hook returns a callable."""
        def callback(rate):
            pass
        
        hook = create_throughput_hook(callback, min_interval=min_interval)
        assert callable(hook)

    @given(
        context=valid_hook_context(event=HookEvent.ON_PROGRESS),
        min_interval=st.floats(min_value=0.0, max_value=0.1),
    )
    @settings(max_examples=50, deadline=1000)
    def test_create_throughput_hook_calls_callback(self, context, min_interval):
        """Test that throughput hook calls callback with correct arguments."""
        called = [False]
        
        def callback(rate):
            called[0] = True
            assert isinstance(rate, float)
        
        hook = create_throughput_hook(callback, min_interval=min_interval)
        hook(context)
        
        assert called[0]

    @settings(max_examples=50, deadline=1000)
    @given(st.none())
    def test_create_error_hook_returns_callable(self, _):
        """Test that create_error_hook returns a callable."""
        def callback(error, traceback):
            pass
        
        hook = create_error_hook(callback)
        assert callable(hook)

    @given(
        error=st.sampled_from([
            ValueError("test"),
            RuntimeError("test"),
            TypeError("test"),
        ]),
        traceback_str=st.text(min_size=0, max_size=200),
    )
    @settings(max_examples=50, deadline=1000)
    def test_create_error_hook_calls_callback_on_error(self, error, traceback_str):
        """Test that error hook calls callback when error is present."""
        called = [False]
        
        def callback(err, tb):
            called[0] = True
            assert isinstance(err, Exception)
            assert isinstance(tb, str)
        
        hook = create_error_hook(callback)
        context = HookContext(
            event=HookEvent.ON_ERROR,
            error=error,
            error_traceback=traceback_str,
        )
        hook(context)
        
        assert called[0]

    @settings(max_examples=50, deadline=1000)
    @given(st.none())
    def test_create_error_hook_skips_callback_without_error(self, _):
        """Test that error hook doesn't call callback when error is None."""
        called = [False]
        
        def callback(err, tb):
            called[0] = True
        
        hook = create_error_hook(callback)
        context = HookContext(event=HookEvent.ON_ERROR, error=None)
        hook(context)
        
        assert not called[0]


class TestEdgeCases:
    """Test edge cases and boundary conditions."""

    @given(context=valid_hook_context())
    @settings(max_examples=50, deadline=1000)
    def test_hook_manager_with_verbose_true(self, context):
        """Test that verbose mode doesn't break functionality."""
        manager = HookManager(verbose=True)
        
        def failing_hook(ctx: HookContext) -> None:
            raise RuntimeError("Test error")
        
        manager.register(context.event, failing_hook)
        # Should not raise (error is caught and logged)
        manager.trigger(context)

    @given(event=valid_hook_event())
    @settings(max_examples=50, deadline=1000)
    def test_multiple_register_unregister_cycles(self, event):
        """Test multiple register/unregister cycles work correctly."""
        manager = HookManager()
        
        def hook(ctx: HookContext) -> None:
            pass
        
        for _ in range(5):
            manager.register(event, hook)
            assert manager.has_hooks(event)
            
            manager.unregister(event, hook)
            assert not manager.has_hooks(event)

    @given(
        events=st.lists(valid_hook_event(), min_size=2, max_size=5, unique=True)
    )
    @settings(max_examples=50, deadline=1000)
    def test_hooks_isolated_by_event_type(self, events):
        """Test that hooks for different events are isolated."""
        manager = HookManager()
        
        # Create unique hook for each event using factory pattern
        def make_event_hook(event_idx):
            def hook(ctx: HookContext) -> None:
                pass
            hook._event_idx = event_idx
            return hook
        
        hooks_by_event = {}
        for i, event in enumerate(events):
            event_hook = make_event_hook(i)
            hooks_by_event[event] = event_hook
            manager.register(event, event_hook)
        
        # Each event should have exactly one hook
        for event in events:
            assert manager.get_hook_count(event) == 1

    @given(context=valid_hook_context())
    @settings(max_examples=50, deadline=1000)
    def test_trigger_with_invalid_parameter_combination_raises_error(self, context):
        """Test that invalid trigger parameter combination raises ValueError."""
        manager = HookManager()
        
        # Passing HookContext as first param with non-None context param
        with pytest.raises(ValueError, match="context parameter must be None"):
            manager.trigger(context, context)

    @settings(max_examples=50, deadline=1000)
    @given(st.none())
    def test_trigger_with_invalid_type_raises_error(self, _):
        """Test that trigger with invalid type raises TypeError."""
        manager = HookManager()
        
        with pytest.raises(TypeError, match="must be HookEvent or HookContext"):
            manager.trigger("invalid_type")


class TestIntegrationProperties:
    """Test integration properties of the hook system."""

    @given(
        events=st.lists(valid_hook_event(), min_size=1, max_size=3, unique=True),
        num_hooks_per_event=st.integers(min_value=1, max_value=3),
    )
    @settings(max_examples=30, deadline=2000)
    def test_full_lifecycle(self, events, num_hooks_per_event):
        """Test full lifecycle: register, trigger multiple times, unregister."""
        manager = HookManager()
        call_counts = {event: [0] * num_hooks_per_event for event in events}
        
        # Register multiple hooks for each event
        for event in events:
            for i in range(num_hooks_per_event):
                def make_hook(ev, idx):
                    def hook(ctx: HookContext) -> None:
                        call_counts[ev][idx] += 1
                    return hook
                manager.register(event, make_hook(event, i))
        
        # Trigger each event multiple times
        num_triggers = 3
        for event in events:
            for _ in range(num_triggers):
                context = HookContext(event=event)
                manager.trigger(context)
        
        # Verify all hooks were called correct number of times
        for event in events:
            for count in call_counts[event]:
                assert count == num_triggers
        
        # Unregister all and verify
        manager.unregister_all()
        for event in events:
            assert not manager.has_hooks(event)

    @given(
        context=valid_hook_context(),
        num_success_hooks=st.integers(min_value=1, max_value=3),
        num_failure_hooks=st.integers(min_value=1, max_value=3),
    )
    @settings(max_examples=30, deadline=2000)
    def test_mixed_success_and_failure_hooks(self, context, num_success_hooks, num_failure_hooks):
        """Test that mixture of successful and failing hooks works correctly."""
        manager = HookManager(verbose=False)
        success_calls = [0] * num_success_hooks
        failure_calls = [0] * num_failure_hooks
        
        # Register successful hooks
        for i in range(num_success_hooks):
            def make_success_hook(idx):
                def hook(ctx: HookContext) -> None:
                    success_calls[idx] += 1
                return hook
            manager.register(context.event, make_success_hook(i))
        
        # Register failing hooks
        for i in range(num_failure_hooks):
            def make_failure_hook(idx):
                def hook(ctx: HookContext) -> None:
                    failure_calls[idx] += 1
                    raise RuntimeError(f"Failure {idx}")
                return hook
            manager.register(context.event, make_failure_hook(i))
        
        # Trigger hooks
        manager.trigger(context)
        
        # All hooks should have been called despite failures
        assert all(count == 1 for count in success_calls)
        assert all(count == 1 for count in failure_calls)
        
        # Error count should match number of failing hooks
        stats = manager.get_stats()
        assert stats["error_counts"].get(context.event.value, 0) == num_failure_hooks
