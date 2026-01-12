"""
Property-based tests for the retry module using Hypothesis.

These tests automatically generate edge cases and verify invariant properties
of the retry logic across a wide range of inputs and configurations.
"""

import time
import threading
from typing import Any

import pytest
from hypothesis import given, settings, strategies as st, HealthCheck

from amorsize.retry import (
    RetryPolicy,
    RetryExhaustedError,
    with_retry,
    retry_call,
    create_batch_retry_wrapper,
)


# Custom strategies for generating test data
@st.composite
def valid_retry_policy(draw):
    """Generate valid RetryPolicy configurations."""
    max_retries = draw(st.integers(min_value=0, max_value=10))
    initial_delay = draw(st.floats(min_value=0.001, max_value=5.0))
    max_delay = draw(st.floats(min_value=initial_delay, max_value=60.0))
    exponential_base = draw(st.floats(min_value=1.0, max_value=3.0))
    jitter = draw(st.booleans())
    
    return RetryPolicy(
        max_retries=max_retries,
        initial_delay=initial_delay,
        max_delay=max_delay,
        exponential_base=exponential_base,
        jitter=jitter
    )


@st.composite
def exception_types_strategy(draw):
    """Generate valid exception type tuples."""
    available_types = [ValueError, TypeError, RuntimeError, KeyError, AttributeError]
    size = draw(st.integers(min_value=1, max_value=3))
    selected = draw(st.lists(st.sampled_from(available_types), min_size=size, max_size=size, unique=True))
    return tuple(selected)


class TestRetryPolicyInvariants:
    """Test invariant properties of RetryPolicy."""

    @given(
        max_retries=st.integers(min_value=0, max_value=100),
        initial_delay=st.floats(min_value=0.001, max_value=10.0),
        exponential_base=st.floats(min_value=1.0, max_value=5.0)
    )
    @settings(max_examples=100, deadline=1000)
    def test_policy_initialization_valid_params(self, max_retries, initial_delay, exponential_base):
        """Test that valid parameters create a policy without errors."""
        max_delay = initial_delay * 10  # Ensure max_delay >= initial_delay
        
        policy = RetryPolicy(
            max_retries=max_retries,
            initial_delay=initial_delay,
            max_delay=max_delay,
            exponential_base=exponential_base
        )
        
        assert policy.max_retries == max_retries
        assert policy.initial_delay == initial_delay
        assert policy.max_delay == max_delay
        assert policy.exponential_base == exponential_base
        assert policy.jitter is True  # Default
        assert policy.retry_on_exceptions is None
        assert policy.on_retry is None

    @given(max_retries=st.integers(max_value=-2))
    @settings(max_examples=50, deadline=1000)
    def test_policy_rejects_invalid_max_retries(self, max_retries):
        """Test that max_retries < -1 raises ValueError."""
        with pytest.raises(ValueError, match="max_retries must be >= -1"):
            RetryPolicy(max_retries=max_retries)

    @given(initial_delay=st.floats(max_value=0.0, exclude_max=True) | st.just(0.0))
    @settings(max_examples=50, deadline=1000)
    def test_policy_rejects_non_positive_initial_delay(self, initial_delay):
        """Test that non-positive initial_delay raises ValueError."""
        with pytest.raises(ValueError, match="initial_delay must be positive"):
            RetryPolicy(initial_delay=initial_delay)

    @given(
        initial_delay=st.floats(min_value=1.0, max_value=10.0),
        max_delay=st.floats(min_value=0.001, max_value=0.999)
    )
    @settings(max_examples=50, deadline=1000)
    def test_policy_rejects_max_delay_less_than_initial(self, initial_delay, max_delay):
        """Test that max_delay < initial_delay raises ValueError."""
        with pytest.raises(ValueError, match="max_delay must be >= initial_delay"):
            RetryPolicy(initial_delay=initial_delay, max_delay=max_delay)

    @given(exponential_base=st.floats(max_value=0.999, exclude_max=True))
    @settings(max_examples=50, deadline=1000)
    def test_policy_rejects_exponential_base_less_than_one(self, exponential_base):
        """Test that exponential_base < 1.0 raises ValueError."""
        with pytest.raises(ValueError, match="exponential_base must be >= 1.0"):
            RetryPolicy(exponential_base=exponential_base)

    @given(exception_types=exception_types_strategy())
    @settings(max_examples=50, deadline=1000)
    def test_policy_accepts_retry_on_exceptions(self, exception_types):
        """Test that retry_on_exceptions can be set."""
        policy = RetryPolicy(retry_on_exceptions=exception_types)
        assert policy.retry_on_exceptions == exception_types

    @given(policy=valid_retry_policy())
    @settings(max_examples=100, deadline=1000)
    def test_policy_has_valid_defaults(self, policy):
        """Test that all policy parameters are valid."""
        assert policy.max_retries >= -1
        assert policy.initial_delay > 0
        assert policy.max_delay >= policy.initial_delay
        assert policy.exponential_base >= 1.0
        assert isinstance(policy.jitter, bool)


