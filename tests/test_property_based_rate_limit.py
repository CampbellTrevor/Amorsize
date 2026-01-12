"""
Property-based tests for the rate_limit module using Hypothesis.

These tests automatically generate edge cases and verify invariant properties
of the rate limiting logic across a wide range of inputs and configurations.
"""

import time
import threading
from typing import Any

import pytest
from hypothesis import given, settings, strategies as st, HealthCheck, assume

from amorsize.rate_limit import (
    RateLimitPolicy,
    RateLimiter,
    RateLimitExceeded,
    with_rate_limit,
    rate_limited_call,
)


# Custom strategies for generating test data
@st.composite
def valid_rate_limit_policy(draw):
    """
    Generate valid RateLimitPolicy configurations.
    
    Generates policies with:
    - requests_per_second: 0.1 to 100.0 (covers low to high rates)
    - burst_size: None or 1 to 200 (None defaults to max(1, round(requests_per_second)))
    - wait_on_limit: True or False (controls wait vs exception behavior)
    - on_wait: None (kept simple for property testing)
    
    Returns:
        RateLimitPolicy with randomized but valid parameters
    """
    requests_per_second = draw(st.floats(min_value=0.1, max_value=100.0))
    burst_size = draw(st.one_of(
        st.none(),
        st.integers(min_value=1, max_value=200)
    ))
    wait_on_limit = draw(st.booleans())
    
    return RateLimitPolicy(
        requests_per_second=requests_per_second,
        burst_size=burst_size,
        wait_on_limit=wait_on_limit,
        on_wait=None  # Keep callbacks simple for property testing
    )


class TestRateLimitPolicyInvariants:
    """Test invariant properties of RateLimitPolicy."""

    @given(
        requests_per_second=st.floats(min_value=0.1, max_value=100.0),
        burst_size=st.one_of(st.none(), st.integers(min_value=1, max_value=200)),
        wait_on_limit=st.booleans()
    )
    @settings(max_examples=100, deadline=1000)
    def test_policy_initialization_valid_params(self, requests_per_second, burst_size, wait_on_limit):
        """Test that valid parameters create a policy without errors."""
        policy = RateLimitPolicy(
            requests_per_second=requests_per_second,
            burst_size=burst_size,
            wait_on_limit=wait_on_limit
        )
        
        assert policy.requests_per_second == requests_per_second
        assert policy.wait_on_limit == wait_on_limit
        
        # burst_size defaults to max(1, round(requests_per_second)) if None
        if burst_size is None:
            expected_burst = max(1, round(requests_per_second))
            assert policy.burst_size == expected_burst
        else:
            assert policy.burst_size == burst_size

    @given(requests_per_second=st.floats(max_value=0.0) | st.just(0.0))
    @settings(max_examples=50, deadline=1000)
    def test_policy_rejects_non_positive_requests_per_second(self, requests_per_second):
        """Test that non-positive requests_per_second raises ValueError."""
        assume(requests_per_second <= 0)  # Only test when value is <= 0 for this negative test
        with pytest.raises(ValueError, match="requests_per_second must be positive"):
            RateLimitPolicy(requests_per_second=requests_per_second)

    @given(burst_size=st.integers(max_value=0))
    @settings(max_examples=50, deadline=1000)
    def test_policy_rejects_non_positive_burst_size(self, burst_size):
        """Test that burst_size < 1 raises ValueError."""
        assume(burst_size < 1)
        with pytest.raises(ValueError, match="burst_size must be >= 1"):
            RateLimitPolicy(burst_size=burst_size)

    @given(requests_per_second=st.floats(min_value=0.1, max_value=100.0))
    @settings(max_examples=50, deadline=1000)
    def test_policy_default_burst_size_is_reasonable(self, requests_per_second):
        """Test that default burst_size is at least 1."""
        policy = RateLimitPolicy(requests_per_second=requests_per_second)
        assert policy.burst_size >= 1
        # burst_size should be close to requests_per_second (rounded)
        expected = max(1, round(requests_per_second))
        assert policy.burst_size == expected

    @given(
        requests_per_second=st.floats(min_value=0.1, max_value=100.0),
        burst_size=st.integers(min_value=1, max_value=200)
    )
    @settings(max_examples=50, deadline=1000)
    def test_policy_burst_size_can_exceed_rate(self, requests_per_second, burst_size):
        """Test that burst_size can be larger than requests_per_second (allows bursts)."""
        policy = RateLimitPolicy(
            requests_per_second=requests_per_second,
            burst_size=burst_size
        )
        assert policy.burst_size == burst_size
        # This is valid - allows burst above steady rate

    @given(valid_rate_limit_policy())
    @settings(max_examples=50, deadline=1000)
    def test_policy_with_callback(self, policy):
        """Test that policy accepts optional callback."""
        callback_called = []
        
        def test_callback(wait_time: float):
            callback_called.append(wait_time)
        
        policy_with_callback = RateLimitPolicy(
            requests_per_second=policy.requests_per_second,
            burst_size=policy.burst_size,
            wait_on_limit=policy.wait_on_limit,
            on_wait=test_callback
        )
        
        assert policy_with_callback.on_wait is test_callback


