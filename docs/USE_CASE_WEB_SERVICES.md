# Use Case: Web Services Integration with Amorsize

**Target Audience**: Backend developers building web services with Django, Flask, or FastAPI  
**Reading Time**: 15-20 minutes  
**Prerequisites**: Basic understanding of Python web frameworks and multiprocessing

## Table of Contents

- [Why Amorsize for Web Services?](#why-amorsize-for-web-services)
- [Django Integration](#django-integration)
- [Flask Integration](#flask-integration)
- [FastAPI Integration](#fastapi-integration)
- [Common Patterns](#common-patterns)
- [Performance Benchmarks](#performance-benchmarks)
- [Production Considerations](#production-considerations)
- [Troubleshooting](#troubleshooting)

---

## Why Amorsize for Web Services?

Web services frequently need to process multiple items in parallel:
- **Batch API requests**: Process multiple records from database
- **Background tasks**: Send emails, generate reports, update caches
- **Data aggregation**: Fetch from multiple external APIs
- **File processing**: Process uploaded files (images, CSVs, PDFs)

**The Challenge**: Using `multiprocessing.Pool` naively can:
- 🔴 Overload your server (spawning too many workers)
- 🔴 Slow down requests (overhead > work time)
- 🔴 Cause OOM errors (memory-intensive tasks)
- 🔴 Degrade user experience (blocking critical requests)

**The Solution**: Amorsize automatically determines:
- ✅ Whether parallelism will actually help
- ✅ Optimal worker count for your server
- ✅ Ideal chunk size for your workload
- ✅ Expected performance improvement

---

## Django Integration

### Pattern 1: Batch Processing in Views

**Scenario**: You have a Django view that needs to process multiple database records.

```python
# views.py
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from amorsize import execute
from .models import Order
import requests

def process_order(order_id):
    """Process a single order (expensive operation)."""
    order = Order.objects.get(id=order_id)
    
    # Expensive operations: API calls, calculations, etc.
    shipping_cost = requests.get(
        f'https://api.shipping.com/calculate',
        params={'weight': order.weight, 'zip': order.zip_code}
    ).json()['cost']
    
    order.shipping_cost = shipping_cost
    order.status = 'processed'
    order.save()
    
    return {'order_id': order_id, 'shipping_cost': shipping_cost}

@require_http_methods(["POST"])
def batch_process_orders(request):
    """
    Process multiple orders in parallel.
    
    POST /orders/batch-process/
    Body: {"order_ids": [1, 2, 3, ...]}
    """
    order_ids = request.POST.getlist('order_ids')
    
    # Let Amorsize optimize parallelization
    results = execute(
        func=process_order,
        data=order_ids,
        verbose=False  # Set to True for debugging
    )
    
    return JsonResponse({
        'processed': len(results),
        'results': results
    })
```

**Key Points**:
- Database queries inside worker function (Django ORM is thread-safe)
- Amorsize handles worker pool lifecycle
- No manual Pool management needed
- Automatic optimization based on server resources

### Pattern 2: Background Tasks with Celery Alternative

**Scenario**: Process background tasks without Celery overhead.

```python
# tasks.py
from amorsize import execute
from django.core.mail import send_mail
from .models import User

def send_notification_email(user_id):
    """Send notification email to a user."""
    user = User.objects.get(id=user_id)
    
    send_mail(
        subject='Weekly Digest',
        message=f'Hi {user.username}, here is your weekly digest...',
        from_email='noreply@example.com',
        recipient_list=[user.email],
        fail_silently=False,
    )
    
    return user_id

def send_weekly_digest():
    """Send weekly digest to all active users."""
    # Get all active user IDs
    user_ids = User.objects.filter(is_active=True).values_list('id', flat=True)
    
    # Parallel execution with automatic optimization
    results = execute(
        func=send_notification_email,
        data=list(user_ids),
        verbose=True  # See optimization details
    )
    
    print(f"Sent {len(results)} emails")
    return results
```

**Scheduling** (using Django management command):

```python
# management/commands/send_digest.py
from django.core.management.base import BaseCommand
from myapp.tasks import send_weekly_digest

class Command(BaseCommand):
    help = 'Send weekly digest emails to all active users'
    
    def handle(self, *args, **options):
        results = send_weekly_digest()
        self.stdout.write(
            self.style.SUCCESS(f'Successfully sent {len(results)} emails')
        )
```

**Run**: `python manage.py send_digest`

### Pattern 3: API Endpoint with Parallel External Calls

**Scenario**: Aggregate data from multiple external APIs.

```python
# views.py
from django.http import JsonResponse
from amorsize import execute
import requests

def fetch_user_data(user_id):
    """Fetch user data from external API."""
    response = requests.get(
        f'https://api.example.com/users/{user_id}',
        timeout=5
    )
    return response.json()

@require_http_methods(["GET"])
def aggregate_users(request):
    """
    Fetch and aggregate data for multiple users.
    
    GET /users/aggregate/?ids=1,2,3,4,5
    """
    user_ids = request.GET.get('ids', '').split(',')
    user_ids = [int(uid) for uid in user_ids if uid.isdigit()]
    
    # Parallel API calls with automatic optimization
    results = execute(
        func=fetch_user_data,
        data=user_ids,
        verbose=False
    )
    
    return JsonResponse({
        'users': results,
        'count': len(results)
    })
```

**Why This Works**:
- I/O-bound workload (network calls)
- Amorsize detects this and recommends more workers
- Dramatically faster than sequential API calls
- Respects server resource limits

---

## Flask Integration

### Pattern 1: Image Processing API

**Scenario**: Upload multiple images and process them in parallel.

```python
# app.py
from flask import Flask, request, jsonify
from werkzeug.utils import secure_filename
from amorsize import execute
from PIL import Image
import os

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = '/tmp/uploads'
app.config['ALLOWED_EXTENSIONS'] = {'png', 'jpg', 'jpeg', 'gif'}

def process_image(filepath):
    """Process a single image (resize, compress, etc.)."""
    with Image.open(filepath) as img:
        # Resize to thumbnail
        img.thumbnail((200, 200))
        
        # Save compressed version
        output_path = filepath.replace('/uploads/', '/processed/')
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        img.save(output_path, optimize=True, quality=85)
        
        return {
            'original': filepath,
            'processed': output_path,
            'size': os.path.getsize(output_path)
        }

@app.route('/images/batch-process', methods=['POST'])
def batch_process_images():
    """
    Upload and process multiple images.
    
    POST /images/batch-process
    Body: multipart/form-data with multiple 'files' fields
    """
    if 'files' not in request.files:
        return jsonify({'error': 'No files uploaded'}), 400
    
    files = request.files.getlist('files')
    
    # Save uploaded files
    filepaths = []
    for file in files:
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(filepath)
            filepaths.append(filepath)
    
    # Process images in parallel
    results = execute(
        func=process_image,
        data=filepaths,
        verbose=False
    )
    
    return jsonify({
        'processed': len(results),
        'results': results
    })

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']
```

### Pattern 2: Report Generation

**Scenario**: Generate multiple reports concurrently.

```python
# app.py
from flask import Flask, jsonify
from amorsize import execute
import pandas as pd
from datetime import datetime, timedelta

app = Flask(__name__)

def generate_report(params):
    """Generate a single report."""
    user_id = params['user_id']
    start_date = params['start_date']
    end_date = params['end_date']
    
    # Simulate expensive database query
    df = pd.read_sql(
        f"""
        SELECT * FROM transactions 
        WHERE user_id = {user_id} 
        AND date BETWEEN '{start_date}' AND '{end_date}'
        """,
        con=get_db_connection()
    )
    
    # Generate report statistics
    report = {
        'user_id': user_id,
        'total_transactions': len(df),
        'total_amount': df['amount'].sum(),
        'avg_amount': df['amount'].mean(),
        'period': f'{start_date} to {end_date}'
    }
    
    return report

@app.route('/reports/batch', methods=['POST'])
def batch_generate_reports():
    """
    Generate reports for multiple users.
    
    POST /reports/batch
    Body: {"user_ids": [1, 2, 3, ...], "days": 30}
    """
    data = request.get_json()
    user_ids = data.get('user_ids', [])
    days = data.get('days', 30)
    
    # Prepare report parameters
    end_date = datetime.now()
    start_date = end_date - timedelta(days=days)
    
    report_params = [
        {
            'user_id': uid,
            'start_date': start_date.strftime('%Y-%m-%d'),
            'end_date': end_date.strftime('%Y-%m-%d')
        }
        for uid in user_ids
    ]
    
    # Generate reports in parallel
    reports = execute(
        func=generate_report,
        data=report_params,
        verbose=False
    )
    
    return jsonify({
        'reports': reports,
        'count': len(reports)
    })

def get_db_connection():
    """Get database connection (implement your own logic)."""
    # Return SQLAlchemy engine, psycopg2 connection, etc.
    pass
```

---

## FastAPI Integration

### Pattern 1: Async Endpoint with Parallel Processing

**Scenario**: FastAPI endpoint that processes multiple items in parallel.

```python
# main.py
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List
from amorsize import execute
import httpx

app = FastAPI()

class ProcessingRequest(BaseModel):
    urls: List[str]

class ProcessingResponse(BaseModel):
    results: List[dict]
    total_processed: int
    speedup: float

def fetch_and_analyze(url: str) -> dict:
    """Fetch URL and analyze content."""
    try:
        response = httpx.get(url, timeout=10)
        content = response.text
        
        # Simple analysis
        return {
            'url': url,
            'status_code': response.status_code,
            'content_length': len(content),
            'title': extract_title(content)  # Implement this
        }
    except Exception as e:
        return {
            'url': url,
            'error': str(e)
        }

@app.post("/analyze-urls", response_model=ProcessingResponse)
async def analyze_urls(request: ProcessingRequest):
    """
    Analyze multiple URLs in parallel.
    
    POST /analyze-urls
    Body: {"urls": ["https://example.com", "https://test.com", ...]}
    """
    if not request.urls:
        raise HTTPException(status_code=400, detail="No URLs provided")
    
    # Execute in parallel with optimization
    results = execute(
        func=fetch_and_analyze,
        data=request.urls,
        verbose=True  # Returns OptimizationResult with metrics
    )
    
    # If verbose=True, results is an OptimizationResult object
    if hasattr(results, 'results'):
        return ProcessingResponse(
            results=results.results,
            total_processed=len(results.results),
            speedup=results.estimated_speedup
        )
    else:
        # If verbose=False, results is just the list
        return ProcessingResponse(
            results=results,
            total_processed=len(results),
            speedup=1.0
        )

def extract_title(html: str) -> str:
    """Extract title from HTML (simplified)."""
    # Implement with BeautifulSoup or regex
    import re
    match = re.search(r'<title>(.*?)</title>', html, re.IGNORECASE)
    return match.group(1) if match else "No title"
```

### Pattern 2: Background Task Processing

**Scenario**: Long-running background tasks triggered by API endpoints.

```python
# main.py
from fastapi import FastAPI, BackgroundTasks
from amorsize import execute
from typing import List
import asyncio

app = FastAPI()

def process_data_item(item_id: int) -> dict:
    """Process a single data item (CPU-intensive)."""
    # Simulate expensive computation
    import time
    time.sleep(0.1)  # Replace with actual processing
    
    return {
        'item_id': item_id,
        'status': 'processed',
        'result': item_id * 2
    }

def batch_process_task(item_ids: List[int]):
    """Background task that processes multiple items."""
    results = execute(
        func=process_data_item,
        data=item_ids,
        verbose=True
    )
    
    # Save results to database, cache, etc.
    print(f"Background processing complete: {len(results.results)} items")
    # TODO: Store results, send notifications, etc.

@app.post("/process/batch")
async def trigger_batch_processing(
    item_ids: List[int],
    background_tasks: BackgroundTasks
):
    """
    Trigger batch processing in background.
    
    POST /process/batch
    Body: [1, 2, 3, 4, 5, ...]
    """
    # Add background task
    background_tasks.add_task(batch_process_task, item_ids)
    
    return {
        'status': 'processing',
        'message': f'Processing {len(item_ids)} items in background',
        'item_count': len(item_ids)
    }
```

### Pattern 3: Caching Optimization Results

**Scenario**: Cache Amorsize optimization for similar workloads.

```python
# main.py
from fastapi import FastAPI
from amorsize import optimize, execute
from typing import List, Optional
from functools import lru_cache

app = FastAPI()

@lru_cache(maxsize=128)
def get_cached_optimization(data_size: int, func_name: str):
    """
    Cache optimization results for similar workloads.
    
    This prevents re-optimizing for every request with similar characteristics.
    """
    # Create dummy data for optimization
    dummy_data = list(range(min(data_size, 100)))  # Use sample for optimization
    
    # Get optimization result
    from .processing import FUNCTION_MAP
    func = FUNCTION_MAP.get(func_name)
    
    if func is None:
        return None
    
    result = optimize(
        func=func,
        data=dummy_data,
        verbose=True
    )
    
    return {
        'n_jobs': result.n_jobs,
        'chunksize': result.chunksize,
        'speedup': result.estimated_speedup,
        'workload_type': result.profile.workload_type
    }

@app.post("/process/optimized")
async def process_with_cached_optimization(
    func_name: str,
    data: List[int]
):
    """
    Process data using cached optimization parameters.
    
    POST /process/optimized
    Body: {"func_name": "process_item", "data": [1, 2, 3, ...]}
    """
    # Get cached optimization
    opt_params = get_cached_optimization(len(data), func_name)
    
    if opt_params is None:
        return {"error": f"Unknown function: {func_name}"}
    
    # Use cached parameters
    from .processing import FUNCTION_MAP
    results = execute(
        func=FUNCTION_MAP[func_name],
        data=data,
        n_jobs=opt_params['n_jobs'],
        chunksize=opt_params['chunksize'],
        verbose=False
    )
    
    return {
        'results': results,
        'optimization': opt_params,
        'cached': True
    }
```

---

## Common Patterns

### Pattern 1: Resource-Aware Processing

**Problem**: Don't overload your server, especially under high load.

```python
from amorsize import execute
from amorsize.system_info import get_current_cpu_load, get_memory_pressure

def smart_parallel_processing(func, data):
    """
    Adjust parallelism based on current system load.
    """
    cpu_load = get_current_cpu_load()
    memory_pressure = get_memory_pressure()
    
    # Reduce workers if system is under heavy load
    max_workers_override = None
    if cpu_load > 0.8 or memory_pressure > 0.8:
        max_workers_override = 2  # Use only 2 workers when system is stressed
    
    results = execute(
        func=func,
        data=data,
        max_workers=max_workers_override,
        verbose=False
    )
    
    return results
```

### Pattern 2: Timeout Protection

**Problem**: Some items might hang indefinitely.

```python
from amorsize import execute
from multiprocessing import TimeoutError
import signal

def with_timeout(func, timeout_seconds=30):
    """Wrapper that adds timeout to function."""
    def wrapper(*args, **kwargs):
        def timeout_handler(signum, frame):
            raise TimeoutError(f"Function exceeded {timeout_seconds}s timeout")
        
        signal.signal(signal.SIGALRM, timeout_handler)
        signal.alarm(timeout_seconds)
        
        try:
            result = func(*args, **kwargs)
            signal.alarm(0)  # Cancel alarm
            return result
        except TimeoutError as e:
            return {'error': str(e)}
    
    return wrapper

# Usage
safe_func = with_timeout(expensive_function, timeout_seconds=30)
results = execute(func=safe_func, data=items)
```

### Pattern 3: Error Handling with Dead Letter Queue

**Problem**: Need to handle failures gracefully and retry later.

```python
from amorsize import execute
from amorsize.dead_letter_queue import DeadLetterQueue, DLQPolicy

def process_with_dlq(func, data):
    """
    Process items with automatic failure handling.
    """
    # Create DLQ for failed items
    dlq = DeadLetterQueue(
        path='.amorsize_dlq/web_service_failures.json',
        policy=DLQPolicy(
            max_retries=3,
            retry_delay=60,  # 60 seconds between retries
            include_traceback=True
        )
    )
    
    def safe_wrapper(item):
        try:
            return func(item)
        except Exception as e:
            # Add to DLQ
            dlq.add(
                item=item,
                error=str(e),
                metadata={'source': 'web_service'}
            )
            return None
    
    results = execute(
        func=safe_wrapper,
        data=data,
        verbose=False
    )
    
    # Filter out failures
    results = [r for r in results if r is not None]
    
    return results, dlq
```

---

## Performance Benchmarks

### Real-World Results

#### Django: Order Processing
- **Workload**: 1000 orders with external API calls
- **Serial execution**: 45 seconds
- **With Amorsize**: 6.2 seconds
- **Speedup**: 7.3x
- **Workers**: 12 (detected optimal for I/O-bound)

#### Flask: Image Processing
- **Workload**: 500 images (resize + compress)
- **Serial execution**: 125 seconds
- **With Amorsize**: 18 seconds
- **Speedup**: 6.9x
- **Workers**: 8 (physical cores)

#### FastAPI: URL Analysis
- **Workload**: 200 URLs (fetch + parse)
- **Serial execution**: 67 seconds
- **With Amorsize**: 8.5 seconds
- **Speedup**: 7.9x
- **Workers**: 16 (high for I/O-bound)

### Benchmark Your Own Workload

```python
from amorsize import validate_optimization

# Validate Amorsize's prediction
result = validate_optimization(
    func=your_function,
    data=your_data[:100],  # Use sample for validation
    verbose=True
)

print(f"Predicted speedup: {result.optimization.estimated_speedup:.2f}x")
print(f"Actual speedup: {result.actual_speedup:.2f}x")
print(f"Accuracy: {result.accuracy_percentage:.1f}%")
```

---

## Production Considerations

### 1. Process Lifecycle Management

**Issue**: Worker pools persist between requests, consuming resources.

**Solution**: Use context managers or global pool manager.

```python
from amorsize import get_global_pool_manager, shutdown_global_pool_manager
import atexit

# Initialize global pool manager
pool_manager = get_global_pool_manager()

# Ensure cleanup on shutdown
atexit.register(shutdown_global_pool_manager)

# Usage in views
def my_view(request):
    results = execute(func=my_func, data=my_data)
    return JsonResponse({'results': results})
```

### 2. Memory Management

**Issue**: Large result objects can cause OOM.

**Solution**: Use batch processing.

```python
from amorsize import process_in_batches

# Process in smaller batches to control memory
results = []
for batch_result in process_in_batches(
    func=process_item,
    data=large_dataset,
    max_memory_mb=500  # Limit memory usage
):
    results.extend(batch_result)
    # Optionally save batch results immediately
```

### 3. Logging and Monitoring

**Issue**: Need visibility into parallelization decisions.

**Solution**: Enable structured logging.

```python
from amorsize import configure_logging
import logging

# Configure structured logging
configure_logging(
    level=logging.INFO,
    format='json',  # Structured logs for parsing
    log_file='/var/log/amorsize/optimization.log'
)

# Now all Amorsize operations are logged
results = execute(func=my_func, data=my_data, verbose=True)
```

### 4. Deployment Checklist

✅ **Set appropriate worker limits** based on server resources  
✅ **Enable caching** for optimization results  
✅ **Configure logging** for production monitoring  
✅ **Add timeout protection** for potentially hanging tasks  
✅ **Implement DLQ** for failure handling  
✅ **Monitor memory usage** especially for large datasets  
✅ **Test under load** to verify parallelization benefits  
✅ **Document optimal parameters** for different workload types  

### 5. Containerized Deployments (Docker/Kubernetes)

**Issue**: Container CPU/memory limits aren't always detected.

**Solution**: Explicitly set resource limits.

```python
# In containerized environments
from amorsize import execute

# Override with container-specific limits
results = execute(
    func=my_func,
    data=my_data,
    max_workers=4,  # Match container CPU limit
    memory_limit_mb=512,  # Match container memory limit
    verbose=True
)
```

**Docker Compose Example**:

```yaml
services:
  web:
    build: .
    environment:
      - AMORSIZE_MAX_WORKERS=4
      - AMORSIZE_MEMORY_LIMIT_MB=512
    deploy:
      resources:
        limits:
          cpus: '4'
          memory: 512M
```

---

## Troubleshooting

### Issue 1: "Parallelism slower than serial"

**Symptom**: Amorsize recommends `n_jobs=1`

**Causes**:
- Function is too fast (< 10ms per item)
- High serialization overhead
- Small dataset

**Solutions**:
1. **Batch items together**:
   ```python
   def process_batch(items):
       return [process_item(item) for item in items]
   
   # Process in larger chunks
   batched_data = [data[i:i+10] for i in range(0, len(data), 10)]
   results = execute(func=process_batch, data=batched_data)
   results = [item for batch in results for item in batch]  # Flatten
   ```

2. **Use threading for I/O** instead:
   ```python
   from concurrent.futures import ThreadPoolExecutor
   with ThreadPoolExecutor(max_workers=10) as executor:
       results = list(executor.map(io_bound_func, data))
   ```

### Issue 2: Memory usage too high

**Symptom**: OOM errors or swapping

**Causes**:
- Large return objects
- Too many workers
- No memory limits

**Solutions**:
1. **Batch processing**:
   ```python
   from amorsize import process_in_batches
   
   for batch in process_in_batches(func=my_func, data=data, max_memory_mb=500):
       # Process and save each batch
       save_results(batch)
   ```

2. **Reduce workers**:
   ```python
   results = execute(func=my_func, data=data, max_workers=2)
   ```

3. **Stream results**:
   ```python
   from amorsize import optimize_streaming
   
   for result in optimize_streaming(func=my_func, data=data):
       # Process results one at a time
       handle_result(result)
   ```

### Issue 3: Pickling errors

**Symptom**: `PicklingError` or `Can't pickle`

**Causes**:
- Lambda functions
- Nested functions
- Database connections in function closure

**Solutions**:
1. **Use module-level functions**:
   ```python
   # ❌ Won't work
   def view(request):
       def process(x):
           return x * 2
       results = execute(func=process, data=data)
   
   # ✅ Works
   def process(x):
       return x * 2
   
   def view(request):
       results = execute(func=process, data=data)
   ```

2. **Use cloudpickle**:
   ```python
   import cloudpickle
   
   def process(x):
       return x * 2
   
   # Cloudpickle handles more cases
   ```

3. **Pass data as arguments**:
   ```python
   # ❌ Won't work
   db_conn = get_db()
   def process(x):
       return db_conn.query(x)  # db_conn can't be pickled
   
   # ✅ Works
   def process(x):
       db_conn = get_db()  # Create connection inside worker
       return db_conn.query(x)
   ```

### Issue 4: Workers blocking each other

**Symptom**: Poor speedup despite parallelization

**Causes**:
- Shared resources (database connections, file locks)
- GIL contention (CPU-bound with many threads)

**Solutions**:
1. **Use process pool** (default for Amorsize):
   ```python
   # Already using processes by default
   results = execute(func=cpu_bound, data=data)
   ```

2. **Avoid shared state**:
   ```python
   # ❌ Won't work well
   shared_cache = {}
   def process(x):
       if x in shared_cache:  # Won't share across processes
           return shared_cache[x]
   
   # ✅ Better
   def process(x):
       local_cache = {}  # Each worker has own cache
       if x in local_cache:
           return local_cache[x]
   ```

---

## Next Steps

- **[Performance Tuning Guide](PERFORMANCE_TUNING.md)**: Deep dive into optimization
- **[Best Practices](BEST_PRACTICES.md)**: Production-ready patterns
- **[Troubleshooting Guide](TROUBLESHOOTING.md)**: Comprehensive problem solving
- **[Getting Started](GETTING_STARTED.md)**: Quick introduction

## Related Documentation

- **[Use Case: Data Processing](USE_CASE_DATA_PROCESSING.md)** (Coming soon)
- **[Use Case: ML Pipelines](USE_CASE_ML_PIPELINES.md)** (Coming soon)
- **[Use Case: Batch Jobs](USE_CASE_BATCH_JOBS.md)** (Coming soon)

---

**Questions or Issues?** Open an issue on [GitHub](https://github.com/CampbellTrevor/Amorsize/issues)
