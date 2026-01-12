"""
Tests for retry logic with exponential backoff.
"""

import time
import pytest
from amorsize.retry import (
    RetryPolicy,
    with_retry,
    retry_call,
    RetryExhaustedError,
    create_batch_retry_wrapper
)


class TestRetryPolicy:
    """Tests for RetryPolicy configuration."""
    
    def test_default_policy(self):
        """Test default policy configuration."""
        policy = RetryPolicy()
        assert policy.max_retries == 3
        assert policy.initial_delay == 0.1
        assert policy.max_delay == 60.0
        assert policy.exponential_base == 2.0
        assert policy.jitter is True
        assert policy.retry_on_exceptions is None
        assert policy.on_retry is None
    
    def test_custom_policy(self):
        """Test custom policy configuration."""
        policy = RetryPolicy(
            max_retries=5,
            initial_delay=0.5,
            max_delay=30.0,
            exponential_base=3.0,
            jitter=False
        )
        assert policy.max_retries == 5
        assert policy.initial_delay == 0.5
        assert policy.max_delay == 30.0
        assert policy.exponential_base == 3.0
        assert policy.jitter is False
    
    def test_invalid_max_retries(self):
        """Test validation of max_retries."""
        with pytest.raises(ValueError, match="max_retries must be >= -1"):
            RetryPolicy(max_retries=-2)
    
    def test_invalid_initial_delay(self):
        """Test validation of initial_delay."""
        with pytest.raises(ValueError, match="initial_delay must be positive"):
            RetryPolicy(initial_delay=0)
        with pytest.raises(ValueError, match="initial_delay must be positive"):
            RetryPolicy(initial_delay=-1)
    
    def test_invalid_max_delay(self):
        """Test validation of max_delay."""
        with pytest.raises(ValueError, match="max_delay must be >= initial_delay"):
            RetryPolicy(initial_delay=1.0, max_delay=0.5)
    
    def test_invalid_exponential_base(self):
        """Test validation of exponential_base."""
        with pytest.raises(ValueError, match="exponential_base must be >= 1.0"):
            RetryPolicy(exponential_base=0.5)
    
    def test_calculate_delay_without_jitter(self):
        """Test delay calculation without jitter."""
        policy = RetryPolicy(
            initial_delay=0.1,
            exponential_base=2.0,
            jitter=False
        )
        
        # Attempt 1: 0.1 * 2^0 = 0.1
        assert policy.calculate_delay(1) == 0.1
        
        # Attempt 2: 0.1 * 2^1 = 0.2
        assert policy.calculate_delay(2) == 0.2
        
        # Attempt 3: 0.1 * 2^2 = 0.4
        assert policy.calculate_delay(3) == 0.4
        
        # Attempt 4: 0.1 * 2^3 = 0.8
        assert policy.calculate_delay(4) == 0.8
    
    def test_calculate_delay_with_max_delay(self):
        """Test delay calculation respects max_delay."""
        policy = RetryPolicy(
            initial_delay=1.0,
            max_delay=5.0,
            exponential_base=2.0,
            jitter=False
        )
        
        # Should be capped at max_delay
        assert policy.calculate_delay(10) == 5.0
    
    def test_calculate_delay_with_jitter(self):
        """Test delay calculation with jitter adds randomness."""
        policy = RetryPolicy(
            initial_delay=1.0,
            exponential_base=2.0,
            jitter=True
        )
        
        # With jitter, delays should vary but be in reasonable range
        delays = [policy.calculate_delay(2) for _ in range(10)]
        
        # Base delay is 2.0, jitter range is [0.75, 1.25]
        # So delays should be in range [1.5, 2.5]
        assert all(1.5 <= d <= 2.5 for d in delays)
        
        # At least some delays should be different (jitter working)
        assert len(set(delays)) > 1
    
    def test_should_retry_within_max_retries(self):
        """Test should_retry returns True within max retries."""
        policy = RetryPolicy(max_retries=3)
        
        exc = ValueError("test error")
        assert policy.should_retry(exc, 1) is True
        assert policy.should_retry(exc, 2) is True
        assert policy.should_retry(exc, 3) is True
        assert policy.should_retry(exc, 4) is False
    
    def test_should_retry_infinite_retries(self):
        """Test should_retry with infinite retries."""
        policy = RetryPolicy(max_retries=-1)
        
        exc = ValueError("test error")
        # Should always return True for infinite retries
        assert policy.should_retry(exc, 100) is True
        assert policy.should_retry(exc, 1000) is True
    
    def test_should_retry_specific_exceptions(self):
        """Test should_retry with specific exception types."""
        policy = RetryPolicy(
            max_retries=3,
            retry_on_exceptions=(ValueError, KeyError)
        )
        
        # Should retry on specified exceptions
        assert policy.should_retry(ValueError("test"), 1) is True
        assert policy.should_retry(KeyError("test"), 1) is True
        
        # Should not retry on other exceptions
        assert policy.should_retry(TypeError("test"), 1) is False
        assert policy.should_retry(RuntimeError("test"), 1) is False


