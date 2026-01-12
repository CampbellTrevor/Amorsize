"""
Property-based tests for the circuit_breaker module using Hypothesis.

These tests automatically generate edge cases and verify invariant properties
of the circuit breaker across a wide range of inputs and state transitions.
"""

import time
import threading

import pytest
from hypothesis import given, settings, strategies as st, HealthCheck

from amorsize.circuit_breaker import (
    CircuitBreaker,
    CircuitBreakerError,
    CircuitBreakerPolicy,
    CircuitState,
    circuit_breaker_call,
    with_circuit_breaker,
)


# Custom strategies for generating test data
@st.composite
def valid_circuit_breaker_policy(draw):
    """Generate valid CircuitBreakerPolicy configurations."""
    failure_threshold = draw(st.integers(min_value=1, max_value=20))
    success_threshold = draw(st.integers(min_value=1, max_value=10))
    timeout = draw(st.floats(min_value=0.001, max_value=60.0))
    
    return CircuitBreakerPolicy(
        failure_threshold=failure_threshold,
        success_threshold=success_threshold,
        timeout=timeout
    )


@st.composite
def exception_types_strategy(draw):
    """Generate valid exception type tuples."""
    # Choose a subset of common exception types
    available_types = [ValueError, TypeError, RuntimeError, KeyError, AttributeError]
    size = draw(st.integers(min_value=1, max_value=3))
    selected = draw(st.lists(st.sampled_from(available_types), min_size=size, max_size=size, unique=True))
    return tuple(selected)


class TestCircuitBreakerPolicyInvariants:
    """Test invariant properties of CircuitBreakerPolicy."""

    @given(
        failure_threshold=st.integers(min_value=1, max_value=100),
        success_threshold=st.integers(min_value=1, max_value=50),
        timeout=st.floats(min_value=0.001, max_value=300.0)
    )
    @settings(max_examples=100, deadline=1000)
    def test_policy_initialization_valid_params(self, failure_threshold, success_threshold, timeout):
        """Test that valid parameters create a policy without errors."""
        policy = CircuitBreakerPolicy(
            failure_threshold=failure_threshold,
            success_threshold=success_threshold,
            timeout=timeout
        )
        
        assert policy.failure_threshold == failure_threshold
        assert policy.success_threshold == success_threshold
        assert policy.timeout == timeout
        assert policy.expected_exceptions is None
        assert policy.excluded_exceptions is None

    @given(failure_threshold=st.integers(max_value=0))
    @settings(max_examples=50, deadline=1000)
    def test_policy_rejects_invalid_failure_threshold(self, failure_threshold):
        """Test that invalid failure_threshold raises ValueError."""
        with pytest.raises(ValueError, match="failure_threshold must be >= 1"):
            CircuitBreakerPolicy(failure_threshold=failure_threshold)

    @given(success_threshold=st.integers(max_value=0))
    @settings(max_examples=50, deadline=1000)
    def test_policy_rejects_invalid_success_threshold(self, success_threshold):
        """Test that invalid success_threshold raises ValueError."""
        with pytest.raises(ValueError, match="success_threshold must be >= 1"):
            CircuitBreakerPolicy(success_threshold=success_threshold)

    @given(timeout=st.floats(max_value=0.0, exclude_max=True) | st.just(0.0))
    @settings(max_examples=50, deadline=1000)
    def test_policy_rejects_invalid_timeout(self, timeout):
        """Test that non-positive timeout raises ValueError."""
        with pytest.raises(ValueError, match="timeout must be positive"):
            CircuitBreakerPolicy(timeout=timeout)

    @given(exception_types=exception_types_strategy())
    @settings(max_examples=50, deadline=1000)
    def test_policy_accepts_expected_exceptions(self, exception_types):
        """Test that expected_exceptions can be set."""
        policy = CircuitBreakerPolicy(expected_exceptions=exception_types)
        assert policy.expected_exceptions == exception_types

    @given(exception_types=exception_types_strategy())
    @settings(max_examples=50, deadline=1000)
    def test_policy_accepts_excluded_exceptions(self, exception_types):
        """Test that excluded_exceptions can be set."""
        policy = CircuitBreakerPolicy(excluded_exceptions=exception_types)
        assert policy.excluded_exceptions == exception_types

    def test_policy_rejects_overlapping_exception_types(self):
        """Test that overlapping expected and excluded exceptions are rejected."""
        with pytest.raises(ValueError, match="Cannot have same exceptions"):
            CircuitBreakerPolicy(
                expected_exceptions=(ValueError, TypeError),
                excluded_exceptions=(ValueError, KeyError)
            )