class TestExponentialBackoffCalculation:
    """Test exponential backoff delay calculation."""

    @given(
        policy=valid_retry_policy(),
        attempt=st.integers(min_value=1, max_value=20)
    )
    @settings(max_examples=100, deadline=1000)
    def test_delay_is_non_negative(self, policy, attempt):
        """Test that calculated delay is always non-negative."""
        delay = policy.calculate_delay(attempt)
        assert delay >= 0

    @given(
        initial_delay=st.floats(min_value=0.1, max_value=1.0),
        max_delay=st.floats(min_value=10.0, max_value=60.0),
        attempt=st.integers(min_value=1, max_value=10)
    )
    @settings(max_examples=100, deadline=1000)
    def test_delay_never_exceeds_max_delay(self, initial_delay, max_delay, attempt):
        """Test that delay is always capped at max_delay."""
        policy = RetryPolicy(
            initial_delay=initial_delay,
            max_delay=max_delay,
            exponential_base=2.0,
            jitter=False  # Disable jitter for deterministic testing
        )
        
        delay = policy.calculate_delay(attempt)
        assert delay <= max_delay

    @given(
        initial_delay=st.floats(min_value=0.1, max_value=1.0),
        exponential_base=st.floats(min_value=1.0, max_value=3.0)
    )
    @settings(max_examples=100, deadline=1000)
    def test_delay_increases_with_attempt(self, initial_delay, exponential_base):
        """Test that delay increases (or stays same) with higher attempts."""
        policy = RetryPolicy(
            initial_delay=initial_delay,
            max_delay=1000.0,  # High max to avoid capping
            exponential_base=exponential_base,
            jitter=False  # Disable jitter for deterministic testing
        )
        
        delay1 = policy.calculate_delay(1)
        delay2 = policy.calculate_delay(2)
        delay3 = policy.calculate_delay(3)
        
        assert delay2 >= delay1
        assert delay3 >= delay2

    @given(
        initial_delay=st.floats(min_value=0.1, max_value=1.0),
        exponential_base=st.floats(min_value=1.0, max_value=3.0)
    )
    @settings(max_examples=100, deadline=1000)
    def test_first_delay_approximates_initial_delay(self, initial_delay, exponential_base):
        """Test that first retry delay is close to initial_delay."""
        policy = RetryPolicy(
            initial_delay=initial_delay,
            exponential_base=exponential_base,
            jitter=False  # Disable jitter for deterministic testing
        )
        
        delay = policy.calculate_delay(1)
        # First delay should be exactly initial_delay when jitter is disabled
        assert abs(delay - initial_delay) < 1e-6

    @given(
        policy=valid_retry_policy(),
        attempt=st.integers(min_value=1, max_value=10)
    )
    @settings(max_examples=100, deadline=1000)
    def test_jitter_adds_variation(self, policy, attempt):
        """Test that jitter adds variation to delays."""
        if not policy.jitter:
            return  # Skip if jitter is disabled
        
        # Calculate multiple delays for the same attempt
        delays = [policy.calculate_delay(attempt) for _ in range(5)]
        
        # With jitter, delays should vary (not all identical)
        # Note: There's a small chance all delays are identical by random chance
        # but it's extremely unlikely with 5 samples
        unique_delays = len(set(delays))
        # Allow for some identical values but expect mostly different ones
        assert unique_delays >= 3 or len(delays) < 3

    @given(
        initial_delay=st.floats(min_value=0.1, max_value=1.0),
        exponential_base=st.just(1.0)  # No exponential growth
    )
    @settings(max_examples=50, deadline=1000)
    def test_exponential_base_one_gives_constant_delay(self, initial_delay, exponential_base):
        """Test that exponential_base=1.0 gives constant delay (no growth)."""
        policy = RetryPolicy(
            initial_delay=initial_delay,
            max_delay=1000.0,
            exponential_base=exponential_base,
            jitter=False
        )
        
        delay1 = policy.calculate_delay(1)
        delay2 = policy.calculate_delay(2)
        delay3 = policy.calculate_delay(3)
        
        assert abs(delay1 - initial_delay) < 1e-6
        assert abs(delay2 - initial_delay) < 1e-6
        assert abs(delay3 - initial_delay) < 1e-6


