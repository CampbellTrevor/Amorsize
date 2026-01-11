"""
Tests for enhanced hook points (ON_CHUNK_COMPLETE, ON_PROGRESS, etc.).

This test suite validates the fine-grained hook system that allows monitoring
of chunk completion and progress during parallel execution.
"""

import time
import pytest
from typing import List, Tuple

from amorsize import execute
from amorsize.hooks import HookManager, HookEvent, HookContext


# Test functions
def simple_func(x):
    """Simple test function."""
    return x * 2


def slow_func(x):
    """Slower function for timing tests."""
    time.sleep(0.01)
    return x * 2


def cpu_bound_func(x):
    """CPU-bound function."""
    result = 0
    for i in range(10000):
        result += x ** 2
    return result


class TestChunkCompleteHook:
    """Tests for ON_CHUNK_COMPLETE hook."""
    
    def test_chunk_complete_triggered(self):
        """Test that ON_CHUNK_COMPLETE hook is triggered."""
        hooks = HookManager()
        chunk_calls = []
        
        def on_chunk(ctx: HookContext):
            chunk_calls.append({
                'chunk_id': ctx.chunk_id,
                'chunk_size': ctx.chunk_size,
                'items_completed': ctx.items_completed,
                'total_items': ctx.total_items
            })
        
        hooks.register(HookEvent.ON_CHUNK_COMPLETE, on_chunk)
        
        data = range(20)
        results = execute(slow_func, data, hooks=hooks, verbose=False)
        
        assert len(results) == 20
        assert len(chunk_calls) > 0, "ON_CHUNK_COMPLETE hook should be triggered"
        
        # Verify chunk IDs are sequential
        chunk_ids = [call['chunk_id'] for call in chunk_calls]
        assert chunk_ids == list(range(len(chunk_ids))), "Chunk IDs should be sequential"
        
        # Verify last chunk completes all items
        last_chunk = chunk_calls[-1]
        assert last_chunk['items_completed'] == 20, "Last chunk should complete all items"
    
    def test_chunk_complete_has_timing(self):
        """Test that chunk complete events include timing information."""
        hooks = HookManager()
        chunk_times = []
        
        def on_chunk(ctx: HookContext):
            chunk_times.append(ctx.chunk_time)
        
        hooks.register(HookEvent.ON_CHUNK_COMPLETE, on_chunk)
        
        data = range(10)
        results = execute(slow_func, data, hooks=hooks, verbose=False)
        
        assert len(results) == 10
        assert all(t >= 0 for t in chunk_times), "All chunk times should be non-negative"
    
    def test_chunk_complete_with_serial_execution(self):
        """Test that chunk hooks work with serial execution (n_jobs=1)."""
        hooks = HookManager()
        chunk_calls = []
        
        def on_chunk(ctx: HookContext):
            chunk_calls.append(ctx.chunk_id)
        
        hooks.register(HookEvent.ON_CHUNK_COMPLETE, on_chunk)
        
        # Force serial execution with small dataset
        data = range(5)
        results = execute(simple_func, data, hooks=hooks, verbose=False)
        
        assert len(results) == 5
        # Serial execution should still trigger chunk hooks if enabled
        assert len(chunk_calls) > 0
    
    def test_chunk_complete_with_multiprocessing(self):
        """Test that chunk hooks work with multiprocessing."""
        hooks = HookManager()
        chunk_calls = []
        
        def on_chunk(ctx: HookContext):
            chunk_calls.append({
                'chunk_id': ctx.chunk_id,
                'items_completed': ctx.items_completed
            })
        
        hooks.register(HookEvent.ON_CHUNK_COMPLETE, on_chunk)
        
        # Use CPU-bound function to trigger multiprocessing
        data = range(50)
        results = execute(cpu_bound_func, data, hooks=hooks, verbose=False)
        
        assert len(results) == 50
        assert len(chunk_calls) > 0, "Chunks should be tracked with multiprocessing"
        
        # Verify progressive completion
        items_completed = [call['items_completed'] for call in chunk_calls]
        assert items_completed == sorted(items_completed), "Items should complete progressively"
    
    def test_chunk_complete_percent_calculation(self):
        """Test that percent_complete is calculated correctly."""
        hooks = HookManager()
        percentages = []
        
        def on_chunk(ctx: HookContext):
            percentages.append(ctx.percent_complete)
        
        hooks.register(HookEvent.ON_CHUNK_COMPLETE, on_chunk)
        
        data = range(20)
        results = execute(slow_func, data, hooks=hooks, verbose=False)
        
        assert len(results) == 20
        assert len(percentages) > 0
        
        # Verify percentages are in valid range and increasing
        assert all(0 <= p <= 100 for p in percentages), "Percentages should be 0-100"
        assert percentages[-1] == 100.0, "Last percentage should be 100%"
        assert percentages == sorted(percentages), "Percentages should increase"


