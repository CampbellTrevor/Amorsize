# Generator Safety Demo

This example demonstrates Amorsize's safe handling of generators and iterators.

## The Problem

Generators can only be consumed once. When `optimize()` samples items from a generator for analysis, those items are consumed. Without proper handling, users would lose data.

## The Solution

Amorsize automatically reconstructs generators using `itertools.chain`, preserving all items. The reconstructed data is available in `result.data`.

## Key Principle

**Always use `result.data` instead of the original generator!**

### ❌ Wrong Way
```python
gen = data_generator()
result = optimize(func, gen)
# Using 'gen' here loses the sampled items!
results = pool.map(func, gen)  # Missing first sample_size items
```

### ✅ Right Way
```python
gen = data_generator()
result = optimize(func, gen)
# Using result.data preserves all items
results = pool.map(func, result.data)  # All items present
```

## Run the Example

```bash
python examples/generator_safety_demo.py
```

## What It Demonstrates

1. **Data Loss Problem**: Shows what happens when using the original generator
2. **Safe Solution**: Demonstrates using `result.data` to preserve all items
3. **Real-world Usage**: Complete example with multiprocessing.Pool
4. **Database Scenario**: Simulates processing database cursor results

## For Lists and Ranges

For non-generator iterables (lists, ranges, tuples), `result.data` simply contains the original data unchanged. The safety mechanism only activates for generators.

## Technical Details

- Uses `itertools.chain(sample, remaining)` to reconstruct the full dataset
- Sample items consumed during dry run are prepended back
- Zero overhead for list/range inputs
- Backward compatible: existing code continues to work