class TestCircuitBreakerStateInvariants:
    """Test state machine invariants of CircuitBreaker."""

    @given(policy=valid_circuit_breaker_policy())
    @settings(max_examples=100, deadline=1000)
    def test_initial_state_is_closed(self, policy):
        """Test that circuit breaker starts in CLOSED state."""
        breaker = CircuitBreaker(policy)
        
        assert breaker.state == CircuitState.CLOSED
        assert breaker.failure_count == 0
        assert breaker.success_count == 0
        assert breaker.opened_at is None

    @given(policy=valid_circuit_breaker_policy())
    @settings(max_examples=50, deadline=2000)
    def test_successful_calls_maintain_closed_state(self, policy):
        """Test that successful calls keep circuit in CLOSED state."""
        breaker = CircuitBreaker(policy)
        
        def success_func():
            return "success"
        
        # Make multiple successful calls
        for _ in range(5):
            result = breaker.call(success_func)
            assert result == "success"
            assert breaker.state == CircuitState.CLOSED
            assert breaker.failure_count == 0

    @given(policy=valid_circuit_breaker_policy())
    @settings(max_examples=50, deadline=3000)
    def test_failures_increment_count(self, policy):
        """Test that failures increment failure count."""
        breaker = CircuitBreaker(policy)
        
        def fail_func():
            raise ValueError("test error")
        
        # Make failures up to threshold - 1
        for i in range(min(policy.failure_threshold - 1, 10)):
            with pytest.raises(ValueError):
                breaker.call(fail_func)
            
            # Should still be CLOSED
            assert breaker.state == CircuitState.CLOSED
            assert breaker.failure_count == i + 1

    @given(policy=valid_circuit_breaker_policy())
    @settings(max_examples=50, deadline=3000)
    def test_threshold_failures_open_circuit(self, policy):
        """Test that reaching failure threshold opens circuit."""
        breaker = CircuitBreaker(policy)
        
        def fail_func():
            raise ValueError("test error")
        
        # Fail exactly threshold times
        for _ in range(policy.failure_threshold):
            with pytest.raises(ValueError):
                breaker.call(fail_func)
        
        # Circuit should now be OPEN
        assert breaker.state == CircuitState.OPEN
        assert breaker.opened_at is not None
        assert breaker.failure_count == policy.failure_threshold

    @given(policy=valid_circuit_breaker_policy())
    @settings(max_examples=50, deadline=2000)
    def test_open_circuit_blocks_calls(self, policy):
        """Test that OPEN circuit blocks calls without executing function."""
        breaker = CircuitBreaker(policy)
        
        # Force circuit to OPEN state
        breaker.state = CircuitState.OPEN
        breaker.opened_at = time.time()
        
        call_count = 0
        def func():
            nonlocal call_count
            call_count += 1
            return "should not execute"
        
        # Attempt call should raise CircuitBreakerError
        with pytest.raises(CircuitBreakerError) as exc_info:
            breaker.call(func)
        
        # Function should not have been called
        assert call_count == 0
        
        # Error should have correct attributes
        assert exc_info.value.state == CircuitState.OPEN
        assert exc_info.value.opened_at == breaker.opened_at
        assert exc_info.value.retry_after >= 0

    @given(policy=valid_circuit_breaker_policy())
    @settings(max_examples=30, deadline=5000, suppress_health_check=[HealthCheck.function_scoped_fixture])
    def test_open_to_half_open_after_timeout(self, policy):
        """Test that circuit transitions to HALF_OPEN after timeout."""
        # Use a very short timeout for testing
        short_policy = CircuitBreakerPolicy(
            failure_threshold=policy.failure_threshold,
            success_threshold=policy.success_threshold,
            timeout=0.01  # 10ms timeout
        )
        breaker = CircuitBreaker(short_policy)
        
        # Force circuit to OPEN state
        breaker.state = CircuitState.OPEN
        breaker.opened_at = time.time()
        
        # Wait for timeout to elapse
        time.sleep(0.02)  # Wait longer than timeout
        
        # Next call attempt should transition to HALF_OPEN
        def success_func():
            return "success"
        
        result = breaker.call(success_func)
        
        # Should have transitioned to HALF_OPEN and executed successfully
        assert result == "success"
        # State could be HALF_OPEN or CLOSED depending on success_threshold
        assert breaker.state in (CircuitState.HALF_OPEN, CircuitState.CLOSED)

    @given(policy=valid_circuit_breaker_policy())
    @settings(max_examples=30, deadline=4000)
    def test_half_open_successes_close_circuit(self, policy):
        """Test that successes in HALF_OPEN close the circuit."""
        breaker = CircuitBreaker(policy)
        
        # Force circuit to HALF_OPEN state
        breaker.state = CircuitState.HALF_OPEN
        breaker.failure_count = 0
        breaker.success_count = 0
        
        def success_func():
            return "success"
        
        # Make successful calls up to success_threshold
        for i in range(policy.success_threshold):
            result = breaker.call(success_func)
            assert result == "success"
        
        # Circuit should now be CLOSED
        assert breaker.state == CircuitState.CLOSED
        assert breaker.failure_count == 0
        assert breaker.success_count == 0
        assert breaker.opened_at is None

    @given(policy=valid_circuit_breaker_policy())
    @settings(max_examples=30, deadline=3000)
    def test_half_open_failure_reopens_circuit(self, policy):
        """Test that failure in HALF_OPEN reopens the circuit."""
        breaker = CircuitBreaker(policy)
        
        # Force circuit to HALF_OPEN state
        breaker.state = CircuitState.HALF_OPEN
        breaker.failure_count = 0
        breaker.success_count = 0
        
        def fail_func():
            raise ValueError("test error")
        
        # Single failure should reopen circuit
        with pytest.raises(ValueError):
            breaker.call(fail_func)
        
        # Circuit should be OPEN again
        assert breaker.state == CircuitState.OPEN
        assert breaker.opened_at is not None


