"""
Input Validation Example for Amorsize

This example demonstrates the input validation features of the optimize() function,
showing how it protects against invalid parameters and provides clear error messages.
"""

from amorsize import optimize


def simple_function(x):
    """A simple function for demonstration."""
    return x * 2


def demonstrate_valid_inputs():
    """Show examples of valid inputs that pass validation."""
    print("=" * 70)
    print("VALID INPUTS - These all work correctly")
    print("=" * 70)
    
    # Example 1: Minimal valid parameters
    print("\n1. Minimal valid parameters:")
    result = optimize(simple_function, [1, 2, 3], sample_size=1)
    print(f"   ✓ Works: n_jobs={result.n_jobs}, chunksize={result.chunksize}")
    
    # Example 2: Maximum valid parameters
    print("\n2. Maximum valid parameters:")
    result = optimize(simple_function, range(10000), sample_size=10000, target_chunk_duration=3600)
    print(f"   ✓ Works: n_jobs={result.n_jobs}, chunksize={result.chunksize}")
    
    # Example 3: Default parameters
    print("\n3. Default parameters:")
    result = optimize(simple_function, [1, 2, 3])
    print(f"   ✓ Works: n_jobs={result.n_jobs}, chunksize={result.chunksize}")
    
    # Example 4: Generator input
    print("\n4. Generator input:")
    result = optimize(simple_function, (x for x in range(100)))
    print(f"   ✓ Works: n_jobs={result.n_jobs}, chunksize={result.chunksize}")
    
    # Example 5: All optional parameters
    print("\n5. All optional parameters enabled:")
    result = optimize(
        simple_function,
        range(100),
        sample_size=10,
        target_chunk_duration=0.5,
        verbose=False,
        use_spawn_benchmark=False,
        use_chunking_benchmark=False,
        profile=True
    )
    print(f"   ✓ Works: n_jobs={result.n_jobs}, chunksize={result.chunksize}")
    print(f"   Profile available: {result.profile is not None}")


def demonstrate_invalid_inputs():
    """Show examples of invalid inputs that raise ValueError."""
    print("\n" + "=" * 70)
    print("INVALID INPUTS - These raise ValueError with clear messages")
    print("=" * 70)
    
    # Example 1: None func
    print("\n1. None func:")
    try:
        optimize(None, [1, 2, 3])
    except ValueError as e:
        print(f"   ✗ ValueError: {e}")
    
    # Example 2: Non-callable func
    print("\n2. Non-callable func:")
    try:
        optimize(123, [1, 2, 3])
    except ValueError as e:
        print(f"   ✗ ValueError: {e}")
    
    # Example 3: None data
    print("\n3. None data:")
    try:
        optimize(simple_function, None)
    except ValueError as e:
        print(f"   ✗ ValueError: {e}")
    
    # Example 4: Non-iterable data
    print("\n4. Non-iterable data:")
    try:
        optimize(simple_function, 123)
    except ValueError as e:
        print(f"   ✗ ValueError: {e}")
    
    # Example 5: Negative sample_size
    print("\n5. Negative sample_size:")
    try:
        optimize(simple_function, [1, 2, 3], sample_size=-1)
    except ValueError as e:
        print(f"   ✗ ValueError: {e}")
    
    # Example 6: Zero sample_size
    print("\n6. Zero sample_size:")
    try:
        optimize(simple_function, [1, 2, 3], sample_size=0)
    except ValueError as e:
        print(f"   ✗ ValueError: {e}")
    
    # Example 7: Too large sample_size
    print("\n7. Too large sample_size:")
    try:
        optimize(simple_function, [1, 2, 3], sample_size=100000)
    except ValueError as e:
        print(f"   ✗ ValueError: {e}")
    
    # Example 8: Non-integer sample_size
    print("\n8. Non-integer sample_size:")
    try:
        optimize(simple_function, [1, 2, 3], sample_size=5.5)
    except ValueError as e:
        print(f"   ✗ ValueError: {e}")
    
    # Example 9: Negative target_chunk_duration
    print("\n9. Negative target_chunk_duration:")
    try:
        optimize(simple_function, [1, 2, 3], target_chunk_duration=-0.1)
    except ValueError as e:
        print(f"   ✗ ValueError: {e}")
    
    # Example 10: Zero target_chunk_duration
    print("\n10. Zero target_chunk_duration:")
    try:
        optimize(simple_function, [1, 2, 3], target_chunk_duration=0)
    except ValueError as e:
        print(f"   ✗ ValueError: {e}")
    
    # Example 11: Too large target_chunk_duration
    print("\n11. Too large target_chunk_duration:")
    try:
        optimize(simple_function, [1, 2, 3], target_chunk_duration=10000)
    except ValueError as e:
        print(f"   ✗ ValueError: {e}")
    
    # Example 12: Non-boolean verbose
    print("\n12. Non-boolean verbose:")
    try:
        optimize(simple_function, [1, 2, 3], verbose=1)
    except ValueError as e:
        print(f"   ✗ ValueError: {e}")
    
    # Example 13: Non-boolean profile
    print("\n13. Non-boolean profile:")
    try:
        optimize(simple_function, [1, 2, 3], profile="true")
    except ValueError as e:
        print(f"   ✗ ValueError: {e}")