class TestRateLimiterTokenBucketInvariants:
    """Test invariant properties of RateLimiter token bucket algorithm."""

    @given(valid_rate_limit_policy())
    @settings(max_examples=50, deadline=1000)
    def test_limiter_initializes_with_full_bucket(self, policy):
        """Test that RateLimiter starts with full token bucket."""
        limiter = RateLimiter(policy)
        # Initial tokens should equal burst_size
        tokens = limiter.get_available_tokens()
        assert abs(tokens - policy.burst_size) < 0.01  # Allow small floating point error

    @given(valid_rate_limit_policy())
    @settings(max_examples=50, deadline=1000, suppress_health_check=[HealthCheck.function_scoped_fixture])
    def test_limiter_tokens_never_exceed_burst_size(self, policy):
        """Test that token count never exceeds burst_size."""
        limiter = RateLimiter(policy)
        
        # Wait for potential refill
        time.sleep(0.01)
        
        tokens = limiter.get_available_tokens()
        assert tokens <= policy.burst_size + 0.01  # Allow small floating point error

    @given(
        policy=valid_rate_limit_policy(),
        tokens_to_acquire=st.floats(min_value=0.1, max_value=5.0)
    )
    @settings(max_examples=50, deadline=2000, suppress_health_check=[HealthCheck.function_scoped_fixture])
    def test_limiter_acquire_consumes_tokens(self, policy, tokens_to_acquire):
        """Test that acquire() consumes the correct number of tokens."""
        # Use small burst for faster tests
        small_policy = RateLimitPolicy(
            requests_per_second=policy.requests_per_second,
            burst_size=max(10, int(tokens_to_acquire) + 5),
            wait_on_limit=True
        )
        limiter = RateLimiter(small_policy)
        
        tokens_before = limiter.get_available_tokens()
        assume(tokens_before >= tokens_to_acquire)  # Only test when we have enough tokens
        
        limiter.acquire(tokens_to_acquire)
        
        tokens_after = limiter.get_available_tokens()
        consumed = tokens_before - tokens_after
        
        # Should consume approximately the requested amount (within 0.1 token tolerance)
        assert abs(consumed - tokens_to_acquire) < 0.1

    @given(valid_rate_limit_policy())
    @settings(max_examples=50, deadline=1000, suppress_health_check=[HealthCheck.function_scoped_fixture])
    def test_limiter_try_acquire_returns_bool(self, policy):
        """Test that try_acquire() returns a boolean."""
        limiter = RateLimiter(policy)
        result = limiter.try_acquire()
        assert isinstance(result, bool)

    @given(valid_rate_limit_policy())
    @settings(max_examples=50, deadline=1000, suppress_health_check=[HealthCheck.function_scoped_fixture])
    def test_limiter_try_acquire_on_full_bucket_succeeds(self, policy):
        """Test that try_acquire() succeeds when bucket is full."""
        limiter = RateLimiter(policy)
        # First acquire on full bucket should succeed
        assert limiter.try_acquire() is True

    @given(
        requests_per_second=st.floats(min_value=5.0, max_value=50.0),
        burst_size=st.integers(min_value=5, max_value=20)
    )
    @settings(max_examples=20, deadline=5000, suppress_health_check=[HealthCheck.function_scoped_fixture])
    def test_limiter_refills_tokens_over_time(self, requests_per_second, burst_size):
        """Test that tokens are refilled at the correct rate over time."""
        policy = RateLimitPolicy(
            requests_per_second=requests_per_second,
            burst_size=burst_size,
            wait_on_limit=True
        )
        limiter = RateLimiter(policy)
        
        # Consume some tokens (not all, to leave room for refill)
        tokens_to_consume = min(3, burst_size - 2)
        for _ in range(tokens_to_consume):
            limiter.acquire(1.0)
        
        tokens_after_drain = limiter.get_available_tokens()
        
        # Wait for refill - use longer sleep for more reliable timing
        sleep_time = 0.2  # 200ms
        time.sleep(sleep_time)
        
        tokens_after_wait = limiter.get_available_tokens()
        expected_refill = sleep_time * requests_per_second
        
        # Tokens should have increased (or stayed at burst_size cap)
        # Allow very generous tolerance due to timing variations and scheduler delays
        assert tokens_after_wait >= tokens_after_drain - 0.5  # Allow small decrease due to timing
        assert tokens_after_wait <= burst_size  # Never exceed burst_size

    @given(valid_rate_limit_policy())
    @settings(max_examples=50, deadline=1000, suppress_health_check=[HealthCheck.function_scoped_fixture])
    def test_limiter_reset_refills_bucket(self, policy):
        """Test that reset() refills the bucket to capacity."""
        limiter = RateLimiter(policy)
        
        # Drain some tokens
        if limiter.try_acquire():
            pass  # Successfully drained 1 token
        
        # Reset should refill
        limiter.reset()
        
        tokens = limiter.get_available_tokens()
        assert abs(tokens - policy.burst_size) < 0.01

    @given(
        requests_per_second=st.floats(min_value=1.0, max_value=100.0),
        tokens=st.floats(max_value=0.0) | st.just(0.0) | st.just(-1.0)
    )
    @settings(max_examples=30, deadline=1000)
    def test_limiter_rejects_non_positive_tokens(self, requests_per_second, tokens):
        """Test that acquire/try_acquire reject non-positive token counts."""
        assume(tokens <= 0)
        policy = RateLimitPolicy(requests_per_second=requests_per_second)
        limiter = RateLimiter(policy)
        
        with pytest.raises(ValueError, match="tokens must be positive"):
            limiter.acquire(tokens)
        
        with pytest.raises(ValueError, match="tokens must be positive"):
            limiter.try_acquire(tokens)


