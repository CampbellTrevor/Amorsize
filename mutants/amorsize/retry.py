"""
Retry logic with exponential backoff for production reliability.

This module provides configurable retry logic to handle transient failures
such as network issues, temporary resource unavailability, or rate limiting.
"""

import functools
import random
import time
from dataclasses import dataclass
from typing import Any, Callable, Optional, Tuple, Type, Union
from inspect import signature as _mutmut_signature
from typing import Annotated
from typing import Callable
from typing import ClassVar


MutantDict = Annotated[dict[str, Callable], "Mutant"]


def _mutmut_trampoline(orig, mutants, call_args, call_kwargs, self_arg = None):
    """Forward call to original or mutated function, depending on the environment"""
    import os
    mutant_under_test = os.environ['MUTANT_UNDER_TEST']
    if mutant_under_test == 'fail':
        from mutmut.__main__ import MutmutProgrammaticFailException
        raise MutmutProgrammaticFailException('Failed programmatically')      
    elif mutant_under_test == 'stats':
        from mutmut.__main__ import record_trampoline_hit
        record_trampoline_hit(orig.__module__ + '.' + orig.__name__)
        result = orig(*call_args, **call_kwargs)
        return result
    prefix = orig.__module__ + '.' + orig.__name__ + '__mutmut_'
    if not mutant_under_test.startswith(prefix):
        result = orig(*call_args, **call_kwargs)
        return result
    mutant_name = mutant_under_test.rpartition('.')[-1]
    if self_arg is not None:
        # call to a class method where self is not bound
        result = mutants[mutant_name](self_arg, *call_args, **call_kwargs)
    else:
        result = mutants[mutant_name](*call_args, **call_kwargs)
    return result


@dataclass
class RetryPolicy:
    """
    Configuration for retry behavior with exponential backoff.
    
    Attributes:
        max_retries: Maximum number of retry attempts (0 = no retries, -1 = infinite).
                    Default: 3
        initial_delay: Initial delay between retries in seconds. Default: 0.1 (100ms)
        max_delay: Maximum delay between retries in seconds. Default: 60.0 (1 minute)
        exponential_base: Multiplier for exponential backoff. Default: 2.0 (doubles each time)
        jitter: Add random jitter to prevent thundering herd. If True, adds up to 25%
               random variation to delay. Default: True
        retry_on_exceptions: Tuple of exception types to retry on. If None, retries on
                           all exceptions. Default: None (retry all)
        on_retry: Optional callback function called on each retry attempt.
                 Receives (exception, attempt_number, delay) as arguments.
                 Default: None
    
    Example:
        >>> # Retry up to 3 times with exponential backoff
        >>> policy = RetryPolicy(max_retries=3, initial_delay=0.5)
        
        >>> # Retry only specific exceptions
        >>> policy = RetryPolicy(
        ...     max_retries=5,
        ...     retry_on_exceptions=(ConnectionError, TimeoutError)
        ... )
        
        >>> # Custom retry callback for logging
        >>> def log_retry(exc, attempt, delay):
        ...     print(f"Retry {attempt} after {delay:.2f}s due to {exc}")
        >>> policy = RetryPolicy(max_retries=3, on_retry=log_retry)
    """
    
    max_retries: int = 3
    initial_delay: float = 0.1
    max_delay: float = 60.0
    exponential_base: float = 2.0
    jitter: bool = True
    retry_on_exceptions: Optional[Tuple[Type[Exception], ...]] = None
    on_retry: Optional[Callable[[Exception, int, float], None]] = None
    
    def __post_init__(self):
        """Validate configuration parameters."""
        if self.max_retries < -1:
            raise ValueError("max_retries must be >= -1 (-1 for infinite, 0 for no retries)")
        if self.initial_delay <= 0:
            raise ValueError("initial_delay must be positive")
        if self.max_delay < self.initial_delay:
            raise ValueError("max_delay must be >= initial_delay")
        if self.exponential_base < 1.0:
            raise ValueError("exponential_base must be >= 1.0")
    
    def calculate_delay(self, attempt: int) -> float:
        """
        Calculate delay for the given retry attempt with exponential backoff.
        
        Args:
            attempt: The retry attempt number (1-indexed)
        
        Returns:
            Delay in seconds before the next retry attempt
        
        Formula:
            delay = min(initial_delay * (exponential_base ^ (attempt - 1)), max_delay)
            With optional jitter: delay * (1 ± random_factor)
        """
        # Calculate exponential delay
        delay = self.initial_delay * (self.exponential_base ** (attempt - 1))
        
        # Cap at max_delay
        delay = min(delay, self.max_delay)
        
        # Add jitter if enabled (±25% random variation)
        if self.jitter:
            jitter_factor = 1.0 + (random.random() - 0.5) * 0.5  # Range: [0.75, 1.25]
            delay *= jitter_factor
        
        return delay
    
    def should_retry(self, exception: Exception, attempt: int) -> bool:
        """
        Determine if we should retry after the given exception and attempt.
        
        Args:
            exception: The exception that was raised
            attempt: The current attempt number (1-indexed)
        
        Returns:
            True if we should retry, False otherwise
        """
        # Check if we've exceeded max retries
        if self.max_retries >= 0 and attempt > self.max_retries:
            return False
        
        # Check if exception type is retryable
        if self.retry_on_exceptions is not None:
            if not isinstance(exception, self.retry_on_exceptions):
                return False
        
        return True


def x_with_retry__mutmut_orig(
    func: Optional[Callable] = None,
    *,
    policy: Optional[RetryPolicy] = None,
    max_retries: int = 3,
    initial_delay: float = 0.1,
    max_delay: float = 60.0,
    exponential_base: float = 2.0,
    jitter: bool = True,
    retry_on_exceptions: Optional[Tuple[Type[Exception], ...]] = None,
    on_retry: Optional[Callable[[Exception, int, float], None]] = None
) -> Callable:
    """
    Decorator to add retry logic with exponential backoff to a function.
    
    Can be used with or without parentheses:
        @with_retry
        def func(): ...
        
        @with_retry(max_retries=5)
        def func(): ...
    
    Args:
        func: Function to wrap (used when decorator is applied without parentheses)
        policy: Pre-configured RetryPolicy instance. If provided, other parameters
               are ignored. Default: None
        max_retries: Maximum retry attempts. Default: 3
        initial_delay: Initial delay in seconds. Default: 0.1
        max_delay: Maximum delay in seconds. Default: 60.0
        exponential_base: Exponential backoff multiplier. Default: 2.0
        jitter: Whether to add random jitter. Default: True
        retry_on_exceptions: Tuple of exception types to retry on. Default: None (all)
        on_retry: Optional callback on retry. Default: None
    
    Returns:
        Decorated function with retry logic
    
    Examples:
        >>> @with_retry
        ... def fetch_data():
        ...     return requests.get("https://api.example.com/data").json()
        
        >>> @with_retry(max_retries=5, initial_delay=0.5)
        ... def process_with_retry(x):
        ...     return expensive_operation(x)
        
        >>> # With custom policy
        >>> policy = RetryPolicy(max_retries=3, retry_on_exceptions=(ConnectionError,))
        >>> @with_retry(policy=policy)
        ... def connect_to_service():
        ...     return connect()
    """
    # If used without parentheses (@with_retry), func will be provided
    if func is not None:
        return _create_retry_wrapper(func, RetryPolicy())
    
    # If used with parentheses (@with_retry(...)), create policy and return decorator
    if policy is None:
        policy = RetryPolicy(
            max_retries=max_retries,
            initial_delay=initial_delay,
            max_delay=max_delay,
            exponential_base=exponential_base,
            jitter=jitter,
            retry_on_exceptions=retry_on_exceptions,
            on_retry=on_retry
        )
    
    def decorator(f: Callable) -> Callable:
        return _create_retry_wrapper(f, policy)
    
    return decorator


def x_with_retry__mutmut_1(
    func: Optional[Callable] = None,
    *,
    policy: Optional[RetryPolicy] = None,
    max_retries: int = 4,
    initial_delay: float = 0.1,
    max_delay: float = 60.0,
    exponential_base: float = 2.0,
    jitter: bool = True,
    retry_on_exceptions: Optional[Tuple[Type[Exception], ...]] = None,
    on_retry: Optional[Callable[[Exception, int, float], None]] = None
) -> Callable:
    """
    Decorator to add retry logic with exponential backoff to a function.
    
    Can be used with or without parentheses:
        @with_retry
        def func(): ...
        
        @with_retry(max_retries=5)
        def func(): ...
    
    Args:
        func: Function to wrap (used when decorator is applied without parentheses)
        policy: Pre-configured RetryPolicy instance. If provided, other parameters
               are ignored. Default: None
        max_retries: Maximum retry attempts. Default: 3
        initial_delay: Initial delay in seconds. Default: 0.1
        max_delay: Maximum delay in seconds. Default: 60.0
        exponential_base: Exponential backoff multiplier. Default: 2.0
        jitter: Whether to add random jitter. Default: True
        retry_on_exceptions: Tuple of exception types to retry on. Default: None (all)
        on_retry: Optional callback on retry. Default: None
    
    Returns:
        Decorated function with retry logic
    
    Examples:
        >>> @with_retry
        ... def fetch_data():
        ...     return requests.get("https://api.example.com/data").json()
        
        >>> @with_retry(max_retries=5, initial_delay=0.5)
        ... def process_with_retry(x):
        ...     return expensive_operation(x)
        
        >>> # With custom policy
        >>> policy = RetryPolicy(max_retries=3, retry_on_exceptions=(ConnectionError,))
        >>> @with_retry(policy=policy)
        ... def connect_to_service():
        ...     return connect()
    """
    # If used without parentheses (@with_retry), func will be provided
    if func is not None:
        return _create_retry_wrapper(func, RetryPolicy())
    
    # If used with parentheses (@with_retry(...)), create policy and return decorator
    if policy is None:
        policy = RetryPolicy(
            max_retries=max_retries,
            initial_delay=initial_delay,
            max_delay=max_delay,
            exponential_base=exponential_base,
            jitter=jitter,
            retry_on_exceptions=retry_on_exceptions,
            on_retry=on_retry
        )
    
    def decorator(f: Callable) -> Callable:
        return _create_retry_wrapper(f, policy)
    
    return decorator


def x_with_retry__mutmut_2(
    func: Optional[Callable] = None,
    *,
    policy: Optional[RetryPolicy] = None,
    max_retries: int = 3,
    initial_delay: float = 1.1,
    max_delay: float = 60.0,
    exponential_base: float = 2.0,
    jitter: bool = True,
    retry_on_exceptions: Optional[Tuple[Type[Exception], ...]] = None,
    on_retry: Optional[Callable[[Exception, int, float], None]] = None
) -> Callable:
    """
    Decorator to add retry logic with exponential backoff to a function.
    
    Can be used with or without parentheses:
        @with_retry
        def func(): ...
        
        @with_retry(max_retries=5)
        def func(): ...
    
    Args:
        func: Function to wrap (used when decorator is applied without parentheses)
        policy: Pre-configured RetryPolicy instance. If provided, other parameters
               are ignored. Default: None
        max_retries: Maximum retry attempts. Default: 3
        initial_delay: Initial delay in seconds. Default: 0.1
        max_delay: Maximum delay in seconds. Default: 60.0
        exponential_base: Exponential backoff multiplier. Default: 2.0
        jitter: Whether to add random jitter. Default: True
        retry_on_exceptions: Tuple of exception types to retry on. Default: None (all)
        on_retry: Optional callback on retry. Default: None
    
    Returns:
        Decorated function with retry logic
    
    Examples:
        >>> @with_retry
        ... def fetch_data():
        ...     return requests.get("https://api.example.com/data").json()
        
        >>> @with_retry(max_retries=5, initial_delay=0.5)
        ... def process_with_retry(x):
        ...     return expensive_operation(x)
        
        >>> # With custom policy
        >>> policy = RetryPolicy(max_retries=3, retry_on_exceptions=(ConnectionError,))
        >>> @with_retry(policy=policy)
        ... def connect_to_service():
        ...     return connect()
    """
    # If used without parentheses (@with_retry), func will be provided
    if func is not None:
        return _create_retry_wrapper(func, RetryPolicy())
    
    # If used with parentheses (@with_retry(...)), create policy and return decorator
    if policy is None:
        policy = RetryPolicy(
            max_retries=max_retries,
            initial_delay=initial_delay,
            max_delay=max_delay,
            exponential_base=exponential_base,
            jitter=jitter,
            retry_on_exceptions=retry_on_exceptions,
            on_retry=on_retry
        )
    
    def decorator(f: Callable) -> Callable:
        return _create_retry_wrapper(f, policy)
    
    return decorator


def x_with_retry__mutmut_3(
    func: Optional[Callable] = None,
    *,
    policy: Optional[RetryPolicy] = None,
    max_retries: int = 3,
    initial_delay: float = 0.1,
    max_delay: float = 61.0,
    exponential_base: float = 2.0,
    jitter: bool = True,
    retry_on_exceptions: Optional[Tuple[Type[Exception], ...]] = None,
    on_retry: Optional[Callable[[Exception, int, float], None]] = None
) -> Callable:
    """
    Decorator to add retry logic with exponential backoff to a function.
    
    Can be used with or without parentheses:
        @with_retry
        def func(): ...
        
        @with_retry(max_retries=5)
        def func(): ...
    
    Args:
        func: Function to wrap (used when decorator is applied without parentheses)
        policy: Pre-configured RetryPolicy instance. If provided, other parameters
               are ignored. Default: None
        max_retries: Maximum retry attempts. Default: 3
        initial_delay: Initial delay in seconds. Default: 0.1
        max_delay: Maximum delay in seconds. Default: 60.0
        exponential_base: Exponential backoff multiplier. Default: 2.0
        jitter: Whether to add random jitter. Default: True
        retry_on_exceptions: Tuple of exception types to retry on. Default: None (all)
        on_retry: Optional callback on retry. Default: None
    
    Returns:
        Decorated function with retry logic
    
    Examples:
        >>> @with_retry
        ... def fetch_data():
        ...     return requests.get("https://api.example.com/data").json()
        
        >>> @with_retry(max_retries=5, initial_delay=0.5)
        ... def process_with_retry(x):
        ...     return expensive_operation(x)
        
        >>> # With custom policy
        >>> policy = RetryPolicy(max_retries=3, retry_on_exceptions=(ConnectionError,))
        >>> @with_retry(policy=policy)
        ... def connect_to_service():
        ...     return connect()
    """
    # If used without parentheses (@with_retry), func will be provided
    if func is not None:
        return _create_retry_wrapper(func, RetryPolicy())
    
    # If used with parentheses (@with_retry(...)), create policy and return decorator
    if policy is None:
        policy = RetryPolicy(
            max_retries=max_retries,
            initial_delay=initial_delay,
            max_delay=max_delay,
            exponential_base=exponential_base,
            jitter=jitter,
            retry_on_exceptions=retry_on_exceptions,
            on_retry=on_retry
        )
    
    def decorator(f: Callable) -> Callable:
        return _create_retry_wrapper(f, policy)
    
    return decorator


