"""
Rate limiting for API throttling and resource control.

This module provides configurable rate limiting using the token bucket algorithm
to prevent exceeding API rate limits and control resource consumption.
"""

import functools
import threading
import time
from dataclasses import dataclass
from typing import Any, Callable, Optional


@dataclass
class RateLimitPolicy:
    """
    Configuration for rate limiting behavior using token bucket algorithm.
    
    The token bucket algorithm allows bursts of requests up to the bucket capacity
    while maintaining a steady average rate over time.
    
    Attributes:
        requests_per_second: Maximum requests allowed per second (rate).
                           Default: 10.0
        burst_size: Maximum burst size (bucket capacity). If None, defaults to
                   requests_per_second. Allows short bursts above the average rate.
                   Default: None (same as requests_per_second)
        wait_on_limit: If True, wait when rate limit is exceeded. If False, raise
                      RateLimitExceeded exception immediately. Default: True
        on_wait: Optional callback called when waiting for rate limit.
                Receives (wait_time,) as argument. Default: None
    
    Example:
        >>> # Allow 10 requests/sec with burst of 20
        >>> policy = RateLimitPolicy(
        ...     requests_per_second=10.0,
        ...     burst_size=20
        ... )
        
        >>> # Strict rate limit without waiting
        >>> policy = RateLimitPolicy(
        ...     requests_per_second=5.0,
        ...     wait_on_limit=False
        ... )
        
        >>> # With callback for monitoring
        >>> def log_wait(wait_time):
        ...     print(f"Rate limited, waiting {wait_time:.2f}s")
        >>> policy = RateLimitPolicy(
        ...     requests_per_second=10.0,
        ...     on_wait=log_wait
        ... )
    """
    
    requests_per_second: float = 10.0
    burst_size: Optional[int] = None
    wait_on_limit: bool = True
    on_wait: Optional[Callable[[float], None]] = None
    
    def __post_init__(self):
        """Validate configuration parameters."""
        if self.requests_per_second <= 0:
            raise ValueError("requests_per_second must be positive")
        
        # Default burst size to requests_per_second (minimum 1)
        if self.burst_size is None:
            self.burst_size = max(1, int(self.requests_per_second))
        
        if self.burst_size < 1:
            raise ValueError("burst_size must be >= 1")