class TestWithRetryDecorator:
    """Tests for @with_retry decorator."""
    
    def test_retry_succeeds_eventually(self):
        """Test function succeeds after retries."""
        call_count = [0]
        
        @with_retry(max_retries=3, initial_delay=0.01)
        def flaky_function():
            call_count[0] += 1
            if call_count[0] < 3:
                raise ValueError("Not yet")
            return "success"
        
        result = flaky_function()
        assert result == "success"
        assert call_count[0] == 3
    
    def test_retry_exhausted(self):
        """Test exception raised when retries exhausted."""
        @with_retry(max_retries=2, initial_delay=0.01)
        def always_fails():
            raise ValueError("Always fails")
        
        with pytest.raises(ValueError, match="Always fails"):
            always_fails()
    
    def test_no_retry_on_success(self):
        """Test function not retried if it succeeds first time."""
        call_count = [0]
        
        @with_retry(max_retries=3, initial_delay=0.01)
        def success_function():
            call_count[0] += 1
            return "success"
        
        result = success_function()
        assert result == "success"
        assert call_count[0] == 1
    
    def test_retry_with_specific_exceptions(self):
        """Test retry only on specific exception types."""
        call_count = [0]
        
        @with_retry(
            max_retries=3,
            initial_delay=0.01,
            retry_on_exceptions=(ValueError,)
        )
        def selective_retry():
            call_count[0] += 1
            if call_count[0] == 1:
                raise ValueError("Retryable")
            elif call_count[0] == 2:
                raise TypeError("Not retryable")
            return "success"
        
        # Should retry ValueError but not TypeError
        with pytest.raises(TypeError, match="Not retryable"):
            selective_retry()
        
        assert call_count[0] == 2  # Called twice (original + 1 retry)
    
    def test_retry_callback(self):
        """Test on_retry callback is called."""
        callback_calls = []
        
        def track_retry(exc, attempt, delay):
            callback_calls.append((exc, attempt, delay))
        
        call_count = [0]
        
        @with_retry(max_retries=3, initial_delay=0.01, on_retry=track_retry)
        def flaky_function():
            call_count[0] += 1
            if call_count[0] < 3:
                raise ValueError(f"Attempt {call_count[0]}")
            return "success"
        
        result = flaky_function()
        assert result == "success"
        
        # Callback should be called twice (for 2 retries)
        assert len(callback_calls) == 2
        
        # Check callback parameters
        exc1, attempt1, delay1 = callback_calls[0]
        assert isinstance(exc1, ValueError)
        assert attempt1 == 1
        assert delay1 > 0
        
        exc2, attempt2, delay2 = callback_calls[1]
        assert isinstance(exc2, ValueError)
        assert attempt2 == 2
        assert delay2 > 0
    
    def test_decorator_without_parentheses(self):
        """Test @with_retry can be used without parentheses."""
        call_count = [0]
        
        @with_retry
        def flaky_function():
            call_count[0] += 1
            if call_count[0] < 2:
                raise ValueError("Not yet")
            return "success"
        
        result = flaky_function()
        assert result == "success"
        assert call_count[0] == 2
    
    def test_decorator_with_policy(self):
        """Test @with_retry can be used with pre-configured policy."""
        policy = RetryPolicy(max_retries=5, initial_delay=0.01)
        call_count = [0]
        
        @with_retry(policy=policy)
        def flaky_function():
            call_count[0] += 1
            if call_count[0] < 4:
                raise ValueError("Not yet")
            return "success"
        
        result = flaky_function()
        assert result == "success"
        assert call_count[0] == 4
    
    def test_retry_with_arguments(self):
        """Test decorated function with arguments works correctly."""
        call_count = [0]
        
        @with_retry(max_retries=2, initial_delay=0.01)
        def add_with_retry(a, b):
            call_count[0] += 1
            if call_count[0] < 2:
                raise ValueError("Not yet")
            return a + b
        
        result = add_with_retry(3, 4)
        assert result == 7
        assert call_count[0] == 2
    
    def test_retry_preserves_function_metadata(self):
        """Test decorator preserves function name and docstring."""
        @with_retry(max_retries=3)
        def my_function():
            """My docstring."""
            return "result"
        
        assert my_function.__name__ == "my_function"
        assert my_function.__doc__ == "My docstring."


