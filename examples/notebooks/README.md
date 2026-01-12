# Amorsize Interactive Notebooks

Welcome to the Amorsize interactive tutorial notebooks! These Jupyter notebooks provide hands-on, visual learning experiences for mastering multiprocessing optimization.

## 📚 Available Notebooks

### 1. Getting Started (`01_getting_started.ipynb`)
**Perfect for newcomers!** Learn the basics of Amorsize in 10 minutes with interactive examples.

**What you'll learn:**
- Why blind parallelization can hurt performance
- How Amorsize analyzes and optimizes workloads
- Hands-on performance comparisons
- Interactive parameter exploration
- Real-world data processing examples

**Prerequisites:** None - start here if you're new to Amorsize!

### 2. Performance Analysis (`02_performance_analysis.ipynb`)
**Deep dive into optimization internals!** Learn how to identify and fix performance bottlenecks.

**What you'll learn:**
- Diagnostic profiling for transparency into optimization decisions
- Bottleneck analysis to identify performance limiters
- Overhead breakdown visualization (spawn, IPC, chunking)
- Real-time monitoring with execution hooks
- Comparative analysis of different configurations
- Complete optimization workflow with dashboard

**Prerequisites:** Complete `01_getting_started.ipynb` first. Basic understanding of parallelization concepts.

### 3. Parameter Tuning (`03_parameter_tuning.ipynb`)
**Master empirical parameter optimization!** Learn advanced tuning strategies for production workloads.

**What you'll learn:**
- Grid search tuning to systematically test configurations
- Quick tuning for rapid prototyping
- Bayesian optimization for intelligent parameter search
- Configuration management (save/load optimal parameters)
- Comparing tuning results with optimizer recommendations
- Complete production tuning workflow with best practices

**Prerequisites:** Complete `01_getting_started.ipynb` first. Recommended: `02_performance_analysis.ipynb`.

### 4. Web Services Integration (`04_use_case_web_services.ipynb`)
**Build optimized web services!** Learn framework-specific patterns for Django, Flask, and FastAPI.

**What you'll learn:**
- Django batch processing and background tasks
- Flask image processing and file handling
- FastAPI async endpoint optimization
- Resource-aware production patterns
- Error handling and retry logic
- Configuration management for deployment
- Performance comparison across frameworks

**Prerequisites:** Complete `01_getting_started.ipynb` first. Basic understanding of web frameworks helpful but not required.

---

## 🚀 Quick Start

### Installation

1. **Install Amorsize:**
```bash
pip install git+https://github.com/CampbellTrevor/Amorsize.git
```

2. **Install Jupyter and visualization dependencies:**
```bash
pip install jupyter matplotlib numpy
```

3. **Optional: Install enhanced features:**
```bash
pip install "git+https://github.com/CampbellTrevor/Amorsize.git#egg=amorsize[full]"
```

### Running the Notebooks

1. **Clone the repository:**
```bash
git clone https://github.com/CampbellTrevor/Amorsize.git
cd Amorsize/examples/notebooks
```

2. **Start Jupyter:**
```bash
jupyter notebook
```

3. **Open a notebook** in your browser and start learning!

---

## 📖 Learning Path

### For Beginners
1. Start with `01_getting_started.ipynb` - Learn the basics
2. Read the [Getting Started Guide](../../docs/GETTING_STARTED.md) for more details
3. Check out [Use Case Guides](../../docs/) for your specific domain

### For Intermediate Users
1. Complete `01_getting_started.ipynb` if you haven't already
2. Work through `02_performance_analysis.ipynb` - Learn to diagnose and optimize
3. Try `03_parameter_tuning.ipynb` - Master advanced tuning strategies
4. Explore `04_use_case_web_services.ipynb` for web service integration
5. Check domain-specific use case guides for your domain

### For Advanced Users
1. Review notebooks `01` through `04` for a complete overview
2. Explore domain-specific interactive notebooks:
   - `04_use_case_web_services.ipynb` - Django, Flask, FastAPI patterns
   - More coming soon: Data Processing, ML Pipelines
3. Read detailed use case guides:
   - [Web Services](../../docs/USE_CASE_WEB_SERVICES.md)
   - [Data Processing](../../docs/USE_CASE_DATA_PROCESSING.md)
   - [ML Pipelines](../../docs/USE_CASE_ML_PIPELINES.md)
4. Study [Performance Optimization](../../docs/PERFORMANCE_OPTIMIZATION.md) for advanced tuning
5. Integrate monitoring hooks with your production systems

---

## 🔧 Dependencies

### Required
- Python 3.7+
- Jupyter Notebook or JupyterLab
- matplotlib (for visualizations)
- numpy (for array operations)

### Optional but Recommended
- psutil (for accurate physical core detection)
- pandas (for data processing examples)
- pillow (for image processing examples)

### Installing All Dependencies
```bash
pip install jupyter matplotlib numpy pandas pillow psutil
```

---

## 💡 Tips for Using the Notebooks

### 1. Run Cells Sequentially
Notebooks are designed to be run from top to bottom. Running cells out of order may cause errors.

### 2. Experiment!
- Modify the code examples
- Try different parameter values
- Test with your own functions and data
- See how changes affect performance

### 3. Restart Kernel If Needed
If you encounter issues, restart the kernel:
- Menu: `Kernel → Restart & Clear Output`
- Or: `Kernel → Restart & Run All`

### 4. Performance Notes
- Timings will vary based on your system
- First run may be slower (caching)
- Close other applications for consistent results

### 5. Visualization Issues
If plots don't appear:
```python
# Add this at the top of the notebook
%matplotlib inline
```

---

## 🐛 Troubleshooting

### Issue: "No module named 'amorsize'"
**Solution:** Install Amorsize:
```bash
pip install git+https://github.com/CampbellTrevor/Amorsize.git
```

### Issue: "No module named 'matplotlib'"
**Solution:** Install matplotlib:
```bash
pip install matplotlib
```

### Issue: Kernel keeps dying
**Solution:** Reduce workload size in examples:
```python
# Instead of:
data = range(10000)

# Try:
data = range(1000)
```

### Issue: Plots look blurry
**Solution:** Increase DPI:
```python
import matplotlib.pyplot as plt
plt.rcParams['figure.dpi'] = 100
```

### Issue: Multiprocessing hangs on Windows
**Solution:** This is expected behavior in Jupyter on Windows. The notebooks will detect this and adjust examples accordingly.

---

## 🌟 What Makes These Notebooks Special?

### Interactive Learning
- Run code and see results immediately
- Modify examples to match your use cases
- Visualizations make concepts concrete

### Real Performance Comparisons
- Actual benchmarks on your system
- See the impact of optimization decisions
- Compare serial vs parallel vs optimized

### Production-Ready Examples
- Not toy examples
- Real-world scenarios
- Copy-paste ready code

### Progressive Complexity
- Start simple, build understanding
- Each section builds on previous
- Clear explanations throughout

---

## 📧 Feedback and Contributions

Found an issue or have a suggestion? 
- Open an issue: https://github.com/CampbellTrevor/Amorsize/issues
- Submit a PR with improvements
- Share your own notebook examples!

---

## 📄 License

These notebooks are part of the Amorsize project and are licensed under the same terms as the main project. See [LICENSE](../../LICENSE) for details.

---

## 🙏 Acknowledgments

These interactive notebooks are inspired by the excellent documentation and tutorials from the Python scientific computing community.

Happy learning! 🚀