def x_with_retry__mutmut_4(
    func: Optional[Callable] = None,
    *,
    policy: Optional[RetryPolicy] = None,
    max_retries: int = 3,
    initial_delay: float = 0.1,
    max_delay: float = 60.0,
    exponential_base: float = 3.0,
    jitter: bool = True,
    retry_on_exceptions: Optional[Tuple[Type[Exception], ...]] = None,
    on_retry: Optional[Callable[[Exception, int, float], None]] = None
) -> Callable:
    """
    Decorator to add retry logic with exponential backoff to a function.
    
    Can be used with or without parentheses:
        @with_retry
        def func(): ...
        
        @with_retry(max_retries=5)
        def func(): ...
    
    Args:
        func: Function to wrap (used when decorator is applied without parentheses)
        policy: Pre-configured RetryPolicy instance. If provided, other parameters
               are ignored. Default: None
        max_retries: Maximum retry attempts. Default: 3
        initial_delay: Initial delay in seconds. Default: 0.1
        max_delay: Maximum delay in seconds. Default: 60.0
        exponential_base: Exponential backoff multiplier. Default: 2.0
        jitter: Whether to add random jitter. Default: True
        retry_on_exceptions: Tuple of exception types to retry on. Default: None (all)
        on_retry: Optional callback on retry. Default: None
    
    Returns:
        Decorated function with retry logic
    
    Examples:
        >>> @with_retry
        ... def fetch_data():
        ...     return requests.get("https://api.example.com/data").json()
        
        >>> @with_retry(max_retries=5, initial_delay=0.5)
        ... def process_with_retry(x):
        ...     return expensive_operation(x)
        
        >>> # With custom policy
        >>> policy = RetryPolicy(max_retries=3, retry_on_exceptions=(ConnectionError,))
        >>> @with_retry(policy=policy)
        ... def connect_to_service():
        ...     return connect()
    """
    # If used without parentheses (@with_retry), func will be provided
    if func is not None:
        return _create_retry_wrapper(func, RetryPolicy())
    
    # If used with parentheses (@with_retry(...)), create policy and return decorator
    if policy is None:
        policy = RetryPolicy(
            max_retries=max_retries,
            initial_delay=initial_delay,
            max_delay=max_delay,
            exponential_base=exponential_base,
            jitter=jitter,
            retry_on_exceptions=retry_on_exceptions,
            on_retry=on_retry
        )
    
    def decorator(f: Callable) -> Callable:
        return _create_retry_wrapper(f, policy)
    
    return decorator


def x_with_retry__mutmut_5(
    func: Optional[Callable] = None,
    *,
    policy: Optional[RetryPolicy] = None,
    max_retries: int = 3,
    initial_delay: float = 0.1,
    max_delay: float = 60.0,
    exponential_base: float = 2.0,
    jitter: bool = False,
    retry_on_exceptions: Optional[Tuple[Type[Exception], ...]] = None,
    on_retry: Optional[Callable[[Exception, int, float], None]] = None
) -> Callable:
    """
    Decorator to add retry logic with exponential backoff to a function.
    
    Can be used with or without parentheses:
        @with_retry
        def func(): ...
        
        @with_retry(max_retries=5)
        def func(): ...
    
    Args:
        func: Function to wrap (used when decorator is applied without parentheses)
        policy: Pre-configured RetryPolicy instance. If provided, other parameters
               are ignored. Default: None
        max_retries: Maximum retry attempts. Default: 3
        initial_delay: Initial delay in seconds. Default: 0.1
        max_delay: Maximum delay in seconds. Default: 60.0
        exponential_base: Exponential backoff multiplier. Default: 2.0
        jitter: Whether to add random jitter. Default: True
        retry_on_exceptions: Tuple of exception types to retry on. Default: None (all)
        on_retry: Optional callback on retry. Default: None
    
    Returns:
        Decorated function with retry logic
    
    Examples:
        >>> @with_retry
        ... def fetch_data():
        ...     return requests.get("https://api.example.com/data").json()
        
        >>> @with_retry(max_retries=5, initial_delay=0.5)
        ... def process_with_retry(x):
        ...     return expensive_operation(x)
        
        >>> # With custom policy
        >>> policy = RetryPolicy(max_retries=3, retry_on_exceptions=(ConnectionError,))
        >>> @with_retry(policy=policy)
        ... def connect_to_service():
        ...     return connect()
    """
    # If used without parentheses (@with_retry), func will be provided
    if func is not None:
        return _create_retry_wrapper(func, RetryPolicy())
    
    # If used with parentheses (@with_retry(...)), create policy and return decorator
    if policy is None:
        policy = RetryPolicy(
            max_retries=max_retries,
            initial_delay=initial_delay,
            max_delay=max_delay,
            exponential_base=exponential_base,
            jitter=jitter,
            retry_on_exceptions=retry_on_exceptions,
            on_retry=on_retry
        )
    
    def decorator(f: Callable) -> Callable:
        return _create_retry_wrapper(f, policy)
    
    return decorator


def x_with_retry__mutmut_6(
    func: Optional[Callable] = None,
    *,
    policy: Optional[RetryPolicy] = None,
    max_retries: int = 3,
    initial_delay: float = 0.1,
    max_delay: float = 60.0,
    exponential_base: float = 2.0,
    jitter: bool = True,
    retry_on_exceptions: Optional[Tuple[Type[Exception], ...]] = None,
    on_retry: Optional[Callable[[Exception, int, float], None]] = None
) -> Callable:
    """
    Decorator to add retry logic with exponential backoff to a function.
    
    Can be used with or without parentheses:
        @with_retry
        def func(): ...
        
        @with_retry(max_retries=5)
        def func(): ...
    
    Args:
        func: Function to wrap (used when decorator is applied without parentheses)
        policy: Pre-configured RetryPolicy instance. If provided, other parameters
               are ignored. Default: None
        max_retries: Maximum retry attempts. Default: 3
        initial_delay: Initial delay in seconds. Default: 0.1
        max_delay: Maximum delay in seconds. Default: 60.0
        exponential_base: Exponential backoff multiplier. Default: 2.0
        jitter: Whether to add random jitter. Default: True
        retry_on_exceptions: Tuple of exception types to retry on. Default: None (all)
        on_retry: Optional callback on retry. Default: None
    
    Returns:
        Decorated function with retry logic
    
    Examples:
        >>> @with_retry
        ... def fetch_data():
        ...     return requests.get("https://api.example.com/data").json()
        
        >>> @with_retry(max_retries=5, initial_delay=0.5)
        ... def process_with_retry(x):
        ...     return expensive_operation(x)
        
        >>> # With custom policy
        >>> policy = RetryPolicy(max_retries=3, retry_on_exceptions=(ConnectionError,))
        >>> @with_retry(policy=policy)
        ... def connect_to_service():
        ...     return connect()
    """
    # If used without parentheses (@with_retry), func will be provided
    if func is None:
        return _create_retry_wrapper(func, RetryPolicy())
    
    # If used with parentheses (@with_retry(...)), create policy and return decorator
    if policy is None:
        policy = RetryPolicy(
            max_retries=max_retries,
            initial_delay=initial_delay,
            max_delay=max_delay,
            exponential_base=exponential_base,
            jitter=jitter,
            retry_on_exceptions=retry_on_exceptions,
            on_retry=on_retry
        )
    
    def decorator(f: Callable) -> Callable:
        return _create_retry_wrapper(f, policy)
    
    return decorator


def x_with_retry__mutmut_7(
    func: Optional[Callable] = None,
    *,
    policy: Optional[RetryPolicy] = None,
    max_retries: int = 3,
    initial_delay: float = 0.1,
    max_delay: float = 60.0,
    exponential_base: float = 2.0,
    jitter: bool = True,
    retry_on_exceptions: Optional[Tuple[Type[Exception], ...]] = None,
    on_retry: Optional[Callable[[Exception, int, float], None]] = None
) -> Callable:
    """
    Decorator to add retry logic with exponential backoff to a function.
    
    Can be used with or without parentheses:
        @with_retry
        def func(): ...
        
        @with_retry(max_retries=5)
        def func(): ...
    
    Args:
        func: Function to wrap (used when decorator is applied without parentheses)
        policy: Pre-configured RetryPolicy instance. If provided, other parameters
               are ignored. Default: None
        max_retries: Maximum retry attempts. Default: 3
        initial_delay: Initial delay in seconds. Default: 0.1
        max_delay: Maximum delay in seconds. Default: 60.0
        exponential_base: Exponential backoff multiplier. Default: 2.0
        jitter: Whether to add random jitter. Default: True
        retry_on_exceptions: Tuple of exception types to retry on. Default: None (all)
        on_retry: Optional callback on retry. Default: None
    
    Returns:
        Decorated function with retry logic
    
    Examples:
        >>> @with_retry
        ... def fetch_data():
        ...     return requests.get("https://api.example.com/data").json()
        
        >>> @with_retry(max_retries=5, initial_delay=0.5)
        ... def process_with_retry(x):
        ...     return expensive_operation(x)
        
        >>> # With custom policy
        >>> policy = RetryPolicy(max_retries=3, retry_on_exceptions=(ConnectionError,))
        >>> @with_retry(policy=policy)
        ... def connect_to_service():
        ...     return connect()
    """
    # If used without parentheses (@with_retry), func will be provided
    if func is not None:
        return _create_retry_wrapper(None, RetryPolicy())
    
    # If used with parentheses (@with_retry(...)), create policy and return decorator
    if policy is None:
        policy = RetryPolicy(
            max_retries=max_retries,
            initial_delay=initial_delay,
            max_delay=max_delay,
            exponential_base=exponential_base,
            jitter=jitter,
            retry_on_exceptions=retry_on_exceptions,
            on_retry=on_retry
        )
    
    def decorator(f: Callable) -> Callable:
        return _create_retry_wrapper(f, policy)
    
    return decorator


def x_with_retry__mutmut_8(
    func: Optional[Callable] = None,
    *,
    policy: Optional[RetryPolicy] = None,
    max_retries: int = 3,
    initial_delay: float = 0.1,
    max_delay: float = 60.0,
    exponential_base: float = 2.0,
    jitter: bool = True,
    retry_on_exceptions: Optional[Tuple[Type[Exception], ...]] = None,
    on_retry: Optional[Callable[[Exception, int, float], None]] = None
) -> Callable:
    """
    Decorator to add retry logic with exponential backoff to a function.
    
    Can be used with or without parentheses:
        @with_retry
        def func(): ...
        
        @with_retry(max_retries=5)
        def func(): ...
    
    Args:
        func: Function to wrap (used when decorator is applied without parentheses)
        policy: Pre-configured RetryPolicy instance. If provided, other parameters
               are ignored. Default: None
        max_retries: Maximum retry attempts. Default: 3
        initial_delay: Initial delay in seconds. Default: 0.1
        max_delay: Maximum delay in seconds. Default: 60.0
        exponential_base: Exponential backoff multiplier. Default: 2.0
        jitter: Whether to add random jitter. Default: True
        retry_on_exceptions: Tuple of exception types to retry on. Default: None (all)
        on_retry: Optional callback on retry. Default: None
    
    Returns:
        Decorated function with retry logic
    
    Examples:
        >>> @with_retry
        ... def fetch_data():
        ...     return requests.get("https://api.example.com/data").json()
        
        >>> @with_retry(max_retries=5, initial_delay=0.5)
        ... def process_with_retry(x):
        ...     return expensive_operation(x)
        
        >>> # With custom policy
        >>> policy = RetryPolicy(max_retries=3, retry_on_exceptions=(ConnectionError,))
        >>> @with_retry(policy=policy)
        ... def connect_to_service():
        ...     return connect()
    """
    # If used without parentheses (@with_retry), func will be provided
    if func is not None:
        return _create_retry_wrapper(func, None)
    
    # If used with parentheses (@with_retry(...)), create policy and return decorator
    if policy is None:
        policy = RetryPolicy(
            max_retries=max_retries,
            initial_delay=initial_delay,
            max_delay=max_delay,
            exponential_base=exponential_base,
            jitter=jitter,
            retry_on_exceptions=retry_on_exceptions,
            on_retry=on_retry
        )
    
    def decorator(f: Callable) -> Callable:
        return _create_retry_wrapper(f, policy)
    
    return decorator


def x_with_retry__mutmut_9(
    func: Optional[Callable] = None,
    *,
    policy: Optional[RetryPolicy] = None,
    max_retries: int = 3,
    initial_delay: float = 0.1,
    max_delay: float = 60.0,
    exponential_base: float = 2.0,
    jitter: bool = True,
    retry_on_exceptions: Optional[Tuple[Type[Exception], ...]] = None,
    on_retry: Optional[Callable[[Exception, int, float], None]] = None
) -> Callable:
    """
    Decorator to add retry logic with exponential backoff to a function.
    
    Can be used with or without parentheses:
        @with_retry
        def func(): ...
        
        @with_retry(max_retries=5)
        def func(): ...
    
    Args:
        func: Function to wrap (used when decorator is applied without parentheses)
        policy: Pre-configured RetryPolicy instance. If provided, other parameters
               are ignored. Default: None
        max_retries: Maximum retry attempts. Default: 3
        initial_delay: Initial delay in seconds. Default: 0.1
        max_delay: Maximum delay in seconds. Default: 60.0
        exponential_base: Exponential backoff multiplier. Default: 2.0
        jitter: Whether to add random jitter. Default: True
        retry_on_exceptions: Tuple of exception types to retry on. Default: None (all)
        on_retry: Optional callback on retry. Default: None
    
    Returns:
        Decorated function with retry logic
    
    Examples:
        >>> @with_retry
        ... def fetch_data():
        ...     return requests.get("https://api.example.com/data").json()
        
        >>> @with_retry(max_retries=5, initial_delay=0.5)
        ... def process_with_retry(x):
        ...     return expensive_operation(x)
        
        >>> # With custom policy
        >>> policy = RetryPolicy(max_retries=3, retry_on_exceptions=(ConnectionError,))
        >>> @with_retry(policy=policy)
        ... def connect_to_service():
        ...     return connect()
    """
    # If used without parentheses (@with_retry), func will be provided
    if func is not None:
        return _create_retry_wrapper(RetryPolicy())
    
    # If used with parentheses (@with_retry(...)), create policy and return decorator
    if policy is None:
        policy = RetryPolicy(
            max_retries=max_retries,
            initial_delay=initial_delay,
            max_delay=max_delay,
            exponential_base=exponential_base,
            jitter=jitter,
            retry_on_exceptions=retry_on_exceptions,
            on_retry=on_retry
        )
    
    def decorator(f: Callable) -> Callable:
        return _create_retry_wrapper(f, policy)
    
    return decorator


