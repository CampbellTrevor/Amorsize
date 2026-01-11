# Structured Logging in Amorsize

Amorsize provides **structured JSON logging** for production observability, enabling easy integration with log aggregation systems (ELK, Splunk, Datadog, CloudWatch, etc.) and machine-readable log analysis.

## Features

- **JSON-formatted logs** - Machine-readable structured data
- **Disabled by default** - Zero impact on existing code
- **Minimal overhead** - Lazy evaluation, optimized for performance
- **Flexible output** - Log to stderr, stdout, or files
- **Configurable levels** - DEBUG, INFO, WARNING, ERROR
- **Production-ready** - Thread-safe and multiprocessing-safe

## Quick Start

```python
from amorsize import configure_logging, optimize

# Enable structured logging
configure_logging(enabled=True, output="stderr", level="INFO")

# Now all optimizations will log structured events
result = optimize(my_function, data)
```

## Configuration

### Basic Usage

```python
from amorsize import configure_logging

# Enable logging to stderr (default)
configure_logging(enabled=True)

# Log to stdout
configure_logging(enabled=True, output="stdout")

# Log to a file
configure_logging(enabled=True, output="/var/log/amorsize.log")

# Set log level to DEBUG for more details
configure_logging(enabled=True, level="DEBUG")

# Disable logging (default behavior)
configure_logging(enabled=False)
```

### API Reference

```python
configure_logging(
    enabled: bool = True,       # Enable/disable logging
    output: str = "stderr",     # Output destination: "stderr", "stdout", or file path
    format_json: bool = True,   # Use JSON formatting (recommended)
    level: str = "INFO"         # Log level: "DEBUG", "INFO", "WARNING", "ERROR"
)
```

## Log Events

Amorsize emits structured log events at key decision points:

### Optimization Lifecycle

| Event | Level | Description |
|-------|-------|-------------|
| `optimization_start` | INFO | Optimization begins |
| `sampling_complete` | INFO | Dry run sampling finished |
| `system_info` | DEBUG | System resources detected |
| `optimization_complete` | INFO | Optimization succeeded |
| `parallelization_rejected` | WARNING | Parallelization not recommended |
| `optimization_constraint` | WARNING | Active constraint detected |
| `error` | ERROR | Error occurred |

### Event Structure

All events are JSON objects with these common fields:

```json
{
  "timestamp": 1234567890.123,
  "level": "INFO",
  "logger": "amorsize",
  "event": "optimization_complete",
  ... event-specific fields ...
}
```

### Event Examples

**optimization_start:**
```json
{
  "timestamp": 1768102286.711,
  "level": "INFO",
  "event": "optimization_start",
  "function": "process_data",
  "data_size": 10000
}
```

**sampling_complete:**
```json
{
  "timestamp": 1768102286.716,
  "level": "INFO",
  "event": "sampling_complete",
  "sample_count": 5,
  "avg_execution_time_seconds": 0.0047,
  "is_picklable": true,
  "workload_type": "cpu_bound"
}
```

**system_info** (DEBUG level):
```json
{
  "timestamp": 1768102286.762,
  "level": "DEBUG",
  "event": "system_info",
  "physical_cores": 8,
  "logical_cores": 16,
  "available_memory_bytes": 16000000000,
  "available_memory_gb": 14.9,
  "multiprocessing_start_method": "fork"
}
```

**optimization_complete:**
```json
{
  "timestamp": 1768102286.744,
  "level": "INFO",
  "event": "optimization_complete",
  "n_jobs": 4,
  "chunksize": 50,
  "estimated_speedup": 3.2,
  "executor_type": "process",
  "cache_hit": false
}
```

**parallelization_rejected:**
```json
{
  "timestamp": 1768102286.750,
  "level": "WARNING",
  "event": "parallelization_rejected",
  "reason": "workload_too_small",
  "estimated_speedup": 1.1
}
```

## Production Integration

### ELK Stack (Elasticsearch, Logstash, Kibana)

```ruby
# Logstash configuration
input {
  file {
    path => "/var/log/amorsize.log"
    codec => "json"
  }
}

filter {
  if [logger] == "amorsize" {
    mutate {
      add_field => { "[@metadata][index]" => "amorsize-logs" }
    }
  }
}

output {
  elasticsearch {
    hosts => ["localhost:9200"]
    index => "%{[@metadata][index]}-%{+YYYY.MM.dd}"
  }
}
```