def demonstrate_best_practices():
    """Show best practices for using optimize() safely."""
    print("\n" + "=" * 70)
    print("BEST PRACTICES - Recommended patterns")
    print("=" * 70)
    
    print("\n1. Validate your function before optimizing:")
    print("   Check if your function is picklable first")
    
    def my_function(x):
        return x ** 2
    
    result = optimize(my_function, range(100))
    if result.n_jobs == 1 and "not picklable" in result.reason.lower():
        print("   ⚠ Function not picklable - using serial execution")
    else:
        print(f"   ✓ Function is picklable - parallel execution recommended")
    
    print("\n2. Use reasonable sample_size values:")
    print("   - Small datasets (< 100 items): sample_size=5 (default)")
    print("   - Medium datasets (100-10K items): sample_size=10-50")
    print("   - Large datasets (> 10K items): sample_size=50-100")
    print("   - Never exceed 10000 (validation limit)")
    
    print("\n3. Adjust target_chunk_duration based on function cost:")
    print("   - Fast functions (< 1ms): target_chunk_duration=0.1-0.5")
    print("   - Medium functions (1-100ms): target_chunk_duration=0.2 (default)")
    print("   - Slow functions (> 100ms): target_chunk_duration=0.5-2.0")
    print("   - Never exceed 3600 (validation limit)")
    
    print("\n4. Handle validation errors gracefully:")
    print("   Use try-except to catch and handle ValueError")
    
    def safe_optimize(func, data, **kwargs):
        """Wrapper that handles validation errors."""
        try:
            return optimize(func, data, **kwargs)
        except ValueError as e:
            print(f"   ⚠ Validation error: {e}")
            print(f"   → Falling back to safe defaults")
            return optimize(func, data)  # Use defaults
    
    result = safe_optimize(simple_function, [1, 2, 3], sample_size=5)
    print(f"   ✓ Safe optimization completed: n_jobs={result.n_jobs}")


def main():
    """Run all demonstrations."""
    print("\n" + "=" * 70)
    print("AMORSIZE INPUT VALIDATION DEMONSTRATION")
    print("=" * 70)
    
    demonstrate_valid_inputs()
    demonstrate_invalid_inputs()
    demonstrate_best_practices()
    
    print("\n" + "=" * 70)
    print("Key Takeaways:")
    print("=" * 70)
    print("""
1. All parameters are validated before optimization begins
2. Invalid parameters raise ValueError with clear, actionable messages
3. Validation prevents common errors like:
   - None or non-callable functions
   - None or non-iterable data
   - Negative, zero, or unreasonably large numeric parameters
   - Wrong types for boolean parameters

4. Validation ensures:
   - Early failure with clear error messages
   - Protection against memory exhaustion (sample_size limit)
   - Protection against unreasonable parameter values
   - Type safety for all parameters

5. The validation does NOT prevent:
   - Empty data (valid input, handled by optimizer)
   - Unpicklable functions (caught by picklability check)
   - Unpicklable data (caught by data picklability check)
   - These are optimization-time issues, not validation errors
    """)


if __name__ == "__main__":
    main()