def x_with_retry__mutmut_10(
    func: Optional[Callable] = None,
    *,
    policy: Optional[RetryPolicy] = None,
    max_retries: int = 3,
    initial_delay: float = 0.1,
    max_delay: float = 60.0,
    exponential_base: float = 2.0,
    jitter: bool = True,
    retry_on_exceptions: Optional[Tuple[Type[Exception], ...]] = None,
    on_retry: Optional[Callable[[Exception, int, float], None]] = None
) -> Callable:
    """
    Decorator to add retry logic with exponential backoff to a function.
    
    Can be used with or without parentheses:
        @with_retry
        def func(): ...
        
        @with_retry(max_retries=5)
        def func(): ...
    
    Args:
        func: Function to wrap (used when decorator is applied without parentheses)
        policy: Pre-configured RetryPolicy instance. If provided, other parameters
               are ignored. Default: None
        max_retries: Maximum retry attempts. Default: 3
        initial_delay: Initial delay in seconds. Default: 0.1
        max_delay: Maximum delay in seconds. Default: 60.0
        exponential_base: Exponential backoff multiplier. Default: 2.0
        jitter: Whether to add random jitter. Default: True
        retry_on_exceptions: Tuple of exception types to retry on. Default: None (all)
        on_retry: Optional callback on retry. Default: None
    
    Returns:
        Decorated function with retry logic
    
    Examples:
        >>> @with_retry
        ... def fetch_data():
        ...     return requests.get("https://api.example.com/data").json()
        
        >>> @with_retry(max_retries=5, initial_delay=0.5)
        ... def process_with_retry(x):
        ...     return expensive_operation(x)
        
        >>> # With custom policy
        >>> policy = RetryPolicy(max_retries=3, retry_on_exceptions=(ConnectionError,))
        >>> @with_retry(policy=policy)
        ... def connect_to_service():
        ...     return connect()
    """
    # If used without parentheses (@with_retry), func will be provided
    if func is not None:
        return _create_retry_wrapper(func, )
    
    # If used with parentheses (@with_retry(...)), create policy and return decorator
    if policy is None:
        policy = RetryPolicy(
            max_retries=max_retries,
            initial_delay=initial_delay,
            max_delay=max_delay,
            exponential_base=exponential_base,
            jitter=jitter,
            retry_on_exceptions=retry_on_exceptions,
            on_retry=on_retry
        )
    
    def decorator(f: Callable) -> Callable:
        return _create_retry_wrapper(f, policy)
    
    return decorator


def x_with_retry__mutmut_11(
    func: Optional[Callable] = None,
    *,
    policy: Optional[RetryPolicy] = None,
    max_retries: int = 3,
    initial_delay: float = 0.1,
    max_delay: float = 60.0,
    exponential_base: float = 2.0,
    jitter: bool = True,
    retry_on_exceptions: Optional[Tuple[Type[Exception], ...]] = None,
    on_retry: Optional[Callable[[Exception, int, float], None]] = None
) -> Callable:
    """
    Decorator to add retry logic with exponential backoff to a function.
    
    Can be used with or without parentheses:
        @with_retry
        def func(): ...
        
        @with_retry(max_retries=5)
        def func(): ...
    
    Args:
        func: Function to wrap (used when decorator is applied without parentheses)
        policy: Pre-configured RetryPolicy instance. If provided, other parameters
               are ignored. Default: None
        max_retries: Maximum retry attempts. Default: 3
        initial_delay: Initial delay in seconds. Default: 0.1
        max_delay: Maximum delay in seconds. Default: 60.0
        exponential_base: Exponential backoff multiplier. Default: 2.0
        jitter: Whether to add random jitter. Default: True
        retry_on_exceptions: Tuple of exception types to retry on. Default: None (all)
        on_retry: Optional callback on retry. Default: None
    
    Returns:
        Decorated function with retry logic
    
    Examples:
        >>> @with_retry
        ... def fetch_data():
        ...     return requests.get("https://api.example.com/data").json()
        
        >>> @with_retry(max_retries=5, initial_delay=0.5)
        ... def process_with_retry(x):
        ...     return expensive_operation(x)
        
        >>> # With custom policy
        >>> policy = RetryPolicy(max_retries=3, retry_on_exceptions=(ConnectionError,))
        >>> @with_retry(policy=policy)
        ... def connect_to_service():
        ...     return connect()
    """
    # If used without parentheses (@with_retry), func will be provided
    if func is not None:
        return _create_retry_wrapper(func, RetryPolicy())
    
    # If used with parentheses (@with_retry(...)), create policy and return decorator
    if policy is not None:
        policy = RetryPolicy(
            max_retries=max_retries,
            initial_delay=initial_delay,
            max_delay=max_delay,
            exponential_base=exponential_base,
            jitter=jitter,
            retry_on_exceptions=retry_on_exceptions,
            on_retry=on_retry
        )
    
    def decorator(f: Callable) -> Callable:
        return _create_retry_wrapper(f, policy)
    
    return decorator


def x_with_retry__mutmut_12(
    func: Optional[Callable] = None,
    *,
    policy: Optional[RetryPolicy] = None,
    max_retries: int = 3,
    initial_delay: float = 0.1,
    max_delay: float = 60.0,
    exponential_base: float = 2.0,
    jitter: bool = True,
    retry_on_exceptions: Optional[Tuple[Type[Exception], ...]] = None,
    on_retry: Optional[Callable[[Exception, int, float], None]] = None
) -> Callable:
    """
    Decorator to add retry logic with exponential backoff to a function.
    
    Can be used with or without parentheses:
        @with_retry
        def func(): ...
        
        @with_retry(max_retries=5)
        def func(): ...
    
    Args:
        func: Function to wrap (used when decorator is applied without parentheses)
        policy: Pre-configured RetryPolicy instance. If provided, other parameters
               are ignored. Default: None
        max_retries: Maximum retry attempts. Default: 3
        initial_delay: Initial delay in seconds. Default: 0.1
        max_delay: Maximum delay in seconds. Default: 60.0
        exponential_base: Exponential backoff multiplier. Default: 2.0
        jitter: Whether to add random jitter. Default: True
        retry_on_exceptions: Tuple of exception types to retry on. Default: None (all)
        on_retry: Optional callback on retry. Default: None
    
    Returns:
        Decorated function with retry logic
    
    Examples:
        >>> @with_retry
        ... def fetch_data():
        ...     return requests.get("https://api.example.com/data").json()
        
        >>> @with_retry(max_retries=5, initial_delay=0.5)
        ... def process_with_retry(x):
        ...     return expensive_operation(x)
        
        >>> # With custom policy
        >>> policy = RetryPolicy(max_retries=3, retry_on_exceptions=(ConnectionError,))
        >>> @with_retry(policy=policy)
        ... def connect_to_service():
        ...     return connect()
    """
    # If used without parentheses (@with_retry), func will be provided
    if func is not None:
        return _create_retry_wrapper(func, RetryPolicy())
    
    # If used with parentheses (@with_retry(...)), create policy and return decorator
    if policy is None:
        policy = None
    
    def decorator(f: Callable) -> Callable:
        return _create_retry_wrapper(f, policy)
    
    return decorator


def x_with_retry__mutmut_13(
    func: Optional[Callable] = None,
    *,
    policy: Optional[RetryPolicy] = None,
    max_retries: int = 3,
    initial_delay: float = 0.1,
    max_delay: float = 60.0,
    exponential_base: float = 2.0,
    jitter: bool = True,
    retry_on_exceptions: Optional[Tuple[Type[Exception], ...]] = None,
    on_retry: Optional[Callable[[Exception, int, float], None]] = None
) -> Callable:
    """
    Decorator to add retry logic with exponential backoff to a function.
    
    Can be used with or without parentheses:
        @with_retry
        def func(): ...
        
        @with_retry(max_retries=5)
        def func(): ...
    
    Args:
        func: Function to wrap (used when decorator is applied without parentheses)
        policy: Pre-configured RetryPolicy instance. If provided, other parameters
               are ignored. Default: None
        max_retries: Maximum retry attempts. Default: 3
        initial_delay: Initial delay in seconds. Default: 0.1
        max_delay: Maximum delay in seconds. Default: 60.0
        exponential_base: Exponential backoff multiplier. Default: 2.0
        jitter: Whether to add random jitter. Default: True
        retry_on_exceptions: Tuple of exception types to retry on. Default: None (all)
        on_retry: Optional callback on retry. Default: None
    
    Returns:
        Decorated function with retry logic
    
    Examples:
        >>> @with_retry
        ... def fetch_data():
        ...     return requests.get("https://api.example.com/data").json()
        
        >>> @with_retry(max_retries=5, initial_delay=0.5)
        ... def process_with_retry(x):
        ...     return expensive_operation(x)
        
        >>> # With custom policy
        >>> policy = RetryPolicy(max_retries=3, retry_on_exceptions=(ConnectionError,))
        >>> @with_retry(policy=policy)
        ... def connect_to_service():
        ...     return connect()
    """
    # If used without parentheses (@with_retry), func will be provided
    if func is not None:
        return _create_retry_wrapper(func, RetryPolicy())
    
    # If used with parentheses (@with_retry(...)), create policy and return decorator
    if policy is None:
        policy = RetryPolicy(
            max_retries=None,
            initial_delay=initial_delay,
            max_delay=max_delay,
            exponential_base=exponential_base,
            jitter=jitter,
            retry_on_exceptions=retry_on_exceptions,
            on_retry=on_retry
        )
    
    def decorator(f: Callable) -> Callable:
        return _create_retry_wrapper(f, policy)
    
    return decorator


def x_with_retry__mutmut_14(
    func: Optional[Callable] = None,
    *,
    policy: Optional[RetryPolicy] = None,
    max_retries: int = 3,
    initial_delay: float = 0.1,
    max_delay: float = 60.0,
    exponential_base: float = 2.0,
    jitter: bool = True,
    retry_on_exceptions: Optional[Tuple[Type[Exception], ...]] = None,
    on_retry: Optional[Callable[[Exception, int, float], None]] = None
) -> Callable:
    """
    Decorator to add retry logic with exponential backoff to a function.
    
    Can be used with or without parentheses:
        @with_retry
        def func(): ...
        
        @with_retry(max_retries=5)
        def func(): ...
    
    Args:
        func: Function to wrap (used when decorator is applied without parentheses)
        policy: Pre-configured RetryPolicy instance. If provided, other parameters
               are ignored. Default: None
        max_retries: Maximum retry attempts. Default: 3
        initial_delay: Initial delay in seconds. Default: 0.1
        max_delay: Maximum delay in seconds. Default: 60.0
        exponential_base: Exponential backoff multiplier. Default: 2.0
        jitter: Whether to add random jitter. Default: True
        retry_on_exceptions: Tuple of exception types to retry on. Default: None (all)
        on_retry: Optional callback on retry. Default: None
    
    Returns:
        Decorated function with retry logic
    
    Examples:
        >>> @with_retry
        ... def fetch_data():
        ...     return requests.get("https://api.example.com/data").json()
        
        >>> @with_retry(max_retries=5, initial_delay=0.5)
        ... def process_with_retry(x):
        ...     return expensive_operation(x)
        
        >>> # With custom policy
        >>> policy = RetryPolicy(max_retries=3, retry_on_exceptions=(ConnectionError,))
        >>> @with_retry(policy=policy)
        ... def connect_to_service():
        ...     return connect()
    """
    # If used without parentheses (@with_retry), func will be provided
    if func is not None:
        return _create_retry_wrapper(func, RetryPolicy())
    
    # If used with parentheses (@with_retry(...)), create policy and return decorator
    if policy is None:
        policy = RetryPolicy(
            max_retries=max_retries,
            initial_delay=None,
            max_delay=max_delay,
            exponential_base=exponential_base,
            jitter=jitter,
            retry_on_exceptions=retry_on_exceptions,
            on_retry=on_retry
        )
    
    def decorator(f: Callable) -> Callable:
        return _create_retry_wrapper(f, policy)
    
    return decorator


def x_with_retry__mutmut_15(
    func: Optional[Callable] = None,
    *,
    policy: Optional[RetryPolicy] = None,
    max_retries: int = 3,
    initial_delay: float = 0.1,
    max_delay: float = 60.0,
    exponential_base: float = 2.0,
    jitter: bool = True,
    retry_on_exceptions: Optional[Tuple[Type[Exception], ...]] = None,
    on_retry: Optional[Callable[[Exception, int, float], None]] = None
) -> Callable:
    """
    Decorator to add retry logic with exponential backoff to a function.
    
    Can be used with or without parentheses:
        @with_retry
        def func(): ...
        
        @with_retry(max_retries=5)
        def func(): ...
    
    Args:
        func: Function to wrap (used when decorator is applied without parentheses)
        policy: Pre-configured RetryPolicy instance. If provided, other parameters
               are ignored. Default: None
        max_retries: Maximum retry attempts. Default: 3
        initial_delay: Initial delay in seconds. Default: 0.1
        max_delay: Maximum delay in seconds. Default: 60.0
        exponential_base: Exponential backoff multiplier. Default: 2.0
        jitter: Whether to add random jitter. Default: True
        retry_on_exceptions: Tuple of exception types to retry on. Default: None (all)
        on_retry: Optional callback on retry. Default: None
    
    Returns:
        Decorated function with retry logic
    
    Examples:
        >>> @with_retry
        ... def fetch_data():
        ...     return requests.get("https://api.example.com/data").json()
        
        >>> @with_retry(max_retries=5, initial_delay=0.5)
        ... def process_with_retry(x):
        ...     return expensive_operation(x)
        
        >>> # With custom policy
        >>> policy = RetryPolicy(max_retries=3, retry_on_exceptions=(ConnectionError,))
        >>> @with_retry(policy=policy)
        ... def connect_to_service():
        ...     return connect()
    """
    # If used without parentheses (@with_retry), func will be provided
    if func is not None:
        return _create_retry_wrapper(func, RetryPolicy())
    
    # If used with parentheses (@with_retry(...)), create policy and return decorator
    if policy is None:
        policy = RetryPolicy(
            max_retries=max_retries,
            initial_delay=initial_delay,
            max_delay=None,
            exponential_base=exponential_base,
            jitter=jitter,
            retry_on_exceptions=retry_on_exceptions,
            on_retry=on_retry
        )
    
    def decorator(f: Callable) -> Callable:
        return _create_retry_wrapper(f, policy)
    
    return decorator


