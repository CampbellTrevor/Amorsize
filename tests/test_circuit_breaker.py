"""
Tests for circuit breaker pattern implementation.

This module tests the CircuitBreaker class, CircuitBreakerPolicy,
and decorator functionality for fault tolerance.
"""

import pytest
import time
import threading
from unittest.mock import Mock

from amorsize.circuit_breaker import (
    CircuitBreaker,
    CircuitBreakerPolicy,
    CircuitBreakerError,
    CircuitState,
    with_circuit_breaker,
    circuit_breaker_call,
)


# Test CircuitBreakerPolicy

def test_circuit_breaker_policy_defaults():
    """Test that CircuitBreakerPolicy has correct defaults."""
    policy = CircuitBreakerPolicy()
    assert policy.failure_threshold == 5
    assert policy.success_threshold == 2
    assert policy.timeout == 60.0
    assert policy.expected_exceptions is None
    assert policy.excluded_exceptions is None
    assert policy.on_open is None
    assert policy.on_close is None
    assert policy.on_half_open is None


def test_circuit_breaker_policy_custom_values():
    """Test CircuitBreakerPolicy with custom values."""
    policy = CircuitBreakerPolicy(
        failure_threshold=3,
        success_threshold=1,
        timeout=30.0,
        expected_exceptions=(ValueError, TypeError),
    )
    assert policy.failure_threshold == 3
    assert policy.success_threshold == 1
    assert policy.timeout == 30.0
    assert policy.expected_exceptions == (ValueError, TypeError)


def test_circuit_breaker_policy_validation():
    """Test that CircuitBreakerPolicy validates parameters."""
    with pytest.raises(ValueError, match="failure_threshold must be >= 1"):
        CircuitBreakerPolicy(failure_threshold=0)
    
    with pytest.raises(ValueError, match="success_threshold must be >= 1"):
        CircuitBreakerPolicy(success_threshold=0)
    
    with pytest.raises(ValueError, match="timeout must be positive"):
        CircuitBreakerPolicy(timeout=0)
    
    with pytest.raises(ValueError, match="timeout must be positive"):
        CircuitBreakerPolicy(timeout=-1)


def test_circuit_breaker_policy_exception_overlap():
    """Test that overlapping exceptions are rejected."""
    with pytest.raises(ValueError, match="Cannot have same exceptions"):
        CircuitBreakerPolicy(
            expected_exceptions=(ValueError, TypeError),
            excluded_exceptions=(ValueError, RuntimeError)
        )


# Test CircuitBreaker

def test_circuit_breaker_initial_state():
    """Test that circuit breaker starts in CLOSED state."""
    breaker = CircuitBreaker()
    assert breaker.state == CircuitState.CLOSED
    assert breaker.failure_count == 0
    assert breaker.success_count == 0
    assert breaker.opened_at is None


def test_circuit_breaker_successful_call():
    """Test successful function call through circuit breaker."""
    breaker = CircuitBreaker()
    
    def success_func(x):
        return x * 2
    
    result = breaker.call(success_func, 5)
    assert result == 10
    assert breaker.state == CircuitState.CLOSED
    assert breaker.failure_count == 0


def test_circuit_breaker_failing_call():
    """Test that failures are counted but circuit stays closed initially."""
    policy = CircuitBreakerPolicy(failure_threshold=3)
    breaker = CircuitBreaker(policy)
    
    def failing_func():
        raise ValueError("Test error")
    
    # First two failures should not open circuit
    with pytest.raises(ValueError):
        breaker.call(failing_func)
    assert breaker.state == CircuitState.CLOSED
    assert breaker.failure_count == 1
    
    with pytest.raises(ValueError):
        breaker.call(failing_func)
    assert breaker.state == CircuitState.CLOSED
    assert breaker.failure_count == 2


def test_circuit_breaker_opens_after_threshold():
    """Test that circuit opens after failure threshold is reached."""
    policy = CircuitBreakerPolicy(failure_threshold=3)
    breaker = CircuitBreaker(policy)
    
    def failing_func():
        raise ValueError("Test error")
    
    # Reach failure threshold
    for _ in range(3):
        with pytest.raises(ValueError):
            breaker.call(failing_func)
    
    assert breaker.state == CircuitState.OPEN
    assert breaker.failure_count == 3
    assert breaker.opened_at is not None


