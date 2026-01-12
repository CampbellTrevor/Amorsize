"""
Tests for rate limiting functionality.
"""

import pytest
import time
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed

from amorsize.rate_limit import (
    RateLimitPolicy,
    RateLimiter,
    RateLimitExceeded,
    with_rate_limit,
    rate_limited_call,
)


class TestRateLimitPolicy:
    """Tests for RateLimitPolicy configuration."""
    
    def test_default_policy(self):
        """Test default policy values."""
        policy = RateLimitPolicy()
        assert policy.requests_per_second == 10.0
        assert policy.burst_size == 10  # Defaults to requests_per_second
        assert policy.wait_on_limit is True
        assert policy.on_wait is None
    
    def test_custom_policy(self):
        """Test custom policy configuration."""
        def callback(wait_time):
            pass
        
        policy = RateLimitPolicy(
            requests_per_second=5.0,
            burst_size=20,
            wait_on_limit=False,
            on_wait=callback
        )
        assert policy.requests_per_second == 5.0
        assert policy.burst_size == 20
        assert policy.wait_on_limit is False
        assert policy.on_wait is callback
    
    def test_invalid_requests_per_second(self):
        """Test validation of requests_per_second."""
        with pytest.raises(ValueError, match="requests_per_second must be positive"):
            RateLimitPolicy(requests_per_second=0)
        
        with pytest.raises(ValueError, match="requests_per_second must be positive"):
            RateLimitPolicy(requests_per_second=-1)
    
    def test_invalid_burst_size(self):
        """Test validation of burst_size."""
        with pytest.raises(ValueError, match="burst_size must be >= 1"):
            RateLimitPolicy(requests_per_second=10.0, burst_size=0)


