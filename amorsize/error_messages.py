"""
Enhanced error messages and actionable guidance for common optimization issues.

This module provides clear, helpful error messages with concrete examples and
step-by-step solutions for users when optimization fails or encounters issues.
"""

from typing import Optional, List


def get_picklability_error_message(
    function_name: Optional[str] = None,
    error_type: Optional[str] = None
) -> str:
    """
    Generate an enhanced error message for function picklability issues.
    
    Args:
        function_name: Name of the function that failed (if available)
        error_type: Type of pickling error (if available)
    
    Returns:
        Detailed error message with actionable guidance
    """
    func_ref = f"'{function_name}'" if function_name else "Function"
    
    message = f"{func_ref} cannot be pickled - multiprocessing requires picklable functions.\n\n"
    message += "COMMON CAUSES:\n"
    message += "  • Lambda functions: lambda x: x**2\n"
    message += "  • Nested functions defined inside another function\n"
    message += "  • Functions using local variables from outer scope\n"
    message += "  • Class methods without proper __reduce__ implementation\n\n"
    message += "SOLUTIONS:\n\n"
    message += "1. Convert lambda to regular function:\n"
    message += "   ❌ func = lambda x: x**2\n"
    message += "   ✅ def func(x): return x**2\n\n"
    message += "2. Move nested function to module level:\n"
    message += "   ❌ def outer():\n"
    message += "       def inner(x): return x**2\n"
    message += "   ✅ def inner(x): return x**2\n"
    message += "      def outer(): pass\n\n"
    message += "3. Use cloudpickle for more flexible serialization:\n"
    message += "   pip install cloudpickle\n"
    message += "   import cloudpickle\n"
    message += "   # Then use concurrent.futures.ProcessPoolExecutor with cloudpickle\n\n"
    message += "4. Use threading instead (if I/O-bound):\n"
    message += "   from concurrent.futures import ThreadPoolExecutor\n"
    message += "   # Threads don't require pickling\n\n"
    message += "NOTE: Serial execution will be used (n_jobs=1)."
    
    return message


def get_data_picklability_error_message(
    index: int,
    error_type: Optional[str] = None,
    item_type: Optional[str] = None
) -> str:
    """
    Generate an enhanced error message for data picklability issues.
    
    Args:
        index: Index of the unpicklable data item
        error_type: Type of pickling error (if available)
        item_type: Type of the unpicklable item (if available)
    
    Returns:
        Detailed error message with actionable guidance
    """
    item_desc = f"Data item at index {index}"
    if item_type:
        item_desc += f" (type: {item_type})"
    
    message = f"{item_desc} cannot be pickled.\n\n"
    message += "COMMON CAUSES:\n"
    message += "  • File handles: open('file.txt')\n"
    message += "  • Database connections: sqlite3.connect(), psycopg2.connect()\n"
    message += "  • Thread locks: threading.Lock()\n"
    message += "  • Socket connections\n"
    message += "  • Objects with __getstate__ that raises errors\n\n"
    message += "SOLUTIONS:\n\n"
    message += "1. Pass file paths instead of file objects:\n"
    message += "   ❌ data = [open(f, 'r') for f in files]\n"
    message += "   ✅ data = files  # Pass paths, open in function\n"
    message += "      def process(filepath):\n"
    message += "          with open(filepath) as f:\n"
    message += "              return process_content(f.read())\n\n"
    message += "2. Pass connection strings instead of connections:\n"
    message += "   ❌ data = [(db_conn, query) for query in queries]\n"
    message += "   ✅ data = queries  # Reconnect in each worker\n"
    message += "      def process(query):\n"
    message += "          conn = create_connection()\n"
    message += "          result = conn.execute(query)\n"
    message += "          conn.close()\n"
    message += "          return result\n\n"
    message += "3. Extract only serializable data:\n"
    message += "   ❌ data = [complex_object for obj in objects]\n"
    message += "   ✅ data = [(obj.id, obj.value) for obj in objects]\n"
    message += "      def process(id, value): ...\n\n"
    message += "4. Use shared memory for large objects (Python 3.8+):\n"
    message += "   from multiprocessing import shared_memory\n"
    message += "   # For numpy arrays, etc.\n\n"
    message += "NOTE: Serial execution will be used (n_jobs=1)."
    
    return message


