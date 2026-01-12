"""
Tests for execution hooks module.
"""

import threading
import time
import pytest
from amorsize.hooks import (
    HookEvent,
    HookContext,
    HookManager,
    create_progress_hook,
    create_timing_hook,
    create_throughput_hook,
    create_error_hook,
)


class TestHookContext:
    """Tests for HookContext dataclass."""
    
    def test_basic_context_creation(self):
        """Test creating a basic hook context."""
        ctx = HookContext(event=HookEvent.PRE_EXECUTE)
        assert ctx.event == HookEvent.PRE_EXECUTE
        assert ctx.timestamp > 0
        assert ctx.items_completed == 0
        assert ctx.metadata == {}
    
    def test_context_with_progress(self):
        """Test context with progress information."""
        ctx = HookContext(
            event=HookEvent.ON_PROGRESS,
            total_items=1000,
            items_completed=250,
            percent_complete=25.0,
            elapsed_time=10.0
        )
        assert ctx.total_items == 1000
        assert ctx.items_completed == 250
        assert ctx.percent_complete == 25.0
        assert ctx.elapsed_time == 10.0
    
    def test_context_with_error(self):
        """Test context with error information."""
        error = ValueError("Test error")
        ctx = HookContext(
            event=HookEvent.ON_ERROR,
            error=error,
            error_message="Test error",
            error_traceback="Traceback..."
        )
        assert ctx.error == error
        assert ctx.error_message == "Test error"
        assert ctx.error_traceback == "Traceback..."
    
    def test_context_with_metadata(self):
        """Test context with custom metadata."""
        ctx = HookContext(
            event=HookEvent.POST_EXECUTE,
            metadata={"custom_key": "custom_value", "count": 42}
        )
        assert ctx.metadata["custom_key"] == "custom_value"
        assert ctx.metadata["count"] == 42