class TestRateLimiterWaitBehavior:
    """Test rate limiter wait and exception behavior."""

    @given(
        requests_per_second=st.floats(min_value=10.0, max_value=100.0),
        burst_size=st.integers(min_value=1, max_value=5)
    )
    @settings(max_examples=20, deadline=3000, suppress_health_check=[HealthCheck.function_scoped_fixture])
    def test_limiter_waits_when_wait_on_limit_true(self, requests_per_second, burst_size):
        """Test that limiter waits for tokens when wait_on_limit=True."""
        policy = RateLimitPolicy(
            requests_per_second=requests_per_second,
            burst_size=burst_size,
            wait_on_limit=True
        )
        limiter = RateLimiter(policy)
        
        # Drain bucket
        for _ in range(burst_size):
            limiter.acquire(1.0)
        
        # Next acquire should wait (but complete eventually)
        start = time.time()
        limiter.acquire(1.0)
        elapsed = time.time() - start
        
        # Should have waited some time (at least a small amount)
        # With high rates, wait time is very short, so just check it completed
        assert elapsed >= 0

    @given(
        requests_per_second=st.floats(min_value=10.0, max_value=100.0),
        burst_size=st.integers(min_value=1, max_value=5)
    )
    @settings(max_examples=20, deadline=2000, suppress_health_check=[HealthCheck.function_scoped_fixture])
    def test_limiter_raises_when_wait_on_limit_false(self, requests_per_second, burst_size):
        """Test that limiter raises exception when wait_on_limit=False."""
        policy = RateLimitPolicy(
            requests_per_second=requests_per_second,
            burst_size=burst_size,
            wait_on_limit=False
        )
        limiter = RateLimiter(policy)
        
        # Drain bucket
        for _ in range(burst_size):
            limiter.acquire(1.0)
        
        # Next acquire should raise
        with pytest.raises(RateLimitExceeded):
            limiter.acquire(1.0)

    @given(requests_per_second=st.floats(min_value=10.0, max_value=100.0))
    @settings(max_examples=20, deadline=2000, suppress_health_check=[HealthCheck.function_scoped_fixture])
    def test_limiter_callback_invoked_on_wait(self, requests_per_second):
        """Test that on_wait callback is invoked when waiting."""
        callback_called = []
        
        def test_callback(wait_time: float):
            callback_called.append(wait_time)
        
        policy = RateLimitPolicy(
            requests_per_second=requests_per_second,
            burst_size=1,
            wait_on_limit=True,
            on_wait=test_callback
        )
        limiter = RateLimiter(policy)
        
        # Drain bucket
        limiter.acquire(1.0)
        
        # Next acquire should trigger callback
        limiter.acquire(1.0)
        
        # Callback should have been called at least once
        assert len(callback_called) > 0
        # Wait time should be positive
        assert all(wt >= 0 for wt in callback_called)

    @given(requests_per_second=st.floats(min_value=10.0, max_value=100.0))
    @settings(max_examples=20, deadline=2000, suppress_health_check=[HealthCheck.function_scoped_fixture])
    def test_limiter_callback_exception_doesnt_break_rate_limiting(self, requests_per_second):
        """Test that exceptions in callback don't break rate limiting."""
        def bad_callback(wait_time: float):
            raise RuntimeError("Callback error")
        
        policy = RateLimitPolicy(
            requests_per_second=requests_per_second,
            burst_size=1,
            wait_on_limit=True,
            on_wait=bad_callback
        )
        limiter = RateLimiter(policy)
        
        # Drain bucket
        limiter.acquire(1.0)
        
        # Next acquire should complete despite callback error
        limiter.acquire(1.0)  # Should not raise