class TestRetryCall:
    """Tests for retry_call function."""
    
    def test_retry_call_succeeds(self):
        """Test retry_call with successful function."""
        def add(a, b):
            return a + b
        
        result = retry_call(add, args=(3, 4), max_retries=3)
        assert result == 7
    
    def test_retry_call_with_retries(self):
        """Test retry_call retries on failure."""
        call_count = [0]
        
        def flaky_function():
            call_count[0] += 1
            if call_count[0] < 3:
                raise ValueError("Not yet")
            return "success"
        
        result = retry_call(flaky_function, max_retries=3, initial_delay=0.01)
        assert result == "success"
        assert call_count[0] == 3
    
    def test_retry_call_with_kwargs(self):
        """Test retry_call with keyword arguments."""
        def greet(name, greeting="Hello"):
            return f"{greeting}, {name}!"
        
        result = retry_call(
            greet,
            args=("World",),
            kwargs={"greeting": "Hi"},
            max_retries=2
        )
        assert result == "Hi, World!"
    
    def test_retry_call_with_policy(self):
        """Test retry_call with pre-configured policy."""
        policy = RetryPolicy(max_retries=5, initial_delay=0.01)
        call_count = [0]
        
        def flaky_function():
            call_count[0] += 1
            if call_count[0] < 4:
                raise ValueError("Not yet")
            return "success"
        
        result = retry_call(flaky_function, policy=policy)
        assert result == "success"
        assert call_count[0] == 4


class TestBatchRetryWrapper:
    """Tests for create_batch_retry_wrapper."""
    
    def test_batch_retry_wrapper(self):
        """Test batch retry wrapper processes items with retry."""
        call_counts = {}
        
        def process_item(x):
            if x not in call_counts:
                call_counts[x] = 0
            call_counts[x] += 1
            
            # Fail first two attempts for items divisible by 3
            if x % 3 == 0 and call_counts[x] < 3:
                raise ValueError(f"Temporary failure for {x}")
            
            return x * 2
        
        policy = RetryPolicy(max_retries=3, initial_delay=0.01)
        wrapper = create_batch_retry_wrapper(process_item, policy)
        
        # Process batch
        items = [1, 2, 3, 4, 5, 6]
        results = [wrapper(item) for item in items]
        
        assert results == [2, 4, 6, 8, 10, 12]
        
        # Items divisible by 3 should have been retried
        assert call_counts[3] == 3
        assert call_counts[6] == 3
        
        # Other items should only be called once
        assert call_counts[1] == 1
        assert call_counts[2] == 1