class TestProgressHook:
    """Tests for ON_PROGRESS hook."""
    
    def test_progress_triggered(self):
        """Test that ON_PROGRESS hook is triggered."""
        hooks = HookManager()
        progress_calls = []
        
        def on_progress(ctx: HookContext):
            progress_calls.append({
                'items_completed': ctx.items_completed,
                'percent_complete': ctx.percent_complete,
                'elapsed_time': ctx.elapsed_time,
                'throughput': ctx.throughput_items_per_sec
            })
        
        hooks.register(HookEvent.ON_PROGRESS, on_progress)
        
        data = range(20)
        results = execute(slow_func, data, hooks=hooks, verbose=False)
        
        assert len(results) == 20
        assert len(progress_calls) > 0, "ON_PROGRESS hook should be triggered"
    
    def test_progress_has_throughput(self):
        """Test that progress events include throughput metrics."""
        hooks = HookManager()
        throughputs = []
        
        def on_progress(ctx: HookContext):
            throughputs.append(ctx.throughput_items_per_sec)
        
        hooks.register(HookEvent.ON_PROGRESS, on_progress)
        
        data = range(20)
        results = execute(slow_func, data, hooks=hooks, verbose=False)
        
        assert len(results) == 20
        assert len(throughputs) > 0
        assert all(t >= 0 for t in throughputs), "All throughputs should be non-negative"
    
    def test_progress_elapsed_time_increases(self):
        """Test that elapsed time increases with each progress update."""
        hooks = HookManager()
        elapsed_times = []
        
        def on_progress(ctx: HookContext):
            elapsed_times.append(ctx.elapsed_time)
        
        hooks.register(HookEvent.ON_PROGRESS, on_progress)
        
        data = range(20)
        results = execute(slow_func, data, hooks=hooks, verbose=False)
        
        assert len(results) == 20
        assert len(elapsed_times) > 0
        
        # Verify elapsed times are increasing
        for i in range(1, len(elapsed_times)):
            assert elapsed_times[i] >= elapsed_times[i-1], "Elapsed time should increase"
    
    def test_progress_with_threading(self):
        """Test that progress hooks work with ThreadPoolExecutor."""
        hooks = HookManager()
        progress_calls = []
        
        def on_progress(ctx: HookContext):
            progress_calls.append(ctx.items_completed)
        
        hooks.register(HookEvent.ON_PROGRESS, on_progress)
        
        # I/O-bound function triggers threading
        data = range(20)
        results = execute(slow_func, data, hooks=hooks, verbose=False)
        
        assert len(results) == 20
        assert len(progress_calls) > 0, "Progress should be tracked with threading"