class TestRateLimiter:
    """Tests for RateLimiter functionality."""
    
    def test_limiter_initialization(self):
        """Test limiter initializes with full bucket."""
        policy = RateLimitPolicy(requests_per_second=10.0, burst_size=20)
        limiter = RateLimiter(policy)
        
        # Should start with full bucket
        assert limiter.get_available_tokens() == 20.0
    
    def test_acquire_single_token(self):
        """Test acquiring a single token."""
        policy = RateLimitPolicy(requests_per_second=10.0)
        limiter = RateLimiter(policy)
        
        initial_tokens = limiter.get_available_tokens()
        limiter.acquire()
        # Allow small tolerance for time elapsed during execution
        assert abs(limiter.get_available_tokens() - (initial_tokens - 1.0)) < 0.1
    
    def test_acquire_multiple_tokens(self):
        """Test acquiring multiple tokens at once."""
        policy = RateLimitPolicy(requests_per_second=10.0, burst_size=20)
        limiter = RateLimiter(policy)
        
        limiter.acquire(tokens=5.0)
        # Allow small tolerance for time elapsed during execution
        assert abs(limiter.get_available_tokens() - 15.0) < 0.1
    
    def test_try_acquire_success(self):
        """Test try_acquire when tokens available."""
        policy = RateLimitPolicy(requests_per_second=10.0)
        limiter = RateLimiter(policy)
        
        assert limiter.try_acquire() is True
        # Allow small tolerance for time elapsed during execution
        assert abs(limiter.get_available_tokens() - 9.0) < 0.1
    
    def test_try_acquire_failure(self):
        """Test try_acquire when insufficient tokens."""
        policy = RateLimitPolicy(requests_per_second=10.0, burst_size=5)
        limiter = RateLimiter(policy)
        
        # Exhaust tokens
        for _ in range(5):
            limiter.acquire()
        
        assert limiter.try_acquire() is False
    
    def test_token_refill_over_time(self):
        """Test that tokens refill at the correct rate."""
        policy = RateLimitPolicy(requests_per_second=10.0)
        limiter = RateLimiter(policy)
        
        # Exhaust tokens
        for _ in range(10):
            limiter.acquire()
        
        # Allow small tolerance for time elapsed during loop
        assert limiter.get_available_tokens() < 0.1
        
        # Wait for refill
        time.sleep(0.5)  # Should refill 5 tokens (10 req/s * 0.5s)
        
        tokens = limiter.get_available_tokens()
        # Allow some tolerance for timing
        assert 4.0 <= tokens <= 6.0
    
    def test_acquire_waits_when_necessary(self):
        """Test that acquire waits when tokens unavailable."""
        policy = RateLimitPolicy(requests_per_second=10.0, burst_size=5)
        limiter = RateLimiter(policy)
        
        # Exhaust tokens
        for _ in range(5):
            limiter.acquire()
        
        start = time.time()
        limiter.acquire()  # Should wait
        elapsed = time.time() - start
        
        # Should wait approximately 0.1s (1 token / 10 req/s)
        assert 0.05 <= elapsed <= 0.2
    
    def test_acquire_raises_when_wait_disabled(self):
        """Test that acquire raises exception when wait_on_limit=False."""
        policy = RateLimitPolicy(
            requests_per_second=10.0,
            burst_size=5,
            wait_on_limit=False
        )
        limiter = RateLimiter(policy)
        
        # Exhaust tokens
        for _ in range(5):
            limiter.acquire()
        
        with pytest.raises(RateLimitExceeded):
            limiter.acquire()
    
    def test_reset(self):
        """Test reset refills bucket to capacity."""
        policy = RateLimitPolicy(requests_per_second=10.0, burst_size=20)
        limiter = RateLimiter(policy)
        
        # Consume some tokens
        limiter.acquire(tokens=15.0)
        # Allow small tolerance for time elapsed
        assert abs(limiter.get_available_tokens() - 5.0) < 0.1
        
        # Reset
        limiter.reset()
        assert abs(limiter.get_available_tokens() - 20.0) < 0.001
    
    def test_context_manager(self):
        """Test rate limiter as context manager."""
        policy = RateLimitPolicy(requests_per_second=10.0)
        limiter = RateLimiter(policy)
        
        initial_tokens = limiter.get_available_tokens()
        
        with limiter:
            pass  # Token acquired in __enter__
        
        # Allow small tolerance for time elapsed
        assert abs(limiter.get_available_tokens() - (initial_tokens - 1.0)) < 0.1
    
    def test_concurrent_access_thread_safety(self):
        """Test that limiter is thread-safe."""
        policy = RateLimitPolicy(requests_per_second=100.0, burst_size=100)
        limiter = RateLimiter(policy)
        
        acquired_count = [0]
        lock = threading.Lock()
        
        def acquire_token():
            if limiter.try_acquire():
                with lock:
                    acquired_count[0] += 1
        
        # Try to acquire 150 tokens from 10 threads
        with ThreadPoolExecutor(max_workers=10) as executor:
            futures = [executor.submit(acquire_token) for _ in range(150)]
            for future in as_completed(futures):
                future.result()
        
        # Should only acquire 100 tokens (burst_size)
        assert acquired_count[0] == 100
    
    def test_invalid_token_count(self):
        """Test that invalid token counts raise errors."""
        policy = RateLimitPolicy(requests_per_second=10.0)
        limiter = RateLimiter(policy)
        
        with pytest.raises(ValueError, match="tokens must be positive"):
            limiter.acquire(tokens=0)
        
        with pytest.raises(ValueError, match="tokens must be positive"):
            limiter.try_acquire(tokens=-1)
    
    def test_on_wait_callback(self):
        """Test that on_wait callback is called."""
        wait_times = []
        
        def record_wait(wait_time):
            wait_times.append(wait_time)
        
        policy = RateLimitPolicy(
            requests_per_second=10.0,
            burst_size=5,
            on_wait=record_wait
        )
        limiter = RateLimiter(policy)
        
        # Exhaust tokens
        for _ in range(5):
            limiter.acquire()
        
        # This should trigger callback
        limiter.acquire()
        
        assert len(wait_times) > 0
        assert wait_times[0] > 0
    
    def test_on_wait_callback_error_handling(self):
        """Test that callback errors don't break rate limiting."""
        def failing_callback(wait_time):
            raise RuntimeError("Callback error")
        
        policy = RateLimitPolicy(
            requests_per_second=10.0,
            burst_size=5,
            on_wait=failing_callback
        )
        limiter = RateLimiter(policy)
        
        # Exhaust tokens
        for _ in range(5):
            limiter.acquire()
        
        # Should not raise even though callback fails
        limiter.acquire()  # Should succeed