### Splunk

```python
# Python app with Splunk HTTP Event Collector
from amorsize import configure_logging

# Log to file, then tail with Splunk Universal Forwarder
configure_logging(enabled=True, output="/var/log/amorsize.log", level="INFO")
```

**Splunk queries:**
```
index=amorsize event=optimization_complete 
| stats avg(estimated_speedup) by executor_type

index=amorsize event=parallelization_rejected 
| stats count by reason
```

### Datadog

```python
# Python app with Datadog agent
from amorsize import configure_logging

# Log to file, Datadog agent tails it
configure_logging(enabled=True, output="/var/log/amorsize.log", level="INFO")
```

**Datadog config (datadog.yaml):**
```yaml
logs:
  - type: file
    path: /var/log/amorsize.log
    service: my-app
    source: amorsize
    sourcecategory: optimization
```

### AWS CloudWatch

```python
import watchtower
import logging
from amorsize.structured_logging import get_logger

# Configure Amorsize logger to use CloudWatch
logger = get_logger()
logger.logger.addHandler(watchtower.CloudWatchLogHandler())
logger.enable(output="stderr", level="INFO")
```

### Custom Parsing

```python
import json

# Parse log file
with open('/var/log/amorsize.log', 'r') as f:
    for line in f:
        event = json.loads(line)
        
        if event['event'] == 'optimization_complete':
            print(f"Optimization: n_jobs={event['n_jobs']}, "
                  f"speedup={event['estimated_speedup']:.2f}x")
        
        elif event['event'] == 'parallelization_rejected':
            print(f"Rejection: {event['reason']}")
```

## Use Cases

### Performance Monitoring

Track optimization performance across your application:

```python
# Monitor average speedup achieved
SELECT AVG(estimated_speedup) 
FROM amorsize_logs 
WHERE event = 'optimization_complete'
GROUP BY DATE(timestamp)
```

### Debugging

Debug why parallelization was rejected:

```python
# Find rejections by reason
SELECT reason, COUNT(*) 
FROM amorsize_logs 
WHERE event = 'parallelization_rejected'
GROUP BY reason
```

### Resource Planning

Understand system resource utilization:

```python
# Analyze worker recommendations
SELECT n_jobs, COUNT(*) 
FROM amorsize_logs 
WHERE event = 'optimization_complete'
GROUP BY n_jobs
```

### Alerting

Set up alerts for optimization issues:

```python
# Alert when too many rejections occur
if rejection_rate > 0.5:
    alert("High parallelization rejection rate")
```

## Best Practices

1. **Enable in production** - Structured logging has minimal overhead
2. **Use INFO level** - Provides good balance of detail vs. volume
3. **Log to files** - Easier to rotate and manage than stderr
4. **Aggregate centrally** - Use log aggregation for multi-instance deployments
5. **Monitor metrics** - Track speedup, rejection rates, and worker recommendations
6. **Set up alerts** - Notify on high rejection rates or errors

## Performance Impact

Structured logging is designed for minimal overhead:

- **Disabled (default):** Zero overhead - no function calls executed
- **Enabled:** ~1-2% overhead during optimization only (not during actual computation)
- **Lazy evaluation:** Event data only constructed if logging is enabled
- **Async-ready:** Compatible with async frameworks (logs synchronously)

## Backward Compatibility

Structured logging is **completely backward compatible**:

- Disabled by default - existing code works unchanged
- No breaking changes to the API
- Optional import - `configure_logging` only imported when needed
- Zero impact on performance when disabled

## Example Script

See [`examples/structured_logging_example.py`](../examples/structured_logging_example.py) for a complete working example.

## Troubleshooting

**Q: Logs not appearing?**
- A: Ensure logging is enabled with `configure_logging(enabled=True)`

**Q: Too much log output?**
- A: Reduce level to `WARNING` or `ERROR` to filter events

**Q: JSON parsing errors?**
- A: Each line is a separate JSON object - parse line by line, not as array

**Q: Performance impact concerns?**
- A: Logging overhead is <2% during optimization only. Disable if needed.

**Q: Want custom formatting?**
- A: Set `format_json=False` for plain text, or extend `StructuredLogger` class