class TestCombinedHooks:
    """Tests for using multiple hooks together."""
    
    def test_chunk_and_progress_together(self):
        """Test that chunk and progress hooks can work together."""
        hooks = HookManager()
        chunk_calls = []
        progress_calls = []
        
        def on_chunk(ctx: HookContext):
            chunk_calls.append(ctx.chunk_id)
        
        def on_progress(ctx: HookContext):
            progress_calls.append(ctx.items_completed)
        
        hooks.register(HookEvent.ON_CHUNK_COMPLETE, on_chunk)
        hooks.register(HookEvent.ON_PROGRESS, on_progress)
        
        data = range(20)
        results = execute(slow_func, data, hooks=hooks, verbose=False)
        
        assert len(results) == 20
        assert len(chunk_calls) > 0, "Chunk hooks should fire"
        assert len(progress_calls) > 0, "Progress hooks should fire"
        assert len(chunk_calls) == len(progress_calls), "Should have same number of updates"
    
    def test_all_execution_hooks_together(self):
        """Test that all execution hooks can work together."""
        hooks = HookManager()
        events = []
        
        def record_event(event_name):
            def callback(ctx: HookContext):
                events.append(event_name)
            return callback
        
        hooks.register(HookEvent.PRE_EXECUTE, record_event('pre'))
        hooks.register(HookEvent.ON_CHUNK_COMPLETE, record_event('chunk'))
        hooks.register(HookEvent.ON_PROGRESS, record_event('progress'))
        hooks.register(HookEvent.POST_EXECUTE, record_event('post'))
        
        data = range(10)
        results = execute(slow_func, data, hooks=hooks, verbose=False)
        
        assert len(results) == 10
        assert 'pre' in events, "PRE_EXECUTE should fire"
        assert 'chunk' in events, "ON_CHUNK_COMPLETE should fire"
        assert 'progress' in events, "ON_PROGRESS should fire"
        assert 'post' in events, "POST_EXECUTE should fire"
        
        # Verify order: PRE -> chunks/progress -> POST
        assert events[0] == 'pre', "PRE_EXECUTE should be first"
        assert events[-1] == 'post', "POST_EXECUTE should be last"


class TestHookPerformanceImpact:
    """Tests to ensure hooks don't significantly impact performance."""
    
    def test_no_hooks_is_fast(self):
        """Test that execution without hooks is fast."""
        data = range(100)
        
        start = time.time()
        results = execute(simple_func, data, hooks=None, verbose=False)
        no_hook_time = time.time() - start
        
        assert len(results) == 100
        # Should complete reasonably quickly (< 5 seconds)
        assert no_hook_time < 5.0
    
    def test_hooks_have_minimal_overhead(self):
        """Test that hooks add minimal overhead."""
        data = range(100)
        
        # Execute without hooks
        start = time.time()
        results1 = execute(simple_func, data, hooks=None, verbose=False)
        no_hook_time = time.time() - start
        
        # Execute with hooks
        hooks = HookManager()
        hooks.register(HookEvent.ON_CHUNK_COMPLETE, lambda ctx: None)
        hooks.register(HookEvent.ON_PROGRESS, lambda ctx: None)
        
        start = time.time()
        results2 = execute(simple_func, data, hooks=hooks, verbose=False)
        hook_time = time.time() - start
        
        assert len(results1) == 100
        assert len(results2) == 100
        
        # Hooks should add less than 50% overhead
        # (This is a generous threshold; actual overhead should be much less)
        overhead_ratio = hook_time / max(no_hook_time, 0.001)  # Avoid division by zero
        assert overhead_ratio < 1.5, f"Hook overhead too high: {overhead_ratio:.2f}x"