class TestCircuitBreakerExceptionFiltering:
    """Test exception filtering logic."""

    @given(policy=valid_circuit_breaker_policy())
    @settings(max_examples=50, deadline=3000)
    def test_expected_exceptions_counted(self, policy):
        """Test that expected exceptions are counted as failures."""
        policy_with_expected = CircuitBreakerPolicy(
            failure_threshold=policy.failure_threshold,
            success_threshold=policy.success_threshold,
            timeout=policy.timeout,
            expected_exceptions=(ValueError, TypeError)
        )
        breaker = CircuitBreaker(policy_with_expected)
        
        def fail_with_value_error():
            raise ValueError("expected")
        
        # ValueError should be counted
        with pytest.raises(ValueError):
            breaker.call(fail_with_value_error)
        
        assert breaker.failure_count == 1

    @given(policy=valid_circuit_breaker_policy())
    @settings(max_examples=50, deadline=3000)
    def test_unexpected_exceptions_not_counted(self, policy):
        """Test that unexpected exceptions are not counted when expected_exceptions is set."""
        policy_with_expected = CircuitBreakerPolicy(
            failure_threshold=policy.failure_threshold,
            success_threshold=policy.success_threshold,
            timeout=policy.timeout,
            expected_exceptions=(ValueError,)
        )
        breaker = CircuitBreaker(policy_with_expected)
        
        def fail_with_runtime_error():
            raise RuntimeError("unexpected")
        
        # RuntimeError should not be counted
        with pytest.raises(RuntimeError):
            breaker.call(fail_with_runtime_error)
        
        assert breaker.failure_count == 0
        assert breaker.state == CircuitState.CLOSED

    @given(policy=valid_circuit_breaker_policy())
    @settings(max_examples=50, deadline=3000)
    def test_excluded_exceptions_not_counted(self, policy):
        """Test that excluded exceptions are not counted as failures."""
        policy_with_excluded = CircuitBreakerPolicy(
            failure_threshold=policy.failure_threshold,
            success_threshold=policy.success_threshold,
            timeout=policy.timeout,
            excluded_exceptions=(ValueError,)
        )
        breaker = CircuitBreaker(policy_with_excluded)
        
        def fail_with_value_error():
            raise ValueError("excluded")
        
        # ValueError should not be counted
        with pytest.raises(ValueError):
            breaker.call(fail_with_value_error)
        
        assert breaker.failure_count == 0
        assert breaker.state == CircuitState.CLOSED