class TestHookManager:
    """Tests for HookManager class."""
    
    def test_manager_creation(self):
        """Test creating a hook manager."""
        manager = HookManager()
        assert manager is not None
        for event in HookEvent:
            assert manager.get_hook_count(event) == 0
    
    def test_register_hook(self):
        """Test registering a hook."""
        manager = HookManager()
        called = []
        
        def test_hook(ctx: HookContext):
            called.append(ctx.event)
        
        manager.register(HookEvent.PRE_EXECUTE, test_hook)
        assert manager.get_hook_count(HookEvent.PRE_EXECUTE) == 1
        assert manager.has_hooks(HookEvent.PRE_EXECUTE)
    
    def test_trigger_hook(self):
        """Test triggering a hook."""
        manager = HookManager()
        called = []
        
        def test_hook(ctx: HookContext):
            called.append(ctx.event)
        
        manager.register(HookEvent.PRE_EXECUTE, test_hook)
        
        ctx = HookContext(event=HookEvent.PRE_EXECUTE)
        manager.trigger(ctx)
        
        assert len(called) == 1
        assert called[0] == HookEvent.PRE_EXECUTE
    
    def test_multiple_hooks_same_event(self):
        """Test registering multiple hooks for same event."""
        manager = HookManager()
        calls = []
        
        def hook1(ctx: HookContext):
            calls.append("hook1")
        
        def hook2(ctx: HookContext):
            calls.append("hook2")
        
        manager.register(HookEvent.ON_PROGRESS, hook1)
        manager.register(HookEvent.ON_PROGRESS, hook2)
        
        assert manager.get_hook_count(HookEvent.ON_PROGRESS) == 2
        
        ctx = HookContext(event=HookEvent.ON_PROGRESS)
        manager.trigger(ctx)
        
        assert len(calls) == 2
        assert "hook1" in calls
        assert "hook2" in calls
    
    def test_unregister_hook(self):
        """Test unregistering a hook."""
        manager = HookManager()
        
        def test_hook(ctx: HookContext):
            pass
        
        manager.register(HookEvent.PRE_EXECUTE, test_hook)
        assert manager.get_hook_count(HookEvent.PRE_EXECUTE) == 1
        
        removed = manager.unregister(HookEvent.PRE_EXECUTE, test_hook)
        assert removed is True
        assert manager.get_hook_count(HookEvent.PRE_EXECUTE) == 0
    
    def test_unregister_nonexistent_hook(self):
        """Test unregistering a hook that wasn't registered."""
        manager = HookManager()
        
        def test_hook(ctx: HookContext):
            pass
        
        removed = manager.unregister(HookEvent.PRE_EXECUTE, test_hook)
        assert removed is False
    
    def test_unregister_all_for_event(self):
        """Test unregistering all hooks for an event."""
        manager = HookManager()
        
        def hook1(ctx: HookContext):
            pass
        
        def hook2(ctx: HookContext):
            pass
        
        manager.register(HookEvent.ON_PROGRESS, hook1)
        manager.register(HookEvent.ON_PROGRESS, hook2)
        manager.register(HookEvent.PRE_EXECUTE, hook1)
        
        count = manager.unregister_all(HookEvent.ON_PROGRESS)
        assert count == 2
        assert manager.get_hook_count(HookEvent.ON_PROGRESS) == 0
        assert manager.get_hook_count(HookEvent.PRE_EXECUTE) == 1
    
    def test_unregister_all_events(self):
        """Test unregistering all hooks for all events."""
        manager = HookManager()
        
        def test_hook(ctx: HookContext):
            pass
        
        manager.register(HookEvent.PRE_EXECUTE, test_hook)
        manager.register(HookEvent.ON_PROGRESS, test_hook)
        manager.register(HookEvent.POST_EXECUTE, test_hook)
        
        count = manager.unregister_all()
        assert count == 3
        
        for event in HookEvent:
            assert manager.get_hook_count(event) == 0
    
    def test_hook_error_isolation(self):
        """Test that hook errors don't crash execution."""
        manager = HookManager(verbose=False)
        calls = []
        
        def failing_hook(ctx: HookContext):
            calls.append("failing_hook")
            raise ValueError("Hook error")
        
        def successful_hook(ctx: HookContext):
            calls.append("successful_hook")
        
        manager.register(HookEvent.ON_PROGRESS, failing_hook)
        manager.register(HookEvent.ON_PROGRESS, successful_hook)
        
        ctx = HookContext(event=HookEvent.ON_PROGRESS)
        manager.trigger(ctx)  # Should not raise
        
        # Both hooks should be called despite the error
        assert "failing_hook" in calls
        assert "successful_hook" in calls
    
    def test_hook_stats(self):
        """Test getting hook statistics."""
        manager = HookManager()
        
        def test_hook(ctx: HookContext):
            pass
        
        manager.register(HookEvent.PRE_EXECUTE, test_hook)
        manager.register(HookEvent.ON_PROGRESS, test_hook)
        
        # Trigger some events
        manager.trigger(HookContext(event=HookEvent.PRE_EXECUTE))
        manager.trigger(HookContext(event=HookEvent.ON_PROGRESS))
        manager.trigger(HookContext(event=HookEvent.ON_PROGRESS))
        
        stats = manager.get_stats()
        assert stats["hook_counts"]["pre_execute"] == 1
        assert stats["hook_counts"]["on_progress"] == 1
        assert stats["call_counts"]["pre_execute"] == 1
        assert stats["call_counts"]["on_progress"] == 2
    
    def test_duplicate_registration_prevented(self):
        """Test that same callback can't be registered twice for same event."""
        manager = HookManager()
        
        def test_hook(ctx: HookContext):
            pass
        
        manager.register(HookEvent.PRE_EXECUTE, test_hook)
        manager.register(HookEvent.PRE_EXECUTE, test_hook)  # Duplicate
        
        # Should only be registered once
        assert manager.get_hook_count(HookEvent.PRE_EXECUTE) == 1


