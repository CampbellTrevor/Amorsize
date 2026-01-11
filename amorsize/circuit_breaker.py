"""
Circuit Breaker pattern for preventing cascade failures in production.

This module provides a circuit breaker implementation that monitors failures
and automatically stops calling failing services, allowing them time to recover.
This prevents cascade failures and reduces system load during outages.
"""

import functools
import threading
import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable, Optional, Tuple, Type, Union


class CircuitState(Enum):
    """
    Circuit breaker states following the classic pattern.
    
    States:
        CLOSED: Normal operation. Requests pass through. Failures are counted.
        OPEN: Circuit is open. Requests fail immediately without calling the function.
              This gives the failing service time to recover.
        HALF_OPEN: Testing if service has recovered. Limited requests pass through.
                   If they succeed, circuit closes. If they fail, circuit reopens.
    """
    CLOSED = "closed"
    OPEN = "open"
    HALF_OPEN = "half_open"


@dataclass
class CircuitBreakerPolicy:
    """
    Configuration for circuit breaker behavior.
    
    Attributes:
        failure_threshold: Number of consecutive failures before opening circuit.
                          Default: 5
        success_threshold: Number of consecutive successes in HALF_OPEN state
                          before closing circuit. Default: 2
        timeout: Time in seconds to wait before transitioning from OPEN to HALF_OPEN.
                Default: 60.0 (1 minute)
        expected_exceptions: Tuple of exception types that count as failures.
                           If None, all exceptions count. Default: None (all exceptions)
        excluded_exceptions: Tuple of exception types that do NOT count as failures.
                           Useful for excluding validation errors, etc. Default: None
        on_open: Optional callback called when circuit opens.
                Receives (failure_count, last_exception) as arguments. Default: None
        on_close: Optional callback called when circuit closes. Default: None
        on_half_open: Optional callback called when circuit enters half-open state.
                     Default: None
    
    Example:
        >>> # Open circuit after 3 failures, try recovery after 30s
        >>> policy = CircuitBreakerPolicy(
        ...     failure_threshold=3,
        ...     timeout=30.0
        ... )
        
        >>> # Only network errors trigger circuit breaker
        >>> policy = CircuitBreakerPolicy(
        ...     expected_exceptions=(ConnectionError, TimeoutError),
        ...     failure_threshold=5
        ... )
        
        >>> # Custom callbacks for monitoring
        >>> def on_open(count, exc):
        ...     print(f"Circuit opened after {count} failures: {exc}")
        >>> policy = CircuitBreakerPolicy(on_open=on_open)
    """
    
    failure_threshold: int = 5
    success_threshold: int = 2
    timeout: float = 60.0
    expected_exceptions: Optional[Tuple[Type[Exception], ...]] = None
    excluded_exceptions: Optional[Tuple[Type[Exception], ...]] = None
    on_open: Optional[Callable[[int, Exception], None]] = None
    on_close: Optional[Callable[[], None]] = None
    on_half_open: Optional[Callable[[], None]] = None
    
    def __post_init__(self):
        """Validate configuration parameters."""
        if self.failure_threshold < 1:
            raise ValueError("failure_threshold must be >= 1")
        if self.success_threshold < 1:
            raise ValueError("success_threshold must be >= 1")
        if self.timeout <= 0:
            raise ValueError("timeout must be positive")
        if self.expected_exceptions and self.excluded_exceptions:
            # Check for overlap
            expected_set = set(self.expected_exceptions)
            excluded_set = set(self.excluded_exceptions)
            overlap = expected_set & excluded_set
            if overlap:
                raise ValueError(
                    f"Cannot have same exceptions in both expected and excluded: {overlap}"
                )


class CircuitBreakerError(Exception):
    """
    Raised when circuit breaker is open and blocks a function call.
    
    Attributes:
        message: Error message describing the circuit state
        state: Current circuit state
        opened_at: Timestamp when circuit was opened
        retry_after: Suggested time to retry (seconds from now)
    """
    
    def __init__(
        self,
        message: str,
        state: CircuitState,
        opened_at: float,
        retry_after: float
    ):
        super().__init__(message)
        self.state = state
        self.opened_at = opened_at
        self.retry_after = retry_after