class TestRetryShouldRetryLogic:
    """Test the retry decision logic."""

    @given(
        max_retries=st.integers(min_value=0, max_value=10),
        attempt=st.integers(min_value=1, max_value=20)
    )
    @settings(max_examples=100, deadline=1000)
    def test_should_retry_respects_max_retries(self, max_retries, attempt):
        """Test that should_retry returns False when max_retries exceeded."""
        policy = RetryPolicy(max_retries=max_retries)
        result = policy.should_retry(ValueError("test"), attempt)
        
        if attempt <= max_retries:
            assert result is True
        else:
            assert result is False

    @given(attempt=st.integers(min_value=1, max_value=100))
    @settings(max_examples=50, deadline=1000)
    def test_should_retry_infinite_retries(self, attempt):
        """Test that max_retries=-1 allows infinite retries."""
        policy = RetryPolicy(max_retries=-1)
        result = policy.should_retry(ValueError("test"), attempt)
        assert result is True

    @given(
        exception_types=exception_types_strategy(),
        max_retries=st.integers(min_value=1, max_value=10)
    )
    @settings(max_examples=50, deadline=1000)
    def test_should_retry_filters_by_exception_type(self, exception_types, max_retries):
        """Test that should_retry filters by exception type."""
        policy = RetryPolicy(
            max_retries=max_retries,
            retry_on_exceptions=exception_types
        )
        
        # Test with exception in the list
        matching_exception = exception_types[0]("test")
        assert policy.should_retry(matching_exception, 1) is True
        
        # Test with exception not in the list
        if ConnectionError not in exception_types:
            non_matching_exception = ConnectionError("test")
            assert policy.should_retry(non_matching_exception, 1) is False

    @given(max_retries=st.integers(min_value=1, max_value=10))
    @settings(max_examples=50, deadline=1000)
    def test_should_retry_accepts_all_exceptions_when_none(self, max_retries):
        """Test that retry_on_exceptions=None retries on all exceptions."""
        policy = RetryPolicy(max_retries=max_retries, retry_on_exceptions=None)
        
        # Test various exception types
        exceptions = [
            ValueError("test"),
            TypeError("test"),
            RuntimeError("test"),
            KeyError("test")
        ]
        
        for exc in exceptions:
            assert policy.should_retry(exc, 1) is True


