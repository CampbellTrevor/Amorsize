"""
pytest configuration for Amorsize test suite.

This module provides fixtures and configuration that apply to all tests.
"""

import pytest
import os


@pytest.fixture(autouse=True)
def clear_global_caches():
    """
    Clear global caches and set testing environment before each test.
    
    This fixture handles test isolation issues:
    
    1. Cache Contamination (Iteration 25):
       The amorsize.system_info module uses global variables to cache expensive
       measurements (spawn_cost, chunking_overhead). When tests run in sequence,
       these cached values from previous tests can contaminate later tests.
    
    2. Nested Parallelism False Positives (Iteration 26):
       The nested parallelism detection in amorsize.sampling can detect
       multiprocessing.pool from other tests running in the same process,
       causing false positive warnings about nested parallelism.
    
    3. Optimization Cache Pollution (Iteration 65):
       The optimization cache stores results from optimize() calls. Tests
       can inadvertently pick up cached results from previous tests.
    
    4. Benchmark Cache Pollution (Iteration 71):
       The benchmark cache stores results from validate_optimization() calls. Tests
       can inadvertently pick up cached benchmark results from previous tests.
    
    Solutions:
    - Clears caches before each test for isolation
    - Sets AMORSIZE_TESTING=1 environment variable to disable nested
      parallelism detection during tests (prevents false positives)
    
    The fixture runs automatically for every test (autouse=True).
    """
    from amorsize.system_info import _clear_spawn_cost_cache, _clear_chunking_overhead_cache
    from amorsize import clear_cache, clear_benchmark_cache
    
    # Set testing environment variable to disable nested parallelism detection
    # This prevents false positives from test runner's multiprocessing usage
    os.environ['AMORSIZE_TESTING'] = '1'
    
    # Clear caches before each test
    _clear_spawn_cost_cache()
    _clear_chunking_overhead_cache()
    clear_cache()  # Clear optimization cache
    clear_benchmark_cache()  # Clear benchmark cache
    
    # Yield to run the test
    yield
    
    # Cleanup after test
    _clear_spawn_cost_cache()
    _clear_chunking_overhead_cache()
    clear_cache()  # Clear optimization cache
    clear_benchmark_cache()  # Clear benchmark cache
    
    # Remove testing environment variable
    if 'AMORSIZE_TESTING' in os.environ:
        del os.environ['AMORSIZE_TESTING']