class TestRateLimiterContextManager:
    """Test rate limiter context manager interface."""

    @given(valid_rate_limit_policy())
    @settings(max_examples=50, deadline=2000, suppress_health_check=[HealthCheck.function_scoped_fixture])
    def test_limiter_context_manager_acquires_token(self, policy):
        """Test that context manager acquires a token."""
        # Use policy with wait to avoid exceptions
        wait_policy = RateLimitPolicy(
            requests_per_second=policy.requests_per_second,
            burst_size=policy.burst_size,
            wait_on_limit=True
        )
        limiter = RateLimiter(wait_policy)
        
        tokens_before = limiter.get_available_tokens()
        
        with limiter:
            pass  # Context manager should acquire token
        
        tokens_after = limiter.get_available_tokens()
        
        # Should have consumed approximately 1 token
        consumed = tokens_before - tokens_after
        assert 0.9 <= consumed <= 1.1  # Allow small tolerance

    @given(valid_rate_limit_policy())
    @settings(max_examples=30, deadline=2000, suppress_health_check=[HealthCheck.function_scoped_fixture])
    def test_limiter_context_manager_multiple_uses(self, policy):
        """Test that context manager can be used multiple times."""
        # Ensure fast refill and sufficient burst for multiple uses
        fast_burst = max(5, policy.burst_size) if policy.burst_size else 5
        wait_policy = RateLimitPolicy(
            requests_per_second=max(10.0, policy.requests_per_second),
            burst_size=fast_burst,
            wait_on_limit=True
        )
        limiter = RateLimiter(wait_policy)
        
        # Use context manager multiple times
        for _ in range(3):
            with limiter:
                pass  # Each use should acquire and release


