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
    
    This fixture handles two test isolation issues:
    
    1. Cache Contamination (Iteration 25):
       The amorsize.system_info module uses global variables to cache expensive
       measurements (spawn_cost, chunking_overhead). When tests run in sequence,
       these cached values from previous tests can contaminate later tests.
    
    2. Nested Parallelism False Positives (Iteration 26):
       The nested parallelism detection in amorsize.sampling can detect
       multiprocessing.pool from other tests running in the same process,
       causing false positive warnings about nested parallelism.
    
    Solutions:
    - Clears caches before each test for isolation
    - Sets AMORSIZE_TESTING=1 environment variable to disable nested
      parallelism detection during tests (prevents false positives)
    
    Example problems this fixes:
    - Test A: System under load → measures spawn_cost = 30ms → caches it
    - Test B: Expects parallelization → uses cached 30ms → rejects parallelization
    - Test B fails because it expected a fresh measurement
    
    - Test A: Uses multiprocessing.Pool → loads multiprocessing.pool module
    - Test B: Simple function → detects multiprocessing.pool in sys.modules → 
      false positive nested parallelism warning
    
    The fixture runs automatically for every test (autouse=True).
    """
    from amorsize.system_info import _clear_spawn_cost_cache, _clear_chunking_overhead_cache
    
    # Set testing environment variable to disable nested parallelism detection
    # This prevents false positives from test runner's multiprocessing usage
    os.environ['AMORSIZE_TESTING'] = '1'
    
    # Clear caches before each test
    _clear_spawn_cost_cache()
    _clear_chunking_overhead_cache()
    
    # Yield to run the test
    yield
    
    # Cleanup after test
    _clear_spawn_cost_cache()
    _clear_chunking_overhead_cache()
    
    # Remove testing environment variable
    if 'AMORSIZE_TESTING' in os.environ:
        del os.environ['AMORSIZE_TESTING']
