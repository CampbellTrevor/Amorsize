#!/usr/bin/env python3
"""
Demo script for Amorsize Watch Mode.

This script demonstrates the continuous monitoring capabilities of Amorsize,
showing how to detect changes in optimal parallelization parameters over time.
"""

import time
import random


def demo_1_basic_watch():
    """Demo 1: Basic watch mode usage."""
    print("=" * 80)
    print("DEMO 1: Basic Watch Mode")
    print("=" * 80)
    print("\nThis demo shows basic watch mode monitoring a simple function.")
    print("Press Ctrl+C after 10-20 seconds to stop monitoring.\n")
    
    from amorsize import watch
    
    def process_item(x):
        """Simple CPU-bound function."""
        result = 0
        for i in range(100):
            result += x ** 2
        return result
    
    # Monitor every 5 seconds (short interval for demo)
    watch(
        process_item,
        range(1000),
        interval=5.0,
        verbose=True
    )


def demo_2_changing_workload():
    """Demo 2: Simulate a changing workload."""
    print("=" * 80)
    print("DEMO 2: Changing Workload Simulation")
    print("=" * 80)
    print("\nThis demo simulates a workload that changes over time,")
    print("demonstrating how watch mode detects parameter changes.")
    print("The function will artificially vary its execution time.\n")
    
    from amorsize import watch
    
    # Global state to simulate changing workload
    global workload_intensity
    workload_intensity = 100
    
    def varying_workload(x):
        """Function with varying execution time."""
        result = 0
        for i in range(workload_intensity):
            result += x ** 2
        return result
    
    def update_workload():
        """Background thread to change workload."""
        global workload_intensity
        for _ in range(10):
            time.sleep(6)
            # Randomly vary workload between 50 and 200
            workload_intensity = random.randint(50, 200)
            print(f"\n[Background] Workload intensity changed to {workload_intensity}")
    
    # Start background thread to change workload
    import threading
    thread = threading.Thread(target=update_workload, daemon=True)
    thread.start()
    
    # Monitor every 5 seconds
    watch(
        varying_workload,
        range(1000),
        interval=5.0,
        change_threshold_n_jobs=1,
        change_threshold_speedup=0.15,  # More sensitive to changes
        verbose=True
    )


def demo_3_cli_usage():
    """Demo 3: CLI usage examples."""
    print("=" * 80)
    print("DEMO 3: CLI Usage Examples")
    print("=" * 80)
    print("\nWatch mode can also be used from the command line:\n")
    
    examples = [
        ("Basic monitoring", 
         "python -m amorsize watch math.factorial --data-range 1000 --interval 60"),
        
        ("Custom thresholds",
         "python -m amorsize watch mymodule.func --data-range 5000 \\",
         "  --interval 30 \\",
         "  --change-threshold-n-jobs 2 \\",
         "  --change-threshold-speedup 0.3"),
        
        ("Verbose output",
         "python -m amorsize watch mymodule.func --data-file data.txt \\",
         "  --interval 45 --verbose"),
        
        ("With custom sampling",
         "python -m amorsize watch mymodule.func --data-range 10000 \\",
         "  --interval 120 \\",
         "  --sample-size 10 \\",
         "  --target-chunk-duration 0.3"),
    ]
    
    for i, example in enumerate(examples, 1):
        title = example[0]
        commands = example[1:]
        
        print(f"{i}. {title}:")
        for cmd in commands:
            print(f"   {cmd}")
        print()


def demo_4_python_api():
    """Demo 4: Python API usage."""
    print("=" * 80)
    print("DEMO 4: Python API Usage")
    print("=" * 80)
    print("\nUsing watch mode in Python code:\n")
    
    code_examples = [
        ("Basic usage", '''
from amorsize import watch

def my_function(x):
    return x ** 2

# Monitor with defaults (60s interval)
watch(my_function, range(10000))
'''),
        
        ("Custom parameters", '''
from amorsize import watch

def expensive_function(x):
    result = 0
    for i in range(1000):
        result += x ** 2
    return result

# Monitor every 30 seconds with custom thresholds
watch(
    expensive_function,
    range(5000),
    interval=30.0,
    change_threshold_n_jobs=2,      # Alert if n_jobs changes by 2+
    change_threshold_speedup=0.25,  # Alert on 25% speedup change
    verbose=True
)
'''),
        
        ("Monitoring generator input", '''
from amorsize import watch

def process_item(item):
    # Your processing logic
    return item.upper()

def data_generator():
    """Generate data from a stream."""
    while True:
        yield fetch_next_item()

# Monitor a generator-based workload
watch(
    process_item,
    data_generator(),
    interval=60.0
)
'''),
    ]
    
    for i, (title, code) in enumerate(code_examples, 1):
        print(f"{i}. {title}:")
        print(code)
        print()