class CircuitBreaker:
    """
    Circuit breaker implementation for fault tolerance.
    
    This class implements the classic circuit breaker pattern with three states:
    CLOSED, OPEN, and HALF_OPEN. It monitors function calls and automatically
    opens the circuit when failures exceed a threshold, preventing cascade
    failures and allowing failing services time to recover.
    
    Thread-safe: Uses locks to ensure consistent state across multiple threads.
    
    Attributes:
        policy: CircuitBreakerPolicy configuration
        state: Current circuit state (CLOSED, OPEN, or HALF_OPEN)
        failure_count: Number of consecutive failures
        success_count: Number of consecutive successes (in HALF_OPEN state)
        last_failure_time: Timestamp of last failure
        opened_at: Timestamp when circuit was opened (None if not open)
        last_exception: Last exception that occurred
    
    Example:
        >>> breaker = CircuitBreaker()
        >>> 
        >>> @with_circuit_breaker(breaker)
        ... def api_call(data):
        ...     return requests.post("api/endpoint", json=data).json()
        >>> 
        >>> try:
        ...     result = api_call({"key": "value"})
        ... except CircuitBreakerError:
        ...     print("Circuit is open, service unavailable")
    """
    
    def __init__(self, policy: Optional[CircuitBreakerPolicy] = None):
        """
        Initialize circuit breaker with given policy.
        
        Args:
            policy: CircuitBreakerPolicy configuration. If None, uses default policy.
        """
        self.policy = policy or CircuitBreakerPolicy()
        self.state = CircuitState.CLOSED
        self.failure_count = 0
        self.success_count = 0
        self.last_failure_time: Optional[float] = None
        self.opened_at: Optional[float] = None
        self.last_exception: Optional[Exception] = None
        self._lock = threading.Lock()
    
    def _should_count_exception(self, exception: Exception) -> bool:
        """
        Determine if an exception should count as a failure for the circuit breaker.
        
        Args:
            exception: The exception to check
        
        Returns:
            True if exception should count as a failure, False otherwise
        """
        # If excluded exceptions specified and this is one of them, don't count
        if self.policy.excluded_exceptions:
            if isinstance(exception, self.policy.excluded_exceptions):
                return False
        
        # If expected exceptions specified, only count those
        if self.policy.expected_exceptions:
            return isinstance(exception, self.policy.expected_exceptions)
        
        # Otherwise, count all exceptions
        return True
    
    def _transition_to_open(self) -> None:
        """Transition circuit to OPEN state."""
        self.state = CircuitState.OPEN
        self.opened_at = time.time()
        self.success_count = 0
        
        # Call callback if provided
        if self.policy.on_open:
            try:
                self.policy.on_open(self.failure_count, self.last_exception)
            except Exception:
                # Don't let callback errors affect circuit breaker operation
                pass
    
    def _transition_to_half_open(self) -> None:
        """Transition circuit to HALF_OPEN state."""
        self.state = CircuitState.HALF_OPEN
        self.failure_count = 0
        self.success_count = 0
        
        # Call callback if provided
        if self.policy.on_half_open:
            try:
                self.policy.on_half_open()
            except Exception:
                # Don't let callback errors affect circuit breaker operation
                pass
    
    def _transition_to_closed(self) -> None:
        """Transition circuit to CLOSED state."""
        self.state = CircuitState.CLOSED
        self.failure_count = 0
        self.success_count = 0
        self.opened_at = None
        self.last_exception = None
        
        # Call callback if provided
        if self.policy.on_close:
            try:
                self.policy.on_close()
            except Exception:
                # Don't let callback errors affect circuit breaker operation
                pass
    
    def _check_and_update_state(self) -> None:
        """
        Check current state and update if necessary based on timeout.
        
        If circuit is OPEN and timeout has elapsed, transition to HALF_OPEN.
        """
        if self.state == CircuitState.OPEN and self.opened_at:
            elapsed = time.time() - self.opened_at
            if elapsed >= self.policy.timeout:
                self._transition_to_half_open()
    
    def call(self, func: Callable, *args: Any, **kwargs: Any) -> Any:
        """
        Call the function with circuit breaker protection.
        
        Args:
            func: Function to call
            *args: Positional arguments for the function
            **kwargs: Keyword arguments for the function
        
        Returns:
            Result of the function call
        
        Raises:
            CircuitBreakerError: If circuit is OPEN
            Exception: Any exception raised by the function
        """
        with self._lock:
            self._check_and_update_state()
            
            # Check if circuit is open
            if self.state == CircuitState.OPEN:
                retry_after = self.policy.timeout - (time.time() - self.opened_at)
                retry_after = max(0, retry_after)
                raise CircuitBreakerError(
                    f"Circuit breaker is OPEN. Last failure: {self.last_exception}. "
                    f"Retry after {retry_after:.1f}s",
                    state=self.state,
                    opened_at=self.opened_at,
                    retry_after=retry_after
                )
        
        # Execute the function (outside the lock to avoid blocking)
        try:
            result = func(*args, **kwargs)
            
            # Record success
            with self._lock:
                if self.state == CircuitState.HALF_OPEN:
                    self.success_count += 1
                    if self.success_count >= self.policy.success_threshold:
                        self._transition_to_closed()
                elif self.state == CircuitState.CLOSED:
                    # Reset failure count on success
                    self.failure_count = 0
            
            return result
        
        except Exception as e:
            # Record failure if it should be counted
            with self._lock:
                if self._should_count_exception(e):
                    self.failure_count += 1
                    self.success_count = 0
                    self.last_failure_time = time.time()
                    self.last_exception = e
                    
                    if self.state == CircuitState.HALF_OPEN:
                        # Failed in half-open, go back to open
                        self._transition_to_open()
                    elif self.state == CircuitState.CLOSED:
                        # Check if we should open the circuit
                        if self.failure_count >= self.policy.failure_threshold:
                            self._transition_to_open()
            
            # Re-raise the exception
            raise
    
    def reset(self) -> None:
        """
        Manually reset the circuit breaker to CLOSED state.
        
        This can be used for manual intervention or testing.
        """
        with self._lock:
            self._transition_to_closed()
    
    def get_state(self) -> Tuple[CircuitState, int, int, Optional[float]]:
        """
        Get current state information.
        
        Returns:
            Tuple of (state, failure_count, success_count, opened_at)
        """
        with self._lock:
            return (self.state, self.failure_count, self.success_count, self.opened_at)