def x_with_retry__mutmut_16(
    func: Optional[Callable] = None,
    *,
    policy: Optional[RetryPolicy] = None,
    max_retries: int = 3,
    initial_delay: float = 0.1,
    max_delay: float = 60.0,
    exponential_base: float = 2.0,
    jitter: bool = True,
    retry_on_exceptions: Optional[Tuple[Type[Exception], ...]] = None,
    on_retry: Optional[Callable[[Exception, int, float], None]] = None
) -> Callable:
    """
    Decorator to add retry logic with exponential backoff to a function.
    
    Can be used with or without parentheses:
        @with_retry
        def func(): ...
        
        @with_retry(max_retries=5)
        def func(): ...
    
    Args:
        func: Function to wrap (used when decorator is applied without parentheses)
        policy: Pre-configured RetryPolicy instance. If provided, other parameters
               are ignored. Default: None
        max_retries: Maximum retry attempts. Default: 3
        initial_delay: Initial delay in seconds. Default: 0.1
        max_delay: Maximum delay in seconds. Default: 60.0
        exponential_base: Exponential backoff multiplier. Default: 2.0
        jitter: Whether to add random jitter. Default: True
        retry_on_exceptions: Tuple of exception types to retry on. Default: None (all)
        on_retry: Optional callback on retry. Default: None
    
    Returns:
        Decorated function with retry logic
    
    Examples:
        >>> @with_retry
        ... def fetch_data():
        ...     return requests.get("https://api.example.com/data").json()
        
        >>> @with_retry(max_retries=5, initial_delay=0.5)
        ... def process_with_retry(x):
        ...     return expensive_operation(x)
        
        >>> # With custom policy
        >>> policy = RetryPolicy(max_retries=3, retry_on_exceptions=(ConnectionError,))
        >>> @with_retry(policy=policy)
        ... def connect_to_service():
        ...     return connect()
    """
    # If used without parentheses (@with_retry), func will be provided
    if func is not None:
        return _create_retry_wrapper(func, RetryPolicy())
    
    # If used with parentheses (@with_retry(...)), create policy and return decorator
    if policy is None:
        policy = RetryPolicy(
            max_retries=max_retries,
            initial_delay=initial_delay,
            max_delay=max_delay,
            exponential_base=None,
            jitter=jitter,
            retry_on_exceptions=retry_on_exceptions,
            on_retry=on_retry
        )
    
    def decorator(f: Callable) -> Callable:
        return _create_retry_wrapper(f, policy)
    
    return decorator


def x_with_retry__mutmut_17(
    func: Optional[Callable] = None,
    *,
    policy: Optional[RetryPolicy] = None,
    max_retries: int = 3,
    initial_delay: float = 0.1,
    max_delay: float = 60.0,
    exponential_base: float = 2.0,
    jitter: bool = True,
    retry_on_exceptions: Optional[Tuple[Type[Exception], ...]] = None,
    on_retry: Optional[Callable[[Exception, int, float], None]] = None
) -> Callable:
    """
    Decorator to add retry logic with exponential backoff to a function.
    
    Can be used with or without parentheses:
        @with_retry
        def func(): ...
        
        @with_retry(max_retries=5)
        def func(): ...
    
    Args:
        func: Function to wrap (used when decorator is applied without parentheses)
        policy: Pre-configured RetryPolicy instance. If provided, other parameters
               are ignored. Default: None
        max_retries: Maximum retry attempts. Default: 3
        initial_delay: Initial delay in seconds. Default: 0.1
        max_delay: Maximum delay in seconds. Default: 60.0
        exponential_base: Exponential backoff multiplier. Default: 2.0
        jitter: Whether to add random jitter. Default: True
        retry_on_exceptions: Tuple of exception types to retry on. Default: None (all)
        on_retry: Optional callback on retry. Default: None
    
    Returns:
        Decorated function with retry logic
    
    Examples:
        >>> @with_retry
        ... def fetch_data():
        ...     return requests.get("https://api.example.com/data").json()
        
        >>> @with_retry(max_retries=5, initial_delay=0.5)
        ... def process_with_retry(x):
        ...     return expensive_operation(x)
        
        >>> # With custom policy
        >>> policy = RetryPolicy(max_retries=3, retry_on_exceptions=(ConnectionError,))
        >>> @with_retry(policy=policy)
        ... def connect_to_service():
        ...     return connect()
    """
    # If used without parentheses (@with_retry), func will be provided
    if func is not None:
        return _create_retry_wrapper(func, RetryPolicy())
    
    # If used with parentheses (@with_retry(...)), create policy and return decorator
    if policy is None:
        policy = RetryPolicy(
            max_retries=max_retries,
            initial_delay=initial_delay,
            max_delay=max_delay,
            exponential_base=exponential_base,
            jitter=None,
            retry_on_exceptions=retry_on_exceptions,
            on_retry=on_retry
        )
    
    def decorator(f: Callable) -> Callable:
        return _create_retry_wrapper(f, policy)
    
    return decorator


def x_with_retry__mutmut_18(
    func: Optional[Callable] = None,
    *,
    policy: Optional[RetryPolicy] = None,
    max_retries: int = 3,
    initial_delay: float = 0.1,
    max_delay: float = 60.0,
    exponential_base: float = 2.0,
    jitter: bool = True,
    retry_on_exceptions: Optional[Tuple[Type[Exception], ...]] = None,
    on_retry: Optional[Callable[[Exception, int, float], None]] = None
) -> Callable:
    """
    Decorator to add retry logic with exponential backoff to a function.
    
    Can be used with or without parentheses:
        @with_retry
        def func(): ...
        
        @with_retry(max_retries=5)
        def func(): ...
    
    Args:
        func: Function to wrap (used when decorator is applied without parentheses)
        policy: Pre-configured RetryPolicy instance. If provided, other parameters
               are ignored. Default: None
        max_retries: Maximum retry attempts. Default: 3
        initial_delay: Initial delay in seconds. Default: 0.1
        max_delay: Maximum delay in seconds. Default: 60.0
        exponential_base: Exponential backoff multiplier. Default: 2.0
        jitter: Whether to add random jitter. Default: True
        retry_on_exceptions: Tuple of exception types to retry on. Default: None (all)
        on_retry: Optional callback on retry. Default: None
    
    Returns:
        Decorated function with retry logic
    
    Examples:
        >>> @with_retry
        ... def fetch_data():
        ...     return requests.get("https://api.example.com/data").json()
        
        >>> @with_retry(max_retries=5, initial_delay=0.5)
        ... def process_with_retry(x):
        ...     return expensive_operation(x)
        
        >>> # With custom policy
        >>> policy = RetryPolicy(max_retries=3, retry_on_exceptions=(ConnectionError,))
        >>> @with_retry(policy=policy)
        ... def connect_to_service():
        ...     return connect()
    """
    # If used without parentheses (@with_retry), func will be provided
    if func is not None:
        return _create_retry_wrapper(func, RetryPolicy())
    
    # If used with parentheses (@with_retry(...)), create policy and return decorator
    if policy is None:
        policy = RetryPolicy(
            max_retries=max_retries,
            initial_delay=initial_delay,
            max_delay=max_delay,
            exponential_base=exponential_base,
            jitter=jitter,
            retry_on_exceptions=None,
            on_retry=on_retry
        )
    
    def decorator(f: Callable) -> Callable:
        return _create_retry_wrapper(f, policy)
    
    return decorator


def x_with_retry__mutmut_19(
    func: Optional[Callable] = None,
    *,
    policy: Optional[RetryPolicy] = None,
    max_retries: int = 3,
    initial_delay: float = 0.1,
    max_delay: float = 60.0,
    exponential_base: float = 2.0,
    jitter: bool = True,
    retry_on_exceptions: Optional[Tuple[Type[Exception], ...]] = None,
    on_retry: Optional[Callable[[Exception, int, float], None]] = None
) -> Callable:
    """
    Decorator to add retry logic with exponential backoff to a function.
    
    Can be used with or without parentheses:
        @with_retry
        def func(): ...
        
        @with_retry(max_retries=5)
        def func(): ...
    
    Args:
        func: Function to wrap (used when decorator is applied without parentheses)
        policy: Pre-configured RetryPolicy instance. If provided, other parameters
               are ignored. Default: None
        max_retries: Maximum retry attempts. Default: 3
        initial_delay: Initial delay in seconds. Default: 0.1
        max_delay: Maximum delay in seconds. Default: 60.0
        exponential_base: Exponential backoff multiplier. Default: 2.0
        jitter: Whether to add random jitter. Default: True
        retry_on_exceptions: Tuple of exception types to retry on. Default: None (all)
        on_retry: Optional callback on retry. Default: None
    
    Returns:
        Decorated function with retry logic
    
    Examples:
        >>> @with_retry
        ... def fetch_data():
        ...     return requests.get("https://api.example.com/data").json()
        
        >>> @with_retry(max_retries=5, initial_delay=0.5)
        ... def process_with_retry(x):
        ...     return expensive_operation(x)
        
        >>> # With custom policy
        >>> policy = RetryPolicy(max_retries=3, retry_on_exceptions=(ConnectionError,))
        >>> @with_retry(policy=policy)
        ... def connect_to_service():
        ...     return connect()
    """
    # If used without parentheses (@with_retry), func will be provided
    if func is not None:
        return _create_retry_wrapper(func, RetryPolicy())
    
    # If used with parentheses (@with_retry(...)), create policy and return decorator
    if policy is None:
        policy = RetryPolicy(
            max_retries=max_retries,
            initial_delay=initial_delay,
            max_delay=max_delay,
            exponential_base=exponential_base,
            jitter=jitter,
            retry_on_exceptions=retry_on_exceptions,
            on_retry=None
        )
    
    def decorator(f: Callable) -> Callable:
        return _create_retry_wrapper(f, policy)
    
    return decorator


def x_with_retry__mutmut_20(
    func: Optional[Callable] = None,
    *,
    policy: Optional[RetryPolicy] = None,
    max_retries: int = 3,
    initial_delay: float = 0.1,
    max_delay: float = 60.0,
    exponential_base: float = 2.0,
    jitter: bool = True,
    retry_on_exceptions: Optional[Tuple[Type[Exception], ...]] = None,
    on_retry: Optional[Callable[[Exception, int, float], None]] = None
) -> Callable:
    """
    Decorator to add retry logic with exponential backoff to a function.
    
    Can be used with or without parentheses:
        @with_retry
        def func(): ...
        
        @with_retry(max_retries=5)
        def func(): ...
    
    Args:
        func: Function to wrap (used when decorator is applied without parentheses)
        policy: Pre-configured RetryPolicy instance. If provided, other parameters
               are ignored. Default: None
        max_retries: Maximum retry attempts. Default: 3
        initial_delay: Initial delay in seconds. Default: 0.1
        max_delay: Maximum delay in seconds. Default: 60.0
        exponential_base: Exponential backoff multiplier. Default: 2.0
        jitter: Whether to add random jitter. Default: True
        retry_on_exceptions: Tuple of exception types to retry on. Default: None (all)
        on_retry: Optional callback on retry. Default: None
    
    Returns:
        Decorated function with retry logic
    
    Examples:
        >>> @with_retry
        ... def fetch_data():
        ...     return requests.get("https://api.example.com/data").json()
        
        >>> @with_retry(max_retries=5, initial_delay=0.5)
        ... def process_with_retry(x):
        ...     return expensive_operation(x)
        
        >>> # With custom policy
        >>> policy = RetryPolicy(max_retries=3, retry_on_exceptions=(ConnectionError,))
        >>> @with_retry(policy=policy)
        ... def connect_to_service():
        ...     return connect()
    """
    # If used without parentheses (@with_retry), func will be provided
    if func is not None:
        return _create_retry_wrapper(func, RetryPolicy())
    
    # If used with parentheses (@with_retry(...)), create policy and return decorator
    if policy is None:
        policy = RetryPolicy(
            initial_delay=initial_delay,
            max_delay=max_delay,
            exponential_base=exponential_base,
            jitter=jitter,
            retry_on_exceptions=retry_on_exceptions,
            on_retry=on_retry
        )
    
    def decorator(f: Callable) -> Callable:
        return _create_retry_wrapper(f, policy)
    
    return decorator


def x_with_retry__mutmut_21(
    func: Optional[Callable] = None,
    *,
    policy: Optional[RetryPolicy] = None,
    max_retries: int = 3,
    initial_delay: float = 0.1,
    max_delay: float = 60.0,
    exponential_base: float = 2.0,
    jitter: bool = True,
    retry_on_exceptions: Optional[Tuple[Type[Exception], ...]] = None,
    on_retry: Optional[Callable[[Exception, int, float], None]] = None
) -> Callable:
    """
    Decorator to add retry logic with exponential backoff to a function.
    
    Can be used with or without parentheses:
        @with_retry
        def func(): ...
        
        @with_retry(max_retries=5)
        def func(): ...
    
    Args:
        func: Function to wrap (used when decorator is applied without parentheses)
        policy: Pre-configured RetryPolicy instance. If provided, other parameters
               are ignored. Default: None
        max_retries: Maximum retry attempts. Default: 3
        initial_delay: Initial delay in seconds. Default: 0.1
        max_delay: Maximum delay in seconds. Default: 60.0
        exponential_base: Exponential backoff multiplier. Default: 2.0
        jitter: Whether to add random jitter. Default: True
        retry_on_exceptions: Tuple of exception types to retry on. Default: None (all)
        on_retry: Optional callback on retry. Default: None
    
    Returns:
        Decorated function with retry logic
    
    Examples:
        >>> @with_retry
        ... def fetch_data():
        ...     return requests.get("https://api.example.com/data").json()
        
        >>> @with_retry(max_retries=5, initial_delay=0.5)
        ... def process_with_retry(x):
        ...     return expensive_operation(x)
        
        >>> # With custom policy
        >>> policy = RetryPolicy(max_retries=3, retry_on_exceptions=(ConnectionError,))
        >>> @with_retry(policy=policy)
        ... def connect_to_service():
        ...     return connect()
    """
    # If used without parentheses (@with_retry), func will be provided
    if func is not None:
        return _create_retry_wrapper(func, RetryPolicy())
    
    # If used with parentheses (@with_retry(...)), create policy and return decorator
    if policy is None:
        policy = RetryPolicy(
            max_retries=max_retries,
            max_delay=max_delay,
            exponential_base=exponential_base,
            jitter=jitter,
            retry_on_exceptions=retry_on_exceptions,
            on_retry=on_retry
        )
    
    def decorator(f: Callable) -> Callable:
        return _create_retry_wrapper(f, policy)
    
    return decorator


