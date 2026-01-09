#!/usr/bin/env python3
"""
Example demonstrating the usage of Amorsize optimizer.
"""

import time
from multiprocessing import Pool
from amorsize import optimize


def cpu_intensive_task(n):
    """Simulate a CPU-intensive task."""
    result = 0
    for i in range(1000):
        result += n ** 2 + n ** 0.5
    return result


def io_simulation_task(n):
    """Simulate an I/O-bound task."""
    time.sleep(0.01)
    return n * 2


def quick_task(n):
    """A very quick task."""
    return n * 2


def main():
    print("=" * 70)
    print("Amorsize Optimization Examples")
    print("=" * 70)
    
    # Example 1: CPU-intensive task with large dataset
    print("\n1. CPU-Intensive Task (Large Dataset)")
    print("-" * 70)
    data1 = list(range(1000))
    result1 = optimize(cpu_intensive_task, data1, verbose=True)
    print(f"\n{result1}\n")
    
    # Example 2: I/O-bound task
    print("\n2. I/O-Bound Task")
    print("-" * 70)
    data2 = list(range(100))
    result2 = optimize(io_simulation_task, data2, verbose=True)
    print(f"\n{result2}\n")
    
    # Example 3: Very quick task (should recommend serial)
    print("\n3. Very Quick Task (Should Recommend Serial)")
    print("-" * 70)
    data3 = list(range(100))
    result3 = optimize(quick_task, data3, verbose=True)
    print(f"\n{result3}\n")
    
    # Example 4: Actually use the recommendations
    print("\n4. Applying Recommendations with multiprocessing.Pool")
    print("-" * 70)
    data4 = list(range(500))
    result4 = optimize(cpu_intensive_task, data4)
    
    print(f"Recommendations: n_jobs={result4.n_jobs}, chunksize={result4.chunksize}")
    
    if result4.n_jobs > 1:
        # Parallel execution
        start = time.time()
        with Pool(processes=result4.n_jobs) as pool:
            results = pool.map(cpu_intensive_task, data4, chunksize=result4.chunksize)
        parallel_time = time.time() - start
        
        print(f"Parallel execution time: {parallel_time:.2f}s")
        print(f"Processed {len(results)} items")
    else:
        # Serial execution
        start = time.time()
        results = [cpu_intensive_task(x) for x in data4]
        serial_time = time.time() - start
        
        print(f"Serial execution time: {serial_time:.2f}s")
        print(f"Processed {len(results)} items")
    
    # Example 5: Generator input with safe data preservation
    print("\n5. Generator Input (Safe Data Preservation)")
    print("-" * 70)
    
    def data_generator():
        """
        Simulates reading from a file, database, or network stream.
        Generators can only be consumed once!
        """
        for i in range(1000):
            yield i
    
    # IMPORTANT: When using generators, always use result.data
    gen = data_generator()
    result5 = optimize(cpu_intensive_task, gen, verbose=False)
    print(f"\n{result5}\n")
    
    # Demonstrate safe usage: use result.data instead of original generator
    print("Safe generator usage: Using result.data ensures no data loss")
    print(f"result.data contains all items (not just remaining after sampling)")
    
    # If we want to actually process the data
    if result5.n_jobs > 1:
        print(f"Would process with {result5.n_jobs} workers using result.data")
        # with Pool(processes=result5.n_jobs) as pool:
        #     results = pool.map(cpu_intensive_task, result.data, chunksize=result5.chunksize)
    else:
        print("Would process serially using result.data")
        # results = list(map(cpu_intensive_task, result.data))
    
    print("\n" + "=" * 70)
    print("Examples completed!")
    print("=" * 70)


if __name__ == "__main__":
    main()