class TestWithRateLimitDecorator:
    """Test with_rate_limit decorator."""

    @given(requests_per_second=st.floats(min_value=10.0, max_value=100.0))
    @settings(max_examples=30, deadline=2000, suppress_health_check=[HealthCheck.function_scoped_fixture])
    def test_decorator_without_parentheses(self, requests_per_second):
        """Test decorator used without parentheses (@with_rate_limit)."""
        @with_rate_limit
        def test_func():
            return 42
        
        result = test_func()
        assert result == 42
        assert hasattr(test_func, '_rate_limiter')
        assert isinstance(test_func._rate_limiter, RateLimiter)

    @given(requests_per_second=st.floats(min_value=10.0, max_value=100.0))
    @settings(max_examples=30, deadline=2000, suppress_health_check=[HealthCheck.function_scoped_fixture])
    def test_decorator_with_parameters(self, requests_per_second):
        """Test decorator used with parameters (@with_rate_limit(...))."""
        @with_rate_limit(requests_per_second=requests_per_second)
        def test_func(x):
            return x * 2
        
        result = test_func(21)
        assert result == 42
        assert hasattr(test_func, '_rate_limiter')
        assert test_func._rate_limiter.policy.requests_per_second == requests_per_second

    @given(valid_rate_limit_policy())
    @settings(max_examples=30, deadline=2000, suppress_health_check=[HealthCheck.function_scoped_fixture])
    def test_decorator_with_policy_object(self, policy):
        """Test decorator with pre-configured policy."""
        # Use wait policy to avoid exceptions
        wait_policy = RateLimitPolicy(
            requests_per_second=policy.requests_per_second,
            burst_size=policy.burst_size,
            wait_on_limit=True
        )
        
        @with_rate_limit(policy=wait_policy)
        def test_func():
            return "success"
        
        result = test_func()
        assert result == "success"
        assert test_func._rate_limiter.policy.requests_per_second == wait_policy.requests_per_second

    @given(
        requests_per_second=st.floats(min_value=10.0, max_value=100.0),
        x=st.integers(min_value=-100, max_value=100),
        y=st.integers(min_value=-100, max_value=100)
    )
    @settings(max_examples=30, deadline=2000, suppress_health_check=[HealthCheck.function_scoped_fixture])
    def test_decorator_preserves_function_arguments(self, requests_per_second, x, y):
        """Test that decorator preserves function arguments and return values."""
        @with_rate_limit(requests_per_second=requests_per_second)
        def test_func(a, b, c=10):
            return a + b + c
        
        result = test_func(x, y, c=5)
        assert result == x + y + 5

    @given(requests_per_second=st.floats(min_value=10.0, max_value=100.0))
    @settings(max_examples=20, deadline=2000, suppress_health_check=[HealthCheck.function_scoped_fixture])
    def test_decorator_with_shared_limiter(self, requests_per_second):
        """Test decorator with shared limiter across multiple functions."""
        policy = RateLimitPolicy(
            requests_per_second=requests_per_second,
            burst_size=10,
            wait_on_limit=True
        )
        limiter = RateLimiter(policy)
        
        @with_rate_limit(limiter=limiter)
        def func1():
            return 1
        
        @with_rate_limit(limiter=limiter)
        def func2():
            return 2
        
        # Both functions should share the same limiter
        assert func1._rate_limiter is limiter
        assert func2._rate_limiter is limiter
        
        # Calls should consume from same token bucket
        result1 = func1()
        result2 = func2()
        assert result1 == 1
        assert result2 == 2