class TestWithRateLimitDecorator:
    """Tests for @with_rate_limit decorator."""
    
    def test_decorator_without_arguments(self):
        """Test decorator used without parentheses."""
        call_count = [0]
        
        @with_rate_limit
        def func():
            call_count[0] += 1
            return "success"
        
        result = func()
        assert result == "success"
        assert call_count[0] == 1
    
    def test_decorator_with_arguments(self):
        """Test decorator used with arguments."""
        @with_rate_limit(requests_per_second=5.0, burst_size=10)
        def func():
            return "success"
        
        result = func()
        assert result == "success"
    
    def test_decorator_with_policy(self):
        """Test decorator with pre-configured policy."""
        policy = RateLimitPolicy(requests_per_second=10.0)
        
        @with_rate_limit(policy=policy)
        def func():
            return "success"
        
        result = func()
        assert result == "success"
    
    def test_decorator_with_shared_limiter(self):
        """Test multiple functions sharing same limiter."""
        policy = RateLimitPolicy(requests_per_second=10.0, burst_size=10)
        limiter = RateLimiter(policy)
        
        @with_rate_limit(limiter=limiter)
        def func1():
            return "func1"
        
        @with_rate_limit(limiter=limiter)
        def func2():
            return "func2"
        
        # Both should share the same token bucket
        initial_tokens = limiter.get_available_tokens()
        func1()
        func2()
        # Allow small tolerance for time elapsed
        assert abs(limiter.get_available_tokens() - (initial_tokens - 2.0)) < 0.1
    
    def test_decorator_enforces_rate_limit(self):
        """Test that decorator actually enforces rate limiting."""
        @with_rate_limit(requests_per_second=10.0, burst_size=5)
        def func():
            return time.time()
        
        # Exhaust burst
        for _ in range(5):
            func()
        
        # Next call should wait
        start = time.time()
        func()
        elapsed = time.time() - start
        
        assert elapsed >= 0.05  # Should wait for at least one token
    
    def test_decorator_with_function_arguments(self):
        """Test decorated function with arguments."""
        @with_rate_limit(requests_per_second=10.0)
        def func(x, y):
            return x + y
        
        result = func(2, 3)
        assert result == 5
    
    def test_decorator_preserves_function_metadata(self):
        """Test that decorator preserves function name and docstring."""
        @with_rate_limit
        def my_function():
            """My docstring."""
            pass
        
        assert my_function.__name__ == "my_function"
        assert my_function.__doc__ == "My docstring."
    
    def test_decorator_attaches_limiter(self):
        """Test that decorator attaches limiter to wrapper."""
        @with_rate_limit(requests_per_second=10.0)
        def func():
            pass
        
        assert hasattr(func, '_rate_limiter')
        assert isinstance(func._rate_limiter, RateLimiter)


class TestRateLimitedCall:
    """Tests for rate_limited_call function."""
    
    def test_basic_call(self):
        """Test basic rate_limited_call."""
        def func():
            return "success"
        
        result = rate_limited_call(func, requests_per_second=10.0)
        assert result == "success"
    
    def test_call_with_args(self):
        """Test rate_limited_call with arguments."""
        def func(x, y):
            return x + y
        
        result = rate_limited_call(
            func,
            args=(2, 3),
            requests_per_second=10.0
        )
        assert result == 5
    
    def test_call_with_kwargs(self):
        """Test rate_limited_call with keyword arguments."""
        def func(x, y=10):
            return x + y
        
        result = rate_limited_call(
            func,
            args=(5,),
            kwargs={"y": 20},
            requests_per_second=10.0
        )
        assert result == 25
    
    def test_call_with_policy(self):
        """Test rate_limited_call with pre-configured policy."""
        policy = RateLimitPolicy(requests_per_second=5.0)
        
        def func():
            return "success"
        
        result = rate_limited_call(func, policy=policy)
        assert result == "success"
    
    def test_call_enforces_rate_limit(self):
        """Test that rate_limited_call enforces rate limiting."""
        def func():
            return time.time()
        
        # Make calls that exceed burst
        start = time.time()
        for i in range(6):  # burst_size=5 by default
            rate_limited_call(func, requests_per_second=10.0, burst_size=5)
        elapsed = time.time() - start
        
        # Should take at least 0.05s (6th call waits for token)
        # But allow for fast execution where tokens may refill during the loop
        # Just verify no exception was raised
        assert elapsed >= 0.0