def test_circuit_breaker_blocks_when_open():
    """Test that circuit breaker blocks calls when open."""
    policy = CircuitBreakerPolicy(failure_threshold=2, timeout=10.0)
    breaker = CircuitBreaker(policy)
    
    def failing_func():
        raise ValueError("Test error")
    
    # Open the circuit
    for _ in range(2):
        with pytest.raises(ValueError):
            breaker.call(failing_func)
    
    assert breaker.state == CircuitState.OPEN
    
    # Next call should raise CircuitBreakerError
    with pytest.raises(CircuitBreakerError) as exc_info:
        breaker.call(failing_func)
    
    assert exc_info.value.state == CircuitState.OPEN
    assert exc_info.value.retry_after > 0


def test_circuit_breaker_transitions_to_half_open():
    """Test that circuit transitions to HALF_OPEN after timeout."""
    policy = CircuitBreakerPolicy(failure_threshold=2, timeout=0.1)
    breaker = CircuitBreaker(policy)
    
    def failing_func():
        raise ValueError("Test error")
    
    # Open the circuit
    for _ in range(2):
        with pytest.raises(ValueError):
            breaker.call(failing_func)
    
    assert breaker.state == CircuitState.OPEN
    
    # Wait for timeout
    time.sleep(0.15)
    
    # Next call should transition to HALF_OPEN (but still fail)
    with pytest.raises(ValueError):
        breaker.call(failing_func)
    
    # Circuit should be OPEN again after failure in HALF_OPEN
    assert breaker.state == CircuitState.OPEN


def test_circuit_breaker_closes_after_success_in_half_open():
    """Test that circuit closes after successes in HALF_OPEN state."""
    policy = CircuitBreakerPolicy(
        failure_threshold=2,
        success_threshold=2,
        timeout=0.1
    )
    breaker = CircuitBreaker(policy)
    
    call_count = [0]
    
    def sometimes_failing_func():
        call_count[0] += 1
        if call_count[0] <= 2:
            raise ValueError("Test error")
        return "success"
    
    # Open the circuit
    for _ in range(2):
        with pytest.raises(ValueError):
            breaker.call(sometimes_failing_func)
    
    assert breaker.state == CircuitState.OPEN
    
    # Wait for timeout
    time.sleep(0.15)
    
    # Manually transition to half-open by checking state
    # (normally happens automatically on next call)
    with breaker._lock:
        breaker._check_and_update_state()
    
    assert breaker.state == CircuitState.HALF_OPEN
    
    # Two successful calls should close the circuit
    result1 = breaker.call(sometimes_failing_func)
    assert result1 == "success"
    assert breaker.state == CircuitState.HALF_OPEN
    
    result2 = breaker.call(sometimes_failing_func)
    assert result2 == "success"
    assert breaker.state == CircuitState.CLOSED


def test_circuit_breaker_success_resets_failures():
    """Test that success resets failure count in CLOSED state."""
    policy = CircuitBreakerPolicy(failure_threshold=3)
    breaker = CircuitBreaker(policy)
    
    call_count = [0]
    
    def intermittent_func():
        call_count[0] += 1
        if call_count[0] in [1, 2]:
            raise ValueError("Test error")
        return "success"
    
    # Two failures
    for _ in range(2):
        with pytest.raises(ValueError):
            breaker.call(intermittent_func)
    
    assert breaker.failure_count == 2
    
    # Success should reset count
    result = breaker.call(intermittent_func)
    assert result == "success"
    assert breaker.failure_count == 0
    assert breaker.state == CircuitState.CLOSED


def test_circuit_breaker_excluded_exceptions():
    """Test that excluded exceptions don't count as failures."""
    policy = CircuitBreakerPolicy(
        failure_threshold=2,
        excluded_exceptions=(ValueError,)
    )
    breaker = CircuitBreaker(policy)
    
    def func_with_excluded_error():
        raise ValueError("This should not count")
    
    # Multiple calls with excluded exception shouldn't open circuit
    for _ in range(5):
        with pytest.raises(ValueError):
            breaker.call(func_with_excluded_error)
    
    assert breaker.state == CircuitState.CLOSED
    assert breaker.failure_count == 0