class TestProgressHook:
    """Tests for create_progress_hook helper."""
    
    def test_basic_progress_hook(self):
        """Test creating and using a progress hook."""
        calls = []
        
        def callback(percent, completed, total):
            calls.append((percent, completed, total))
        
        hook = create_progress_hook(callback, min_interval=0.0)
        
        ctx = HookContext(
            event=HookEvent.ON_PROGRESS,
            percent_complete=50.0,
            items_completed=500,
            total_items=1000
        )
        
        hook(ctx)
        
        assert len(calls) == 1
        assert calls[0] == (50.0, 500, 1000)
    
    def test_progress_throttling(self):
        """Test that progress updates are throttled."""
        calls = []
        
        def callback(percent, completed, total):
            calls.append((percent, completed, total))
        
        hook = create_progress_hook(callback, min_interval=0.5)
        
        # First call should go through
        ctx1 = HookContext(
            event=HookEvent.ON_PROGRESS,
            percent_complete=25.0,
            items_completed=250,
            total_items=1000,
            timestamp=1.0
        )
        hook(ctx1)
        assert len(calls) == 1
        
        # Second call too soon - should be throttled
        ctx2 = HookContext(
            event=HookEvent.ON_PROGRESS,
            percent_complete=30.0,
            items_completed=300,
            total_items=1000,
            timestamp=1.3  # Only 0.3s later
        )
        hook(ctx2)
        assert len(calls) == 1  # Still 1
        
        # Third call after interval - should go through
        ctx3 = HookContext(
            event=HookEvent.ON_PROGRESS,
            percent_complete=50.0,
            items_completed=500,
            total_items=1000,
            timestamp=1.6  # 0.6s after first call
        )
        hook(ctx3)
        assert len(calls) == 2


class TestTimingHook:
    """Tests for create_timing_hook helper."""
    
    def test_timing_hook(self):
        """Test creating and using a timing hook."""
        calls = []
        
        def callback(event_name, elapsed):
            calls.append((event_name, elapsed))
        
        hook = create_timing_hook(callback)
        
        ctx = HookContext(
            event=HookEvent.POST_EXECUTE,
            elapsed_time=12.5
        )
        
        hook(ctx)
        
        assert len(calls) == 1
        assert calls[0][0] == "post_execute"
        assert calls[0][1] == 12.5


class TestThroughputHook:
    """Tests for create_throughput_hook helper."""
    
    def test_throughput_hook(self):
        """Test creating and using a throughput hook."""
        calls = []
        
        def callback(rate):
            calls.append(rate)
        
        hook = create_throughput_hook(callback, min_interval=0.0)
        
        ctx = HookContext(
            event=HookEvent.ON_PROGRESS,
            throughput_items_per_sec=125.5
        )
        
        hook(ctx)
        
        assert len(calls) == 1
        assert calls[0] == 125.5
    
    def test_throughput_throttling(self):
        """Test that throughput updates are throttled."""
        calls = []
        
        def callback(rate):
            calls.append(rate)
        
        hook = create_throughput_hook(callback, min_interval=2.0)
        
        # First call (starts at t=3.0 to pass initial check)
        ctx1 = HookContext(
            event=HookEvent.ON_PROGRESS,
            throughput_items_per_sec=100.0,
            timestamp=3.0
        )
        hook(ctx1)
        assert len(calls) == 1
        
        # Second call too soon (only 1.5s later)
        ctx2 = HookContext(
            event=HookEvent.ON_PROGRESS,
            throughput_items_per_sec=110.0,
            timestamp=4.5
        )
        hook(ctx2)
        assert len(calls) == 1  # Still 1 - throttled
        
        # Third call after interval (2.5s after first)
        ctx3 = HookContext(
            event=HookEvent.ON_PROGRESS,
            throughput_items_per_sec=120.0,
            timestamp=5.5
        )
        hook(ctx3)
        assert len(calls) == 2


class TestErrorHook:
    """Tests for create_error_hook helper."""
    
    def test_error_hook(self):
        """Test creating and using an error hook."""
        calls = []
        
        def callback(error, traceback_str):
            calls.append((str(error), traceback_str))
        
        hook = create_error_hook(callback)
        
        error = ValueError("Test error")
        ctx = HookContext(
            event=HookEvent.ON_ERROR,
            error=error,
            error_traceback="Traceback...\nValueError: Test error"
        )
        
        hook(ctx)
        
        assert len(calls) == 1
        assert "Test error" in calls[0][0]
        assert "Traceback..." in calls[0][1]
    
    def test_error_hook_no_error(self):
        """Test error hook when context has no error."""
        calls = []
        
        def callback(error, traceback_str):
            calls.append((str(error), traceback_str))
        
        hook = create_error_hook(callback)
        
        ctx = HookContext(
            event=HookEvent.ON_ERROR,
            error=None
        )
        
        hook(ctx)
        
        # Callback should not be called when no error
        assert len(calls) == 0