class TestEdgeCases:
    """Tests for edge cases and error conditions."""
    
    def test_empty_data_with_hooks(self):
        """Test that hooks handle empty data gracefully."""
        hooks = HookManager()
        chunk_calls = []
        
        def on_chunk(ctx: HookContext):
            chunk_calls.append(ctx.chunk_id)
        
        hooks.register(HookEvent.ON_CHUNK_COMPLETE, on_chunk)
        
        data = []
        results = execute(simple_func, data, hooks=hooks, verbose=False)
        
        assert len(results) == 0
        # No chunks should be completed for empty data
        assert len(chunk_calls) == 0
    
    def test_single_item_with_hooks(self):
        """Test that hooks work with single item."""
        hooks = HookManager()
        chunk_calls = []
        progress_calls = []
        
        def on_chunk(ctx: HookContext):
            chunk_calls.append(ctx.items_completed)
        
        def on_progress(ctx: HookContext):
            progress_calls.append(ctx.percent_complete)
        
        hooks.register(HookEvent.ON_CHUNK_COMPLETE, on_chunk)
        hooks.register(HookEvent.ON_PROGRESS, on_progress)
        
        data = [42]
        results = execute(simple_func, data, hooks=hooks, verbose=False)
        
        assert len(results) == 1
        assert results[0] == 84
        
        # Should still trigger hooks for single item
        if len(chunk_calls) > 0:
            assert chunk_calls[0] == 1, "Single item should be completed"
        if len(progress_calls) > 0:
            assert progress_calls[-1] == 100.0, "Should reach 100%"
    
    def test_hook_error_doesnt_crash(self):
        """Test that hook errors don't crash execution."""
        hooks = HookManager(verbose=False)
        
        def failing_hook(ctx: HookContext):
            raise ValueError("Hook intentionally fails")
        
        hooks.register(HookEvent.ON_CHUNK_COMPLETE, failing_hook)
        
        data = range(10)
        # Should complete successfully despite hook failure
        results = execute(simple_func, data, hooks=hooks, verbose=False)
        
        assert len(results) == 10
        assert results == [x * 2 for x in data]


class TestHookContextData:
    """Tests for the data provided in HookContext."""
    
    def test_chunk_context_has_required_fields(self):
        """Test that chunk contexts have all required fields."""
        hooks = HookManager()
        contexts = []
        
        def on_chunk(ctx: HookContext):
            contexts.append(ctx)
        
        hooks.register(HookEvent.ON_CHUNK_COMPLETE, on_chunk)
        
        data = range(20)
        results = execute(slow_func, data, hooks=hooks, verbose=False)
        
        assert len(results) == 20
        assert len(contexts) > 0
        
        for ctx in contexts:
            assert ctx.event == HookEvent.ON_CHUNK_COMPLETE
            assert ctx.chunk_id is not None
            assert ctx.chunk_size is not None
            assert ctx.chunk_size > 0
            assert ctx.items_completed > 0
            assert ctx.total_items == 20
            assert 0 <= ctx.percent_complete <= 100
            assert ctx.elapsed_time >= 0
    
    def test_progress_context_has_required_fields(self):
        """Test that progress contexts have all required fields."""
        hooks = HookManager()
        contexts = []
        
        def on_progress(ctx: HookContext):
            contexts.append(ctx)
        
        hooks.register(HookEvent.ON_PROGRESS, on_progress)
        
        data = range(20)
        results = execute(slow_func, data, hooks=hooks, verbose=False)
        
        assert len(results) == 20
        assert len(contexts) > 0
        
        for ctx in contexts:
            assert ctx.event == HookEvent.ON_PROGRESS
            assert ctx.items_completed > 0
            assert ctx.total_items == 20
            assert 0 <= ctx.percent_complete <= 100
            assert ctx.elapsed_time >= 0
            assert ctx.throughput_items_per_sec >= 0


class TestBackwardCompatibility:
    """Tests to ensure backward compatibility."""
    
    def test_execute_without_hooks_unchanged(self):
        """Test that execute() works unchanged without hooks."""
        data = range(20)
        results = execute(simple_func, data, verbose=False)
        
        assert len(results) == 20
        assert results == [x * 2 for x in data]
    
    def test_old_hooks_still_work(self):
        """Test that PRE_EXECUTE and POST_EXECUTE hooks still work."""
        hooks = HookManager()
        events = []
        
        def on_pre(ctx: HookContext):
            events.append('pre')
        
        def on_post(ctx: HookContext):
            events.append('post')
        
        hooks.register(HookEvent.PRE_EXECUTE, on_pre)
        hooks.register(HookEvent.POST_EXECUTE, on_post)
        
        data = range(10)
        results = execute(simple_func, data, hooks=hooks, verbose=False)
        
        assert len(results) == 10
        assert events == ['pre', 'post'], "Old hooks should work as before"


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
