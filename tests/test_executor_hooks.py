"""
Tests for executor integration with hooks.
"""

import pytest
from amorsize import execute, HookManager, HookEvent, HookContext


def simple_function(x):
    """Simple test function."""
    return x * 2


class TestExecutorHooksIntegration:
    """Tests for executor hooks integration."""
    
    def test_execute_without_hooks(self):
        """Test execute works without hooks (backward compatibility)."""
        data = range(10)
        results = execute(simple_function, data, verbose=False)
        assert len(results) == 10
        assert results[0] == 0
        assert results[9] == 18
    
    def test_execute_with_empty_hooks(self):
        """Test execute with empty hook manager."""
        hooks = HookManager()
        data = range(10)
        results = execute(simple_function, data, hooks=hooks, verbose=False)
        assert len(results) == 10
    
    def test_pre_execute_hook_triggered(self):
        """Test that PRE_EXECUTE hook is triggered."""
        hooks = HookManager()
        contexts = []
        
        def capture_context(ctx: HookContext):
            contexts.append(ctx)
        
        hooks.register(HookEvent.PRE_EXECUTE, capture_context)
        
        data = range(10)
        results = execute(simple_function, data, hooks=hooks, verbose=False)
        
        assert len(results) == 10
        assert len(contexts) == 1
        assert contexts[0].event == HookEvent.PRE_EXECUTE
        assert contexts[0].n_jobs is not None
        assert contexts[0].chunksize is not None
    
    def test_post_execute_hook_triggered(self):
        """Test that POST_EXECUTE hook is triggered."""
        hooks = HookManager()
        contexts = []
        
        def capture_context(ctx: HookContext):
            contexts.append(ctx)
        
        hooks.register(HookEvent.POST_EXECUTE, capture_context)
        
        data = range(10)
        results = execute(simple_function, data, hooks=hooks, verbose=False)
        
        assert len(results) == 10
        assert len(contexts) == 1
        assert contexts[0].event == HookEvent.POST_EXECUTE
        assert contexts[0].items_completed == 10
        assert contexts[0].percent_complete == 100.0
        assert contexts[0].elapsed_time > 0
    
    def test_both_hooks_triggered(self):
        """Test that both PRE and POST hooks are triggered."""
        hooks = HookManager()
        events = []
        
        def capture_event(ctx: HookContext):
            events.append(ctx.event)
        
        hooks.register(HookEvent.PRE_EXECUTE, capture_event)
        hooks.register(HookEvent.POST_EXECUTE, capture_event)
        
        data = range(10)
        results = execute(simple_function, data, hooks=hooks, verbose=False)
        
        assert len(results) == 10
        assert len(events) == 2
        assert events[0] == HookEvent.PRE_EXECUTE
        assert events[1] == HookEvent.POST_EXECUTE
    
    def test_hook_receives_execution_metadata(self):
        """Test that hooks receive execution metadata."""
        hooks = HookManager()
        metadata_list = []
        
        def capture_metadata(ctx: HookContext):
            metadata_list.append(ctx.metadata)
        
        hooks.register(HookEvent.PRE_EXECUTE, capture_metadata)
        hooks.register(HookEvent.POST_EXECUTE, capture_metadata)
        
        data = range(10)
        execute(simple_function, data, hooks=hooks, verbose=False)
        
        assert len(metadata_list) == 2
        # PRE_EXECUTE metadata
        assert "executor_type" in metadata_list[0]
        assert "estimated_speedup" in metadata_list[0]
        # POST_EXECUTE metadata
        assert "executor_type" in metadata_list[1]
        assert "estimated_speedup" in metadata_list[1]
    
    def test_hook_error_doesnt_break_execution(self):
        """Test that hook errors don't break execution."""
        hooks = HookManager(verbose=False)
        
        def failing_hook(ctx: HookContext):
            raise ValueError("Hook error")
        
        hooks.register(HookEvent.PRE_EXECUTE, failing_hook)
        hooks.register(HookEvent.POST_EXECUTE, failing_hook)
        
        data = range(10)
        # Should not raise despite hook errors
        results = execute(simple_function, data, hooks=hooks, verbose=False)
        
        assert len(results) == 10
        assert results[0] == 0
    
    def test_multiple_hooks_same_event(self):
        """Test multiple hooks for same event."""
        hooks = HookManager()
        calls = []
        
        def hook1(ctx: HookContext):
            calls.append("hook1")
        
        def hook2(ctx: HookContext):
            calls.append("hook2")
        
        hooks.register(HookEvent.POST_EXECUTE, hook1)
        hooks.register(HookEvent.POST_EXECUTE, hook2)
        
        data = range(10)
        execute(simple_function, data, hooks=hooks, verbose=False)
        
        assert "hook1" in calls
        assert "hook2" in calls
    
    def test_throughput_calculation(self):
        """Test that throughput is calculated in POST_EXECUTE."""
        hooks = HookManager()
        throughputs = []
        
        def capture_throughput(ctx: HookContext):
            throughputs.append(ctx.throughput_items_per_sec)
        
        hooks.register(HookEvent.POST_EXECUTE, capture_throughput)
        
        data = range(100)
        execute(simple_function, data, hooks=hooks, verbose=False)
        
        assert len(throughputs) == 1
        assert throughputs[0] > 0  # Should have positive throughput
    
    def test_hooks_with_return_optimization_result(self):
        """Test hooks work when returning optimization result."""
        hooks = HookManager()
        contexts = []
        
        def capture_context(ctx: HookContext):
            contexts.append(ctx)
        
        hooks.register(HookEvent.PRE_EXECUTE, capture_context)
        hooks.register(HookEvent.POST_EXECUTE, capture_context)
        
        data = range(10)
        results, opt_result = execute(
            simple_function,
            data,
            hooks=hooks,
            return_optimization_result=True,
            verbose=False
        )
        
        assert len(results) == 10
        assert opt_result is not None
        assert len(contexts) == 2  # Both hooks triggered
    
    def test_hook_stats_after_execution(self):
        """Test that hook statistics are updated after execution."""
        hooks = HookManager()
        
        def test_hook(ctx: HookContext):
            pass
        
        hooks.register(HookEvent.PRE_EXECUTE, test_hook)
        hooks.register(HookEvent.POST_EXECUTE, test_hook)
        
        data = range(10)
        execute(simple_function, data, hooks=hooks, verbose=False)
        
        stats = hooks.get_stats()
        assert stats["call_counts"]["pre_execute"] == 1
        assert stats["call_counts"]["post_execute"] == 1


