# Rate Limiting Pattern in Amorsize

## Overview

The rate limiting module provides a thread-safe token bucket implementation for controlling the rate of API calls, preventing API throttling, and managing resource consumption.

## Quick Start

### Basic Usage

```python
from amorsize import with_rate_limit

# Limit to 10 requests per second
@with_rate_limit(requests_per_second=10.0)
def api_call(url):
    response = requests.get(url)
    return response.json()

# Make calls - automatically rate limited
urls = ["https://api.example.com/data/{}".format(i) for i in range(100)]
results = [api_call(url) for url in urls]
```

### As Context Manager

```python
from amorsize import RateLimiter, RateLimitPolicy

# Create rate limiter
policy = RateLimitPolicy(requests_per_second=5.0)
limiter = RateLimiter(policy)

# Use in context
for url in urls:
    with limiter:
        response = requests.get(url)
        process(response)
```

## Features

### Token Bucket Algorithm

The rate limiter uses the token bucket algorithm:
- **Bucket Capacity**: Maximum burst size (tokens available at once)
- **Refill Rate**: Tokens added per second (requests_per_second)
- **Smooth Rate Limiting**: Allows bursts while maintaining average rate

```python
# Allow 10 req/s average, with bursts up to 20
policy = RateLimitPolicy(
    requests_per_second=10.0,
    burst_size=20
)
```

### Thread Safety

All operations are thread-safe:

```python
from concurrent.futures import ThreadPoolExecutor
from amorsize import RateLimiter, RateLimitPolicy

# Shared rate limiter across threads
limiter = RateLimiter(RateLimitPolicy(requests_per_second=10.0))

@with_rate_limit(limiter=limiter)
def api_call(item):
    return process_via_api(item)

# Process in parallel with rate limiting
with ThreadPoolExecutor(max_workers=20) as executor:
    results = list(executor.map(api_call, items))
```

### Combining with Retry

```python
from amorsize import with_rate_limit, with_retry

# Combine rate limiting with retry for robust API calls
@with_rate_limit(requests_per_second=10.0)
@with_retry(max_retries=3)
def robust_api_call(url):
    response = requests.get(url)
    response.raise_for_status()
    return response.json()
```

## Configuration Options

### RateLimitPolicy

```python
from amorsize import RateLimitPolicy

policy = RateLimitPolicy(
    requests_per_second=10.0,  # Maximum average rate
    burst_size=20,              # Maximum burst (default: requests_per_second)
    wait_on_limit=True,         # Wait vs. raise exception (default: True)
    on_wait=callback_func       # Optional callback when waiting
)
```

### Wait vs. Raise

**Waiting Mode (default):**
```python
# Automatically waits when rate limit exceeded
@with_rate_limit(requests_per_second=10.0, wait_on_limit=True)
def api_call(url):
    return requests.get(url).json()
```

**Exception Mode:**
```python
from amorsize import RateLimitExceeded

# Raises RateLimitExceeded when rate limit exceeded
@with_rate_limit(requests_per_second=10.0, wait_on_limit=False)
def api_call(url):
    return requests.get(url).json()

try:
    result = api_call(url)
except RateLimitExceeded:
    print("Rate limit exceeded - try again later")
```

### Monitoring with Callbacks

```python
def log_rate_limit(wait_time):
    print(f"Rate limited - waiting {wait_time:.2f}s")

policy = RateLimitPolicy(
    requests_per_second=10.0,
    on_wait=log_rate_limit
)

limiter = RateLimiter(policy)
```

## Use Cases

### 1. API Rate Limiting

Respect API rate limits:

```python
from amorsize import with_rate_limit

# GitHub API: 5000 requests/hour = 83.3 req/min ≈ 1.39 req/s
@with_rate_limit(requests_per_second=1.0, burst_size=5)
def github_api_call(endpoint):
    response = requests.get(
        f"https://api.github.com/{endpoint}",
        headers={"Authorization": f"token {token}"}
    )
    return response.json()

# Make calls safely
repos = [github_api_call(f"repos/{user}/{repo}") for user in users]
```

### 2. Web Scraping

Avoid overwhelming target servers:

```python
from amorsize import with_rate_limit, with_retry

# Be polite: 1 request per second
@with_rate_limit(requests_per_second=1.0)
@with_retry(max_retries=3)
def scrape_page(url):
    response = requests.get(url)
    return parse_html(response.text)

pages = [scrape_page(url) for url in urls]
```

### 3. Database Connection Pooling

Control database query rate:

```python
from amorsize import RateLimiter, RateLimitPolicy

# Limit to 100 queries/second
db_limiter = RateLimiter(RateLimitPolicy(requests_per_second=100.0))

def execute_query(query):
    with db_limiter:
        return db.execute(query).fetchall()
```

### 4. Parallel Processing with Rate Limits

Combine with Amorsize's `execute()`:

```python
from amorsize import execute, with_rate_limit

# Rate-limited API call
@with_rate_limit(requests_per_second=10.0)
def fetch_data(item_id):
    return requests.get(f"https://api.example.com/items/{item_id}").json()

# Optimize and execute with automatic rate limiting
results = execute(
    fetch_data,
    item_ids,
    prefer_threads_for_io=True
)
```

### 5. Multi-Tier Rate Limiting

Different limits for different resources:

```python
from amorsize import RateLimiter, RateLimitPolicy

# Fast API (100 req/s)
fast_limiter = RateLimiter(RateLimitPolicy(requests_per_second=100.0))

# Slow API (10 req/s)
slow_limiter = RateLimiter(RateLimitPolicy(requests_per_second=10.0))

@with_rate_limit(limiter=fast_limiter)
def fast_api_call():
    return requests.get("https://fast-api.example.com/").json()

@with_rate_limit(limiter=slow_limiter)
def slow_api_call():
    return requests.get("https://slow-api.example.com/").json()
```

## Advanced Usage

### Fractional Rates

For very slow rates:

```python
# 1 request every 2 seconds = 0.5 requests/second
policy = RateLimitPolicy(requests_per_second=0.5)
```

### Dynamic Rate Adjustment

Adjust rate based on conditions:

```python
from amorsize import RateLimiter, RateLimitPolicy

def create_adaptive_limiter(peak_hours):
    if peak_hours:
        rate = 5.0  # Slower during peak
    else:
        rate = 20.0  # Faster off-peak
    
    return RateLimiter(RateLimitPolicy(requests_per_second=rate))

limiter = create_adaptive_limiter(is_peak_hours())
```

### Checking Available Tokens

```python
limiter = RateLimiter(RateLimitPolicy(requests_per_second=10.0))

# Check if request would be allowed
if limiter.try_acquire():
    make_api_call()
else:
    print("Rate limit would be exceeded")

# Get available tokens
tokens = limiter.get_available_tokens()
print(f"{tokens:.1f} requests immediately available")
```

### Manual Acquire/Release

```python
limiter = RateLimiter(RateLimitPolicy(requests_per_second=10.0))

# Acquire token explicitly
limiter.acquire()
try:
    result = make_api_call()
finally:
    pass  # No explicit release needed (token already consumed)
```

## Performance Considerations

### Overhead

Rate limiting adds minimal overhead (~1-5 microseconds per call when tokens available).

### Memory

Each RateLimiter instance uses ~200 bytes of memory.

### Thread Contention

For high-concurrency scenarios (100+ threads), consider:
- Using separate limiters for independent resources
- Batching requests to reduce acquire() calls
- Pre-checking with try_acquire() to avoid waiting

## Best Practices

### 1. Share Limiters Appropriately

```python
# ✅ Good: Share limiter for same API
github_limiter = RateLimiter(RateLimitPolicy(requests_per_second=1.0))

@with_rate_limit(limiter=github_limiter)
def get_repo(name): ...

@with_rate_limit(limiter=github_limiter)
def get_user(name): ...

# ❌ Bad: Separate limiters for same API
@with_rate_limit(requests_per_second=1.0)
def get_repo(name): ...  # Creates new limiter

@with_rate_limit(requests_per_second=1.0)
def get_user(name): ...  # Creates another new limiter
```

### 2. Set Appropriate Burst Size