class TestCircuitBreakerCallbacks:
    """Test callback functionality."""

    @given(policy=valid_circuit_breaker_policy())
    @settings(max_examples=30, deadline=3000)
    def test_on_open_callback_invoked(self, policy):
        """Test that on_open callback is invoked when circuit opens."""
        callback_invoked = []
        
        def on_open(count, exc):
            callback_invoked.append((count, exc))
        
        policy_with_callback = CircuitBreakerPolicy(
            failure_threshold=policy.failure_threshold,
            success_threshold=policy.success_threshold,
            timeout=policy.timeout,
            on_open=on_open
        )
        breaker = CircuitBreaker(policy_with_callback)
        
        def fail_func():
            raise ValueError("test")
        
        # Fail enough times to open circuit
        for _ in range(policy.failure_threshold):
            with pytest.raises(ValueError):
                breaker.call(fail_func)
        
        # Callback should have been invoked
        assert len(callback_invoked) == 1
        count, exc = callback_invoked[0]
        assert count == policy.failure_threshold
        assert isinstance(exc, ValueError)

    @given(policy=valid_circuit_breaker_policy())
    @settings(max_examples=30, deadline=4000)
    def test_on_close_callback_invoked(self, policy):
        """Test that on_close callback is invoked when circuit closes."""
        callback_invoked = []
        
        def on_close():
            callback_invoked.append(True)
        
        policy_with_callback = CircuitBreakerPolicy(
            failure_threshold=policy.failure_threshold,
            success_threshold=policy.success_threshold,
            timeout=policy.timeout,
            on_close=on_close
        )
        breaker = CircuitBreaker(policy_with_callback)
        
        # Force to HALF_OPEN and then close
        breaker.state = CircuitState.HALF_OPEN
        breaker.success_count = 0
        
        def success_func():
            return "success"
        
        for _ in range(policy.success_threshold):
            breaker.call(success_func)
        
        # Callback should have been invoked
        assert len(callback_invoked) == 1

    @given(policy=valid_circuit_breaker_policy())
    @settings(max_examples=30, deadline=3000)
    def test_callback_exceptions_dont_break_circuit(self, policy):
        """Test that exceptions in callbacks don't break circuit breaker operation."""
        def bad_callback(*args, **kwargs):
            raise RuntimeError("callback error")
        
        policy_with_bad_callback = CircuitBreakerPolicy(
            failure_threshold=policy.failure_threshold,
            success_threshold=policy.success_threshold,
            timeout=policy.timeout,
            on_open=bad_callback
        )
        breaker = CircuitBreaker(policy_with_bad_callback)
        
        def fail_func():
            raise ValueError("test")
        
        # Even with bad callback, circuit should still open
        for _ in range(policy.failure_threshold):
            with pytest.raises(ValueError):
                breaker.call(fail_func)
        
        # Circuit should be OPEN despite callback error
        assert breaker.state == CircuitState.OPEN


