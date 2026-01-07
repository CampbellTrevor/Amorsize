# DNS Log Entropy Analysis Example

This example demonstrates using Amorsize to optimize the analysis of a large DNS log file (>100MB) for detecting suspicious domain names through entropy calculation.

## What It Does

1. **Generates a realistic DNS log file** (120MB by default)
   - Contains ~1.2 million DNS query entries
   - Mixture of legitimate domains (80%) and DGA-like domains (20%)
   - Realistic log format with timestamps, IPs, query types, etc.

2. **Calculates Shannon entropy** for each domain name
   - Higher entropy indicates more randomness (potential DGA/malware)
   - Typical legitimate domains: entropy 2.5-4.0
   - Suspicious DGA domains: entropy 3.5-5.0

3. **Uses Amorsize** to determine optimal parallelization
   - Analyzes the computational cost of entropy calculation
   - Recommends optimal `n_jobs` and `chunksize`
   - Automatically parallelizes if beneficial

4. **Provides performance comparison** (optional)
   - Compares serial vs parallel execution on a subset
   - Shows actual vs estimated speedup

## Running the Example

```bash
python examples/dns_entropy_analysis.py
```

### Expected Output

The script will:
1. Generate a 120MB DNS log file in `/tmp/dns_log_large.txt`
2. Analyze optimal parallelization parameters using Amorsize
3. Process all domains with the recommended settings
4. Display statistics about suspicious domains found
5. Show performance metrics

### Sample Output

```
======================================================================
DNS Log Entropy Analysis with Amorsize
======================================================================

[Step 1] Generating large DNS log file...
  Generated: 10.0 MB (105,644 entries)
  ...
  ✓ DNS log generated successfully!
  Size: 120.00 MB
  Entries: 1,267,612

[Step 2] Analyzing DNS log with Amorsize optimization...
  Amorsize Recommendations:
    n_jobs: 4
    chunksize: 109
    estimated_speedup: 3.98x
    reason: Parallelization beneficial: 4 workers with chunks of 109

  Processed: 1,267,612 domains
  Time: 95.23 seconds

======================================================================
DNS Log Entropy Analysis Summary
======================================================================

Total domains analyzed: 1,267,612
Suspicious domains (entropy > 4.0): 1,229 (0.1%)

Entropy Statistics:
  Average: 2.706
  Minimum: 1.447
  Maximum: 4.248

Top 10 Most Suspicious Domains (highest entropy):
   1. umjtprleknzhbxfaqwi.org                  entropy=4.248 length=19
   2. ltnjwizvobcsqyhgrud.net                  entropy=4.248 length=19
   ...
```

## Understanding Shannon Entropy

Shannon entropy measures the randomness/unpredictability of a string:

```
H(X) = -Σ p(xi) * log2(p(xi))
```

Where:
- `p(xi)` = probability of character xi
- Higher values = more random/unpredictable

### Domain Examples

**Low Entropy (Legitimate):**
- `google.com` - entropy ~2.5 (repeated letters)
- `facebook.com` - entropy ~3.0 (common patterns)

**High Entropy (Suspicious):**
- `xqpzkvjwmrgthbay.com` - entropy ~4.2 (random characters)
- `a8f3k9m2p5x7n1q4.net` - entropy ~4.0 (mixed random)

## Use Cases

This example demonstrates real-world scenarios where Amorsize is beneficial:

1. **Security Analysis**: Processing large volumes of DNS logs for threat detection
2. **DGA Detection**: Identifying domain generation algorithms used by malware
3. **Traffic Analysis**: Analyzing network traffic patterns at scale
4. **Log Processing**: Efficiently processing large log files with complex analysis

## Customization

You can customize the example by modifying:

```python
# File size
target_size_mb = 120  # Change to generate larger/smaller files

# Entropy threshold for suspicious domains
result['suspicious'] = entropy > 4.0  # Adjust threshold

# Computation complexity
for i in range(500):  # Increase/decrease iterations
```

## Performance Notes

- **File Generation**: Takes ~30-60 seconds for 120MB
- **Analysis Time**: 
  - Serial: ~200+ seconds for 1.2M domains
  - Parallel (4 cores): ~50-100 seconds
  - Actual speedup depends on system and function cost
- **Memory Usage**: ~500MB-1GB during processing

## Technical Details

The example includes:
- **Realistic DNS log generation** with proper timestamps, IPs, query types
- **Mixed domain types**: Legitimate domains from common TLDs plus DGA-like random domains
- **Expensive computation**: Multiple passes for pattern detection to simulate real security analysis
- **Proper error handling**: Handles malformed log lines gracefully
- **Statistical analysis**: Calculates mean, min, max entropy across all domains

## Amorsize Benefits Demonstrated

This example shows how Amorsize:
1. **Automatically detects** when parallelization is beneficial
2. **Calculates optimal parameters** (workers and chunksize)
3. **Prevents negative scaling** by recommending serial execution for fast functions
4. **Adapts to workload** - handles both fast and expensive operations appropriately
5. **Provides speedup estimates** before execution

## Requirements

- Python 3.7+
- Amorsize package
- ~200MB free disk space for log file
- Multicore CPU recommended for parallel processing benefits

## Cleanup

The script creates temporary files in `/tmp/`. To clean up:

```bash
rm /tmp/dns_log_large.txt
rm /tmp/dns_log_subset.txt  # If performance comparison was run
```

Or the files will be automatically cleaned up on system reboot.