def get_memory_constraint_message(
    required_mb: float,
    available_mb: float,
    optimal_workers: int,
    constrained_workers: int
) -> str:
    """
    Generate an enhanced message for memory constraint issues.
    
    Args:
        required_mb: Memory required per worker in MB
        available_mb: Available system memory in MB
        optimal_workers: Optimal worker count without memory constraints
        constrained_workers: Worker count limited by memory
    
    Returns:
        Detailed message with actionable guidance
    """
    message = f"Memory constraints limit parallelization:\n"
    message += f"  • Each worker needs: ~{required_mb:.1f} MB\n"
    message += f"  • Available memory: ~{available_mb:.1f} MB\n"
    message += f"  • Optimal workers: {optimal_workers}\n"
    message += f"  • Memory-limited workers: {constrained_workers}\n\n"
    message += "SOLUTIONS:\n\n"
    message += "1. Reduce memory footprint in your function:\n"
    message += "   • Process data in smaller chunks\n"
    message += "   • Use generators instead of lists\n"
    message += "   • Delete intermediate results: del temp_data\n"
    message += "   • Use numpy views instead of copies\n\n"
    message += "2. Use batch processing for large results:\n"
    message += "   from amorsize import process_in_batches\n"
    message += "   results = process_in_batches(\n"
    message += "       func, data,\n"
    message += "       batch_size=100,  # Process 100 at a time\n"
    message += "       max_memory_percent=0.5  # Use 50% of RAM\n"
    message += "   )\n\n"
    message += "3. Use streaming for large datasets:\n"
    message += "   from amorsize import optimize_streaming\n"
    message += "   result = optimize_streaming(func, data)\n"
    message += "   # Process with imap/imap_unordered (no accumulation)\n\n"
    message += "4. Add more RAM to your system\n\n"
    message += f"Current recommendation: n_jobs={constrained_workers}"
    
    return message


def get_no_speedup_benefit_message(
    estimated_speedup: float,
    avg_function_time_ms: float,
    overhead_ms: float,
    min_function_time_ms: float
) -> str:
    """
    Generate an enhanced message when parallelization provides no benefit.
    
    Args:
        estimated_speedup: Estimated speedup (< 1.2 typically)
        avg_function_time_ms: Average function execution time in milliseconds
        overhead_ms: Overhead per worker in milliseconds
        min_function_time_ms: Minimum function time needed for benefit
    
    Returns:
        Detailed message with actionable guidance
    """
    message = f"Parallelization overhead exceeds benefit:\n"
    message += f"  • Estimated speedup: {estimated_speedup:.2f}x (threshold: 1.2x)\n"
    message += f"  • Function time: {avg_function_time_ms:.2f}ms\n"
    message += f"  • Overhead per worker: {overhead_ms:.1f}ms\n\n"
    message += "WHY THIS HAPPENS:\n"
    message += "  Multiprocessing has startup costs (process creation, data serialization)\n"
    message += "  that can exceed the time saved for fast functions or small datasets.\n\n"
    message += "SOLUTIONS:\n\n"
    message += "1. Make your function slower (do more work per call):\n"
    message += "   ❌ def process(x): return x**2  # Too fast\n"
    message += "   ✅ def process(x):\n"
    message += "       # Batch multiple operations\n"
    message += "       return sum(x**i for i in range(100))\n\n"
    message += "2. Process more data per function call:\n"
    message += "   ❌ data = range(100)  # Small dataset\n"
    message += "   ✅ data = range(100000)  # Larger dataset\n\n"
    message += "3. Batch multiple items together:\n"
    message += "   def process_batch(items):\n"
    message += "       return [process_one(x) for x in items]\n"
    message += "   \n"
    message += "   batched_data = [data[i:i+10] for i in range(0, len(data), 10)]\n"
    message += "   result = optimize(process_batch, batched_data)\n\n"
    message += f"4. Function should take more than {min_function_time_ms:.1f}ms for parallel benefit\n\n"
    message += "NOTE: Serial execution recommended (n_jobs=1)."
    
    return message


def get_workload_too_small_message(
    total_items: int,
    speedup_with_2_workers: float,
    min_items_recommended: int
) -> str:
    """
    Generate an enhanced message when workload is too small to benefit.
    
    Args:
        total_items: Total number of items to process
        speedup_with_2_workers: Speedup with 2 workers
        min_items_recommended: Minimum items recommended for parallel benefit
    
    Returns:
        Detailed message with actionable guidance
    """
    message = f"Workload too small for effective parallelization:\n"
    message += f"  • Total items: {total_items}\n"
    message += f"  • Speedup with 2 workers: {speedup_with_2_workers:.2f}x\n"
    message += f"  • Recommended minimum: {min_items_recommended}+ items\n\n"
    message += "WHY THIS HAPPENS:\n"
    message += "  With few items, the overhead of splitting work across workers\n"
    message += "  outweighs the benefit of parallel processing.\n\n"
    message += "SOLUTIONS:\n\n"
    message += "1. Increase dataset size:\n"
    message += "   ❌ data = range(10)  # Too small\n"
    message += "   ✅ data = range(1000)  # Better\n\n"
    message += "2. Make each item more expensive to process:\n"
    message += "   def expensive_process(x):\n"
    message += "       result = 0\n"
    message += "       for i in range(10000):  # More computation\n"
    message += "           result += x ** 2\n"
    message += "       return result\n\n"
    message += "3. Accumulate items before processing:\n"
    message += "   # Process in larger batches when ready\n"
    message += "   if len(accumulated_items) >= 1000:\n"
    message += "       results = optimize(process, accumulated_items)\n\n"
    message += "NOTE: Serial execution recommended (n_jobs=1)."
    
    return message