class TestCircuitBreakerReset:
    """Test manual reset functionality."""

    @given(policy=valid_circuit_breaker_policy())
    @settings(max_examples=50, deadline=2000)
    def test_reset_closes_circuit(self, policy):
        """Test that reset() closes the circuit."""
        breaker = CircuitBreaker(policy)
        
        # Force circuit to OPEN
        breaker.state = CircuitState.OPEN
        breaker.opened_at = time.time()
        breaker.failure_count = policy.failure_threshold
        
        # Reset should close circuit
        breaker.reset()
        
        assert breaker.state == CircuitState.CLOSED
        assert breaker.failure_count == 0
        assert breaker.success_count == 0
        assert breaker.opened_at is None

    @given(policy=valid_circuit_breaker_policy())
    @settings(max_examples=50, deadline=2000)
    def test_reset_from_half_open(self, policy):
        """Test that reset() works from HALF_OPEN state."""
        breaker = CircuitBreaker(policy)
        
        # Force circuit to HALF_OPEN
        breaker.state = CircuitState.HALF_OPEN
        breaker.success_count = 1
        
        # Reset should close circuit
        breaker.reset()
        
        assert breaker.state == CircuitState.CLOSED
        assert breaker.success_count == 0


class TestCircuitBreakerGetState:
    """Test state inspection."""

    @given(policy=valid_circuit_breaker_policy())
    @settings(max_examples=50, deadline=2000)
    def test_get_state_returns_tuple(self, policy):
        """Test that get_state() returns correct tuple."""
        breaker = CircuitBreaker(policy)
        
        state, failure_count, success_count, opened_at = breaker.get_state()
        
        assert state == CircuitState.CLOSED
        assert failure_count == 0
        assert success_count == 0
        assert opened_at is None

    @given(policy=valid_circuit_breaker_policy())
    @settings(max_examples=50, deadline=3000)
    def test_get_state_reflects_current_state(self, policy):
        """Test that get_state() reflects current state accurately."""
        breaker = CircuitBreaker(policy)
        
        # Open the circuit
        def fail_func():
            raise ValueError("test")
        
        for _ in range(policy.failure_threshold):
            with pytest.raises(ValueError):
                breaker.call(fail_func)
        
        state, failure_count, success_count, opened_at = breaker.get_state()
        
        assert state == CircuitState.OPEN
        assert failure_count == policy.failure_threshold
        assert opened_at is not None


class TestCircuitBreakerThreadSafety:
    """Test thread safety of circuit breaker."""

    @given(policy=valid_circuit_breaker_policy())
    @settings(max_examples=20, deadline=5000, suppress_health_check=[HealthCheck.function_scoped_fixture])
    def test_concurrent_access(self, policy):
        """Test that concurrent access doesn't corrupt state."""
        breaker = CircuitBreaker(policy)
        errors = []
        
        def concurrent_call():
            try:
                def success_func():
                    return "success"
                
                for _ in range(5):
                    breaker.call(success_func)
            except Exception as e:
                errors.append(e)
        
        # Create multiple threads
        threads = [threading.Thread(target=concurrent_call) for _ in range(5)]
        
        # Start all threads
        for t in threads:
            t.start()
        
        # Wait for all threads
        for t in threads:
            t.join()
        
        # No errors should have occurred
        assert len(errors) == 0
        
        # State should be consistent
        state, failure_count, success_count, opened_at = breaker.get_state()
        assert state == CircuitState.CLOSED
        assert failure_count == 0