def x_with_retry__mutmut_22(
    func: Optional[Callable] = None,
    *,
    policy: Optional[RetryPolicy] = None,
    max_retries: int = 3,
    initial_delay: float = 0.1,
    max_delay: float = 60.0,
    exponential_base: float = 2.0,
    jitter: bool = True,
    retry_on_exceptions: Optional[Tuple[Type[Exception], ...]] = None,
    on_retry: Optional[Callable[[Exception, int, float], None]] = None
) -> Callable:
    """
    Decorator to add retry logic with exponential backoff to a function.
    
    Can be used with or without parentheses:
        @with_retry
        def func(): ...
        
        @with_retry(max_retries=5)
        def func(): ...
    
    Args:
        func: Function to wrap (used when decorator is applied without parentheses)
        policy: Pre-configured RetryPolicy instance. If provided, other parameters
               are ignored. Default: None
        max_retries: Maximum retry attempts. Default: 3
        initial_delay: Initial delay in seconds. Default: 0.1
        max_delay: Maximum delay in seconds. Default: 60.0
        exponential_base: Exponential backoff multiplier. Default: 2.0
        jitter: Whether to add random jitter. Default: True
        retry_on_exceptions: Tuple of exception types to retry on. Default: None (all)
        on_retry: Optional callback on retry. Default: None
    
    Returns:
        Decorated function with retry logic
    
    Examples:
        >>> @with_retry
        ... def fetch_data():
        ...     return requests.get("https://api.example.com/data").json()
        
        >>> @with_retry(max_retries=5, initial_delay=0.5)
        ... def process_with_retry(x):
        ...     return expensive_operation(x)
        
        >>> # With custom policy
        >>> policy = RetryPolicy(max_retries=3, retry_on_exceptions=(ConnectionError,))
        >>> @with_retry(policy=policy)
        ... def connect_to_service():
        ...     return connect()
    """
    # If used without parentheses (@with_retry), func will be provided
    if func is not None:
        return _create_retry_wrapper(func, RetryPolicy())
    
    # If used with parentheses (@with_retry(...)), create policy and return decorator
    if policy is None:
        policy = RetryPolicy(
            max_retries=max_retries,
            initial_delay=initial_delay,
            exponential_base=exponential_base,
            jitter=jitter,
            retry_on_exceptions=retry_on_exceptions,
            on_retry=on_retry
        )
    
    def decorator(f: Callable) -> Callable:
        return _create_retry_wrapper(f, policy)
    
    return decorator


def x_with_retry__mutmut_23(
    func: Optional[Callable] = None,
    *,
    policy: Optional[RetryPolicy] = None,
    max_retries: int = 3,
    initial_delay: float = 0.1,
    max_delay: float = 60.0,
    exponential_base: float = 2.0,
    jitter: bool = True,
    retry_on_exceptions: Optional[Tuple[Type[Exception], ...]] = None,
    on_retry: Optional[Callable[[Exception, int, float], None]] = None
) -> Callable:
    """
    Decorator to add retry logic with exponential backoff to a function.
    
    Can be used with or without parentheses:
        @with_retry
        def func(): ...
        
        @with_retry(max_retries=5)
        def func(): ...
    
    Args:
        func: Function to wrap (used when decorator is applied without parentheses)
        policy: Pre-configured RetryPolicy instance. If provided, other parameters
               are ignored. Default: None
        max_retries: Maximum retry attempts. Default: 3
        initial_delay: Initial delay in seconds. Default: 0.1
        max_delay: Maximum delay in seconds. Default: 60.0
        exponential_base: Exponential backoff multiplier. Default: 2.0
        jitter: Whether to add random jitter. Default: True
        retry_on_exceptions: Tuple of exception types to retry on. Default: None (all)
        on_retry: Optional callback on retry. Default: None
    
    Returns:
        Decorated function with retry logic
    
    Examples:
        >>> @with_retry
        ... def fetch_data():
        ...     return requests.get("https://api.example.com/data").json()
        
        >>> @with_retry(max_retries=5, initial_delay=0.5)
        ... def process_with_retry(x):
        ...     return expensive_operation(x)
        
        >>> # With custom policy
        >>> policy = RetryPolicy(max_retries=3, retry_on_exceptions=(ConnectionError,))
        >>> @with_retry(policy=policy)
        ... def connect_to_service():
        ...     return connect()
    """
    # If used without parentheses (@with_retry), func will be provided
    if func is not None:
        return _create_retry_wrapper(func, RetryPolicy())
    
    # If used with parentheses (@with_retry(...)), create policy and return decorator
    if policy is None:
        policy = RetryPolicy(
            max_retries=max_retries,
            initial_delay=initial_delay,
            max_delay=max_delay,
            jitter=jitter,
            retry_on_exceptions=retry_on_exceptions,
            on_retry=on_retry
        )
    
    def decorator(f: Callable) -> Callable:
        return _create_retry_wrapper(f, policy)
    
    return decorator


def x_with_retry__mutmut_24(
    func: Optional[Callable] = None,
    *,
    policy: Optional[RetryPolicy] = None,
    max_retries: int = 3,
    initial_delay: float = 0.1,
    max_delay: float = 60.0,
    exponential_base: float = 2.0,
    jitter: bool = True,
    retry_on_exceptions: Optional[Tuple[Type[Exception], ...]] = None,
    on_retry: Optional[Callable[[Exception, int, float], None]] = None
) -> Callable:
    """
    Decorator to add retry logic with exponential backoff to a function.
    
    Can be used with or without parentheses:
        @with_retry
        def func(): ...
        
        @with_retry(max_retries=5)
        def func(): ...
    
    Args:
        func: Function to wrap (used when decorator is applied without parentheses)
        policy: Pre-configured RetryPolicy instance. If provided, other parameters
               are ignored. Default: None
        max_retries: Maximum retry attempts. Default: 3
        initial_delay: Initial delay in seconds. Default: 0.1
        max_delay: Maximum delay in seconds. Default: 60.0
        exponential_base: Exponential backoff multiplier. Default: 2.0
        jitter: Whether to add random jitter. Default: True
        retry_on_exceptions: Tuple of exception types to retry on. Default: None (all)
        on_retry: Optional callback on retry. Default: None
    
    Returns:
        Decorated function with retry logic
    
    Examples:
        >>> @with_retry
        ... def fetch_data():
        ...     return requests.get("https://api.example.com/data").json()
        
        >>> @with_retry(max_retries=5, initial_delay=0.5)
        ... def process_with_retry(x):
        ...     return expensive_operation(x)
        
        >>> # With custom policy
        >>> policy = RetryPolicy(max_retries=3, retry_on_exceptions=(ConnectionError,))
        >>> @with_retry(policy=policy)
        ... def connect_to_service():
        ...     return connect()
    """
    # If used without parentheses (@with_retry), func will be provided
    if func is not None:
        return _create_retry_wrapper(func, RetryPolicy())
    
    # If used with parentheses (@with_retry(...)), create policy and return decorator
    if policy is None:
        policy = RetryPolicy(
            max_retries=max_retries,
            initial_delay=initial_delay,
            max_delay=max_delay,
            exponential_base=exponential_base,
            retry_on_exceptions=retry_on_exceptions,
            on_retry=on_retry
        )
    
    def decorator(f: Callable) -> Callable:
        return _create_retry_wrapper(f, policy)
    
    return decorator


def x_with_retry__mutmut_25(
    func: Optional[Callable] = None,
    *,
    policy: Optional[RetryPolicy] = None,
    max_retries: int = 3,
    initial_delay: float = 0.1,
    max_delay: float = 60.0,
    exponential_base: float = 2.0,
    jitter: bool = True,
    retry_on_exceptions: Optional[Tuple[Type[Exception], ...]] = None,
    on_retry: Optional[Callable[[Exception, int, float], None]] = None
) -> Callable:
    """
    Decorator to add retry logic with exponential backoff to a function.
    
    Can be used with or without parentheses:
        @with_retry
        def func(): ...
        
        @with_retry(max_retries=5)
        def func(): ...
    
    Args:
        func: Function to wrap (used when decorator is applied without parentheses)
        policy: Pre-configured RetryPolicy instance. If provided, other parameters
               are ignored. Default: None
        max_retries: Maximum retry attempts. Default: 3
        initial_delay: Initial delay in seconds. Default: 0.1
        max_delay: Maximum delay in seconds. Default: 60.0
        exponential_base: Exponential backoff multiplier. Default: 2.0
        jitter: Whether to add random jitter. Default: True
        retry_on_exceptions: Tuple of exception types to retry on. Default: None (all)
        on_retry: Optional callback on retry. Default: None
    
    Returns:
        Decorated function with retry logic
    
    Examples:
        >>> @with_retry
        ... def fetch_data():
        ...     return requests.get("https://api.example.com/data").json()
        
        >>> @with_retry(max_retries=5, initial_delay=0.5)
        ... def process_with_retry(x):
        ...     return expensive_operation(x)
        
        >>> # With custom policy
        >>> policy = RetryPolicy(max_retries=3, retry_on_exceptions=(ConnectionError,))
        >>> @with_retry(policy=policy)
        ... def connect_to_service():
        ...     return connect()
    """
    # If used without parentheses (@with_retry), func will be provided
    if func is not None:
        return _create_retry_wrapper(func, RetryPolicy())
    
    # If used with parentheses (@with_retry(...)), create policy and return decorator
    if policy is None:
        policy = RetryPolicy(
            max_retries=max_retries,
            initial_delay=initial_delay,
            max_delay=max_delay,
            exponential_base=exponential_base,
            jitter=jitter,
            on_retry=on_retry
        )
    
    def decorator(f: Callable) -> Callable:
        return _create_retry_wrapper(f, policy)
    
    return decorator


def x_with_retry__mutmut_26(
    func: Optional[Callable] = None,
    *,
    policy: Optional[RetryPolicy] = None,
    max_retries: int = 3,
    initial_delay: float = 0.1,
    max_delay: float = 60.0,
    exponential_base: float = 2.0,
    jitter: bool = True,
    retry_on_exceptions: Optional[Tuple[Type[Exception], ...]] = None,
    on_retry: Optional[Callable[[Exception, int, float], None]] = None
) -> Callable:
    """
    Decorator to add retry logic with exponential backoff to a function.
    
    Can be used with or without parentheses:
        @with_retry
        def func(): ...
        
        @with_retry(max_retries=5)
        def func(): ...
    
    Args:
        func: Function to wrap (used when decorator is applied without parentheses)
        policy: Pre-configured RetryPolicy instance. If provided, other parameters
               are ignored. Default: None
        max_retries: Maximum retry attempts. Default: 3
        initial_delay: Initial delay in seconds. Default: 0.1
        max_delay: Maximum delay in seconds. Default: 60.0
        exponential_base: Exponential backoff multiplier. Default: 2.0
        jitter: Whether to add random jitter. Default: True
        retry_on_exceptions: Tuple of exception types to retry on. Default: None (all)
        on_retry: Optional callback on retry. Default: None
    
    Returns:
        Decorated function with retry logic
    
    Examples:
        >>> @with_retry
        ... def fetch_data():
        ...     return requests.get("https://api.example.com/data").json()
        
        >>> @with_retry(max_retries=5, initial_delay=0.5)
        ... def process_with_retry(x):
        ...     return expensive_operation(x)
        
        >>> # With custom policy
        >>> policy = RetryPolicy(max_retries=3, retry_on_exceptions=(ConnectionError,))
        >>> @with_retry(policy=policy)
        ... def connect_to_service():
        ...     return connect()
    """
    # If used without parentheses (@with_retry), func will be provided
    if func is not None:
        return _create_retry_wrapper(func, RetryPolicy())
    
    # If used with parentheses (@with_retry(...)), create policy and return decorator
    if policy is None:
        policy = RetryPolicy(
            max_retries=max_retries,
            initial_delay=initial_delay,
            max_delay=max_delay,
            exponential_base=exponential_base,
            jitter=jitter,
            retry_on_exceptions=retry_on_exceptions,
            )
    
    def decorator(f: Callable) -> Callable:
        return _create_retry_wrapper(f, policy)
    
    return decorator


def x_with_retry__mutmut_27(
    func: Optional[Callable] = None,
    *,
    policy: Optional[RetryPolicy] = None,
    max_retries: int = 3,
    initial_delay: float = 0.1,
    max_delay: float = 60.0,
    exponential_base: float = 2.0,
    jitter: bool = True,
    retry_on_exceptions: Optional[Tuple[Type[Exception], ...]] = None,
    on_retry: Optional[Callable[[Exception, int, float], None]] = None
) -> Callable:
    """
    Decorator to add retry logic with exponential backoff to a function.
    
    Can be used with or without parentheses:
        @with_retry
        def func(): ...
        
        @with_retry(max_retries=5)
        def func(): ...
    
    Args:
        func: Function to wrap (used when decorator is applied without parentheses)
        policy: Pre-configured RetryPolicy instance. If provided, other parameters
               are ignored. Default: None
        max_retries: Maximum retry attempts. Default: 3
        initial_delay: Initial delay in seconds. Default: 0.1
        max_delay: Maximum delay in seconds. Default: 60.0
        exponential_base: Exponential backoff multiplier. Default: 2.0
        jitter: Whether to add random jitter. Default: True
        retry_on_exceptions: Tuple of exception types to retry on. Default: None (all)
        on_retry: Optional callback on retry. Default: None
    
    Returns:
        Decorated function with retry logic
    
    Examples:
        >>> @with_retry
        ... def fetch_data():
        ...     return requests.get("https://api.example.com/data").json()
        
        >>> @with_retry(max_retries=5, initial_delay=0.5)
        ... def process_with_retry(x):
        ...     return expensive_operation(x)
        
        >>> # With custom policy
        >>> policy = RetryPolicy(max_retries=3, retry_on_exceptions=(ConnectionError,))
        >>> @with_retry(policy=policy)
        ... def connect_to_service():
        ...     return connect()
    """
    # If used without parentheses (@with_retry), func will be provided
    if func is not None:
        return _create_retry_wrapper(func, RetryPolicy())
    
    # If used with parentheses (@with_retry(...)), create policy and return decorator
    if policy is None:
        policy = RetryPolicy(
            max_retries=max_retries,
            initial_delay=initial_delay,
            max_delay=max_delay,
            exponential_base=exponential_base,
            jitter=jitter,
            retry_on_exceptions=retry_on_exceptions,
            on_retry=on_retry
        )
    
    def decorator(f: Callable) -> Callable:
        return _create_retry_wrapper(None, policy)
    
    return decorator


