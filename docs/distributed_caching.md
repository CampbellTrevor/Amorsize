# Distributed Caching with Redis

Amorsize supports distributed caching using Redis, allowing multiple machines to share optimization results. This is particularly useful in distributed computing environments like Kubernetes clusters, distributed batch processing systems, or multi-server deployments.

## Why Distributed Caching?

When running the same functions across multiple machines, each machine would normally need to perform its own dry-run sampling and optimization analysis. With distributed caching:

- **Share Results**: One machine optimizes, all machines benefit
- **Faster Startup**: Skip redundant sampling on worker nodes
- **Consistent Parameters**: All machines use the same optimal settings
- **Reduced Load**: Minimize overhead on shared resources

## Installation

Install Amorsize with Redis support:

```bash
pip install amorsize redis
```

## Quick Start

### 1. Configure Distributed Cache

```python
from amorsize import configure_distributed_cache, optimize

# Connect to Redis
configure_distributed_cache(redis_url="redis://localhost:6379/0")

# Now optimize() will use Redis for caching
result = optimize(my_function, data)
```

### 2. Share Results Across Machines

**Machine 1 (First to optimize):**
```python
from amorsize import configure_distributed_cache, optimize

configure_distributed_cache(redis_url="redis://shared-redis:6379/0")

def process_item(x):
    # Your processing logic
    return x ** 2

data = range(10000)
result = optimize(process_item, data)
# Result is cached in Redis
```

**Machine 2, 3, 4... (Later machines):**
```python
from amorsize import configure_distributed_cache, optimize

# Same Redis connection
configure_distributed_cache(redis_url="redis://shared-redis:6379/0")

def process_item(x):
    return x ** 2

data = range(10000)
result = optimize(process_item, data)
# Instant! Uses cached result from Machine 1
```

## Advanced Usage

### Pre-warming Cache

Pre-populate the cache with optimization results before deploying to production:

```python
from amorsize import configure_distributed_cache, prewarm_distributed_cache

configure_distributed_cache(redis_url="redis://localhost:6379/0")

# Define workload scenarios
workloads = [
    {'data_size': 1000, 'avg_time_per_item': 0.001},
    {'data_size': 10000, 'avg_time_per_item': 0.001},
    {'data_size': 100000, 'avg_time_per_item': 0.001},
]

# Pre-warm cache for all scenarios
count = prewarm_distributed_cache(my_function, workloads)
print(f"Pre-warmed {count} cache entries")
```

### Custom Configuration

Customize Redis connection parameters:

```python
from amorsize import configure_distributed_cache

configure_distributed_cache(
    redis_url="redis://localhost:6379/0",
    key_prefix="amorsize:prod:",  # Namespace for cache keys
    ttl_seconds=86400,  # 24 hours (default: 7 days)
    socket_timeout=5.0,  # Connection timeout
    max_connections=50   # Connection pool size
)
```

### Cache Management

Monitor and manage the distributed cache:

```python
from amorsize import (
    is_distributed_cache_enabled,
    get_distributed_cache_stats,
    clear_distributed_cache,
    disable_distributed_cache
)

# Check status
if is_distributed_cache_enabled():
    print("Distributed cache is active")

# Get statistics
stats = get_distributed_cache_stats()
print(f"Total cached entries: {stats['total_keys']}")
print(f"Memory used: {stats['memory_used'] / (1024**2):.2f} MB")

# Clear specific entries
clear_distributed_cache("func:abc123*")  # Clear for specific function

# Clear all entries
clear_distributed_cache()

# Disable caching
disable_distributed_cache()
```

## Deployment Patterns

### Pattern 1: Kubernetes with Redis

**redis-deployment.yaml:**
```yaml
apiVersion: v1
kind: Service
metadata:
  name: amorsize-redis
spec:
  ports:
  - port: 6379
  selector:
    app: redis
---
apiVersion: apps/v1
kind: Deployment
metadata:
  name: redis
spec:
  replicas: 1
  selector:
    matchLabels:
      app: redis
  template:
    metadata:
      labels:
        app: redis
    spec:
      containers:
      - name: redis
        image: redis:7-alpine
        ports:
        - containerPort: 6379
```

**worker-deployment.yaml:**
```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: worker
spec:
  replicas: 10
  template:
    spec:
      containers:
      - name: worker
        image: myapp:latest
        env:
        - name: REDIS_URL
          value: "redis://amorsize-redis:6379/0"
```

**Application code:**
```python
import os
from amorsize import configure_distributed_cache, optimize

# Configure from environment
redis_url = os.environ.get('REDIS_URL', 'redis://localhost:6379/0')
configure_distributed_cache(redis_url=redis_url)

# Your processing logic
result = optimize(my_function, data)
```

### Pattern 2: AWS ElastiCache

```python
from amorsize import configure_distributed_cache

# Connect to ElastiCache Redis
configure_distributed_cache(
    redis_url="redis://my-cluster.cache.amazonaws.com:6379/0",
    socket_timeout=10.0,  # Higher timeout for network latency
    max_connections=100   # Larger pool for high-traffic apps
)
```

### Pattern 3: Development with Docker Compose