def with_circuit_breaker(
    breaker: Optional[Union[CircuitBreaker, CircuitBreakerPolicy]] = None
) -> Callable:
    """
    Decorator to apply circuit breaker protection to a function.
    
    Args:
        breaker: CircuitBreaker instance or CircuitBreakerPolicy to use.
                If CircuitBreakerPolicy, creates a new CircuitBreaker.
                If None, creates a CircuitBreaker with default policy.
    
    Returns:
        Decorated function with circuit breaker protection
    
    Example:
        >>> # Use default circuit breaker
        >>> @with_circuit_breaker()
        ... def api_call(data):
        ...     return requests.post("api/endpoint", json=data).json()
        
        >>> # Use custom policy
        >>> policy = CircuitBreakerPolicy(failure_threshold=3, timeout=30.0)
        >>> @with_circuit_breaker(policy)
        ... def api_call(data):
        ...     return requests.post("api/endpoint", json=data).json()
        
        >>> # Share circuit breaker across functions
        >>> breaker = CircuitBreaker()
        >>> @with_circuit_breaker(breaker)
        ... def api_call_1(data):
        ...     return requests.get("api/endpoint1").json()
        >>> @with_circuit_breaker(breaker)
        ... def api_call_2(data):
        ...     return requests.get("api/endpoint2").json()
    """
    # Convert policy to breaker if needed
    if isinstance(breaker, CircuitBreakerPolicy):
        breaker = CircuitBreaker(breaker)
    elif breaker is None:
        breaker = CircuitBreaker()
    
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            return breaker.call(func, *args, **kwargs)
        
        # Attach breaker for introspection
        wrapper._circuit_breaker = breaker
        
        return wrapper
    
    return decorator


def circuit_breaker_call(
    func: Callable,
    *args: Any,
    policy: Optional[CircuitBreakerPolicy] = None,
    breaker: Optional[CircuitBreaker] = None,
    **kwargs: Any
) -> Any:
    """
    Call a function with circuit breaker protection without using a decorator.
    
    Args:
        func: Function to call
        *args: Positional arguments for the function
        policy: CircuitBreakerPolicy to use (creates new CircuitBreaker)
        breaker: Existing CircuitBreaker to use
        **kwargs: Keyword arguments for the function
    
    Returns:
        Result of the function call
    
    Raises:
        CircuitBreakerError: If circuit is open
        ValueError: If both policy and breaker are provided
    
    Example:
        >>> def api_call(data):
        ...     return requests.post("api/endpoint", json=data).json()
        >>> 
        >>> policy = CircuitBreakerPolicy(failure_threshold=3)
        >>> result = circuit_breaker_call(
        ...     api_call,
        ...     {"key": "value"},
        ...     policy=policy
        ... )
    """
    if policy and breaker:
        raise ValueError("Cannot specify both policy and breaker")
    
    if breaker is None:
        breaker = CircuitBreaker(policy or CircuitBreakerPolicy())
    
    return breaker.call(func, *args, **kwargs)