class TestWithRetryDecorator:
    """Test the with_retry decorator."""

    @given(failures_before_success=st.integers(min_value=0, max_value=5))
    @settings(max_examples=50, deadline=2000)
    def test_decorator_without_parens_works(self, failures_before_success):
        """Test that @with_retry (without parentheses) works."""
        call_count = [0]
        
        @with_retry
        def func():
            call_count[0] += 1
            if call_count[0] <= failures_before_success:
                raise ValueError("retry me")
            return "success"
        
        # Default policy has max_retries=3, so if failures_before_success > 3, it should fail
        if failures_before_success > 3:
            with pytest.raises(ValueError):
                func()
            assert call_count[0] == 4  # 1 initial + 3 retries
        else:
            result = func()
            assert result == "success"
            assert call_count[0] == failures_before_success + 1

    @given(
        max_retries=st.integers(min_value=1, max_value=5),
        initial_delay=st.floats(min_value=0.001, max_value=0.01)
    )
    @settings(max_examples=30, deadline=2000, suppress_health_check=[HealthCheck.function_scoped_fixture])
    def test_decorator_with_params_works(self, max_retries, initial_delay):
        """Test that @with_retry(params) works."""
        call_count = [0]
        
        @with_retry(max_retries=max_retries, initial_delay=initial_delay, jitter=False)
        def func():
            call_count[0] += 1
            if call_count[0] <= max_retries:
                raise ValueError("retry me")
            return "success"
        
        result = func()
        assert result == "success"
        assert call_count[0] == max_retries + 1

    @given(policy=valid_retry_policy())
    @settings(max_examples=30, deadline=2000)
    def test_decorator_with_policy_works(self, policy):
        """Test that @with_retry(policy=policy) works."""
        # Adjust policy to have short delays for fast testing
        policy.initial_delay = 0.001
        policy.max_delay = 0.01
        
        call_count = [0]
        # Fail more times than allowed retries to ensure we hit the limit
        failures_before_success = (policy.max_retries if policy.max_retries >= 0 else 2) + 1
        
        @with_retry(policy=policy)
        def func():
            call_count[0] += 1
            if call_count[0] <= failures_before_success:
                raise ValueError("retry me")
            return "success"
        
        if policy.max_retries == 0:
            # With 0 retries, function tries once and fails (1 attempt, 0 retries)
            with pytest.raises(ValueError):
                func()
            assert call_count[0] == 1
        else:
            # Will exhaust retries and fail
            with pytest.raises(ValueError):
                func()
            # Should try: 1 initial + max_retries
            assert call_count[0] == 1 + policy.max_retries

    @given(
        max_retries=st.integers(min_value=1, max_value=3),
        arg1=st.integers(min_value=1, max_value=10),
        arg2=st.text(min_size=1, max_size=10)
    )
    @settings(max_examples=30, deadline=2000)
    def test_decorator_preserves_function_args(self, max_retries, arg1, arg2):
        """Test that decorated function correctly receives arguments."""
        call_count = [0]
        
        @with_retry(max_retries=max_retries, initial_delay=0.001)
        def func(x, y):
            call_count[0] += 1
            if call_count[0] <= max_retries:
                raise ValueError("retry me")
            return x, y
        
        result = func(arg1, arg2)
        assert result == (arg1, arg2)


class TestRetryCall:
    """Test the retry_call function."""

    @given(
        max_retries=st.integers(min_value=1, max_value=5),
        initial_delay=st.floats(min_value=0.001, max_value=0.01)
    )
    @settings(max_examples=30, deadline=2000)
    def test_retry_call_basic_usage(self, max_retries, initial_delay):
        """Test that retry_call works with basic parameters."""
        call_count = [0]
        
        def func():
            call_count[0] += 1
            if call_count[0] <= max_retries:
                raise ValueError("retry me")
            return "success"
        
        result = retry_call(func, max_retries=max_retries, initial_delay=initial_delay, jitter=False)
        assert result == "success"
        assert call_count[0] == max_retries + 1

    @given(
        arg1=st.integers(min_value=1, max_value=10),
        arg2=st.integers(min_value=1, max_value=10)
    )
    @settings(max_examples=50, deadline=2000)
    def test_retry_call_with_args(self, arg1, arg2):
        """Test that retry_call correctly passes args."""
        def func(x, y):
            return x + y
        
        result = retry_call(func, args=(arg1, arg2), max_retries=0)
        assert result == arg1 + arg2

    @given(
        kwarg1=st.integers(min_value=1, max_value=10),
        kwarg2=st.integers(min_value=1, max_value=10)
    )
    @settings(max_examples=50, deadline=2000)
    def test_retry_call_with_kwargs(self, kwarg1, kwarg2):
        """Test that retry_call correctly passes kwargs."""
        def func(x=0, y=0):
            return x * y
        
        result = retry_call(func, kwargs={"x": kwarg1, "y": kwarg2}, max_retries=0)
        assert result == kwarg1 * kwarg2

    @given(policy=valid_retry_policy())
    @settings(max_examples=30, deadline=2000)
    def test_retry_call_with_policy(self, policy):
        """Test that retry_call works with a pre-configured policy."""
        # Adjust policy for fast testing
        policy.initial_delay = 0.001
        policy.max_delay = 0.01
        
        call_count = [0]
        # Fail more times than allowed retries to ensure we hit the limit
        failures_before_success = (policy.max_retries if policy.max_retries >= 0 else 2) + 1
        
        def func():
            call_count[0] += 1
            if call_count[0] <= failures_before_success:
                raise ValueError("retry me")
            return "success"
        
        if policy.max_retries == 0:
            # With 0 retries, function tries once and fails (1 attempt, 0 retries)
            with pytest.raises(ValueError):
                retry_call(func, policy=policy)
            assert call_count[0] == 1
        else:
            # Will exhaust retries and fail
            with pytest.raises(ValueError):
                retry_call(func, policy=policy)
            # Should try: 1 initial + max_retries
            assert call_count[0] == 1 + policy.max_retries


