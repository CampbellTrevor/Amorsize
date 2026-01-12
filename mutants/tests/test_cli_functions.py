"""
Test functions for CLI testing.

These are simple, predictable functions that can be used
to test the CLI interface without complex dependencies.
"""


def square(x):
    """Simple function that squares a number."""
    try:
        return int(x) ** 2
    except (ValueError, TypeError):
        return 0


def double(x):
    """Simple function that doubles a number."""
    try:
        return int(x) * 2
    except (ValueError, TypeError):
        return 0


def expensive_computation(x):
    """Expensive function for testing parallelization."""
    try:
        x_int = int(x)
    except (ValueError, TypeError):
        x_int = 0
    
    result = 0
    for i in range(10000):
        result += x_int ** 2
    return result


def fast_computation(x):
    """Fast function that won't benefit from parallelization."""
    try:
        return int(x) + 1
    except (ValueError, TypeError):
        return 1