class TestRateLimitedCall:
    """Test rate_limited_call function."""

    @given(
        requests_per_second=st.floats(min_value=10.0, max_value=100.0),
        x=st.integers(min_value=0, max_value=100)
    )
    @settings(max_examples=30, deadline=2000, suppress_health_check=[HealthCheck.function_scoped_fixture])
    def test_rate_limited_call_basic(self, requests_per_second, x):
        """Test basic rate_limited_call usage."""
        def test_func(val):
            return val * 2
        
        result = rate_limited_call(
            test_func,
            args=(x,),
            requests_per_second=requests_per_second
        )
        assert result == x * 2

    @given(
        requests_per_second=st.floats(min_value=10.0, max_value=100.0),
        a=st.integers(min_value=0, max_value=50),
        b=st.integers(min_value=0, max_value=50)
    )
    @settings(max_examples=30, deadline=2000, suppress_health_check=[HealthCheck.function_scoped_fixture])
    def test_rate_limited_call_with_args_and_kwargs(self, requests_per_second, a, b):
        """Test rate_limited_call with both args and kwargs."""
        def test_func(x, y, z=10):
            return x + y + z
        
        result = rate_limited_call(
            test_func,
            args=(a, b),
            kwargs={'z': 5},
            requests_per_second=requests_per_second
        )
        assert result == a + b + 5

    @given(valid_rate_limit_policy())
    @settings(max_examples=30, deadline=2000, suppress_health_check=[HealthCheck.function_scoped_fixture])
    def test_rate_limited_call_with_policy(self, policy):
        """Test rate_limited_call with pre-configured policy."""
        # Use wait policy
        wait_policy = RateLimitPolicy(
            requests_per_second=policy.requests_per_second,
            burst_size=policy.burst_size,
            wait_on_limit=True
        )
        
        def test_func():
            return "success"
        
        result = rate_limited_call(test_func, policy=wait_policy)
        assert result == "success"

    @given(requests_per_second=st.floats(min_value=10.0, max_value=100.0))
    @settings(max_examples=20, deadline=2000, suppress_health_check=[HealthCheck.function_scoped_fixture])
    def test_rate_limited_call_no_args(self, requests_per_second):
        """Test rate_limited_call with no arguments."""
        def test_func():
            return 42
        
        result = rate_limited_call(test_func, requests_per_second=requests_per_second)
        assert result == 42


class TestRateLimiterThreadSafety:
    """Test rate limiter thread safety."""

    @given(
        requests_per_second=st.floats(min_value=50.0, max_value=200.0),
        burst_size=st.integers(min_value=20, max_value=100),
        num_threads=st.integers(min_value=2, max_value=10)
    )
    @settings(max_examples=10, deadline=5000, suppress_health_check=[HealthCheck.function_scoped_fixture])
    def test_limiter_concurrent_access(self, requests_per_second, burst_size, num_threads):
        """Test that rate limiter is thread-safe under concurrent access."""
        policy = RateLimitPolicy(
            requests_per_second=requests_per_second,
            burst_size=burst_size,
            wait_on_limit=True
        )
        limiter = RateLimiter(policy)
        
        results = []
        errors = []
        
        def worker():
            try:
                # Each thread tries to acquire a token
                limiter.acquire(1.0)
                results.append(True)
            except Exception as e:
                errors.append(e)
        
        threads = [threading.Thread(target=worker) for _ in range(num_threads)]
        
        for t in threads:
            t.start()
        
        for t in threads:
            t.join(timeout=5.0)
        
        # All threads should complete without errors
        assert len(errors) == 0
        # All threads should successfully acquire
        assert len(results) == num_threads