class TestRetryCallbacks:
    """Test retry callback functionality."""

    @given(
        max_retries=st.integers(min_value=1, max_value=3),
        initial_delay=st.floats(min_value=0.001, max_value=0.01)
    )
    @settings(max_examples=30, deadline=2000)
    def test_on_retry_callback_invoked(self, max_retries, initial_delay):
        """Test that on_retry callback is invoked on each retry."""
        callback_calls = []
        
        def on_retry_callback(exc, attempt, delay):
            callback_calls.append((exc, attempt, delay))
        
        call_count = [0]
        
        @with_retry(max_retries=max_retries, initial_delay=initial_delay, 
                    on_retry=on_retry_callback, jitter=False)
        def func():
            call_count[0] += 1
            if call_count[0] <= max_retries:
                raise ValueError("retry me")
            return "success"
        
        result = func()
        assert result == "success"
        assert len(callback_calls) == max_retries
        
        # Verify callback received correct parameters
        for i, (exc, attempt, delay) in enumerate(callback_calls, start=1):
            assert isinstance(exc, ValueError)
            assert attempt == i
            assert delay > 0

    @given(max_retries=st.integers(min_value=1, max_value=3))
    @settings(max_examples=30, deadline=2000)
    def test_callback_exception_doesnt_break_retry(self, max_retries):
        """Test that exceptions in callback don't break retry logic."""
        def broken_callback(exc, attempt, delay):
            raise RuntimeError("callback error")
        
        call_count = [0]
        
        @with_retry(max_retries=max_retries, initial_delay=0.001, 
                    on_retry=broken_callback)
        def func():
            call_count[0] += 1
            if call_count[0] <= max_retries:
                raise ValueError("retry me")
            return "success"
        
        # Should succeed despite callback errors
        result = func()
        assert result == "success"


class TestRetryEdgeCases:
    """Test edge cases in retry logic."""

    def test_zero_retries_fails_immediately(self):
        """Test that max_retries=0 fails on first exception."""
        @with_retry(max_retries=0)
        def func():
            raise ValueError("always fails")
        
        with pytest.raises(ValueError):
            func()

    @given(exception_types=exception_types_strategy())
    @settings(max_examples=30, deadline=2000)
    def test_retry_on_specific_exceptions_only(self, exception_types):
        """Test that retry_on_exceptions filters correctly."""
        call_count = [0]
        
        @with_retry(max_retries=3, initial_delay=0.001, 
                    retry_on_exceptions=exception_types)
        def func():
            call_count[0] += 1
            if call_count[0] == 1:
                # First call raises non-retryable exception
                raise ConnectionError("not retryable")
            return "success"
        
        # Should not retry ConnectionError
        if ConnectionError not in exception_types:
            with pytest.raises(ConnectionError):
                func()
            assert call_count[0] == 1
        else:
            # Would retry, but let's not test this path to keep test simple
            pass

    @given(
        initial_delay=st.floats(min_value=0.001, max_value=0.01),
        max_delay=st.floats(min_value=0.001, max_value=0.01)
    )
    @settings(max_examples=30, deadline=2000)
    def test_max_delay_equal_to_initial_delay(self, initial_delay, max_delay):
        """Test that max_delay can equal initial_delay."""
        # Ensure max_delay >= initial_delay
        if max_delay < initial_delay:
            initial_delay, max_delay = max_delay, initial_delay
        
        policy = RetryPolicy(
            initial_delay=initial_delay,
            max_delay=max_delay,
            jitter=False
        )
        
        delay = policy.calculate_delay(10)  # High attempt number
        assert delay <= max_delay

    @given(
        max_retries=st.just(-1),  # Infinite retries
        failure_count=st.integers(min_value=5, max_value=10)
    )
    @settings(max_examples=20, deadline=2000)
    def test_infinite_retries_with_eventual_success(self, max_retries, failure_count):
        """Test that max_retries=-1 allows many retries until success."""
        call_count = [0]
        
        @with_retry(max_retries=max_retries, initial_delay=0.001)
        def func():
            call_count[0] += 1
            if call_count[0] <= failure_count:
                raise ValueError("retry me")
            return "success"
        
        result = func()
        assert result == "success"
        assert call_count[0] == failure_count + 1

    def test_very_short_initial_delay(self):
        """Test that very short delays work correctly."""
        policy = RetryPolicy(initial_delay=0.0001, max_delay=0.001, jitter=False)
        delay = policy.calculate_delay(1)
        assert delay > 0
        assert delay <= 0.001

    def test_very_long_max_delay(self):
        """Test that very long max_delay works correctly."""
        policy = RetryPolicy(initial_delay=0.1, max_delay=3600.0, jitter=False)
        # Even with many attempts, delay is capped
        delay = policy.calculate_delay(100)
        assert delay <= 3600.0


