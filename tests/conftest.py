"""
pytest configuration for Amorsize test suite.

This module provides fixtures and configuration that apply to all tests.
"""

import pytest


@pytest.fixture(autouse=True)
def clear_global_caches():
    """
    Clear global caches before each test to prevent test isolation issues.
    
    The amorsize.system_info module uses global variables to cache expensive
    measurements (spawn_cost, chunking_overhead). When tests run in sequence,
    these cached values from previous tests can contaminate later tests,
    causing unexpected behavior.
    
    This fixture automatically clears both caches before each test runs,
    ensuring test isolation and preventing false failures.
    
    Example of the problem this fixes:
    - Test A: System under load → measures spawn_cost = 30ms → caches it
    - Test B: Expects parallelization → uses cached 30ms → rejects parallelization
    - Test B fails because it expected a fresh measurement
    
    The fixture runs automatically for every test (autouse=True).
    """
    from amorsize.system_info import _clear_spawn_cost_cache, _clear_chunking_overhead_cache
    
    # Clear caches before each test
    _clear_spawn_cost_cache()
    _clear_chunking_overhead_cache()
    
    # Yield to run the test
    yield
    
    # Optionally clear again after test (not strictly necessary but ensures cleanup)
    _clear_spawn_cost_cache()
    _clear_chunking_overhead_cache()
