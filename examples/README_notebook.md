# Amorsize Quick Start Notebook

A beginner-friendly Jupyter notebook template for using Amorsize with minimal setup.

## What's Inside

The notebook (`amorsize_quickstart.ipynb`) provides:

- **Drop-in template**: Clear sections marked "PLACE YOUR FUNCTION HERE" and "PLACE YOUR DATASET HERE"
- **Minimal imports**: Just `from amorsize import optimize`
- **Step-by-step guide**: From setup to execution
- **Multiple examples**: Image processing, data transformation, mathematical computation
- **Advanced options**: Custom parameters for fine-tuning
- **Best practices**: Tips and important notes

## Quick Start

### 1. Open the Notebook

```bash
jupyter notebook examples/amorsize_quickstart.ipynb
```

Or use JupyterLab:
```bash
jupyter lab examples/amorsize_quickstart.ipynb
```

### 2. Follow the Steps

The notebook has 6 simple steps:

1. **Import Amorsize** - One line: `from amorsize import optimize`
2. **Define Your Function** - Replace the example with your function
3. **Prepare Your Dataset** - Replace the example with your data
4. **Run Analysis** - Let Amorsize analyze your workload
5. **View Results** - See the recommendations
6. **Apply Recommendations** - Use the optimized parameters

### 3. Run All Cells

Use `Cell > Run All` or press `Shift+Enter` through each cell.

## Example Usage

Here's what the drop-in template looks like:

```python
# Step 1: Import
from amorsize import optimize

# Step 2: Your Function
def my_function(data_item):
    # Your code here
    return result

# Step 3: Your Dataset
my_data = [1, 2, 3, 4, 5, ...]  # Your data here

# Step 4: Get Recommendations
result = optimize(my_function, my_data, verbose=True)

# Step 5: View Results
print(f"Workers: {result.n_jobs}")
print(f"Chunksize: {result.chunksize}")
print(f"Speedup: {result.estimated_speedup:.2f}x")

# Step 6: Apply
from multiprocessing import Pool
with Pool(processes=result.n_jobs) as pool:
    results = pool.map(my_function, my_data, chunksize=result.chunksize)
```

## Features

### ✅ Beginner-Friendly
- Clear instructions for each step
- Helpful comments and explanations
- No prior knowledge of parallelization needed

### ✅ Comprehensive Examples
The notebook includes three complete examples:
1. **Image Processing** - Processing multiple image files
2. **Data Transformation** - Transforming data records
3. **Mathematical Computation** - Statistical calculations

### ✅ Advanced Options
Learn about optional parameters:
- `sample_size` - Number of items to test (default: 5)
- `target_chunk_duration` - Target time per chunk (default: 0.2s)
- `verbose` - Detailed output (default: False)

### ✅ Best Practices
The notebook includes:
- Function requirements
- When to use serial vs parallel
- Performance tips
- Common pitfalls to avoid

## Requirements

- Python 3.7+
- Jupyter Notebook or JupyterLab
- Amorsize package installed

Install Jupyter if needed:
```bash
pip install jupyter
```

## Use Cases

Perfect for:
- **Data scientists** exploring parallelization options
- **Researchers** processing large datasets
- **Engineers** optimizing batch processing jobs
- **Anyone** who wants to speed up Python code

## Structure

The notebook is organized into sections:

1. **Introduction** - What is Amorsize?
2. **Quick Start (Steps 1-6)** - The main template
3. **Example Use Cases** - Three complete examples
4. **Advanced Options** - Fine-tuning parameters
5. **Important Notes** - Best practices and tips

## Tips for Success

1. **Start Simple**: Use the provided examples first
2. **Test Small**: Start with a small dataset to verify it works
3. **Scale Up**: Once verified, use your full dataset
4. **Check Output**: Always review the recommendations
5. **Measure**: Compare serial vs parallel execution times

## Output Example

When you run the notebook, you'll see output like:

```
Performing dry run sampling...
Average execution time: 0.0012s
Average return size: 24 bytes
Peak memory: 8192 bytes
Estimated total items: 1000
Physical cores: 4

======================================================================
AMORSIZE RECOMMENDATIONS
======================================================================
Recommended: n_jobs=4, chunksize=167
Reason: Parallelization beneficial: 4 workers with chunks of 167
Estimated speedup: 3.2x
```

## Common Questions

**Q: Why does it recommend serial execution?**
A: Your function is too fast or dataset too small. Parallelization overhead would slow it down.

**Q: Can I use this with pandas DataFrames?**
A: Yes! Convert to a list first: `my_data = df['column'].tolist()`

**Q: What if my function isn't picklable?**
A: Amorsize will detect this and recommend serial execution.

**Q: How accurate is the speedup estimate?**
A: Typically within 20-30% of actual speedup, depending on system load.

## Next Steps

After mastering the quick start notebook:

1. Check out `examples/basic_usage.py` for command-line usage
2. Review `examples/dns_entropy_analysis.py` for a real-world example
3. Read the full documentation in `README.md`
4. Run the test suite to see more examples: `pytest tests/`

## Troubleshooting

**Notebook won't run?**
- Make sure Jupyter is installed: `pip install jupyter`
- Verify Amorsize is installed: `pip install -e .`

**Import error?**
- Install from the repository root: `pip install -e .`
- Or ensure Amorsize is in your Python path

**Results seem wrong?**
- Try increasing `sample_size` for more accurate estimates
- Check that your function works correctly in serial first
- Review warnings in the output

## Contributing

Found a typo or have a suggestion? Please open an issue or PR!

---

**Happy parallel processing with Amorsize!** 🚀