class TestBatchRetryWrapper:
    """Test the create_batch_retry_wrapper function."""

    @given(
        max_retries=st.integers(min_value=1, max_value=3),
        num_items=st.integers(min_value=1, max_value=5)
    )
    @settings(max_examples=20, deadline=3000)
    def test_batch_wrapper_retries_individual_items(self, max_retries, num_items):
        """Test that batch wrapper applies retry to each item."""
        policy = RetryPolicy(max_retries=max_retries, initial_delay=0.001, jitter=False)
        
        call_counts = {i: 0 for i in range(num_items)}
        
        def process_item(x):
            call_counts[x] += 1
            if call_counts[x] <= max_retries:
                raise ValueError(f"retry item {x}")
            return x * 2
        
        wrapper = create_batch_retry_wrapper(process_item, policy)
        
        results = [wrapper(i) for i in range(num_items)]
        assert results == [i * 2 for i in range(num_items)]
        
        # Each item should have been retried max_retries times
        for count in call_counts.values():
            assert count == max_retries + 1

    @given(policy=valid_retry_policy())
    @settings(max_examples=20, deadline=2000)
    def test_batch_wrapper_with_policy(self, policy):
        """Test that batch wrapper accepts custom policy."""
        # Adjust for fast testing
        policy.initial_delay = 0.001
        policy.max_delay = 0.01
        
        def process_item(x):
            return x * 2
        
        wrapper = create_batch_retry_wrapper(process_item, policy)
        assert callable(wrapper)
        
        result = wrapper(5)
        assert result == 10


class TestRetryIntegration:
    """Test integration scenarios combining multiple retry features."""

    @given(
        max_retries=st.integers(min_value=1, max_value=3),
        exception_types=exception_types_strategy()
    )
    @settings(max_examples=20, deadline=2000)
    def test_full_retry_lifecycle(self, max_retries, exception_types):
        """Test complete retry lifecycle with all features."""
        callback_calls = []
        
        def on_retry_callback(exc, attempt, delay):
            callback_calls.append(attempt)
        
        # Use first exception type from the tuple
        exception_type = exception_types[0]
        
        call_count = [0]
        
        @with_retry(
            max_retries=max_retries,
            initial_delay=0.001,
            retry_on_exceptions=exception_types,
            on_retry=on_retry_callback,
            jitter=False
        )
        def func():
            call_count[0] += 1
            if call_count[0] <= max_retries:
                raise exception_type("retry me")
            return "success"
        
        result = func()
        assert result == "success"
        assert call_count[0] == max_retries + 1
        assert len(callback_calls) == max_retries

    @given(
        max_retries=st.integers(min_value=1, max_value=3),
        initial_delay=st.floats(min_value=0.001, max_value=0.01)
    )
    @settings(max_examples=20, deadline=2000)
    def test_retry_with_complex_function(self, max_retries, initial_delay):
        """Test retry with function that has multiple parameters and return values."""
        call_count = [0]
        
        def complex_func(x, y, z=10):
            call_count[0] += 1
            if call_count[0] <= max_retries:
                raise ValueError("retry me")
            return {"sum": x + y + z, "product": x * y * z}
        
        result = retry_call(
            complex_func,
            args=(1, 2),
            kwargs={"z": 3},
            max_retries=max_retries,
            initial_delay=initial_delay,
            jitter=False
        )
        
        assert result == {"sum": 6, "product": 6}
        assert call_count[0] == max_retries + 1