class TestWithCircuitBreakerDecorator:
    """Test the with_circuit_breaker decorator."""

    @given(policy=valid_circuit_breaker_policy())
    @settings(max_examples=30, deadline=3000)
    def test_decorator_with_policy(self, policy):
        """Test decorator with a policy."""
        @with_circuit_breaker(policy)
        def func():
            return "success"
        
        result = func()
        assert result == "success"
        assert hasattr(func, '_circuit_breaker')
        assert isinstance(func._circuit_breaker, CircuitBreaker)

    def test_decorator_with_none(self):
        """Test decorator with None creates default policy."""
        @with_circuit_breaker(None)
        def func():
            return "success"
        
        result = func()
        assert result == "success"
        assert hasattr(func, '_circuit_breaker')

    @given(policy=valid_circuit_breaker_policy())
    @settings(max_examples=30, deadline=3000)
    def test_decorator_with_breaker_instance(self, policy):
        """Test decorator with CircuitBreaker instance."""
        breaker = CircuitBreaker(policy)
        
        @with_circuit_breaker(breaker)
        def func():
            return "success"
        
        result = func()
        assert result == "success"
        assert func._circuit_breaker is breaker

    @given(policy=valid_circuit_breaker_policy())
    @settings(max_examples=30, deadline=3000)
    def test_decorated_function_opens_circuit(self, policy):
        """Test that decorated function can open circuit."""
        @with_circuit_breaker(policy)
        def func():
            raise ValueError("error")
        
        # Fail enough times to open circuit
        for _ in range(policy.failure_threshold):
            with pytest.raises(ValueError):
                func()
        
        # Next call should raise CircuitBreakerError
        with pytest.raises(CircuitBreakerError):
            func()


class TestCircuitBreakerCall:
    """Test the circuit_breaker_call function."""

    @given(policy=valid_circuit_breaker_policy())
    @settings(max_examples=30, deadline=2000)
    def test_call_with_policy(self, policy):
        """Test circuit_breaker_call with a policy."""
        def func(x):
            return x * 2
        
        result = circuit_breaker_call(func, 21, policy=policy)
        assert result == 42

    def test_call_with_breaker(self):
        """Test circuit_breaker_call with a breaker instance."""
        breaker = CircuitBreaker()
        
        def func(x):
            return x * 2
        
        result = circuit_breaker_call(func, 21, breaker=breaker)
        assert result == 42

    def test_call_rejects_both_policy_and_breaker(self):
        """Test that providing both policy and breaker raises error."""
        policy = CircuitBreakerPolicy()
        breaker = CircuitBreaker()
        
        def func():
            return "test"
        
        with pytest.raises(ValueError, match="Cannot specify both policy and breaker"):
            circuit_breaker_call(func, policy=policy, breaker=breaker)

    @given(policy=valid_circuit_breaker_policy())
    @settings(max_examples=30, deadline=3000)
    def test_call_with_kwargs(self, policy):
        """Test circuit_breaker_call with keyword arguments."""
        def func(x, y=10):
            return x + y
        
        result = circuit_breaker_call(func, 5, y=15, policy=policy)
        assert result == 20


