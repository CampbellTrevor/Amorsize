# Project Design Document: Amorsize
**Dynamic Parallelism Optimizer & Overhead Calculator**

## 1. Core Objective
To build a Python utility that accepts a `job` (function) and `data` (iterable), analyzes the cost-benefit ratio of parallelization, and returns the optimal `n_jobs` and `chunksize` to minimize total execution time. 

The tool does not execute the full workload; it performs a heuristic analysis to prevent "Negative Scaling" (where parallelism is slower than serial execution).

## 2. The Fundamental Equation
The tool operates on the principle of **Amdahl's Law** modified for IPC (Inter-Process Communication) overhead. Parallelism is only viable if:

$$
T_{serial} > (T_{overhead} + \frac{T_{serial}}{N}) + T_{IPC}
$$

Where:
* **T_serial:** Time to run the job on one core.
* **T_overhead:** Time to spawn processes (OS-dependent).
* **T_IPC:** Time to serialize (pickle) input data and deserialize output data.

---

## 3. System Constraints (The Environment)
*Hard limits imposed by the hardware/OS.*

### A. Physical vs. Logical Cores
* **Constraint:** Python's `os.cpu_count()` returns logical cores (Hyper-threading). For CPU-bound tasks (especially NumPy/Matrix operations), hyper-threading often yields 0% gain due to FPU saturation.
* **Requirement:** Tool must distinguish physical cores using libraries like `psutil`.

### B. OS Forking Methods
* **Constraint:** * **Linux:** Uses `fork` (Copy-on-Write). Fast start-up.
    * **Windows/macOS:** Uses `spawn`. Requires reloading the interpreter. High start-up cost.
* **Requirement:** The "Break-even point" calculation must adjust based on `os.name`.

### C. Memory Ceiling (The "OOM Killer")
* **Constraint:** Spawning `N` workers creates `N` copies of the memory footprint.
* **Requirement:** Calculate `Max_Workers = min(CPU_Count, Available_RAM / Est_Job_RAM)`.

---

## 4. Workload Constraints (The Job)
*Variable limits specific to the user's function.*

### A. Input/Output Serialization (Pickle Bloat)
* **Constraint:** If passing large data structures (e.g., a 500MB DataFrame) takes longer than the computation itself, parallelism fails.
* **Requirement:** Measure `sys.getsizeof` or pickle dump length during the sampling phase.

### B. Task Granularity (Chunksize)
* **Constraint:** Python `multiprocessing` has fixed overhead per task submission.
* **Requirement:** Calculate an optimal `chunksize` such that each chunk takes at least **100ms** to execute, amortizing the IPC cost.

---

## 5. Proposed Architecture

### Step 1: The "Dry Run" (Sampling)
Perform a safe execution of the function on a small subset of data.
* **Action:** Take first `K` items (e.g., 5) using `itertools.islice`.
* **Measure:** 1.  Average execution time ($t_{avg}$).
    2.  Return object size (bytes).
    3.  RAM delta (peak memory usage).
* **Fast Fail:** If $t_{avg} < 0.05s$ and `len(data)` is small, return `n_jobs=1`.

### Step 2: Overhead Estimation
Define $C_{spawn}$ based on OS (e.g., 0.05s Linux, 0.2s Windows).
* **Calc:** $T_{est\_total} = t_{avg} \times Total\_Items$.
* **Logic:** If $T_{est\_total} < C_{spawn} \times 2$, parallelism is not worth the "spin up" time.

### Step 3: The Calculator
If the job passes the Fast Fail check:
1.  **Determine Chunksize:** Target chunk duration $\approx$ 0.1s to 0.5s.
    ```python
    optimal_chunksize = max(1, int(0.2 / t_avg))
    ```
2.  **Determine Cores:** Start with physical cores, reduce if Memory Ceiling is hit.

---

## 6. Implementation Checklist

- [ ] **Generator Handling:** Ensure the tool handles iterators/generators without consuming them (use `itertools.tee` or list conversion for the sample).
- [ ] **Picklability Check:** Attempt `pickle.dumps(func)` inside a `try/except` block immediately. If it fails, force Serial execution.
- [ ] **Shared State:** Warn or detect if the user is relying on global variables (which may not propagate in `spawn` contexts).
- [ ] **Exceptions:** Ensure the "Dry Run" propagates errors clearly, rather than burying them in a process pool crash.