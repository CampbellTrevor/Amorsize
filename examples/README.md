# Amorsize Examples

This directory contains comprehensive examples demonstrating various use cases for Amorsize.

## Quick Start Examples

### 1. Basic Usage (`basic_usage.py`)
Simple examples showing core functionality:
- CPU-intensive tasks
- I/O-bound tasks
- Quick tasks (serial recommendation)
- Using recommendations with multiprocessing.Pool
- Generator input

**Run:** `python examples/basic_usage.py`

### 2. Jupyter Notebook Quick Start (`amorsize_quickstart.ipynb`)
Interactive notebook template with drop-in placeholders:
- Minimal imports: Just `from amorsize import optimize`
- Clear "PLACE YOUR FUNCTION HERE" and "PLACE YOUR DATASET HERE" sections
- 6-step workflow: Import → Define → Prepare → Analyze → View → Apply
- 3 complete working examples (image processing, data transformation, mathematical computation)

**Run:** `jupyter notebook examples/amorsize_quickstart.ipynb`

**Documentation:** [README_notebook.md](README_notebook.md)

## Advanced Examples

### 3. DNS Log Entropy Analysis (`dns_entropy_analysis.py`)
Real-world security use case:
- Generates 120MB DNS log file with ~1.2 million entries
- Calculates Shannon entropy to detect DGA (Domain Generation Algorithm) malware
- Demonstrates large-scale log processing
- Includes performance comparison showing ~4x speedup

**Run:** `python examples/dns_entropy_analysis.py`

**Documentation:** [README_dns_entropy.md](README_dns_entropy.md)

## Memory-Constrained Parallelization Examples

These examples demonstrate scenarios where optimal `n_jobs` is between 1 and maximum cores due to memory constraints.

### 4. Memory-Constrained Example (`memory_constrained_example.py`)
Shows how memory per task limits worker count:
- High memory tasks (~50MB per task)
- Medium memory tasks (~20MB per task)
- Low memory tasks (~1MB per task)
- Demonstrates: `n_jobs = min(cores, available_memory / memory_per_task)`

**Run:** `python examples/memory_constrained_example.py`

### 5. Intermediate n_jobs Demo (`intermediate_njobs_demo.py`)
Comprehensive demonstration of all scenarios producing intermediate n_jobs:
- Memory constraints
- Small dataset overhead
- Real-world examples (image processing simulation)
- Dataset size effects

**Run:** `python examples/intermediate_njobs_demo.py`

### 6. Reliable Intermediate n_jobs (`reliable_intermediate_njobs.py`)
Uses module-level (picklable) functions with varying memory profiles:
- Best for typical development systems (4 cores, 1-8GB RAM)
- Tests 200MB, 100MB, 50MB, 10MB per task
- Shows intermediate values on memory-constrained systems

**Run:** `python examples/reliable_intermediate_njobs.py`

**Documentation:** [README_intermediate_explained.md](README_intermediate_explained.md)

### 7. High-End System Intermediate (`high_end_system_intermediate.py`)
Specifically for high-resource systems (96 cores, 700GB RAM):
- Demonstrates tasks with 6GB-48GB memory requirements
- Shows intermediate n_jobs on very powerful hardware
- 6GB/task → 93 workers (97% of cores)
- 12GB/task → 46 workers (48% of cores) ✓ Intermediate!
- 24GB/task → 23 workers (24% of cores) ✓ Intermediate!
- 48GB/task → 11 workers (11% of cores) ✓ Intermediate!

**Run:** `python examples/high_end_system_intermediate.py`

**Documentation:** [README_high_end_intermediate.md](README_high_end_intermediate.md)

## General Documentation

- **Memory Constraints Overview:** [README_intermediate_njobs.md](README_intermediate_njobs.md)
- **Why Intermediate Values Vary by System:** [README_intermediate_explained.md](README_intermediate_explained.md)

## Summary

| Example | Use Case | Best For | Key Insight |
|---------|----------|----------|-------------|
| `basic_usage.py` | Learning basics | Everyone | Quick start guide |
| `amorsize_quickstart.ipynb` | Interactive learning | Beginners | Drop-in template |
| `dns_entropy_analysis.py` | Real-world application | Security/Data science | Large-scale processing |
| `memory_constrained_example.py` | Understanding memory limits | Systems with limited RAM | Memory awareness |
| `intermediate_njobs_demo.py` | All scenarios | Understanding edge cases | Comprehensive view |
| `reliable_intermediate_njobs.py` | Typical systems | 4-8 core laptops/desktops | Practical examples |
| `high_end_system_intermediate.py` | High-end hardware | 96+ core servers | Enterprise scenarios |

## Running All Examples

To run all Python examples (excluding Jupyter notebook):

```bash
cd examples
python basic_usage.py
python dns_entropy_analysis.py
python memory_constrained_example.py
python intermediate_njobs_demo.py
python reliable_intermediate_njobs.py
python high_end_system_intermediate.py
```

## Requirements

All examples require the Amorsize package to be installed:

```bash
pip install -e .
```

For full functionality:

```bash
pip install -e ".[full]"
```

The DNS entropy example generates temporary files (~120MB) that are automatically cleaned up after execution.
