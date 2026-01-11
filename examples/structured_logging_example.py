"""
Example demonstrating structured logging in Amorsize.

This example shows how to enable JSON-formatted structured logging
for production observability, integration with log aggregation systems,
and machine-readable log analysis.
"""

import time
from amorsize import configure_logging, optimize


def cpu_bound_task(x):
    """Example CPU-bound task."""
    result = 0
    for i in range(1000):
        result += x ** 2
    return result


def io_simulation_task(x):
    """Example I/O-simulating task."""
    time.sleep(0.001)  # Simulate I/O operation
    return x * 2


def main():
    print("=" * 70)
    print("Amorsize Structured Logging Example")
    print("=" * 70)
    
    # Example 1: Enable logging to stderr (default)
    print("\n[Example 1] Logging to stderr with JSON format")
    print("-" * 70)
    configure_logging(enabled=True, output="stderr", level="INFO")
    
    data = list(range(1000))
    result = optimize(cpu_bound_task, data, sample_size=5, verbose=False)
    
    print(f"\nOptimization result: n_jobs={result.n_jobs}, chunksize={result.chunksize}")
    print("Check stderr for JSON-formatted log events")
    
    # Example 2: Logging to a file
    print("\n[Example 2] Logging to file")
    print("-" * 70)
    log_file = "/tmp/amorsize_example.log"
    configure_logging(enabled=True, output=log_file, level="INFO")
    
    result = optimize(io_simulation_task, data, sample_size=5, verbose=False)
    
    print(f"Optimization result: n_jobs={result.n_jobs}, chunksize={result.chunksize}")
    print(f"Logs written to: {log_file}")
    
    # Show log contents
    print("\nLog file contents:")
    with open(log_file, 'r') as f:
        for line in f:
            print(f"  {line.rstrip()}")
    
    # Example 3: Debug level logging
    print("\n[Example 3] Debug level logging (includes system_info)")
    print("-" * 70)
    configure_logging(enabled=True, output="stderr", level="DEBUG")
    
    result = optimize(cpu_bound_task, list(range(100)), sample_size=3, verbose=False)
    
    print(f"\nOptimization result: n_jobs={result.n_jobs}, chunksize={result.chunksize}")
    print("Debug logs include detailed system information")
    
    # Example 4: Disable logging
    print("\n[Example 4] Disable logging")
    print("-" * 70)
    configure_logging(enabled=False)
    
    result = optimize(cpu_bound_task, list(range(100)), sample_size=3, verbose=False)
    
    print(f"Optimization result: n_jobs={result.n_jobs}, chunksize={result.chunksize}")
    print("No log output (default behavior)")
    
    print("\n" + "=" * 70)
    print("Log Event Types:")
    print("=" * 70)
    print("  • optimization_start - Beginning of optimization")
    print("  • sampling_complete - Dry run sampling finished")
    print("  • system_info - System resource information (DEBUG level)")
    print("  • optimization_complete - Successful optimization")
    print("  • parallelization_rejected - Parallelization not recommended")
    print("  • optimization_constraint - Active constraints")
    print("  • error - Error occurred during optimization")
    
    print("\n" + "=" * 70)
    print("Production Integration:")
    print("=" * 70)
    print("  • ELK Stack: Parse JSON logs with Logstash")
    print("  • Splunk: Ingest JSON logs for analysis")
    print("  • Datadog: Ship logs via file tail or agent")
    print("  • CloudWatch: Use JSON formatter for structured queries")
    print("  • Custom: Parse JSON with standard json library")


if __name__ == "__main__":
    main()