class TestProgressHookIntegration:
    """Tests for progress hook integration patterns."""
    
    def test_progress_tracking_pattern(self):
        """Test common progress tracking pattern."""
        from amorsize import create_progress_hook
        
        hooks = HookManager()
        progress_updates = []
        
        def track_progress(percent, completed, total):
            progress_updates.append({
                "percent": percent,
                "completed": completed,
                "total": total
            })
        
        hook = create_progress_hook(track_progress, min_interval=0.0)
        # Note: Currently only POST_EXECUTE has progress info
        # In future, ON_PROGRESS events could be added during execution
        hooks.register(HookEvent.POST_EXECUTE, hook)
        
        data = range(50)
        execute(simple_function, data, hooks=hooks, verbose=False)
        
        # Should have at least final progress update
        assert len(progress_updates) >= 1
        final = progress_updates[-1]
        assert final["percent"] == 100.0
        assert final["completed"] == 50


class TestTimingHookIntegration:
    """Tests for timing hook integration patterns."""
    
    def test_execution_timing_pattern(self):
        """Test execution timing measurement pattern."""
        from amorsize import create_timing_hook
        
        hooks = HookManager()
        timings = []
        
        def record_timing(event_name, elapsed):
            timings.append({
                "event": event_name,
                "elapsed": elapsed
            })
        
        hook = create_timing_hook(record_timing)
        hooks.register(HookEvent.POST_EXECUTE, hook)
        
        data = range(50)
        execute(simple_function, data, hooks=hooks, verbose=False)
        
        assert len(timings) == 1
        assert timings[0]["event"] == "post_execute"
        assert timings[0]["elapsed"] > 0