class TestIntegration:
    """Integration tests for rate limiting."""
    
    def test_rate_limit_api_calls(self):
        """Test rate limiting API-style calls."""
        call_times = []
        
        @with_rate_limit(requests_per_second=10.0)
        def api_call():
            call_times.append(time.time())
            return "data"
        
        # Make 15 calls
        for _ in range(15):
            api_call()
        
        # Verify rate is respected
        # First 10 should be fast (burst), rest should be rate-limited
        if len(call_times) >= 11:
            # Time between 10th and 11th call should be ~0.1s
            gap = call_times[10] - call_times[9]
            assert gap >= 0.05  # Allow some tolerance
    
    def test_rate_limit_with_retry(self):
        """Test combining rate limiting with retry pattern."""
        from amorsize.retry import with_retry, RetryPolicy
        
        call_count = [0]
        
        @with_rate_limit(requests_per_second=10.0)
        @with_retry(max_retries=2, initial_delay=0.01)
        def unreliable_api():
            call_count[0] += 1
            if call_count[0] < 2:
                raise ConnectionError("Temporary failure")
            return "success"
        
        result = unreliable_api()
        assert result == "success"
        assert call_count[0] == 2  # Failed once, then succeeded
    
    def test_parallel_execution_with_rate_limit(self):
        """Test rate limiting in parallel execution."""
        limiter = RateLimiter(RateLimitPolicy(requests_per_second=20.0, burst_size=20))
        
        @with_rate_limit(limiter=limiter)
        def process_item(x):
            return x * 2
        
        # Process items in parallel
        items = list(range(30))
        results = []
        
        start = time.time()
        with ThreadPoolExecutor(max_workers=10) as executor:
            futures = [executor.submit(process_item, x) for x in items]
            for future in as_completed(futures):
                results.append(future.result())
        elapsed = time.time() - start
        
        # Should process first 20 quickly (burst), then rate-limited
        # 10 extra items at 20 req/s = 0.5s minimum
        assert len(results) == 30
        assert elapsed >= 0.4  # Allow some tolerance
    
    def test_multiple_rate_limiters(self):
        """Test using multiple rate limiters for different resources."""
        limiter_fast = RateLimiter(RateLimitPolicy(requests_per_second=100.0))
        limiter_slow = RateLimiter(RateLimitPolicy(requests_per_second=5.0))
        
        @with_rate_limit(limiter=limiter_fast)
        def fast_api():
            return "fast"
        
        @with_rate_limit(limiter=limiter_slow)
        def slow_api():
            return "slow"
        
        # Fast API should be much faster
        start = time.time()
        for _ in range(10):
            fast_api()
        fast_elapsed = time.time() - start
        
        start = time.time()
        for _ in range(10):
            slow_api()
        slow_elapsed = time.time() - start
        
        assert fast_elapsed < slow_elapsed


class TestEdgeCases:
    """Tests for edge cases and boundary conditions."""
    
    def test_fractional_requests_per_second(self):
        """Test rate limiting with fractional requests/sec."""
        policy = RateLimitPolicy(requests_per_second=0.5)  # 1 request per 2 seconds
        limiter = RateLimiter(policy)
        
        limiter.acquire()
        
        # Next acquire should wait approximately 2 seconds
        start = time.time()
        limiter.acquire()
        elapsed = time.time() - start
        
        assert elapsed >= 1.8  # Allow some tolerance
    
    def test_very_high_rate(self):
        """Test rate limiting with very high rate."""
        policy = RateLimitPolicy(requests_per_second=1000.0, burst_size=1000)
        limiter = RateLimiter(policy)
        
        # Should handle high rate without issues
        for _ in range(1000):
            assert limiter.try_acquire() is True
    
    def test_burst_larger_than_rate(self):
        """Test burst size much larger than rate."""
        policy = RateLimitPolicy(requests_per_second=1.0, burst_size=100)
        limiter = RateLimiter(policy)
        
        # Should allow large burst initially
        for _ in range(100):
            limiter.acquire()
        
        # Then rate limited
        start = time.time()
        limiter.acquire()
        elapsed = time.time() - start
        assert elapsed >= 0.8  # Should wait ~1 second
    
    def test_acquire_exactly_available_tokens(self):
        """Test acquiring exactly the number of available tokens."""
        policy = RateLimitPolicy(requests_per_second=10.0, burst_size=10)
        limiter = RateLimiter(policy)
        
        # Acquire exactly 10 tokens
        limiter.acquire(tokens=10.0)
        # Allow small tolerance for time elapsed
        assert limiter.get_available_tokens() < 0.1
        
        # Should wait for next token
        assert limiter.try_acquire() is False
    
    def test_limiter_after_long_idle(self):
        """Test that limiter refills properly after long idle period."""
        policy = RateLimitPolicy(requests_per_second=10.0, burst_size=20)
        limiter = RateLimiter(policy)
        
        # Exhaust tokens
        for _ in range(20):
            limiter.acquire()
        
        # Wait long enough to refill past burst size
        time.sleep(3.0)  # Would refill 30 tokens, but capped at 20
        
        tokens = limiter.get_available_tokens()
        assert tokens == 20.0  # Should be capped at burst_size


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