```python
# For bursty workloads
policy = RateLimitPolicy(
    requests_per_second=10.0,
    burst_size=50  # Allow initial burst
)

# For steady workloads
policy = RateLimitPolicy(
    requests_per_second=10.0,
    burst_size=10  # Match rate
)
```

### 3. Combine with Retries

```python
# Rate limiting prevents overwhelming API
# Retries handle transient failures
@with_rate_limit(requests_per_second=10.0)
@with_retry(max_retries=3)
def api_call(url):
    return requests.get(url).json()
```

### 4. Monitor Rate Limiting

```python
rate_limit_waits = []

def track_waits(wait_time):
    rate_limit_waits.append(wait_time)

policy = RateLimitPolicy(
    requests_per_second=10.0,
    on_wait=track_waits
)

# Analyze after execution
print(f"Rate limited {len(rate_limit_waits)} times")
print(f"Average wait: {sum(rate_limit_waits) / len(rate_limit_waits):.2f}s")
```

## API Reference

### RateLimitPolicy

Configuration for rate limiting behavior.

**Attributes:**
- `requests_per_second` (float): Maximum requests per second
- `burst_size` (int, optional): Maximum burst size (default: requests_per_second)
- `wait_on_limit` (bool): Wait or raise exception (default: True)
- `on_wait` (callable, optional): Callback when waiting

### RateLimiter

Thread-safe rate limiter using token bucket algorithm.

**Methods:**
- `acquire(tokens=1.0)`: Acquire tokens (wait if necessary)
- `try_acquire(tokens=1.0)`: Try to acquire without waiting
- `reset()`: Reset limiter to full capacity
- `get_available_tokens()`: Get current token count
- `__enter__` / `__exit__`: Context manager support

### Decorators

**@with_rate_limit:**
```python
@with_rate_limit(
    requests_per_second=10.0,
    burst_size=None,
    wait_on_limit=True,
    on_wait=None
)
def func(): ...
```

**rate_limited_call:**
```python
result = rate_limited_call(
    func,
    args=(),
    kwargs=None,
    policy=None,
    **rate_limit_kwargs
)
```

### Exceptions

**RateLimitExceeded:**

Raised when rate limit exceeded and `wait_on_limit=False`.

## Integration with Amorsize

Rate limiting works seamlessly with Amorsize's optimization:

```python
from amorsize import execute, with_rate_limit

@with_rate_limit(requests_per_second=10.0)
def api_call(item):
    return requests.get(f"https://api.example.com/items/{item}").json()

# Amorsize optimizes parallelism, rate limiting controls API calls
results = execute(
    api_call,
    items,
    prefer_threads_for_io=True,
    verbose=True
)
```

The combination provides:
- **Optimal Parallelism**: Amorsize finds best n_jobs/chunksize
- **Rate Control**: Rate limiter prevents API throttling
- **Thread Safety**: Both are fully thread-safe

## Troubleshooting

### Rate Limiting Too Aggressive

If seeing excessive waits:

```python
# Increase rate or burst size
policy = RateLimitPolicy(
    requests_per_second=20.0,  # Was 10.0
    burst_size=50               # Was 20
)
```

### Not Rate Limiting Enough

If still hitting API limits:

```python
# Decrease rate
policy = RateLimitPolicy(
    requests_per_second=5.0,   # Was 10.0
    burst_size=5                # Reduce burst
)
```

### Unexpected Waits

Check token refill rate:

```python
limiter = RateLimiter(policy)
print(f"Available tokens: {limiter.get_available_tokens()}")
```

### Memory Issues with Many Limiters

Use shared limiters:

```python
# ✅ Good: One limiter for all API calls
api_limiter = RateLimiter(RateLimitPolicy(requests_per_second=10.0))

functions = [
    with_rate_limit(limiter=api_limiter)(f)
    for f in [func1, func2, func3]
]

# ❌ Bad: New limiter per function
functions = [
    with_rate_limit(requests_per_second=10.0)(f)
    for f in [func1, func2, func3]
]
```

## See Also

- [Retry Pattern Documentation](RETRY_PATTERN.md)
- [Circuit Breaker Documentation](CIRCUIT_BREAKER.md)
- [Web Services Use Case](USE_CASE_WEB_SERVICES.md)
- [API Documentation](API_REFERENCE.md)