def x_with_retry__mutmut_28(
    func: Optional[Callable] = None,
    *,
    policy: Optional[RetryPolicy] = None,
    max_retries: int = 3,
    initial_delay: float = 0.1,
    max_delay: float = 60.0,
    exponential_base: float = 2.0,
    jitter: bool = True,
    retry_on_exceptions: Optional[Tuple[Type[Exception], ...]] = None,
    on_retry: Optional[Callable[[Exception, int, float], None]] = None
) -> Callable:
    """
    Decorator to add retry logic with exponential backoff to a function.
    
    Can be used with or without parentheses:
        @with_retry
        def func(): ...
        
        @with_retry(max_retries=5)
        def func(): ...
    
    Args:
        func: Function to wrap (used when decorator is applied without parentheses)
        policy: Pre-configured RetryPolicy instance. If provided, other parameters
               are ignored. Default: None
        max_retries: Maximum retry attempts. Default: 3
        initial_delay: Initial delay in seconds. Default: 0.1
        max_delay: Maximum delay in seconds. Default: 60.0
        exponential_base: Exponential backoff multiplier. Default: 2.0
        jitter: Whether to add random jitter. Default: True
        retry_on_exceptions: Tuple of exception types to retry on. Default: None (all)
        on_retry: Optional callback on retry. Default: None
    
    Returns:
        Decorated function with retry logic
    
    Examples:
        >>> @with_retry
        ... def fetch_data():
        ...     return requests.get("https://api.example.com/data").json()
        
        >>> @with_retry(max_retries=5, initial_delay=0.5)
        ... def process_with_retry(x):
        ...     return expensive_operation(x)
        
        >>> # With custom policy
        >>> policy = RetryPolicy(max_retries=3, retry_on_exceptions=(ConnectionError,))
        >>> @with_retry(policy=policy)
        ... def connect_to_service():
        ...     return connect()
    """
    # If used without parentheses (@with_retry), func will be provided
    if func is not None:
        return _create_retry_wrapper(func, RetryPolicy())
    
    # If used with parentheses (@with_retry(...)), create policy and return decorator
    if policy is None:
        policy = RetryPolicy(
            max_retries=max_retries,
            initial_delay=initial_delay,
            max_delay=max_delay,
            exponential_base=exponential_base,
            jitter=jitter,
            retry_on_exceptions=retry_on_exceptions,
            on_retry=on_retry
        )
    
    def decorator(f: Callable) -> Callable:
        return _create_retry_wrapper(f, None)
    
    return decorator


def x_with_retry__mutmut_29(
    func: Optional[Callable] = None,
    *,
    policy: Optional[RetryPolicy] = None,
    max_retries: int = 3,
    initial_delay: float = 0.1,
    max_delay: float = 60.0,
    exponential_base: float = 2.0,
    jitter: bool = True,
    retry_on_exceptions: Optional[Tuple[Type[Exception], ...]] = None,
    on_retry: Optional[Callable[[Exception, int, float], None]] = None
) -> Callable:
    """
    Decorator to add retry logic with exponential backoff to a function.
    
    Can be used with or without parentheses:
        @with_retry
        def func(): ...
        
        @with_retry(max_retries=5)
        def func(): ...
    
    Args:
        func: Function to wrap (used when decorator is applied without parentheses)
        policy: Pre-configured RetryPolicy instance. If provided, other parameters
               are ignored. Default: None
        max_retries: Maximum retry attempts. Default: 3
        initial_delay: Initial delay in seconds. Default: 0.1
        max_delay: Maximum delay in seconds. Default: 60.0
        exponential_base: Exponential backoff multiplier. Default: 2.0
        jitter: Whether to add random jitter. Default: True
        retry_on_exceptions: Tuple of exception types to retry on. Default: None (all)
        on_retry: Optional callback on retry. Default: None
    
    Returns:
        Decorated function with retry logic
    
    Examples:
        >>> @with_retry
        ... def fetch_data():
        ...     return requests.get("https://api.example.com/data").json()
        
        >>> @with_retry(max_retries=5, initial_delay=0.5)
        ... def process_with_retry(x):
        ...     return expensive_operation(x)
        
        >>> # With custom policy
        >>> policy = RetryPolicy(max_retries=3, retry_on_exceptions=(ConnectionError,))
        >>> @with_retry(policy=policy)
        ... def connect_to_service():
        ...     return connect()
    """
    # If used without parentheses (@with_retry), func will be provided
    if func is not None:
        return _create_retry_wrapper(func, RetryPolicy())
    
    # If used with parentheses (@with_retry(...)), create policy and return decorator
    if policy is None:
        policy = RetryPolicy(
            max_retries=max_retries,
            initial_delay=initial_delay,
            max_delay=max_delay,
            exponential_base=exponential_base,
            jitter=jitter,
            retry_on_exceptions=retry_on_exceptions,
            on_retry=on_retry
        )
    
    def decorator(f: Callable) -> Callable:
        return _create_retry_wrapper(policy)
    
    return decorator


def x_with_retry__mutmut_30(
    func: Optional[Callable] = None,
    *,
    policy: Optional[RetryPolicy] = None,
    max_retries: int = 3,
    initial_delay: float = 0.1,
    max_delay: float = 60.0,
    exponential_base: float = 2.0,
    jitter: bool = True,
    retry_on_exceptions: Optional[Tuple[Type[Exception], ...]] = None,
    on_retry: Optional[Callable[[Exception, int, float], None]] = None
) -> Callable:
    """
    Decorator to add retry logic with exponential backoff to a function.
    
    Can be used with or without parentheses:
        @with_retry
        def func(): ...
        
        @with_retry(max_retries=5)
        def func(): ...
    
    Args:
        func: Function to wrap (used when decorator is applied without parentheses)
        policy: Pre-configured RetryPolicy instance. If provided, other parameters
               are ignored. Default: None
        max_retries: Maximum retry attempts. Default: 3
        initial_delay: Initial delay in seconds. Default: 0.1
        max_delay: Maximum delay in seconds. Default: 60.0
        exponential_base: Exponential backoff multiplier. Default: 2.0
        jitter: Whether to add random jitter. Default: True
        retry_on_exceptions: Tuple of exception types to retry on. Default: None (all)
        on_retry: Optional callback on retry. Default: None
    
    Returns:
        Decorated function with retry logic
    
    Examples:
        >>> @with_retry
        ... def fetch_data():
        ...     return requests.get("https://api.example.com/data").json()
        
        >>> @with_retry(max_retries=5, initial_delay=0.5)
        ... def process_with_retry(x):
        ...     return expensive_operation(x)
        
        >>> # With custom policy
        >>> policy = RetryPolicy(max_retries=3, retry_on_exceptions=(ConnectionError,))
        >>> @with_retry(policy=policy)
        ... def connect_to_service():
        ...     return connect()
    """
    # If used without parentheses (@with_retry), func will be provided
    if func is not None:
        return _create_retry_wrapper(func, RetryPolicy())
    
    # If used with parentheses (@with_retry(...)), create policy and return decorator
    if policy is None:
        policy = RetryPolicy(
            max_retries=max_retries,
            initial_delay=initial_delay,
            max_delay=max_delay,
            exponential_base=exponential_base,
            jitter=jitter,
            retry_on_exceptions=retry_on_exceptions,
            on_retry=on_retry
        )
    
    def decorator(f: Callable) -> Callable:
        return _create_retry_wrapper(f, )
    
    return decorator

x_with_retry__mutmut_mutants : ClassVar[MutantDict] = {
'x_with_retry__mutmut_1': x_with_retry__mutmut_1, 
    'x_with_retry__mutmut_2': x_with_retry__mutmut_2, 
    'x_with_retry__mutmut_3': x_with_retry__mutmut_3, 
    'x_with_retry__mutmut_4': x_with_retry__mutmut_4, 
    'x_with_retry__mutmut_5': x_with_retry__mutmut_5, 
    'x_with_retry__mutmut_6': x_with_retry__mutmut_6, 
    'x_with_retry__mutmut_7': x_with_retry__mutmut_7, 
    'x_with_retry__mutmut_8': x_with_retry__mutmut_8, 
    'x_with_retry__mutmut_9': x_with_retry__mutmut_9, 
    'x_with_retry__mutmut_10': x_with_retry__mutmut_10, 
    'x_with_retry__mutmut_11': x_with_retry__mutmut_11, 
    'x_with_retry__mutmut_12': x_with_retry__mutmut_12, 
    'x_with_retry__mutmut_13': x_with_retry__mutmut_13, 
    'x_with_retry__mutmut_14': x_with_retry__mutmut_14, 
    'x_with_retry__mutmut_15': x_with_retry__mutmut_15, 
    'x_with_retry__mutmut_16': x_with_retry__mutmut_16, 
    'x_with_retry__mutmut_17': x_with_retry__mutmut_17, 
    'x_with_retry__mutmut_18': x_with_retry__mutmut_18, 
    'x_with_retry__mutmut_19': x_with_retry__mutmut_19, 
    'x_with_retry__mutmut_20': x_with_retry__mutmut_20, 
    'x_with_retry__mutmut_21': x_with_retry__mutmut_21, 
    'x_with_retry__mutmut_22': x_with_retry__mutmut_22, 
    'x_with_retry__mutmut_23': x_with_retry__mutmut_23, 
    'x_with_retry__mutmut_24': x_with_retry__mutmut_24, 
    'x_with_retry__mutmut_25': x_with_retry__mutmut_25, 
    'x_with_retry__mutmut_26': x_with_retry__mutmut_26, 
    'x_with_retry__mutmut_27': x_with_retry__mutmut_27, 
    'x_with_retry__mutmut_28': x_with_retry__mutmut_28, 
    'x_with_retry__mutmut_29': x_with_retry__mutmut_29, 
    'x_with_retry__mutmut_30': x_with_retry__mutmut_30
}

def with_retry(*args, **kwargs):
    result = _mutmut_trampoline(x_with_retry__mutmut_orig, x_with_retry__mutmut_mutants, args, kwargs)
    return result 

with_retry.__signature__ = _mutmut_signature(x_with_retry__mutmut_orig)
x_with_retry__mutmut_orig.__name__ = 'x_with_retry'


def _create_retry_wrapper(func: Callable, policy: RetryPolicy) -> Callable:
    """
    Internal function to create the actual retry wrapper.
    
    Args:
        func: Function to wrap
        policy: Retry policy configuration
    
    Returns:
        Wrapped function with retry logic
    """
    @functools.wraps(func)
    def wrapper(*args: Any, **kwargs: Any) -> Any:
        attempt = 0
        last_exception = None
        
        while True:
            attempt += 1
            
            try:
                return func(*args, **kwargs)
            except Exception as e:
                last_exception = e
                
                # Check if we should retry
                if not policy.should_retry(e, attempt):
                    # Re-raise the exception if we shouldn't retry
                    raise
                
                # Calculate delay for next attempt
                delay = policy.calculate_delay(attempt)
                
                # Call retry callback if provided
                if policy.on_retry is not None:
                    try:
                        policy.on_retry(e, attempt, delay)
                    except Exception:
                        # Don't let callback errors break the retry logic
                        pass
                
                # Wait before retrying
                time.sleep(delay)
        
        # This should never be reached, but just in case
        if last_exception is not None:
            raise last_exception
    
    return wrapper


def x_retry_call__mutmut_orig(
    func: Callable,
    args: Tuple = (),
    kwargs: Optional[dict] = None,
    policy: Optional[RetryPolicy] = None,
    **retry_kwargs
) -> Any:
    """
    Execute a function with retry logic without using a decorator.
    
    This is useful when you want to apply retry logic to a function call
    without modifying the function itself.
    
    Args:
        func: Function to call
        args: Positional arguments to pass to func
        kwargs: Keyword arguments to pass to func
        policy: Pre-configured RetryPolicy. If None, create from retry_kwargs
        **retry_kwargs: Additional keyword arguments to create RetryPolicy
                       (max_retries, initial_delay, etc.)
    
    Returns:
        Result of calling func(*args, **kwargs)
    
    Raises:
        Exception: If all retry attempts fail, raises the last exception
    
    Examples:
        >>> # Retry a function call
        >>> result = retry_call(fetch_data, max_retries=5)
        
        >>> # With arguments
        >>> result = retry_call(process_item, args=(item,), max_retries=3)
        
        >>> # With custom policy
        >>> policy = RetryPolicy(max_retries=3, initial_delay=0.5)
        >>> result = retry_call(connect, policy=policy)
    """
    if kwargs is None:
        kwargs = {}
    
    if policy is None:
        policy = RetryPolicy(**retry_kwargs)
    
    # Create a wrapper and call it
    wrapped = _create_retry_wrapper(func, policy)
    return wrapped(*args, **kwargs)


def x_retry_call__mutmut_1(
    func: Callable,
    args: Tuple = (),
    kwargs: Optional[dict] = None,
    policy: Optional[RetryPolicy] = None,
    **retry_kwargs
) -> Any:
    """
    Execute a function with retry logic without using a decorator.
    
    This is useful when you want to apply retry logic to a function call
    without modifying the function itself.
    
    Args:
        func: Function to call
        args: Positional arguments to pass to func
        kwargs: Keyword arguments to pass to func
        policy: Pre-configured RetryPolicy. If None, create from retry_kwargs
        **retry_kwargs: Additional keyword arguments to create RetryPolicy
                       (max_retries, initial_delay, etc.)
    
    Returns:
        Result of calling func(*args, **kwargs)
    
    Raises:
        Exception: If all retry attempts fail, raises the last exception
    
    Examples:
        >>> # Retry a function call
        >>> result = retry_call(fetch_data, max_retries=5)
        
        >>> # With arguments
        >>> result = retry_call(process_item, args=(item,), max_retries=3)
        
        >>> # With custom policy
        >>> policy = RetryPolicy(max_retries=3, initial_delay=0.5)
        >>> result = retry_call(connect, policy=policy)
    """
    if kwargs is not None:
        kwargs = {}
    
    if policy is None:
        policy = RetryPolicy(**retry_kwargs)
    
    # Create a wrapper and call it
    wrapped = _create_retry_wrapper(func, policy)
    return wrapped(*args, **kwargs)


