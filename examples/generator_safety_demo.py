#!/usr/bin/env python3
"""
Example demonstrating safe generator handling in Amorsize.

This example shows how to safely use generators with the optimizer,
ensuring no data is lost during the sampling process.
"""

import time
from multiprocessing import Pool
from amorsize import optimize


def expensive_computation(x):
    """Simulate an expensive computation."""
    result = 0
    for i in range(1000):
        result += x ** 2 + x ** 0.5
    return result


def file_reader_simulation():
    """
    Simulates reading data from a file, database, or network stream.
    
    In real applications, this might be:
    - Reading large CSV files line by line
    - Streaming data from a database cursor
    - Processing network responses
    - Reading from a message queue
    
    Generators are efficient because they don't load all data into memory,
    but they can only be consumed once!
    """
    print("Simulating data stream...")
    for i in range(100):
        # Simulate I/O delay
        if i % 20 == 0:
            time.sleep(0.001)
        yield i


def main():
    print("=" * 70)
    print("Generator Safety Example")
    print("=" * 70)
    
    # Example 1: The WRONG way (without using result.data)
    print("\n1. ❌ WRONG: Using original generator")
    print("-" * 70)
    
    gen1 = file_reader_simulation()
    result1 = optimize(expensive_computation, gen1, sample_size=5, verbose=False)
    
    print(f"Optimization result: n_jobs={result1.n_jobs}, chunksize={result1.chunksize}")
    print("\nTrying to use original generator...")
    
    # This will fail! The first 5 items were consumed during sampling
    remaining_data = list(gen1)
    print(f"❌ Problem: Only {len(remaining_data)} items left (expected 100)")
    print(f"❌ Lost the first 5 items that were used for sampling!")
    
    # Example 2: The RIGHT way (using result.data)
    print("\n2. ✅ CORRECT: Using result.data")
    print("-" * 70)
    
    gen2 = file_reader_simulation()
    result2 = optimize(expensive_computation, gen2, sample_size=5, verbose=False)
    
    print(f"Optimization result: n_jobs={result2.n_jobs}, chunksize={result2.chunksize}")
    print("\nUsing result.data instead of original generator...")
    
    # This works perfectly! result.data has all items
    all_data = list(result2.data)
    print(f"✅ Success: Got all {len(all_data)} items (expected 100)")
    print(f"✅ No data lost! All items from [0, 1, 2, ..., 99] preserved")
    
    # Example 3: Using result.data with multiprocessing.Pool
    print("\n3. ✅ Real-world usage with multiprocessing.Pool")
    print("-" * 70)
    
    gen3 = file_reader_simulation()
    result3 = optimize(expensive_computation, gen3, sample_size=5, verbose=True)
    
    print(f"\n{result3}\n")
    
    # Process the data using the recommendations
    if result3.n_jobs > 1:
        print(f"Processing with {result3.n_jobs} workers...")
        start = time.time()
        
        with Pool(processes=result3.n_jobs) as pool:
            # IMPORTANT: Use result.data, not the original generator!
            results = pool.map(
                expensive_computation,
                result3.data,
                chunksize=result3.chunksize
            )
        
        elapsed = time.time() - start
        print(f"✅ Processed {len(results)} items in {elapsed:.2f}s")
    else:
        print("Processing serially...")
        start = time.time()
        
        # IMPORTANT: Use result.data, not the original generator!
        results = list(map(expensive_computation, result3.data))
        
        elapsed = time.time() - start
        print(f"✅ Processed {len(results)} items in {elapsed:.2f}s")
    
    # Example 4: Why this matters - Database cursor simulation
    print("\n4. Real-world scenario: Database query results")
    print("-" * 70)
    
    def database_cursor_simulation():
        """
        Simulates a database cursor that yields rows.
        
        In real code, this might be:
            cursor = conn.execute("SELECT * FROM large_table")
            for row in cursor:
                yield process_row(row)
        """
        print("Fetching rows from database...")
        for row_id in range(1000):
            yield {"id": row_id, "value": row_id * 2}
    
    def process_row(row):
        """Process a database row."""
        result = 0
        for _ in range(100):
            result += row["value"] ** 2
        return result
    
    # Get optimization recommendations
    cursor = database_cursor_simulation()
    result4 = optimize(process_row, cursor, sample_size=10)
    
    print(f"\nOptimization complete:")
    print(f"  Recommended: n_jobs={result4.n_jobs}, chunksize={result4.chunksize}")
    print(f"  Estimated speedup: {result4.estimated_speedup:.2f}x")
    
    # Process all rows using result.data
    print("\nProcessing all 1000 rows using result.data...")
    if result4.n_jobs > 1:
        with Pool(processes=result4.n_jobs) as pool:
            processed_rows = pool.map(
                process_row,
                result4.data,
                chunksize=result4.chunksize
            )
    else:
        processed_rows = list(map(process_row, result4.data))
    
    print(f"✅ Successfully processed {len(processed_rows)} rows")
    print("✅ No rows lost - all data preserved!")
    
    print("\n" + "=" * 70)
    print("Key Takeaways:")
    print("=" * 70)
    print("1. Always use result.data instead of the original generator")
    print("2. result.data contains ALL items, including those sampled")
    print("3. For lists/ranges, result.data is just the original data")
    print("4. This prevents silent data loss in your pipelines")
    print("=" * 70)


if __name__ == "__main__":
    main()