class TestRetryTiming:
    """Tests for retry timing and exponential backoff."""
    
    def test_exponential_backoff_timing(self):
        """Test that delays increase exponentially."""
        retry_times = []
        
        def track_retry(exc, attempt, delay):
            retry_times.append((attempt, delay))
        
        call_count = [0]
        
        @with_retry(
            max_retries=4,
            initial_delay=0.05,
            exponential_base=2.0,
            jitter=False,
            on_retry=track_retry
        )
        def always_fails():
            call_count[0] += 1
            raise ValueError("Fail")
        
        try:
            always_fails()
        except ValueError:
            pass
        
        # Check that delays increase exponentially
        assert len(retry_times) == 4
        
        # Delays should be approximately 0.05, 0.1, 0.2, 0.4
        # (Allow small margin for timing variations)
        assert 0.04 <= retry_times[0][1] <= 0.06  # ~0.05
        assert 0.09 <= retry_times[1][1] <= 0.11  # ~0.10
        assert 0.18 <= retry_times[2][1] <= 0.22  # ~0.20
        assert 0.36 <= retry_times[3][1] <= 0.44  # ~0.40
    
    def test_actual_wait_time(self):
        """Test that function actually waits between retries."""
        call_times = []
        
        @with_retry(max_retries=3, initial_delay=0.1, jitter=False)
        def timed_function():
            call_times.append(time.time())
            if len(call_times) < 3:
                raise ValueError("Not yet")
            return "success"
        
        start = time.time()
        result = timed_function()
        total_time = time.time() - start
        
        assert result == "success"
        assert len(call_times) == 3
        
        # Should have waited ~0.1s + ~0.2s = ~0.3s total
        # Allow margin for execution time
        assert total_time >= 0.25
        
        # Check timing between calls
        time_between_1_2 = call_times[1] - call_times[0]
        time_between_2_3 = call_times[2] - call_times[1]
        
        # First retry delay: ~0.1s
        assert 0.08 <= time_between_1_2 <= 0.15
        
        # Second retry delay: ~0.2s
        assert 0.18 <= time_between_2_3 <= 0.25


class TestEdgeCases:
    """Tests for edge cases and error conditions."""
    
    def test_zero_retries(self):
        """Test with max_retries=0 (no retries)."""
        call_count = [0]
        
        @with_retry(max_retries=0, initial_delay=0.01)
        def fails_once():
            call_count[0] += 1
            raise ValueError("Fail")
        
        with pytest.raises(ValueError, match="Fail"):
            fails_once()
        
        # Should only be called once (no retries)
        assert call_count[0] == 1
    
    def test_callback_exception_doesnt_break_retry(self):
        """Test that exceptions in callback don't break retry logic."""
        call_count = [0]
        
        def broken_callback(exc, attempt, delay):
            raise RuntimeError("Callback error")
        
        @with_retry(
            max_retries=3,
            initial_delay=0.01,
            on_retry=broken_callback
        )
        def flaky_function():
            call_count[0] += 1
            if call_count[0] < 3:
                raise ValueError("Not yet")
            return "success"
        
        # Should still succeed despite callback errors
        result = flaky_function()
        assert result == "success"
        assert call_count[0] == 3
    
    def test_retry_with_return_value(self):
        """Test that return values are preserved through retries."""
        call_count = [0]
        
        @with_retry(max_retries=3, initial_delay=0.01)
        def get_value():
            call_count[0] += 1
            if call_count[0] < 2:
                raise ValueError("Not yet")
            return {"status": "ok", "data": [1, 2, 3]}
        
        result = get_value()
        assert result == {"status": "ok", "data": [1, 2, 3]}
    
    def test_retry_with_none_return(self):
        """Test that None return values work correctly."""
        call_count = [0]
        
        @with_retry(max_retries=3, initial_delay=0.01)
        def returns_none():
            call_count[0] += 1
            if call_count[0] < 2:
                raise ValueError("Not yet")
            return None
        
        result = returns_none()
        assert result is None
        assert call_count[0] == 2