def test_circuit_breaker_expected_exceptions():
    """Test that only expected exceptions count as failures."""
    policy = CircuitBreakerPolicy(
        failure_threshold=2,
        expected_exceptions=(ConnectionError, TimeoutError)
    )
    breaker = CircuitBreaker(policy)
    
    def func_with_unexpected_error():
        raise ValueError("This should not count")
    
    # Multiple calls with unexpected exception shouldn't open circuit
    for _ in range(5):
        with pytest.raises(ValueError):
            breaker.call(func_with_unexpected_error)
    
    assert breaker.state == CircuitState.CLOSED
    assert breaker.failure_count == 0
    
    # But expected exception should count
    def func_with_expected_error():
        raise ConnectionError("This should count")
    
    for _ in range(2):
        with pytest.raises(ConnectionError):
            breaker.call(func_with_expected_error)
    
    assert breaker.state == CircuitState.OPEN


def test_circuit_breaker_callbacks():
    """Test that callbacks are called at state transitions."""
    open_calls = []
    close_calls = []
    half_open_calls = []
    
    def on_open(count, exc):
        open_calls.append((count, exc))
    
    def on_close():
        close_calls.append(True)
    
    def on_half_open():
        half_open_calls.append(True)
    
    policy = CircuitBreakerPolicy(
        failure_threshold=2,
        success_threshold=1,
        timeout=0.1,
        on_open=on_open,
        on_close=on_close,
        on_half_open=on_half_open
    )
    breaker = CircuitBreaker(policy)
    
    call_count = [0]
    
    def func():
        call_count[0] += 1
        if call_count[0] <= 2:
            raise ValueError("Test error")
        return "success"
    
    # Open circuit
    for _ in range(2):
        with pytest.raises(ValueError):
            breaker.call(func)
    
    assert len(open_calls) == 1
    assert open_calls[0][0] == 2  # failure count
    assert isinstance(open_calls[0][1], ValueError)
    
    # Wait and transition to half-open
    time.sleep(0.15)
    result = breaker.call(func)
    
    assert len(half_open_calls) == 1
    
    # Close circuit with success
    assert result == "success"
    assert len(close_calls) == 1


def test_circuit_breaker_reset():
    """Test manual reset of circuit breaker."""
    policy = CircuitBreakerPolicy(failure_threshold=2)
    breaker = CircuitBreaker(policy)
    
    def failing_func():
        raise ValueError("Test error")
    
    # Open circuit
    for _ in range(2):
        with pytest.raises(ValueError):
            breaker.call(failing_func)
    
    assert breaker.state == CircuitState.OPEN
    
    # Manual reset
    breaker.reset()
    
    assert breaker.state == CircuitState.CLOSED
    assert breaker.failure_count == 0
    assert breaker.success_count == 0
    assert breaker.opened_at is None


def test_circuit_breaker_get_state():
    """Test getting current circuit state."""
    breaker = CircuitBreaker()
    
    state, failures, successes, opened = breaker.get_state()
    assert state == CircuitState.CLOSED
    assert failures == 0
    assert successes == 0
    assert opened is None


# Test decorator

def test_with_circuit_breaker_decorator_default():
    """Test decorator with default policy."""
    @with_circuit_breaker()
    def test_func(x):
        return x * 2
    
    result = test_func(5)
    assert result == 10
    
    # Should have breaker attached
    assert hasattr(test_func, '_circuit_breaker')
    assert isinstance(test_func._circuit_breaker, CircuitBreaker)


def test_with_circuit_breaker_decorator_custom_policy():
    """Test decorator with custom policy."""
    policy = CircuitBreakerPolicy(failure_threshold=2)
    
    @with_circuit_breaker(policy)
    def failing_func():
        raise ValueError("Test error")
    
    # Open circuit with 2 failures
    for _ in range(2):
        with pytest.raises(ValueError):
            failing_func()
    
    # Should now raise CircuitBreakerError
    with pytest.raises(CircuitBreakerError):
        failing_func()


def test_with_circuit_breaker_decorator_shared_breaker():
    """Test that multiple functions can share a circuit breaker."""
    breaker = CircuitBreaker(CircuitBreakerPolicy(failure_threshold=2))
    
    @with_circuit_breaker(breaker)
    def func1():
        raise ValueError("Error in func1")
    
    @with_circuit_breaker(breaker)
    def func2():
        raise ValueError("Error in func2")
    
    # Failure in func1 counts toward shared breaker
    with pytest.raises(ValueError):
        func1()
    
    assert breaker.failure_count == 1
    
    # Failure in func2 opens the shared breaker
    with pytest.raises(ValueError):
        func2()
    
    assert breaker.state == CircuitState.OPEN
    
    # Both functions should now be blocked
    with pytest.raises(CircuitBreakerError):
        func1()
    
    with pytest.raises(CircuitBreakerError):
        func2()