def x_retry_call__mutmut_2(
    func: Callable,
    args: Tuple = (),
    kwargs: Optional[dict] = None,
    policy: Optional[RetryPolicy] = None,
    **retry_kwargs
) -> Any:
    """
    Execute a function with retry logic without using a decorator.
    
    This is useful when you want to apply retry logic to a function call
    without modifying the function itself.
    
    Args:
        func: Function to call
        args: Positional arguments to pass to func
        kwargs: Keyword arguments to pass to func
        policy: Pre-configured RetryPolicy. If None, create from retry_kwargs
        **retry_kwargs: Additional keyword arguments to create RetryPolicy
                       (max_retries, initial_delay, etc.)
    
    Returns:
        Result of calling func(*args, **kwargs)
    
    Raises:
        Exception: If all retry attempts fail, raises the last exception
    
    Examples:
        >>> # Retry a function call
        >>> result = retry_call(fetch_data, max_retries=5)
        
        >>> # With arguments
        >>> result = retry_call(process_item, args=(item,), max_retries=3)
        
        >>> # With custom policy
        >>> policy = RetryPolicy(max_retries=3, initial_delay=0.5)
        >>> result = retry_call(connect, policy=policy)
    """
    if kwargs is None:
        kwargs = None
    
    if policy is None:
        policy = RetryPolicy(**retry_kwargs)
    
    # Create a wrapper and call it
    wrapped = _create_retry_wrapper(func, policy)
    return wrapped(*args, **kwargs)


def x_retry_call__mutmut_3(
    func: Callable,
    args: Tuple = (),
    kwargs: Optional[dict] = None,
    policy: Optional[RetryPolicy] = None,
    **retry_kwargs
) -> Any:
    """
    Execute a function with retry logic without using a decorator.
    
    This is useful when you want to apply retry logic to a function call
    without modifying the function itself.
    
    Args:
        func: Function to call
        args: Positional arguments to pass to func
        kwargs: Keyword arguments to pass to func
        policy: Pre-configured RetryPolicy. If None, create from retry_kwargs
        **retry_kwargs: Additional keyword arguments to create RetryPolicy
                       (max_retries, initial_delay, etc.)
    
    Returns:
        Result of calling func(*args, **kwargs)
    
    Raises:
        Exception: If all retry attempts fail, raises the last exception
    
    Examples:
        >>> # Retry a function call
        >>> result = retry_call(fetch_data, max_retries=5)
        
        >>> # With arguments
        >>> result = retry_call(process_item, args=(item,), max_retries=3)
        
        >>> # With custom policy
        >>> policy = RetryPolicy(max_retries=3, initial_delay=0.5)
        >>> result = retry_call(connect, policy=policy)
    """
    if kwargs is None:
        kwargs = {}
    
    if policy is not None:
        policy = RetryPolicy(**retry_kwargs)
    
    # Create a wrapper and call it
    wrapped = _create_retry_wrapper(func, policy)
    return wrapped(*args, **kwargs)


def x_retry_call__mutmut_4(
    func: Callable,
    args: Tuple = (),
    kwargs: Optional[dict] = None,
    policy: Optional[RetryPolicy] = None,
    **retry_kwargs
) -> Any:
    """
    Execute a function with retry logic without using a decorator.
    
    This is useful when you want to apply retry logic to a function call
    without modifying the function itself.
    
    Args:
        func: Function to call
        args: Positional arguments to pass to func
        kwargs: Keyword arguments to pass to func
        policy: Pre-configured RetryPolicy. If None, create from retry_kwargs
        **retry_kwargs: Additional keyword arguments to create RetryPolicy
                       (max_retries, initial_delay, etc.)
    
    Returns:
        Result of calling func(*args, **kwargs)
    
    Raises:
        Exception: If all retry attempts fail, raises the last exception
    
    Examples:
        >>> # Retry a function call
        >>> result = retry_call(fetch_data, max_retries=5)
        
        >>> # With arguments
        >>> result = retry_call(process_item, args=(item,), max_retries=3)
        
        >>> # With custom policy
        >>> policy = RetryPolicy(max_retries=3, initial_delay=0.5)
        >>> result = retry_call(connect, policy=policy)
    """
    if kwargs is None:
        kwargs = {}
    
    if policy is None:
        policy = None
    
    # Create a wrapper and call it
    wrapped = _create_retry_wrapper(func, policy)
    return wrapped(*args, **kwargs)


def x_retry_call__mutmut_5(
    func: Callable,
    args: Tuple = (),
    kwargs: Optional[dict] = None,
    policy: Optional[RetryPolicy] = None,
    **retry_kwargs
) -> Any:
    """
    Execute a function with retry logic without using a decorator.
    
    This is useful when you want to apply retry logic to a function call
    without modifying the function itself.
    
    Args:
        func: Function to call
        args: Positional arguments to pass to func
        kwargs: Keyword arguments to pass to func
        policy: Pre-configured RetryPolicy. If None, create from retry_kwargs
        **retry_kwargs: Additional keyword arguments to create RetryPolicy
                       (max_retries, initial_delay, etc.)
    
    Returns:
        Result of calling func(*args, **kwargs)
    
    Raises:
        Exception: If all retry attempts fail, raises the last exception
    
    Examples:
        >>> # Retry a function call
        >>> result = retry_call(fetch_data, max_retries=5)
        
        >>> # With arguments
        >>> result = retry_call(process_item, args=(item,), max_retries=3)
        
        >>> # With custom policy
        >>> policy = RetryPolicy(max_retries=3, initial_delay=0.5)
        >>> result = retry_call(connect, policy=policy)
    """
    if kwargs is None:
        kwargs = {}
    
    if policy is None:
        policy = RetryPolicy(**retry_kwargs)
    
    # Create a wrapper and call it
    wrapped = None
    return wrapped(*args, **kwargs)


def x_retry_call__mutmut_6(
    func: Callable,
    args: Tuple = (),
    kwargs: Optional[dict] = None,
    policy: Optional[RetryPolicy] = None,
    **retry_kwargs
) -> Any:
    """
    Execute a function with retry logic without using a decorator.
    
    This is useful when you want to apply retry logic to a function call
    without modifying the function itself.
    
    Args:
        func: Function to call
        args: Positional arguments to pass to func
        kwargs: Keyword arguments to pass to func
        policy: Pre-configured RetryPolicy. If None, create from retry_kwargs
        **retry_kwargs: Additional keyword arguments to create RetryPolicy
                       (max_retries, initial_delay, etc.)
    
    Returns:
        Result of calling func(*args, **kwargs)
    
    Raises:
        Exception: If all retry attempts fail, raises the last exception
    
    Examples:
        >>> # Retry a function call
        >>> result = retry_call(fetch_data, max_retries=5)
        
        >>> # With arguments
        >>> result = retry_call(process_item, args=(item,), max_retries=3)
        
        >>> # With custom policy
        >>> policy = RetryPolicy(max_retries=3, initial_delay=0.5)
        >>> result = retry_call(connect, policy=policy)
    """
    if kwargs is None:
        kwargs = {}
    
    if policy is None:
        policy = RetryPolicy(**retry_kwargs)
    
    # Create a wrapper and call it
    wrapped = _create_retry_wrapper(None, policy)
    return wrapped(*args, **kwargs)


def x_retry_call__mutmut_7(
    func: Callable,
    args: Tuple = (),
    kwargs: Optional[dict] = None,
    policy: Optional[RetryPolicy] = None,
    **retry_kwargs
) -> Any:
    """
    Execute a function with retry logic without using a decorator.
    
    This is useful when you want to apply retry logic to a function call
    without modifying the function itself.
    
    Args:
        func: Function to call
        args: Positional arguments to pass to func
        kwargs: Keyword arguments to pass to func
        policy: Pre-configured RetryPolicy. If None, create from retry_kwargs
        **retry_kwargs: Additional keyword arguments to create RetryPolicy
                       (max_retries, initial_delay, etc.)
    
    Returns:
        Result of calling func(*args, **kwargs)
    
    Raises:
        Exception: If all retry attempts fail, raises the last exception
    
    Examples:
        >>> # Retry a function call
        >>> result = retry_call(fetch_data, max_retries=5)
        
        >>> # With arguments
        >>> result = retry_call(process_item, args=(item,), max_retries=3)
        
        >>> # With custom policy
        >>> policy = RetryPolicy(max_retries=3, initial_delay=0.5)
        >>> result = retry_call(connect, policy=policy)
    """
    if kwargs is None:
        kwargs = {}
    
    if policy is None:
        policy = RetryPolicy(**retry_kwargs)
    
    # Create a wrapper and call it
    wrapped = _create_retry_wrapper(func, None)
    return wrapped(*args, **kwargs)


def x_retry_call__mutmut_8(
    func: Callable,
    args: Tuple = (),
    kwargs: Optional[dict] = None,
    policy: Optional[RetryPolicy] = None,
    **retry_kwargs
) -> Any:
    """
    Execute a function with retry logic without using a decorator.
    
    This is useful when you want to apply retry logic to a function call
    without modifying the function itself.
    
    Args:
        func: Function to call
        args: Positional arguments to pass to func
        kwargs: Keyword arguments to pass to func
        policy: Pre-configured RetryPolicy. If None, create from retry_kwargs
        **retry_kwargs: Additional keyword arguments to create RetryPolicy
                       (max_retries, initial_delay, etc.)
    
    Returns:
        Result of calling func(*args, **kwargs)
    
    Raises:
        Exception: If all retry attempts fail, raises the last exception
    
    Examples:
        >>> # Retry a function call
        >>> result = retry_call(fetch_data, max_retries=5)
        
        >>> # With arguments
        >>> result = retry_call(process_item, args=(item,), max_retries=3)
        
        >>> # With custom policy
        >>> policy = RetryPolicy(max_retries=3, initial_delay=0.5)
        >>> result = retry_call(connect, policy=policy)
    """
    if kwargs is None:
        kwargs = {}
    
    if policy is None:
        policy = RetryPolicy(**retry_kwargs)
    
    # Create a wrapper and call it
    wrapped = _create_retry_wrapper(policy)
    return wrapped(*args, **kwargs)


def x_retry_call__mutmut_9(
    func: Callable,
    args: Tuple = (),
    kwargs: Optional[dict] = None,
    policy: Optional[RetryPolicy] = None,
    **retry_kwargs
) -> Any:
    """
    Execute a function with retry logic without using a decorator.
    
    This is useful when you want to apply retry logic to a function call
    without modifying the function itself.
    
    Args:
        func: Function to call
        args: Positional arguments to pass to func
        kwargs: Keyword arguments to pass to func
        policy: Pre-configured RetryPolicy. If None, create from retry_kwargs
        **retry_kwargs: Additional keyword arguments to create RetryPolicy
                       (max_retries, initial_delay, etc.)
    
    Returns:
        Result of calling func(*args, **kwargs)
    
    Raises:
        Exception: If all retry attempts fail, raises the last exception
    
    Examples:
        >>> # Retry a function call
        >>> result = retry_call(fetch_data, max_retries=5)
        
        >>> # With arguments
        >>> result = retry_call(process_item, args=(item,), max_retries=3)
        
        >>> # With custom policy
        >>> policy = RetryPolicy(max_retries=3, initial_delay=0.5)
        >>> result = retry_call(connect, policy=policy)
    """
    if kwargs is None:
        kwargs = {}
    
    if policy is None:
        policy = RetryPolicy(**retry_kwargs)
    
    # Create a wrapper and call it
    wrapped = _create_retry_wrapper(func, )
    return wrapped(*args, **kwargs)


def x_retry_call__mutmut_10(
    func: Callable,
    args: Tuple = (),
    kwargs: Optional[dict] = None,
    policy: Optional[RetryPolicy] = None,
    **retry_kwargs
) -> Any:
    """
    Execute a function with retry logic without using a decorator.
    
    This is useful when you want to apply retry logic to a function call
    without modifying the function itself.
    
    Args:
        func: Function to call
        args: Positional arguments to pass to func
        kwargs: Keyword arguments to pass to func
        policy: Pre-configured RetryPolicy. If None, create from retry_kwargs
        **retry_kwargs: Additional keyword arguments to create RetryPolicy
                       (max_retries, initial_delay, etc.)
    
    Returns:
        Result of calling func(*args, **kwargs)
    
    Raises:
        Exception: If all retry attempts fail, raises the last exception
    
    Examples:
        >>> # Retry a function call
        >>> result = retry_call(fetch_data, max_retries=5)
        
        >>> # With arguments
        >>> result = retry_call(process_item, args=(item,), max_retries=3)
        
        >>> # With custom policy
        >>> policy = RetryPolicy(max_retries=3, initial_delay=0.5)
        >>> result = retry_call(connect, policy=policy)
    """
    if kwargs is None:
        kwargs = {}
    
    if policy is None:
        policy = RetryPolicy(**retry_kwargs)
    
    # Create a wrapper and call it
    wrapped = _create_retry_wrapper(func, policy)
    return wrapped(**kwargs)


def x_retry_call__mutmut_11(
    func: Callable,
    args: Tuple = (),
    kwargs: Optional[dict] = None,
    policy: Optional[RetryPolicy] = None,
    **retry_kwargs
) -> Any:
    """
    Execute a function with retry logic without using a decorator.
    
    This is useful when you want to apply retry logic to a function call
    without modifying the function itself.
    
    Args:
        func: Function to call
        args: Positional arguments to pass to func
        kwargs: Keyword arguments to pass to func
        policy: Pre-configured RetryPolicy. If None, create from retry_kwargs
        **retry_kwargs: Additional keyword arguments to create RetryPolicy
                       (max_retries, initial_delay, etc.)
    
    Returns:
        Result of calling func(*args, **kwargs)
    
    Raises:
        Exception: If all retry attempts fail, raises the last exception
    
    Examples:
        >>> # Retry a function call
        >>> result = retry_call(fetch_data, max_retries=5)
        
        >>> # With arguments
        >>> result = retry_call(process_item, args=(item,), max_retries=3)
        
        >>> # With custom policy
        >>> policy = RetryPolicy(max_retries=3, initial_delay=0.5)
        >>> result = retry_call(connect, policy=policy)
    """
    if kwargs is None:
        kwargs = {}
    
    if policy is None:
        policy = RetryPolicy(**retry_kwargs)
    
    # Create a wrapper and call it
    wrapped = _create_retry_wrapper(func, policy)
    return wrapped(*args, )