def get_sampling_failure_message(error: Exception) -> str:
    """
    Generate an enhanced message for sampling failures.
    
    Args:
        error: The exception that occurred during sampling
    
    Returns:
        Detailed message with actionable guidance
    """
    error_name = type(error).__name__
    error_str = str(error)
    
    message = f"Sampling failed during optimization analysis:\n"
    message += f"  • Error type: {error_name}\n"
    message += f"  • Error message: {error_str}\n\n"
    message += "COMMON CAUSES:\n"
    message += "  • Function raises an exception for sample data\n"
    message += "  • Data iterator is exhausted or invalid\n"
    message += "  • Memory allocation failure\n"
    message += "  • Import errors in function code\n\n"
    message += "SOLUTIONS:\n\n"
    message += "1. Test your function with sample data:\n"
    message += "   try:\n"
    message += "       result = func(data[0])\n"
    message += "       print(f\"Success: {result}\")\n"
    message += "   except Exception as e:\n"
    message += "       print(f\"Function error: {e}\")\n\n"
    message += "2. Validate your data:\n"
    message += "   • Ensure data is not empty\n"
    message += "   • Check data types are correct\n"
    message += "   • Verify iterator is not exhausted\n\n"
    message += "3. Handle edge cases in your function:\n"
    message += "   def robust_func(x):\n"
    message += "       if x is None:\n"
    message += "           return default_value\n"
    message += "       try:\n"
    message += "           return process(x)\n"
    message += "       except ValueError:\n"
    message += "           return fallback(x)\n\n"
    message += "4. Use verbose mode for more details:\n"
    message += "   result = optimize(func, data, verbose=True)\n\n"
    message += "NOTE: Serial execution will be used (n_jobs=1)."
    
    return message


def format_warning_with_guidance(warning_type: str, **kwargs) -> List[str]:
    """
    Format warnings with additional helpful guidance.
    
    Args:
        warning_type: Type of warning (e.g., 'io_bound', 'heterogeneous')
        **kwargs: Additional context for the warning
    
    Returns:
        List of warning lines with guidance
    """
    warnings = []
    
    if warning_type == 'io_bound':
        warnings.append("I/O-bound workload detected - multiprocessing may not be optimal")
        warnings.append("Consider using ThreadPoolExecutor for I/O operations:")
        warnings.append("  from concurrent.futures import ThreadPoolExecutor")
        warnings.append("  with ThreadPoolExecutor(max_workers=n_jobs) as pool:")
        warnings.append("      results = list(pool.map(func, data))")
    
    elif warning_type == 'heterogeneous':
        cv = kwargs.get('cv', 0.0)
        warnings.append(f"Heterogeneous workload detected (CV={cv:.2f})")
        warnings.append("Variable execution times may cause load imbalance")
        warnings.append("Consider using imap_unordered for better work distribution:")
        warnings.append("  pool.imap_unordered(func, data, chunksize=1)")
    
    elif warning_type == 'nested_parallelism':
        internal_threads = kwargs.get('internal_threads', 0)
        warnings.append(f"Function uses internal parallelism (~{internal_threads} threads)")
        warnings.append("To avoid oversubscription, workers were reduced")
        warnings.append("Set environment variables to control internal threading:")
        warnings.append("  export OMP_NUM_THREADS=1")
        warnings.append("  export MKL_NUM_THREADS=1")
    
    elif warning_type == 'memory_pressure':
        warnings.append("High memory usage detected during sampling")
        warnings.append("Consider using streaming or batch processing:")
        warnings.append("  from amorsize import optimize_streaming")
        warnings.append("  # or")
        warnings.append("  from amorsize import process_in_batches")
    
    return warnings


def get_helpful_tips() -> str:
    """
    Get general helpful tips for optimization.
    
    Returns:
        String with general optimization tips
    """
    tips = "OPTIMIZATION TIPS:\n\n"
    tips += "1. Profile your function first:\n"
    tips += "   result = optimize(func, data, enable_function_profiling=True)\n"
    tips += "   result.show_function_profile()\n\n"
    tips += "2. Use diagnostic mode for detailed analysis:\n"
    tips += "   result = optimize(func, data, profile=True, verbose=True)\n"
    tips += "   print(result.explain())\n\n"
    tips += "3. Cache results for repeated workloads:\n"
    tips += "   result.save_config('config.json')\n"
    tips += "   # Later: config = load_config('config.json')\n\n"
    tips += "4. Validate optimization accuracy:\n"
    tips += "   from amorsize import validate_optimization\n"
    tips += "   validation = validate_optimization(func, data)\n"
    tips += "   print(f\"Accuracy: {validation.accuracy_percent:.1f}%\")\n\n"
    tips += "5. Compare strategies:\n"
    tips += "   from amorsize import compare_strategies\n"
    tips += "   comparison = compare_strategies(func, data)\n"
    
    return tips
