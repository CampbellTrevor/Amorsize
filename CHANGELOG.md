# Changelog

All notable changes to Amorsize will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- Initial release of Amorsize
- Core optimization engine with 3-module pipeline:
  - `system_info.py` - Physical core detection, OS-specific spawn costs, memory constraints
  - `sampling.py` - Dry-run execution with timing, memory, and serialization analysis
  - `optimizer.py` - Break-even analysis using Amdahl's Law
- Main `optimize()` API function
- Support for generators and iterators via `itertools.islice`
- Picklability checking with graceful fallback to serial execution
- Memory-aware optimization: `n_jobs = min(physical_cores, available_RAM / job_RAM)`
- OS-specific overhead estimation (Linux: 0.05s, Windows/macOS: 0.2s)
- Fast-fail triggers for functions too quick to benefit from parallelization
- Comprehensive test suite with 44 tests (100% pass rate):
  - Core functionality tests
  - Expensive function scenarios
  - Edge case handling
  - Performance benchmarks
- Examples:
  - `basic_usage.py` - Quick start examples
  - `amorsize_quickstart.ipynb` - Interactive Jupyter notebook template
  - `dns_entropy_analysis.py` - Real-world security use case (120MB log analysis)
  - Memory-constrained parallelization examples
  - High-end system examples (96 cores, 700GB RAM)
- Complete documentation:
  - README with installation, usage, and API reference
  - Examples README with detailed descriptions
  - Design document (Writeup.md)
  - Per-example documentation
- Package configuration for pip installation
- Optional `psutil` dependency for enhanced physical core detection
- MIT License

### Features
- 🚀 Automatic optimization of parallelization parameters
- 🔍 Intelligent sampling without full workload execution
- 💾 Memory-aware worker allocation
- 🖥️ OS-aware overhead estimation
- ⚡ Physical vs logical core detection
- 🛡️ Safety checks and graceful degradation
- 📊 Speedup estimation based on Amdahl's Law
- ⚠️ Warning system for constraints and edge cases

### Technical Details
- Python 3.7+ support
- No required dependencies (psutil optional)
- Generator/iterator support without consumption
- Pickle size measurement for IPC cost estimation
- Peak memory tracking with tracemalloc
- Clear error propagation
- Verbose mode for debugging
