"""
Example: Rate Limiting API Calls

This example demonstrates how to use Amorsize's rate limiting pattern
to prevent API throttling while processing data efficiently.
"""

import time
from typing import Dict, List

from amorsize import execute, with_rate_limit, with_retry


# Simulate an API that limits to 10 requests/second
class FakeAPI:
    """
    Simulated API with rate limiting.
    
    Note: The higher limit (50 req/s) is used to simulate a real API
    that has some capacity above our rate limiter's target (10 req/s).
    This allows us to demonstrate that our rate limiter effectively
    controls the request rate.
    """
    
    def __init__(self):
        self.request_times: List[float] = []
        self.rate_limit_per_second = 50  # Higher than our rate limiter to allow demonstration
    
    def get_data(self, item_id: int) -> Dict:
        """Fetch data for an item (simulated)."""
        current_time = time.time()
        
        # Check if we're being rate limited
        recent_requests = [
            t for t in self.request_times
            if current_time - t < 1.0
        ]
        
        if len(recent_requests) >= self.rate_limit_per_second:
            raise Exception(f"Rate limit exceeded: {len(recent_requests)} requests in last second")
        
        self.request_times.append(current_time)
        
        # Simulate API response time
        time.sleep(0.01)
        
        return {
            "id": item_id,
            "name": f"Item {item_id}",
            "value": item_id * 10
        }


# Create shared API instance
api = FakeAPI()


# Example 1: Basic rate limiting
@with_rate_limit(requests_per_second=10.0)
def fetch_item_basic(item_id: int) -> Dict:
    """Fetch item with basic rate limiting."""
    return api.get_data(item_id)


# Example 2: Rate limiting with retry for robustness
@with_rate_limit(requests_per_second=10.0)
@with_retry(max_retries=3, initial_delay=0.1)
def fetch_item_robust(item_id: int) -> Dict:
    """Fetch item with rate limiting and automatic retry."""
    return api.get_data(item_id)


# Example 3: Monitoring rate limiting
rate_limit_waits = []

def log_rate_limit(wait_time: float):
    """Log when rate limiting occurs."""
    rate_limit_waits.append(wait_time)
    print(f"⏱️  Rate limited - waiting {wait_time:.3f}s")


@with_rate_limit(
    requests_per_second=10.0,
    burst_size=15,
    on_wait=log_rate_limit
)
@with_retry(max_retries=2)
def fetch_item_monitored(item_id: int) -> Dict:
    """Fetch item with monitoring."""
    return api.get_data(item_id)


def main():
    """Run examples."""
    
    print("=" * 60)
    print("Amorsize Rate Limiting Examples")
    print("=" * 60)
    
    # Example 1: Basic rate limiting
    print("\n1. Basic Rate Limiting")
    print("-" * 60)
    print("Fetching 30 items with 10 req/s rate limit...")
    
    items = list(range(30))
    start = time.time()
    
    results = [fetch_item_basic(i) for i in items]
    
    elapsed = time.time() - start
    print(f"✓ Fetched {len(results)} items in {elapsed:.2f}s")
    print(f"  Average rate: {len(results) / elapsed:.1f} req/s")
    print(f"  (Should be ~10 req/s due to rate limiting)")
    
    # Example 2: Using with Amorsize execute()
    print("\n2. Parallel Execution with Rate Limiting")
    print("-" * 60)
    print("Using Amorsize to optimize parallelism...")
    
    api.request_times.clear()  # Reset API tracking
    items = list(range(50))
    start = time.time()
    
    results = execute(
        fetch_item_robust,
        items,
        prefer_threads_for_io=True,
        verbose=True
    )
    
    elapsed = time.time() - start
    print(f"✓ Fetched {len(results)} items in {elapsed:.2f}s")
    print(f"  Amorsize optimized n_jobs and chunksize")
    print(f"  Rate limiting prevented API throttling")
    
    # Example 3: Monitoring rate limiting
    print("\n3. Rate Limiting with Monitoring")
    print("-" * 60)
    print("Fetching 40 items with burst support...")
    
    api.request_times.clear()
    rate_limit_waits.clear()
    items = list(range(40))
    start = time.time()
    
    results = [fetch_item_monitored(i) for i in items]
    
    elapsed = time.time() - start
    print(f"✓ Fetched {len(results)} items in {elapsed:.2f}s")
    print(f"  Rate limited {len(rate_limit_waits)} times")
    if rate_limit_waits:
        avg_wait = sum(rate_limit_waits) / len(rate_limit_waits)
        print(f"  Average wait when limited: {avg_wait:.3f}s")
    
    # Summary
    print("\n" + "=" * 60)
    print("Summary")
    print("=" * 60)
    print("✓ Rate limiting prevents API throttling")
    print("✓ Combines with retry for robustness")
    print("✓ Works with Amorsize optimization")
    print("✓ Monitoring helps tune parameters")


if __name__ == "__main__":
    main()