class TestThreadSafety:
    """Tests for thread safety of HookManager."""
    
    def test_concurrent_registration(self):
        """Test that concurrent registration is thread-safe."""
        
        manager = HookManager()
        
        def register_hooks(thread_id):
            # Create factory function to avoid closure issues
            def make_hook(tid):
                def hook(ctx: HookContext):
                    pass
                return hook
            
            for i in range(10):
                manager.register(HookEvent.ON_PROGRESS, make_hook(thread_id))
        
        threads = [
            threading.Thread(target=register_hooks, args=(i,))
            for i in range(5)
        ]
        
        for t in threads:
            t.start()
        for t in threads:
            t.join()
        
        # All hooks should be registered (5 threads * 10 hooks each)
        assert manager.get_hook_count(HookEvent.ON_PROGRESS) == 50
    
    def test_concurrent_triggering(self):
        """Test that concurrent triggering is thread-safe."""
        
        manager = HookManager()
        call_count = [0]
        lock = threading.Lock()
        
        def hook(ctx: HookContext):
            with lock:
                call_count[0] += 1
        
        manager.register(HookEvent.ON_PROGRESS, hook)
        
        def trigger_hook():
            for _ in range(10):
                ctx = HookContext(event=HookEvent.ON_PROGRESS)
                manager.trigger(ctx)
        
        threads = [
            threading.Thread(target=trigger_hook)
            for _ in range(5)
        ]
        
        for t in threads:
            t.start()
        for t in threads:
            t.join()
        
        # Hook should be called for each trigger (5 threads * 10 calls each)
        assert call_count[0] == 50