def demo_5_use_cases():
    """Demo 5: Common use cases."""
    print("=" * 80)
    print("DEMO 5: Common Use Cases")
    print("=" * 80)
    print("\nWhen to use watch mode:\n")
    
    use_cases = [
        ("Production Monitoring",
         "Monitor a service endpoint that processes requests in parallel",
         "Detect when system load changes affect optimal parallelization"),
        
        ("Performance Regression Detection",
         "Continuously monitor a data pipeline",
         "Alert when optimal parameters change (may indicate regression)"),
        
        ("Workload Characterization",
         "Observe how optimal parameters vary with different data patterns",
         "Learn about your workload's behavior over time"),
        
        ("System Health Monitoring",
         "Track system resources (CPU, memory) impact on parallelization",
         "Detect when hardware constraints change optimal configuration"),
        
        ("Development & Testing",
         "Monitor optimization during load testing",
         "Understand how your code scales under different conditions"),
    ]
    
    for i, (title, *descriptions) in enumerate(use_cases, 1):
        print(f"{i}. {title}")
        for desc in descriptions:
            print(f"   • {desc}")
        print()


def demo_6_interpreting_output():
    """Demo 6: Interpreting watch mode output."""
    print("=" * 80)
    print("DEMO 6: Interpreting Watch Mode Output")
    print("=" * 80)
    print("\nUnderstanding what watch mode tells you:\n")
    
    print("Sample Output:")
    print("-" * 80)
    print("""
[10:15:30] Iteration #1
  n_jobs=4, chunksize=25, speedup=3.20x
------------------------------------------------------------------------

[10:16:30] Iteration #2
  n_jobs=4, chunksize=25, speedup=3.15x
------------------------------------------------------------------------

[10:17:30] Iteration #3
  n_jobs=2, chunksize=50, speedup=1.80x

  ⚠️  CHANGES DETECTED:
    • n_jobs changed: 4 → 2 (Δ-2)
    • Speedup changed: 3.15x → 1.80x (42.9% change)
------------------------------------------------------------------------
""")
    
    print("\nWhat this means:")
    print("  • Iteration #1-2: System stable, parameters consistent")
    print("  • Iteration #3: Significant change detected!")
    print("    - n_jobs decreased (system may be under load)")
    print("    - Speedup decreased (parallelization less effective)")
    print("    - Action: Investigate what changed (system load, data pattern, etc.)\n")
    
    print("Summary Statistics:")
    print("-" * 80)
    print("""
Duration: 10 iterations over 600s

Initial:  n_jobs=4, chunksize=25, speedup=3.20x
Final:    n_jobs=2, chunksize=50, speedup=1.80x

Stability:
  n_jobs: ⚠ Variable
  Speedup variance: 1.40x
""")
    
    print("\nInterpretation:")
    print("  • n_jobs variability suggests changing system conditions")
    print("  • High speedup variance indicates inconsistent performance")
    print("  • Consider: system load, competing processes, memory pressure\n")


def main():
    """Run all demos or a specific one."""
    import sys
    
    demos = {
        '1': demo_1_basic_watch,
        '2': demo_2_changing_workload,
        '3': demo_3_cli_usage,
        '4': demo_4_python_api,
        '5': demo_5_use_cases,
        '6': demo_6_interpreting_output,
    }
    
    if len(sys.argv) > 1 and sys.argv[1] in demos:
        # Run specific demo
        demos[sys.argv[1]]()
    else:
        # Show menu
        print("=" * 80)
        print("Amorsize Watch Mode Demo")
        print("=" * 80)
        print("\nAvailable demos:")
        print("  1. Basic watch mode")
        print("  2. Changing workload simulation")
        print("  3. CLI usage examples")
        print("  4. Python API usage")
        print("  5. Common use cases")
        print("  6. Interpreting output")
        print("\nRun all non-interactive demos? (Demos 3-6)")
        print("Or run a specific demo:")
        print("  python watch_demo.py [1-6]")
        print("\nNote: Demos 1-2 are interactive and will run indefinitely.")
        print("      Press Ctrl+C to stop them.\n")
        
        response = input("Run all non-interactive demos? [y/N]: ")
        if response.lower() in ('y', 'yes'):
            for key in ['3', '4', '5', '6']:
                demos[key]()
                print("\n" + "=" * 80 + "\n")
        else:
            print("\nRun a specific demo with: python watch_demo.py [1-6]")


if __name__ == '__main__':
    main()
