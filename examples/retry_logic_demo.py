"""
Example: Using retry logic with exponential backoff in Amorsize.

This example demonstrates how to use the retry functionality to handle
transient failures in your parallel workloads.
"""

import random
import time
from amorsize import execute, RetryPolicy, with_retry


# Example 1: Basic retry with decorator
print("=" * 70)
print("Example 1: Basic retry with decorator")
print("=" * 70)

# Simulate a function that fails occasionally due to network issues
@with_retry(max_retries=3, initial_delay=0.1)
def fetch_data(url_id):
    """Simulate fetching data from an API with occasional failures."""
    # Simulate 30% failure rate
    if random.random() < 0.3:
        raise ConnectionError(f"Failed to fetch URL {url_id}")
    return f"data_from_{url_id}"

# Process multiple URLs with automatic retry
urls = [f"url_{i}" for i in range(10)]
try:
    results = [fetch_data(url) for url in urls]
    print(f"✓ Successfully fetched {len(results)} items")
    print(f"  Sample results: {results[:3]}")
except Exception as e:
    print(f"✗ Failed: {e}")

print()


# Example 2: Retry with custom policy and callback
print("=" * 70)
print("Example 2: Retry with custom policy and logging")
print("=" * 70)

# Track retries for monitoring
retry_stats = {"total_retries": 0, "failed_items": []}

def log_retry(exception, attempt, delay):
    """Callback to log retry attempts."""
    retry_stats["total_retries"] += 1
    print(f"  ⚠ Retry #{attempt} after {delay:.2f}s: {exception}")

# Create a policy for handling connection errors
policy = RetryPolicy(
    max_retries=5,
    initial_delay=0.1,
    exponential_base=2.0,
    retry_on_exceptions=(ConnectionError, TimeoutError),
    on_retry=log_retry
)

@with_retry(policy=policy)
def process_with_network(item_id):
    """Simulate processing that requires network access."""
    # Simulate occasional network failures
    if random.random() < 0.2:
        raise ConnectionError(f"Network timeout for item {item_id}")
    return item_id ** 2

# Process items
items = list(range(20))
print(f"Processing {len(items)} items with retry policy...")
start = time.time()
results = [process_with_network(i) for i in items]
elapsed = time.time() - start

print(f"✓ Processed {len(results)} items in {elapsed:.2f}s")
print(f"  Total retries: {retry_stats['total_retries']}")
print()


# Example 3: Using retry with Amorsize execute()
print("=" * 70)
print("Example 3: Retry with parallel execution")
print("=" * 70)

# Function with potential failures that we want to parallelize
@with_retry(max_retries=3, initial_delay=0.05)
def expensive_compute_with_failures(x):
    """Simulate expensive computation with occasional failures."""
    # Simulate 20% failure rate on first attempt
    if random.random() < 0.2:
        raise RuntimeError(f"Transient computation error for {x}")
    
    # Simulate expensive computation
    result = 0
    for i in range(1000):
        result += x ** 2
    return result

# Execute with automatic parallelization and retry
data = range(100)
print(f"Processing {len(data)} items with parallel execution + retry...")
start = time.time()
results = execute(expensive_compute_with_failures, data, verbose=True)
elapsed = time.time() - start

print(f"✓ Completed in {elapsed:.2f}s")
print(f"  Results: {len(results)} items processed")
print()


# Example 4: Selective retry for specific exceptions
print("=" * 70)
print("Example 4: Selective retry for specific exceptions")
print("=" * 70)

class RateLimitError(Exception):
    """Custom exception for rate limiting."""
    pass

@with_retry(
    max_retries=5,
    initial_delay=0.5,
    retry_on_exceptions=(RateLimitError, ConnectionError)
)
def api_call_with_rate_limit(item):
    """Simulate API call with rate limiting."""
    # Simulate different error types
    rand = random.random()
    if rand < 0.1:
        raise RateLimitError(f"Rate limit hit for {item}")  # Will retry
    elif rand < 0.15:
        raise ConnectionError(f"Connection failed for {item}")  # Will retry
    elif rand < 0.17:
        raise ValueError(f"Invalid data for {item}")  # Will NOT retry
    return f"result_{item}"

# Process items - some errors will be retried, others won't
items = list(range(50))
successful = []
failed = []

for item in items:
    try:
        result = api_call_with_rate_limit(item)
        successful.append(result)
    except (RateLimitError, ConnectionError) as e:
        # These should be rare after retries
        failed.append((item, "retryable", str(e)))
    except ValueError as e:
        # These are immediate failures (not retried)
        failed.append((item, "non-retryable", str(e)))

print(f"✓ Successful: {len(successful)} items")
print(f"✗ Failed after retries: {len(failed)} items")
if failed:
    print(f"  Failed items: {failed[:3]}...")
print()


# Example 5: Retry with jitter to prevent thundering herd
print("=" * 70)
print("Example 5: Retry with jitter (prevents thundering herd)")
print("=" * 70)

# Policy with jitter - delays will vary randomly to prevent all clients
# from retrying at the exact same time
policy_with_jitter = RetryPolicy(
    max_retries=3,
    initial_delay=0.1,
    jitter=True  # Adds ±25% random variation
)

@with_retry(policy=policy_with_jitter)
def shared_resource_access(client_id):
    """Simulate accessing a shared resource with contention."""
    if random.random() < 0.3:
        raise ConnectionError(f"Resource busy for client {client_id}")
    return f"data_for_client_{client_id}"

# Multiple clients accessing shared resource
clients = list(range(20))
print("Accessing shared resource with jittered retry delays...")
results = [shared_resource_access(c) for c in clients]
print(f"✓ All {len(results)} clients succeeded")
print("  (Jitter prevented thundering herd effect)")
print()


# Example 6: Demonstrating exponential backoff
print("=" * 70)
print("Example 6: Exponential backoff demonstration")
print("=" * 70)

retry_attempts = []

def track_backoff(exc, attempt, delay):
    retry_attempts.append((attempt, delay))
    print(f"  Attempt {attempt}: waiting {delay:.3f}s before retry")

@with_retry(
    max_retries=5,
    initial_delay=0.05,
    exponential_base=2.0,
    jitter=False,  # Disable jitter to show exact exponential progression
    on_retry=track_backoff
)
def always_fails_for_demo():
    """Function that always fails to demonstrate backoff."""
    raise RuntimeError("Demo failure")

print("Demonstrating exponential backoff (delays: 0.05, 0.1, 0.2, 0.4, 0.8):")
try:
    always_fails_for_demo()
except RuntimeError:
    pass

print(f"✓ Observed {len(retry_attempts)} retry attempts")
print(f"  Delays doubled each time: {[f'{d:.3f}s' for _, d in retry_attempts]}")
print()


# Summary
print("=" * 70)
print("Summary: Retry Logic Benefits")
print("=" * 70)
print("""
✓ Handles transient failures automatically
✓ Configurable retry policies (max retries, delays, exceptions)
✓ Exponential backoff prevents overwhelming services
✓ Jitter prevents thundering herd effect
✓ Selective retry for specific exception types
✓ Works seamlessly with parallel execution
✓ Callback support for monitoring and logging
✓ Zero external dependencies

Use cases:
• Network API calls with temporary failures
• Database connections with transient errors
• Cloud service rate limiting
• Distributed system temporary unavailability
• File I/O with retry on lock contention
""")