class TestTriggerAPIConventions:
    """Tests for trigger() method supporting multiple calling conventions."""
    
    def test_trigger_with_context_only(self):
        """Test trigger() with HookContext (preferred style)."""
        manager = HookManager()
        called = []
        
        def hook(ctx: HookContext):
            called.append(ctx.event)
        
        manager.register(HookEvent.PRE_EXECUTE, hook)
        
        # Call with context only (preferred style)
        ctx = HookContext(event=HookEvent.PRE_EXECUTE, n_jobs=4)
        manager.trigger(ctx)
        
        assert len(called) == 1
        assert called[0] == HookEvent.PRE_EXECUTE
    
    def test_trigger_with_event_and_context(self):
        """Test trigger() with event and context separately (legacy style)."""
        manager = HookManager()
        called = []
        
        def hook(ctx: HookContext):
            called.append((ctx.event, ctx.n_jobs))
        
        manager.register(HookEvent.ON_PROGRESS, hook)
        
        # Call with event and context separately (legacy style)
        ctx = HookContext(event=HookEvent.ON_PROGRESS, n_jobs=8)
        manager.trigger(HookEvent.ON_PROGRESS, ctx)
        
        assert len(called) == 1
        assert called[0] == (HookEvent.ON_PROGRESS, 8)
    
    def test_trigger_both_conventions_work(self):
        """Test that both calling conventions produce the same results."""
        manager = HookManager()
        results = []
        
        def hook(ctx: HookContext):
            results.append({
                'event': ctx.event,
                'n_jobs': ctx.n_jobs,
                'timestamp': ctx.timestamp
            })
        
        manager.register(HookEvent.PRE_EXECUTE, hook)
        manager.register(HookEvent.POST_EXECUTE, hook)
        
        # Test preferred style
        ctx1 = HookContext(event=HookEvent.PRE_EXECUTE, n_jobs=4)
        manager.trigger(ctx1)
        
        # Test legacy style
        ctx2 = HookContext(event=HookEvent.POST_EXECUTE, n_jobs=8)
        manager.trigger(HookEvent.POST_EXECUTE, ctx2)
        
        assert len(results) == 2
        assert results[0]['event'] == HookEvent.PRE_EXECUTE
        assert results[0]['n_jobs'] == 4
        assert results[1]['event'] == HookEvent.POST_EXECUTE
        assert results[1]['n_jobs'] == 8
    
    def test_trigger_event_mismatch_correction(self):
        """Test that event parameter overrides context.event when both provided."""
        manager = HookManager()
        captured_events = []
        
        def hook(ctx: HookContext):
            captured_events.append(ctx.event)
        
        manager.register(HookEvent.ON_PROGRESS, hook)
        manager.register(HookEvent.POST_EXECUTE, hook)
        
        # Create context with one event, but trigger with different event
        # The event parameter should take precedence
        ctx = HookContext(event=HookEvent.POST_EXECUTE, n_jobs=4)
        manager.trigger(HookEvent.ON_PROGRESS, ctx)
        
        # Hook for ON_PROGRESS should be called, not POST_EXECUTE
        assert len(captured_events) == 1
        assert captured_events[0] == HookEvent.ON_PROGRESS
    
    def test_trigger_with_invalid_first_param(self):
        """Test that trigger() rejects invalid first parameter."""
        manager = HookManager()
        
        # Should reject string
        with pytest.raises(TypeError, match="First parameter must be HookEvent or HookContext"):
            manager.trigger("invalid")
        
        # Should reject integer
        with pytest.raises(TypeError, match="First parameter must be HookEvent or HookContext"):
            manager.trigger(42)
        
        # Should reject None
        with pytest.raises(TypeError, match="First parameter must be HookEvent or HookContext"):
            manager.trigger(None)
    
    def test_trigger_context_with_extra_param(self):
        """Test that trigger(context, extra) raises ValueError."""
        manager = HookManager()
        ctx = HookContext(event=HookEvent.PRE_EXECUTE)
        extra_ctx = HookContext(event=HookEvent.POST_EXECUTE)
        
        with pytest.raises(ValueError, match="context parameter must be None"):
            manager.trigger(ctx, extra_ctx)
    
    def test_trigger_event_without_context(self):
        """Test that trigger(event) without context raises ValueError."""
        manager = HookManager()
        
        with pytest.raises(ValueError, match="context parameter must be provided"):
            manager.trigger(HookEvent.PRE_EXECUTE)
    
    def test_trigger_legacy_style_in_thread_safety(self):
        """Test that legacy calling style is thread-safe."""
        
        manager = HookManager()
        call_count = [0]
        lock = threading.Lock()
        
        def hook(ctx: HookContext):
            with lock:
                call_count[0] += 1
        
        manager.register(HookEvent.ON_PROGRESS, hook)
        
        def trigger_hook_legacy():
            for i in range(10):
                ctx = HookContext(event=HookEvent.ON_PROGRESS, items_completed=i)
                # Use legacy calling style
                manager.trigger(HookEvent.ON_PROGRESS, ctx)
        
        threads = [
            threading.Thread(target=trigger_hook_legacy)
            for _ in range(5)
        ]
        
        for t in threads:
            t.start()
        for t in threads:
            t.join()
        
        # Hook should be called for each trigger (5 threads * 10 calls each)
        assert call_count[0] == 50
    
    def test_trigger_mixed_styles_interleaved(self):
        """Test that preferred and legacy styles can be interleaved."""
        manager = HookManager()
        events_received = []
        
        def hook(ctx: HookContext):
            events_received.append((ctx.event, ctx.n_jobs))
        
        manager.register(HookEvent.PRE_EXECUTE, hook)
        manager.register(HookEvent.POST_EXECUTE, hook)
        manager.register(HookEvent.ON_PROGRESS, hook)
        
        # Interleave both styles
        ctx1 = HookContext(event=HookEvent.PRE_EXECUTE, n_jobs=2)
        manager.trigger(ctx1)  # Preferred
        
        ctx2 = HookContext(event=HookEvent.POST_EXECUTE, n_jobs=4)
        manager.trigger(HookEvent.POST_EXECUTE, ctx2)  # Legacy
        
        ctx3 = HookContext(event=HookEvent.ON_PROGRESS, n_jobs=6)
        manager.trigger(ctx3)  # Preferred
        
        ctx4 = HookContext(event=HookEvent.PRE_EXECUTE, n_jobs=8)
        manager.trigger(HookEvent.PRE_EXECUTE, ctx4)  # Legacy
        
        assert len(events_received) == 4
        assert events_received[0] == (HookEvent.PRE_EXECUTE, 2)
        assert events_received[1] == (HookEvent.POST_EXECUTE, 4)
        assert events_received[2] == (HookEvent.ON_PROGRESS, 6)
        assert events_received[3] == (HookEvent.PRE_EXECUTE, 8)