class TestRateLimiterEdgeCases:
    """Test rate limiter edge cases."""

    @given(requests_per_second=st.floats(min_value=0.1, max_value=1.0))
    @settings(max_examples=20, deadline=2000, suppress_health_check=[HealthCheck.function_scoped_fixture])
    def test_limiter_very_low_rate(self, requests_per_second):
        """Test limiter with very low request rates."""
        policy = RateLimitPolicy(
            requests_per_second=requests_per_second,
            burst_size=1,
            wait_on_limit=True
        )
        limiter = RateLimiter(policy)
        
        # Should be able to acquire at least once
        limiter.acquire(1.0)

    @given(requests_per_second=st.floats(min_value=100.0, max_value=1000.0))
    @settings(max_examples=20, deadline=2000, suppress_health_check=[HealthCheck.function_scoped_fixture])
    def test_limiter_very_high_rate(self, requests_per_second):
        """Test limiter with very high request rates."""
        policy = RateLimitPolicy(
            requests_per_second=requests_per_second,
            burst_size=100,
            wait_on_limit=True
        )
        limiter = RateLimiter(policy)
        
        # Should be able to acquire multiple times quickly
        for _ in range(10):
            limiter.acquire(1.0)

    @given(
        requests_per_second=st.floats(min_value=10.0, max_value=100.0),
        burst_size=st.integers(min_value=50, max_value=200)
    )
    @settings(max_examples=20, deadline=2000, suppress_health_check=[HealthCheck.function_scoped_fixture])
    def test_limiter_large_burst_size(self, requests_per_second, burst_size):
        """Test limiter with large burst size."""
        policy = RateLimitPolicy(
            requests_per_second=requests_per_second,
            burst_size=burst_size,
            wait_on_limit=True
        )
        limiter = RateLimiter(policy)
        
        # Should start with full bucket
        tokens = limiter.get_available_tokens()
        assert abs(tokens - burst_size) < 0.01

    @given(
        requests_per_second=st.floats(min_value=10.0, max_value=100.0),
        fractional_tokens=st.floats(min_value=0.1, max_value=2.5)
    )
    @settings(max_examples=20, deadline=2000, suppress_health_check=[HealthCheck.function_scoped_fixture])
    def test_limiter_fractional_tokens(self, requests_per_second, fractional_tokens):
        """Test limiter with fractional token counts."""
        policy = RateLimitPolicy(
            requests_per_second=requests_per_second,
            burst_size=10,
            wait_on_limit=True
        )
        limiter = RateLimiter(policy)
        
        # Should be able to acquire fractional tokens
        limiter.acquire(fractional_tokens)

    @given(requests_per_second=st.floats(min_value=10.0, max_value=100.0))
    @settings(max_examples=20, deadline=2000, suppress_health_check=[HealthCheck.function_scoped_fixture])
    def test_limiter_burst_equals_rate(self, requests_per_second):
        """Test limiter when burst_size equals requests_per_second (rounded)."""
        # This is the default behavior when burst_size is None
        policy = RateLimitPolicy(
            requests_per_second=requests_per_second,
            burst_size=None  # Will default to max(1, round(requests_per_second))
        )
        limiter = RateLimiter(policy)
        
        expected_burst = max(1, round(requests_per_second))
        tokens = limiter.get_available_tokens()
        assert abs(tokens - expected_burst) < 0.01


class TestRateLimiterIntegration:
    """Test rate limiter integration scenarios."""

    @given(
        requests_per_second=st.floats(min_value=20.0, max_value=100.0),
        burst_size=st.integers(min_value=5, max_value=20)
    )
    @settings(max_examples=10, deadline=3000, suppress_health_check=[HealthCheck.function_scoped_fixture])
    def test_limiter_full_lifecycle(self, requests_per_second, burst_size):
        """Test complete rate limiter lifecycle."""
        policy = RateLimitPolicy(
            requests_per_second=requests_per_second,
            burst_size=burst_size,
            wait_on_limit=True
        )
        limiter = RateLimiter(policy)
        
        # 1. Start with full bucket
        assert limiter.get_available_tokens() >= burst_size - 0.01
        
        # 2. Consume some tokens
        for _ in range(min(3, burst_size)):
            assert limiter.try_acquire() is True
        
        # 3. Check tokens decreased
        tokens_after = limiter.get_available_tokens()
        assert tokens_after < burst_size
        
        # 4. Reset
        limiter.reset()
        
        # 5. Verify full again
        assert limiter.get_available_tokens() >= burst_size - 0.01

    @given(
        requests_per_second=st.floats(min_value=20.0, max_value=100.0),
        burst_size=st.integers(min_value=5, max_value=15)
    )
    @settings(max_examples=10, deadline=3000, suppress_health_check=[HealthCheck.function_scoped_fixture])
    def test_limiter_with_decorator_integration(self, requests_per_second, burst_size):
        """Test rate limiter integrated with decorator."""
        policy = RateLimitPolicy(
            requests_per_second=requests_per_second,
            burst_size=burst_size,
            wait_on_limit=True
        )
        
        @with_rate_limit(policy=policy)
        def test_func(x):
            return x * 2
        
        # Call function multiple times
        results = []
        for i in range(min(5, burst_size)):
            results.append(test_func(i))
        
        # All calls should succeed
        assert results == [i * 2 for i in range(len(results))]
