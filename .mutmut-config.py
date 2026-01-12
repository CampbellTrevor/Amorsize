"""
Mutation testing configuration for Amorsize.

This configuration file controls which code is subject to mutation testing
and how the tests are executed.

Mutation testing helps validate test suite quality by introducing small
changes (mutations) to the source code and verifying that tests catch them.
"""

def pre_mutation(context):
    """Called before each mutation is applied."""
    pass


def init():
    """
    Initialize mutation testing configuration.
    
    Returns a dictionary with mutation testing parameters.
    """
    return {
        # Paths to mutate (core library code only)
        'paths_to_mutate': 'amorsize/',
        
        # Test command to run after each mutation
        'test_command': 'python -m pytest tests/ -x --tb=short -q',
        
        # Exclude patterns for files we don't want to mutate
        # We exclude:
        # - __init__.py (mostly imports, low mutation value)
        # - __main__.py (CLI entry point, tested differently)
        # - dashboards.py (template strings, low mutation value)
        # - monitoring.py (optional dependency, integration focused)
        'exclude_patterns': [
            '*/__init__.py',
            '*/__main__.py',
            '*/dashboards.py',
        ],
        
        # Focus on core modules with high mutation testing value
        # These are the modules where catching bugs is most critical
        'priority_paths': [
            'amorsize/optimizer.py',      # Core optimization logic
            'amorsize/sampling.py',       # Dry run and measurement
            'amorsize/system_info.py',    # Hardware detection
            'amorsize/cost_model.py',     # Cost calculations
            'amorsize/cache.py',          # Caching logic
        ],
    }