class RateLimiter:
    """
    Thread-safe rate limiter using token bucket algorithm.
    
    The token bucket algorithm maintains a bucket of tokens that refills at a steady rate.
    Each request consumes one token. If tokens are available, the request proceeds immediately.
    If not, it either waits for tokens to be available (wait_on_limit=True) or raises an
    exception (wait_on_limit=False).
    
    This allows short bursts up to the bucket capacity while maintaining a steady average
    rate over time.
    
    Example:
        >>> # Create rate limiter
        >>> limiter = RateLimiter(RateLimitPolicy(requests_per_second=10.0))
        
        >>> # Use as context manager
        >>> with limiter:
        ...     make_api_call()
        
        >>> # Or acquire explicitly
        >>> limiter.acquire()
        >>> make_api_call()
        
        >>> # Check if request would be allowed
        >>> if limiter.try_acquire():
        ...     make_api_call()
    """
    
    def __init__(self, policy: RateLimitPolicy):
        """
        Initialize rate limiter.
        
        Args:
            policy: Rate limiting policy configuration
        """
        self.policy = policy
        self._tokens = float(policy.burst_size)
        self._last_refill_time = time.time()
        self._lock = threading.Lock()
    
    def _refill_tokens(self) -> None:
        """
        Refill tokens based on elapsed time since last refill.
        
        Must be called with self._lock held.
        """
        now = time.time()
        elapsed = now - self._last_refill_time
        
        # Calculate tokens to add based on elapsed time
        tokens_to_add = elapsed * self.policy.requests_per_second
        
        # Add tokens, capped at burst size
        self._tokens = min(
            self.policy.burst_size,
            self._tokens + tokens_to_add
        )
        
        self._last_refill_time = now
    
    def try_acquire(self, tokens: float = 1.0) -> bool:
        """
        Try to acquire tokens without waiting.
        
        Args:
            tokens: Number of tokens to acquire. Default: 1.0
        
        Returns:
            True if tokens were acquired, False otherwise
        
        Example:
            >>> limiter = RateLimiter(RateLimitPolicy(requests_per_second=10.0))
            >>> if limiter.try_acquire():
            ...     make_api_call()
            ... else:
            ...     print("Rate limit exceeded")
        """
        if tokens <= 0:
            raise ValueError("tokens must be positive")
        
        with self._lock:
            self._refill_tokens()
            
            if self._tokens >= tokens:
                self._tokens -= tokens
                return True
            
            return False
    
    def acquire(self, tokens: float = 1.0) -> None:
        """
        Acquire tokens, waiting if necessary.
        
        Args:
            tokens: Number of tokens to acquire. Default: 1.0
        
        Raises:
            RateLimitExceeded: If policy.wait_on_limit=False and rate limit exceeded
        
        Example:
            >>> limiter = RateLimiter(RateLimitPolicy(requests_per_second=10.0))
            >>> limiter.acquire()  # Wait if necessary
            >>> make_api_call()
        """
        if tokens <= 0:
            raise ValueError("tokens must be positive")
        
        while True:
            with self._lock:
                self._refill_tokens()
                
                if self._tokens >= tokens:
                    self._tokens -= tokens
                    return
                
                # Check if we should wait or raise exception
                if not self.policy.wait_on_limit:
                    raise RateLimitExceeded(
                        f"Rate limit exceeded: {self.policy.requests_per_second} requests/sec"
                    )
                
                # Calculate wait time needed
                tokens_needed = tokens - self._tokens
                wait_time = tokens_needed / self.policy.requests_per_second
            
            # Call wait callback if provided
            if self.policy.on_wait is not None:
                try:
                    self.policy.on_wait(wait_time)
                except Exception:
                    # Don't let callback errors break rate limiting
                    pass
            
            # Wait for tokens to become available
            # Use small sleep to avoid busy-waiting
            time.sleep(min(wait_time, 0.1))
    
    def __enter__(self):
        """Context manager entry: acquire a token."""
        self.acquire()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit: nothing to do."""
        return False
    
    def reset(self) -> None:
        """
        Reset the rate limiter state.
        
        This immediately refills the bucket to capacity. Useful for testing
        or when rate limits are reset externally (e.g., API rate limit window resets).
        
        Example:
            >>> limiter = RateLimiter(RateLimitPolicy(requests_per_second=10.0))
            >>> limiter.reset()  # Start fresh
        """
        with self._lock:
            self._tokens = float(self.policy.burst_size)
            self._last_refill_time = time.time()
    
    def get_available_tokens(self) -> float:
        """
        Get the current number of available tokens.
        
        Returns:
            Current token count (may be fractional)
        
        Example:
            >>> limiter = RateLimiter(RateLimitPolicy(requests_per_second=10.0))
            >>> tokens = limiter.get_available_tokens()
            >>> print(f"{tokens:.1f} requests available")
        """
        with self._lock:
            self._refill_tokens()
            return self._tokens


class RateLimitExceeded(Exception):
    """
    Exception raised when rate limit is exceeded and wait_on_limit=False.
    
    This allows callers to handle rate limiting errors explicitly rather than
    automatically waiting.
    """
    pass


def with_rate_limit(
    func: Optional[Callable] = None,
    *,
    policy: Optional[RateLimitPolicy] = None,
    limiter: Optional[RateLimiter] = None,
    requests_per_second: float = 10.0,
    burst_size: Optional[int] = None,
    wait_on_limit: bool = True,
    on_wait: Optional[Callable[[float], None]] = None
) -> Callable:
    """
    Decorator to add rate limiting to a function.
    
    Can be used with or without parentheses:
        @with_rate_limit
        def func(): ...
        
        @with_rate_limit(requests_per_second=5.0)
        def func(): ...
    
    Args:
        func: Function to wrap (used when decorator is applied without parentheses)
        policy: Pre-configured RateLimitPolicy instance. If provided, other
               parameters are ignored. Default: None
        limiter: Pre-configured RateLimiter instance to share across multiple functions.
                If provided, policy parameters are ignored. Default: None
        requests_per_second: Maximum requests per second. Default: 10.0
        burst_size: Maximum burst size. Default: None (same as requests_per_second)
        wait_on_limit: Whether to wait when rate limited. Default: True
        on_wait: Optional callback when waiting. Default: None
    
    Returns:
        Decorated function with rate limiting
    
    Examples:
        >>> @with_rate_limit
        ... def fetch_data():
        ...     return requests.get("https://api.example.com/data").json()
        
        >>> @with_rate_limit(requests_per_second=5.0)
        ... def api_call(x):
        ...     return process_via_api(x)
        
        >>> # Share rate limiter across multiple functions
        >>> limiter = RateLimiter(RateLimitPolicy(requests_per_second=10.0))
        >>> @with_rate_limit(limiter=limiter)
        ... def func1(): ...
        >>> @with_rate_limit(limiter=limiter)
        ... def func2(): ...
    """
    # If used without parentheses (@with_rate_limit), func will be provided
    if func is not None:
        return _create_rate_limit_wrapper(func, RateLimiter(RateLimitPolicy()))
    
    # If limiter is provided, use it directly
    if limiter is not None:
        def decorator(f: Callable) -> Callable:
            return _create_rate_limit_wrapper(f, limiter)
        return decorator
    
    # If used with parentheses (@with_rate_limit(...)), create limiter and return decorator
    if policy is None:
        policy = RateLimitPolicy(
            requests_per_second=requests_per_second,
            burst_size=burst_size,
            wait_on_limit=wait_on_limit,
            on_wait=on_wait
        )
    
    rate_limiter = RateLimiter(policy)
    
    def decorator(f: Callable) -> Callable:
        return _create_rate_limit_wrapper(f, rate_limiter)
    
    return decorator


def _create_rate_limit_wrapper(func: Callable, limiter: RateLimiter) -> Callable:
    """
    Internal function to create the actual rate limit wrapper.
    
    Args:
        func: Function to wrap
        limiter: Rate limiter instance
    
    Returns:
        Wrapped function with rate limiting
    """
    @functools.wraps(func)
    def wrapper(*args: Any, **kwargs: Any) -> Any:
        limiter.acquire()
        return func(*args, **kwargs)
    
    # Attach limiter to wrapper for inspection/testing
    wrapper._rate_limiter = limiter
    
    return wrapper


def rate_limited_call(
    func: Callable,
    args: tuple = (),
    kwargs: Optional[dict] = None,
    policy: Optional[RateLimitPolicy] = None,
    **rate_limit_kwargs
) -> Any:
    """
    Execute a function with rate limiting without using a decorator.
    
    This is useful when you want to apply rate limiting to a function call
    without modifying the function itself.
    
    Args:
        func: Function to call
        args: Positional arguments to pass to func
        kwargs: Keyword arguments to pass to func
        policy: Pre-configured RateLimitPolicy. If None, create from rate_limit_kwargs
        **rate_limit_kwargs: Additional keyword arguments to create RateLimitPolicy
                           (requests_per_second, burst_size, etc.)
    
    Returns:
        Result of calling func(*args, **kwargs)
    
    Raises:
        RateLimitExceeded: If rate limit exceeded and wait_on_limit=False
    
    Examples:
        >>> # Rate limit a function call
        >>> result = rate_limited_call(fetch_data, requests_per_second=5.0)
        
        >>> # With arguments
        >>> result = rate_limited_call(
        ...     process_item,
        ...     args=(item,),
        ...     requests_per_second=10.0
        ... )
        
        >>> # With custom policy
        >>> policy = RateLimitPolicy(requests_per_second=5.0, burst_size=10)
        >>> result = rate_limited_call(api_call, policy=policy)
    """
    if kwargs is None:
        kwargs = {}
    
    if policy is None:
        policy = RateLimitPolicy(**rate_limit_kwargs)
    
    limiter = RateLimiter(policy)
    wrapped = _create_rate_limit_wrapper(func, limiter)
    return wrapped(*args, **kwargs)