x_retry_call__mutmut_mutants : ClassVar[MutantDict] = {
'x_retry_call__mutmut_1': x_retry_call__mutmut_1, 
    'x_retry_call__mutmut_2': x_retry_call__mutmut_2, 
    'x_retry_call__mutmut_3': x_retry_call__mutmut_3, 
    'x_retry_call__mutmut_4': x_retry_call__mutmut_4, 
    'x_retry_call__mutmut_5': x_retry_call__mutmut_5, 
    'x_retry_call__mutmut_6': x_retry_call__mutmut_6, 
    'x_retry_call__mutmut_7': x_retry_call__mutmut_7, 
    'x_retry_call__mutmut_8': x_retry_call__mutmut_8, 
    'x_retry_call__mutmut_9': x_retry_call__mutmut_9, 
    'x_retry_call__mutmut_10': x_retry_call__mutmut_10, 
    'x_retry_call__mutmut_11': x_retry_call__mutmut_11
}

def retry_call(*args, **kwargs):
    result = _mutmut_trampoline(x_retry_call__mutmut_orig, x_retry_call__mutmut_mutants, args, kwargs)
    return result 

retry_call.__signature__ = _mutmut_signature(x_retry_call__mutmut_orig)
x_retry_call__mutmut_orig.__name__ = 'x_retry_call'


class RetryExhaustedError(Exception):
    """
    Exception raised when all retry attempts have been exhausted.
    
    Attributes:
        original_exception: The last exception that caused the failure
        attempts: Number of attempts made
    """
    
    def xǁRetryExhaustedErrorǁ__init____mutmut_orig(self, original_exception: Exception, attempts: int):
        self.original_exception = original_exception
        self.attempts = attempts
        super().__init__(
            f"Retry exhausted after {attempts} attempts. "
            f"Last exception: {type(original_exception).__name__}: {original_exception}"
        )
    
    def xǁRetryExhaustedErrorǁ__init____mutmut_1(self, original_exception: Exception, attempts: int):
        self.original_exception = None
        self.attempts = attempts
        super().__init__(
            f"Retry exhausted after {attempts} attempts. "
            f"Last exception: {type(original_exception).__name__}: {original_exception}"
        )
    
    def xǁRetryExhaustedErrorǁ__init____mutmut_2(self, original_exception: Exception, attempts: int):
        self.original_exception = original_exception
        self.attempts = None
        super().__init__(
            f"Retry exhausted after {attempts} attempts. "
            f"Last exception: {type(original_exception).__name__}: {original_exception}"
        )
    
    def xǁRetryExhaustedErrorǁ__init____mutmut_3(self, original_exception: Exception, attempts: int):
        self.original_exception = original_exception
        self.attempts = attempts
        super().__init__(
            None
        )
    
    def xǁRetryExhaustedErrorǁ__init____mutmut_4(self, original_exception: Exception, attempts: int):
        self.original_exception = original_exception
        self.attempts = attempts
        super().__init__(
            f"Retry exhausted after {attempts} attempts. "
            f"Last exception: {type(None).__name__}: {original_exception}"
        )
    
    xǁRetryExhaustedErrorǁ__init____mutmut_mutants : ClassVar[MutantDict] = {
    'xǁRetryExhaustedErrorǁ__init____mutmut_1': xǁRetryExhaustedErrorǁ__init____mutmut_1, 
        'xǁRetryExhaustedErrorǁ__init____mutmut_2': xǁRetryExhaustedErrorǁ__init____mutmut_2, 
        'xǁRetryExhaustedErrorǁ__init____mutmut_3': xǁRetryExhaustedErrorǁ__init____mutmut_3, 
        'xǁRetryExhaustedErrorǁ__init____mutmut_4': xǁRetryExhaustedErrorǁ__init____mutmut_4
    }
    
    def __init__(self, *args, **kwargs):
        result = _mutmut_trampoline(object.__getattribute__(self, "xǁRetryExhaustedErrorǁ__init____mutmut_orig"), object.__getattribute__(self, "xǁRetryExhaustedErrorǁ__init____mutmut_mutants"), args, kwargs, self)
        return result 
    
    __init__.__signature__ = _mutmut_signature(xǁRetryExhaustedErrorǁ__init____mutmut_orig)
    xǁRetryExhaustedErrorǁ__init____mutmut_orig.__name__ = 'xǁRetryExhaustedErrorǁ__init__'


def x_create_batch_retry_wrapper__mutmut_orig(
    func: Callable,
    policy: Optional[RetryPolicy] = None,
    fail_fast: bool = False
) -> Callable:
    """
    Create a wrapper that applies retry logic to batch processing.
    
    This is useful when processing multiple items and you want to retry
    individual item failures without stopping the entire batch.
    
    Args:
        func: Function that processes a single item
        policy: Retry policy to apply. If None, uses default policy
        fail_fast: If True, stop processing on first permanent failure.
                  If False, collect all errors and continue. Default: False
    
    Returns:
        Wrapped function that processes items with retry logic
    
    Example:
        >>> def process_item(x):
        ...     # May fail transiently
        ...     return risky_operation(x)
        
        >>> policy = RetryPolicy(max_retries=3)
        >>> batch_processor = create_batch_retry_wrapper(process_item, policy)
        
        >>> # Process batch with automatic retry on failures
        >>> results = [batch_processor(item) for item in items]
    """
    if policy is None:
        policy = RetryPolicy()
    
    return _create_retry_wrapper(func, policy)


def x_create_batch_retry_wrapper__mutmut_1(
    func: Callable,
    policy: Optional[RetryPolicy] = None,
    fail_fast: bool = True
) -> Callable:
    """
    Create a wrapper that applies retry logic to batch processing.
    
    This is useful when processing multiple items and you want to retry
    individual item failures without stopping the entire batch.
    
    Args:
        func: Function that processes a single item
        policy: Retry policy to apply. If None, uses default policy
        fail_fast: If True, stop processing on first permanent failure.
                  If False, collect all errors and continue. Default: False
    
    Returns:
        Wrapped function that processes items with retry logic
    
    Example:
        >>> def process_item(x):
        ...     # May fail transiently
        ...     return risky_operation(x)
        
        >>> policy = RetryPolicy(max_retries=3)
        >>> batch_processor = create_batch_retry_wrapper(process_item, policy)
        
        >>> # Process batch with automatic retry on failures
        >>> results = [batch_processor(item) for item in items]
    """
    if policy is None:
        policy = RetryPolicy()
    
    return _create_retry_wrapper(func, policy)


def x_create_batch_retry_wrapper__mutmut_2(
    func: Callable,
    policy: Optional[RetryPolicy] = None,
    fail_fast: bool = False
) -> Callable:
    """
    Create a wrapper that applies retry logic to batch processing.
    
    This is useful when processing multiple items and you want to retry
    individual item failures without stopping the entire batch.
    
    Args:
        func: Function that processes a single item
        policy: Retry policy to apply. If None, uses default policy
        fail_fast: If True, stop processing on first permanent failure.
                  If False, collect all errors and continue. Default: False
    
    Returns:
        Wrapped function that processes items with retry logic
    
    Example:
        >>> def process_item(x):
        ...     # May fail transiently
        ...     return risky_operation(x)
        
        >>> policy = RetryPolicy(max_retries=3)
        >>> batch_processor = create_batch_retry_wrapper(process_item, policy)
        
        >>> # Process batch with automatic retry on failures
        >>> results = [batch_processor(item) for item in items]
    """
    if policy is not None:
        policy = RetryPolicy()
    
    return _create_retry_wrapper(func, policy)


def x_create_batch_retry_wrapper__mutmut_3(
    func: Callable,
    policy: Optional[RetryPolicy] = None,
    fail_fast: bool = False
) -> Callable:
    """
    Create a wrapper that applies retry logic to batch processing.
    
    This is useful when processing multiple items and you want to retry
    individual item failures without stopping the entire batch.
    
    Args:
        func: Function that processes a single item
        policy: Retry policy to apply. If None, uses default policy
        fail_fast: If True, stop processing on first permanent failure.
                  If False, collect all errors and continue. Default: False
    
    Returns:
        Wrapped function that processes items with retry logic
    
    Example:
        >>> def process_item(x):
        ...     # May fail transiently
        ...     return risky_operation(x)
        
        >>> policy = RetryPolicy(max_retries=3)
        >>> batch_processor = create_batch_retry_wrapper(process_item, policy)
        
        >>> # Process batch with automatic retry on failures
        >>> results = [batch_processor(item) for item in items]
    """
    if policy is None:
        policy = None
    
    return _create_retry_wrapper(func, policy)


def x_create_batch_retry_wrapper__mutmut_4(
    func: Callable,
    policy: Optional[RetryPolicy] = None,
    fail_fast: bool = False
) -> Callable:
    """
    Create a wrapper that applies retry logic to batch processing.
    
    This is useful when processing multiple items and you want to retry
    individual item failures without stopping the entire batch.
    
    Args:
        func: Function that processes a single item
        policy: Retry policy to apply. If None, uses default policy
        fail_fast: If True, stop processing on first permanent failure.
                  If False, collect all errors and continue. Default: False
    
    Returns:
        Wrapped function that processes items with retry logic
    
    Example:
        >>> def process_item(x):
        ...     # May fail transiently
        ...     return risky_operation(x)
        
        >>> policy = RetryPolicy(max_retries=3)
        >>> batch_processor = create_batch_retry_wrapper(process_item, policy)
        
        >>> # Process batch with automatic retry on failures
        >>> results = [batch_processor(item) for item in items]
    """
    if policy is None:
        policy = RetryPolicy()
    
    return _create_retry_wrapper(None, policy)


def x_create_batch_retry_wrapper__mutmut_5(
    func: Callable,
    policy: Optional[RetryPolicy] = None,
    fail_fast: bool = False
) -> Callable:
    """
    Create a wrapper that applies retry logic to batch processing.
    
    This is useful when processing multiple items and you want to retry
    individual item failures without stopping the entire batch.
    
    Args:
        func: Function that processes a single item
        policy: Retry policy to apply. If None, uses default policy
        fail_fast: If True, stop processing on first permanent failure.
                  If False, collect all errors and continue. Default: False
    
    Returns:
        Wrapped function that processes items with retry logic
    
    Example:
        >>> def process_item(x):
        ...     # May fail transiently
        ...     return risky_operation(x)
        
        >>> policy = RetryPolicy(max_retries=3)
        >>> batch_processor = create_batch_retry_wrapper(process_item, policy)
        
        >>> # Process batch with automatic retry on failures
        >>> results = [batch_processor(item) for item in items]
    """
    if policy is None:
        policy = RetryPolicy()
    
    return _create_retry_wrapper(func, None)


def x_create_batch_retry_wrapper__mutmut_6(
    func: Callable,
    policy: Optional[RetryPolicy] = None,
    fail_fast: bool = False
) -> Callable:
    """
    Create a wrapper that applies retry logic to batch processing.
    
    This is useful when processing multiple items and you want to retry
    individual item failures without stopping the entire batch.
    
    Args:
        func: Function that processes a single item
        policy: Retry policy to apply. If None, uses default policy
        fail_fast: If True, stop processing on first permanent failure.
                  If False, collect all errors and continue. Default: False
    
    Returns:
        Wrapped function that processes items with retry logic
    
    Example:
        >>> def process_item(x):
        ...     # May fail transiently
        ...     return risky_operation(x)
        
        >>> policy = RetryPolicy(max_retries=3)
        >>> batch_processor = create_batch_retry_wrapper(process_item, policy)
        
        >>> # Process batch with automatic retry on failures
        >>> results = [batch_processor(item) for item in items]
    """
    if policy is None:
        policy = RetryPolicy()
    
    return _create_retry_wrapper(policy)


def x_create_batch_retry_wrapper__mutmut_7(
    func: Callable,
    policy: Optional[RetryPolicy] = None,
    fail_fast: bool = False
) -> Callable:
    """
    Create a wrapper that applies retry logic to batch processing.
    
    This is useful when processing multiple items and you want to retry
    individual item failures without stopping the entire batch.
    
    Args:
        func: Function that processes a single item
        policy: Retry policy to apply. If None, uses default policy
        fail_fast: If True, stop processing on first permanent failure.
                  If False, collect all errors and continue. Default: False
    
    Returns:
        Wrapped function that processes items with retry logic
    
    Example:
        >>> def process_item(x):
        ...     # May fail transiently
        ...     return risky_operation(x)
        
        >>> policy = RetryPolicy(max_retries=3)
        >>> batch_processor = create_batch_retry_wrapper(process_item, policy)
        
        >>> # Process batch with automatic retry on failures
        >>> results = [batch_processor(item) for item in items]
    """
    if policy is None:
        policy = RetryPolicy()
    
    return _create_retry_wrapper(func, )

x_create_batch_retry_wrapper__mutmut_mutants : ClassVar[MutantDict] = {
'x_create_batch_retry_wrapper__mutmut_1': x_create_batch_retry_wrapper__mutmut_1, 
    'x_create_batch_retry_wrapper__mutmut_2': x_create_batch_retry_wrapper__mutmut_2, 
    'x_create_batch_retry_wrapper__mutmut_3': x_create_batch_retry_wrapper__mutmut_3, 
    'x_create_batch_retry_wrapper__mutmut_4': x_create_batch_retry_wrapper__mutmut_4, 
    'x_create_batch_retry_wrapper__mutmut_5': x_create_batch_retry_wrapper__mutmut_5, 
    'x_create_batch_retry_wrapper__mutmut_6': x_create_batch_retry_wrapper__mutmut_6, 
    'x_create_batch_retry_wrapper__mutmut_7': x_create_batch_retry_wrapper__mutmut_7
}

def create_batch_retry_wrapper(*args, **kwargs):
    result = _mutmut_trampoline(x_create_batch_retry_wrapper__mutmut_orig, x_create_batch_retry_wrapper__mutmut_mutants, args, kwargs)
    return result 

create_batch_retry_wrapper.__signature__ = _mutmut_signature(x_create_batch_retry_wrapper__mutmut_orig)
x_create_batch_retry_wrapper__mutmut_orig.__name__ = 'x_create_batch_retry_wrapper'