def test_with_circuit_breaker_preserves_metadata():
    """Test that decorator preserves function metadata."""
    @with_circuit_breaker()
    def documented_func(x: int) -> int:
        """This is a documented function."""
        return x * 2
    
    assert documented_func.__name__ == "documented_func"
    assert documented_func.__doc__ == "This is a documented function."


# Test circuit_breaker_call

def test_circuit_breaker_call_with_policy():
    """Test circuit_breaker_call with policy."""
    policy = CircuitBreakerPolicy(failure_threshold=2)
    
    def test_func(x):
        return x * 2
    
    result = circuit_breaker_call(test_func, 5, policy=policy)
    assert result == 10


def test_circuit_breaker_call_with_breaker():
    """Test circuit_breaker_call with existing breaker."""
    breaker = CircuitBreaker(CircuitBreakerPolicy(failure_threshold=2))
    
    def failing_func():
        raise ValueError("Test error")
    
    # Open circuit with 2 failures
    for _ in range(2):
        with pytest.raises(ValueError):
            circuit_breaker_call(failing_func, breaker=breaker)
    
    assert breaker.state == CircuitState.OPEN
    
    # Next call should be blocked
    with pytest.raises(CircuitBreakerError):
        circuit_breaker_call(failing_func, breaker=breaker)


def test_circuit_breaker_call_rejects_both_policy_and_breaker():
    """Test that circuit_breaker_call rejects both policy and breaker."""
    policy = CircuitBreakerPolicy()
    breaker = CircuitBreaker()
    
    def test_func():
        return "test"
    
    with pytest.raises(ValueError, match="Cannot specify both policy and breaker"):
        circuit_breaker_call(test_func, policy=policy, breaker=breaker)


# Test thread safety

def test_circuit_breaker_thread_safety():
    """Test that circuit breaker is thread-safe."""
    policy = CircuitBreakerPolicy(failure_threshold=10)
    breaker = CircuitBreaker(policy)
    
    call_count = [0]
    lock = threading.Lock()
    
    def concurrent_func():
        with lock:
            call_count[0] += 1
        if call_count[0] <= 5:
            raise ValueError("Test error")
        return "success"
    
    def worker():
        try:
            breaker.call(concurrent_func)
        except (ValueError, CircuitBreakerError):
            pass
    
    # Run multiple threads concurrently
    threads = [threading.Thread(target=worker) for _ in range(20)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()
    
    # Circuit should still be in valid state
    state, failures, _, _ = breaker.get_state()
    assert state in [CircuitState.CLOSED, CircuitState.OPEN]


# Test edge cases

def test_circuit_breaker_zero_timeout():
    """Test circuit breaker behavior with very short timeout."""
    policy = CircuitBreakerPolicy(failure_threshold=2, timeout=0.01)
    breaker = CircuitBreaker(policy)
    
    def failing_func():
        raise ValueError("Test error")
    
    # Open circuit
    for _ in range(2):
        with pytest.raises(ValueError):
            breaker.call(failing_func)
    
    assert breaker.state == CircuitState.OPEN
    
    # Wait briefly
    time.sleep(0.02)
    
    # Should transition to HALF_OPEN automatically
    with pytest.raises(ValueError):
        breaker.call(failing_func)
    
    # Back to OPEN after failure in HALF_OPEN
    assert breaker.state == CircuitState.OPEN


def test_circuit_breaker_with_args_and_kwargs():
    """Test circuit breaker with various argument types."""
    breaker = CircuitBreaker()
    
    def func_with_args(a, b, c=10, d=20):
        return a + b + c + d
    
    result = breaker.call(func_with_args, 1, 2, c=3, d=4)
    assert result == 10


def test_circuit_breaker_callback_exception_handling():
    """Test that callback exceptions don't break circuit breaker."""
    def bad_callback(*args):
        raise RuntimeError("Callback error")
    
    policy = CircuitBreakerPolicy(
        failure_threshold=2,
        on_open=bad_callback
    )
    breaker = CircuitBreaker(policy)
    
    def failing_func():
        raise ValueError("Test error")
    
    # Should still work even though callback fails
    for _ in range(2):
        with pytest.raises(ValueError):
            breaker.call(failing_func)
    
    assert breaker.state == CircuitState.OPEN