class TestCircuitBreakerEdgeCases:
    """Test edge cases and boundary conditions."""

    def test_minimum_thresholds(self):
        """Test circuit breaker with minimum thresholds (1)."""
        policy = CircuitBreakerPolicy(
            failure_threshold=1,
            success_threshold=1,
            timeout=0.01
        )
        breaker = CircuitBreaker(policy)
        
        def fail_func():
            raise ValueError("error")
        
        # Single failure should open circuit
        with pytest.raises(ValueError):
            breaker.call(fail_func)
        
        assert breaker.state == CircuitState.OPEN

    def test_very_short_timeout(self):
        """Test circuit breaker with very short timeout."""
        policy = CircuitBreakerPolicy(
            failure_threshold=1,
            success_threshold=1,
            timeout=0.001  # 1ms
        )
        breaker = CircuitBreaker(policy)
        
        # Force to OPEN
        breaker.state = CircuitState.OPEN
        breaker.opened_at = time.time()
        
        # Wait for timeout
        time.sleep(0.002)
        
        # Should transition to HALF_OPEN
        def success_func():
            return "success"
        
        result = breaker.call(success_func)
        assert result == "success"

    @given(
        failure_threshold=st.integers(min_value=10, max_value=50),
        success_threshold=st.integers(min_value=10, max_value=30)
    )
    @settings(max_examples=20, deadline=5000)
    def test_large_thresholds(self, failure_threshold, success_threshold):
        """Test circuit breaker with large thresholds."""
        policy = CircuitBreakerPolicy(
            failure_threshold=failure_threshold,
            success_threshold=success_threshold,
            timeout=0.01
        )
        breaker = CircuitBreaker(policy)
        
        assert breaker.policy.failure_threshold == failure_threshold
        assert breaker.policy.success_threshold == success_threshold

    def test_none_policy_uses_defaults(self):
        """Test that None policy uses default values."""
        breaker = CircuitBreaker(None)
        
        assert breaker.policy.failure_threshold == 5
        assert breaker.policy.success_threshold == 2
        assert breaker.policy.timeout == 60.0

    @given(timeout=st.floats(min_value=60.0, max_value=3600.0))
    @settings(max_examples=30, deadline=1000)
    def test_long_timeouts(self, timeout):
        """Test circuit breaker with long timeouts."""
        policy = CircuitBreakerPolicy(
            failure_threshold=1,
            success_threshold=1,
            timeout=timeout
        )
        breaker = CircuitBreaker(policy)
        
        # Force to OPEN
        breaker.state = CircuitState.OPEN
        breaker.opened_at = time.time()
        
        # Without waiting, should still be OPEN
        with pytest.raises(CircuitBreakerError) as exc_info:
            breaker.call(lambda: "test")
        
        # retry_after should be close to timeout
        assert exc_info.value.retry_after > timeout - 1


class TestCircuitBreakerIntegration:
    """Test integration scenarios."""

    @given(policy=valid_circuit_breaker_policy())
    @settings(max_examples=20, deadline=5000)
    def test_full_lifecycle(self, policy):
        """Test complete lifecycle: CLOSED -> OPEN -> HALF_OPEN -> CLOSED."""
        # Use short timeout for faster test
        short_policy = CircuitBreakerPolicy(
            failure_threshold=policy.failure_threshold,
            success_threshold=policy.success_threshold,
            timeout=0.01
        )
        breaker = CircuitBreaker(short_policy)
        
        # Start CLOSED
        assert breaker.state == CircuitState.CLOSED
        
        # Fail to OPEN
        def fail_func():
            raise ValueError("error")
        
        for _ in range(short_policy.failure_threshold):
            with pytest.raises(ValueError):
                breaker.call(fail_func)
        
        assert breaker.state == CircuitState.OPEN
        
        # Wait for timeout
        time.sleep(0.02)
        
        # Succeed to HALF_OPEN then CLOSED
        def success_func():
            return "success"
        
        for _ in range(short_policy.success_threshold):
            result = breaker.call(success_func)
            assert result == "success"
        
        assert breaker.state == CircuitState.CLOSED

    @given(policy=valid_circuit_breaker_policy())
    @settings(max_examples=20, deadline=3000)
    def test_success_resets_failure_count_in_closed(self, policy):
        """Test that success in CLOSED state resets failure count."""
        breaker = CircuitBreaker(policy)
        
        # Accumulate some failures
        def fail_func():
            raise ValueError("error")
        
        failures_to_make = min(policy.failure_threshold - 1, 3)
        for _ in range(failures_to_make):
            with pytest.raises(ValueError):
                breaker.call(fail_func)
        
        assert breaker.failure_count == failures_to_make
        
        # One success should reset
        def success_func():
            return "success"
        
        breaker.call(success_func)
        assert breaker.failure_count == 0