**docker-compose.yml:**
```yaml
version: '3.8'
services:
  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
  
  app:
    build: .
    depends_on:
      - redis
    environment:
      - REDIS_URL=redis://redis:6379/0
```

## Graceful Fallback

Amorsize gracefully falls back to local file-based caching when:
- Redis is not available
- `redis-py` library is not installed
- Connection fails

This ensures your application continues to work even if distributed caching is unavailable.

```python
from amorsize import configure_distributed_cache, optimize

# Try to configure (fails gracefully if Redis unavailable)
success = configure_distributed_cache(redis_url="redis://localhost:6379/0")
if not success:
    print("Using local file cache as fallback")

# optimize() works regardless
result = optimize(my_function, data)
```

## Cache Key Design

Cache keys are computed based on:
1. **Function bytecode hash** - Detects function changes
2. **Data size bucket** - Groups similar workload sizes
3. **Execution time bucket** - Groups similar performance characteristics

This bucketing strategy ensures:
- Cache hits for similar workloads
- Separate cache entries for different functions
- Automatic invalidation when functions change

## System Compatibility

Cache entries include system information and are automatically validated:
- Physical core count
- Available memory (±20% tolerance)
- Multiprocessing start method

Incompatible cache entries are automatically rejected, ensuring optimal recommendations for each system.

## TTL (Time-To-Live)

Cache entries automatically expire after the TTL period (default: 7 days). Redis handles expiration automatically, ensuring stale entries don't persist.

Configure custom TTL:
```python
configure_distributed_cache(
    redis_url="redis://localhost:6379/0",
    ttl_seconds=3600  # 1 hour for frequently-changing workloads
)
```

## Security Considerations

**1. Network Security:**
- Use TLS for Redis connections in production:
  ```python
  configure_distributed_cache(
      redis_url="rediss://secure-redis:6379/0"  # Note: rediss (TLS)
  )
  ```

**2. Authentication:**
- Configure Redis with password:
  ```python
  configure_distributed_cache(
      redis_url="redis://:password@redis:6379/0"
  )
  ```

**3. Network Isolation:**
- Keep Redis in private network
- Use VPC peering or VPN for multi-region deployments

## Monitoring

Monitor distributed cache performance:

```python
from amorsize import get_distributed_cache_stats
import json

stats = get_distributed_cache_stats()
print(json.dumps(stats, indent=2))
```

Output:
```json
{
  "enabled": true,
  "total_keys": 42,
  "memory_used": 1048576,
  "redis_info": {
    "version": "7.0.8",
    "connected_clients": 5,
    "uptime_seconds": 86400
  }
}
```

## Troubleshooting

**Problem: Cache not being used**

Check if distributed cache is enabled:
```python
from amorsize import is_distributed_cache_enabled

print(f"Enabled: {is_distributed_cache_enabled()}")
```

**Problem: Connection timeouts**

Increase timeout values:
```python
configure_distributed_cache(
    redis_url="redis://localhost:6379/0",
    socket_timeout=10.0,
    socket_connect_timeout=10.0
)
```

**Problem: Out of memory errors**

Reduce TTL or clear old entries:
```python
from amorsize import clear_distributed_cache

# Clear old entries
clear_distributed_cache()
```

## Performance Impact

**Latency:**
- Cache hit: ~1-5ms (network + deserialization)
- Cache miss: Full optimization time (~50-500ms)

**Memory:**
- Per cache entry: ~1-2 KB
- 1000 entries: ~1-2 MB

**Network:**
- Minimal bandwidth (~1-2 KB per operation)
- Connection pooling minimizes overhead

## Best Practices

1. **Pre-warm in development**: Generate cache entries before production deployment
2. **Monitor cache stats**: Track hit rates and memory usage
3. **Use namespaces**: Separate cache keys by environment (dev/staging/prod)
4. **Configure appropriate TTL**: Balance freshness vs cache hit rate
5. **Handle failures gracefully**: Always have fallback to local cache

## Example: Complete Production Setup

```python
import os
import logging
from amorsize import (
    configure_distributed_cache,
    is_distributed_cache_enabled,
    optimize
)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Configure distributed cache from environment
redis_url = os.environ.get('REDIS_URL')
if redis_url:
    success = configure_distributed_cache(
        redis_url=redis_url,
        key_prefix=f"amorsize:{os.environ.get('ENV', 'dev')}:",
        ttl_seconds=int(os.environ.get('CACHE_TTL', '604800'))  # Default: 7 days
    )
    if success:
        logger.info("Distributed caching enabled")
    else:
        logger.warning("Distributed caching unavailable, using local cache")
else:
    logger.info("No REDIS_URL configured, using local cache")

# Your application logic
def process_batch(items):
    def process_item(x):
        # Your processing logic
        return complex_computation(x)
    
    # Optimize (uses distributed or local cache)
    result = optimize(process_item, items)
    
    logger.info(
        f"Optimized: n_jobs={result.n_jobs}, "
        f"chunksize={result.chunksize}, "
        f"cached={result.cache_hit}"
    )
    
    # Execute with optimal parameters
    with multiprocessing.Pool(result.n_jobs) as pool:
        results = pool.map(process_item, items, chunksize=result.chunksize)
    
    return results
```
