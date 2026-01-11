"""
Circuit Breaker Pattern Demo

This demo shows how to use the circuit breaker pattern to prevent cascade
failures and improve system resilience when dealing with unreliable services.
"""

import time
from amorsize import (
    CircuitBreaker,
    CircuitBreakerPolicy,
    CircuitBreakerError,
    with_circuit_breaker,
    execute,
)


def demo_1_basic_circuit_breaker():
    """Demo 1: Basic circuit breaker usage with decorator."""
    print("\n" + "="*70)
    print("Demo 1: Basic Circuit Breaker with Decorator")
    print("="*70)
    
    call_count = [0]
    
    @with_circuit_breaker()
    def unreliable_api_call(item_id):
        """Simulates an API that fails initially then recovers."""
        call_count[0] += 1
        
        # Fail for the first 5 calls
        if call_count[0] <= 5:
            print(f"  ❌ API call {call_count[0]} failed")
            raise ConnectionError(f"API unavailable for item {item_id}")
        
        # Succeed after that
        print(f"  ✅ API call {call_count[0]} succeeded")
        return f"Data for {item_id}"
    
    print("\nMaking API calls (default policy: 5 failures opens circuit):")
    
    # Make calls until circuit opens
    for i in range(10):
        try:
            result = unreliable_api_call(i)
            print(f"  Result: {result}")
        except ConnectionError as e:
            print(f"  Connection error: {e}")
        except CircuitBreakerError as e:
            print(f"  🔴 Circuit OPEN! Service unavailable. {e}")
            break
        
        time.sleep(0.1)
    
    print(f"\n✓ Circuit opened after {call_count[0]} failures")
    print("  This prevents overwhelming a failing service!")


def demo_2_custom_policy():
    """Demo 2: Custom circuit breaker policy with callbacks."""
    print("\n" + "="*70)
    print("Demo 2: Custom Policy with Monitoring Callbacks")
    print("="*70)
    
    def on_open(failure_count, last_exception):
        print(f"  🚨 ALERT: Circuit opened after {failure_count} failures!")
        print(f"     Last error: {last_exception}")
    
    def on_close():
        print("  ✅ Circuit closed - service recovered!")
    
    def on_half_open():
        print("  ⚠️  Circuit half-open - testing recovery...")
    
    policy = CircuitBreakerPolicy(
        failure_threshold=3,      # Open after 3 failures
        success_threshold=2,      # Close after 2 successes
        timeout=1.0,              # Try recovery after 1 second
        on_open=on_open,
        on_close=on_close,
        on_half_open=on_half_open,
    )
    
    breaker = CircuitBreaker(policy)
    call_count = [0]
    
    def flaky_service(x):
        call_count[0] += 1
        # Fail first 3 times, succeed after recovery
        if call_count[0] <= 3:
            raise TimeoutError("Service timeout")
        return f"Result: {x}"
    
    print("\nPhase 1: Initial failures (opens circuit)")
    for i in range(5):
        try:
            result = breaker.call(flaky_service, i)
            print(f"  {i+1}. Success: {result}")
        except (TimeoutError, CircuitBreakerError) as e:
            print(f"  {i+1}. Failed: {type(e).__name__}")
        time.sleep(0.1)
    
    print("\nPhase 2: Wait for timeout and recovery")
    time.sleep(1.1)
    
    print("\nPhase 3: Recovery attempts (closes circuit)")
    for i in range(5, 8):
        try:
            result = breaker.call(flaky_service, i)
            print(f"  {i+1}. Success: {result}")
        except (TimeoutError, CircuitBreakerError) as e:
            print(f"  {i+1}. Failed: {type(e).__name__}")
        time.sleep(0.1)


def demo_3_integration_with_parallel():
    """Demo 3: Circuit breaker with parallel execution."""
    print("\n" + "="*70)
    print("Demo 3: Circuit Breaker with Parallel Execution")
    print("="*70)
    
    policy = CircuitBreakerPolicy(
        failure_threshold=10,
        expected_exceptions=(ConnectionError, TimeoutError),
    )
    breaker = CircuitBreaker(policy)
    
    call_count = [0]
    
    def protected_api_call(item_id):
        """API call protected by circuit breaker."""
        call_count[0] += 1
        
        # Simulate intermittent failures (5% failure rate)
        import random
        if random.random() < 0.05:
            raise ConnectionError(f"Timeout for item {item_id}")
        
        # Simulate processing
        time.sleep(0.001)
        return f"Processed {item_id}"
    
    # Wrap with circuit breaker and handle exceptions
    def safe_api_call(item_id):
        try:
            return breaker.call(protected_api_call, item_id)
        except (ConnectionError, CircuitBreakerError) as e:
            return None  # Return None for failed items
    
    print("\nProcessing 100 items with circuit breaker protection:")
    print("  (Some items may fail, but circuit protects the service)")
    
    data = range(100)
    results = [safe_api_call(i) for i in data]
    
    successful = sum(1 for r in results if r is not None)
    failed = len(results) - successful
    
    state, failures, successes, _ = breaker.get_state()
    
    print(f"\n✓ Completed:")
    print(f"  • Total attempts: {call_count[0]}")
    print(f"  • Successful: {successful}")
    print(f"  • Failed: {failed}")
    print(f"  • Circuit state: {state.value}")
    print(f"  • Current failures: {failures}")
    
    if state.value == "open":
        print("\n⚠️  Circuit opened during processing")
        print("   Service needs time to recover")


def demo_4_selective_exceptions():
    """Demo 4: Only specific exceptions trigger circuit breaker."""
    print("\n" + "="*70)
    print("Demo 4: Selective Exception Handling")
    print("="*70)
    
    policy = CircuitBreakerPolicy(
        failure_threshold=3,
        expected_exceptions=(ConnectionError, TimeoutError),
        # ValueError won't trigger circuit breaker
    )
    
    @with_circuit_breaker(policy)
    def api_with_validation(data):
        """API that can fail with network errors OR validation errors."""
        if data < 0:
            # Validation errors don't trigger circuit breaker
            raise ValueError("Data must be non-negative")
        
        if data > 100:
            # Network errors DO trigger circuit breaker
            raise ConnectionError("API rate limit exceeded")
        
        return f"Valid: {data}"
    
    print("\nValidation errors (don't count toward circuit):")
    for val in [-1, -2, -3, -4]:
        try:
            result = api_with_validation(val)
            print(f"  {val}: {result}")
        except ValueError as e:
            print(f"  {val}: ValueError (doesn't affect circuit)")
    
    print("\nNetwork errors (do count toward circuit):")
    for val in [101, 102, 103, 104]:
        try:
            result = api_with_validation(val)
            print(f"  {val}: {result}")
        except ConnectionError as e:
            print(f"  {val}: ConnectionError (counts toward circuit)")
        except CircuitBreakerError as e:
            print(f"  {val}: Circuit OPEN!")
            break
    
    print("\n✓ Circuit opened only after network errors")
    print("  Validation errors are handled separately")


def demo_5_shared_circuit_breaker():
    """Demo 5: Multiple functions share a circuit breaker."""
    print("\n" + "="*70)
    print("Demo 5: Shared Circuit Breaker Across Services")
    print("="*70)
    
    # Shared breaker for the same backend service
    backend_breaker = CircuitBreaker(
        CircuitBreakerPolicy(failure_threshold=3, timeout=0.5)
    )
    
    call_counts = {"read": 0, "write": 0}
    
    @with_circuit_breaker(backend_breaker)
    def read_from_backend(key):
        call_counts["read"] += 1
        if call_counts["read"] <= 2:
            raise ConnectionError("Read failed")
        return f"Value for {key}"
    
    @with_circuit_breaker(backend_breaker)
    def write_to_backend(key, value):
        call_counts["write"] += 1
        if call_counts["write"] <= 2:
            raise ConnectionError("Write failed")
        return f"Wrote {key}={value}"
    
    print("\nBoth read and write operations share the same circuit:")
    
    # Failures in read operations
    for i in range(2):
        try:
            read_from_backend(f"key{i}")
        except ConnectionError:
            print(f"  Read {i+1} failed (count: {call_counts['read']})")
    
    # One more failure (from write) opens the circuit
    try:
        write_to_backend("key", "value")
    except ConnectionError:
        print(f"  Write failed (count: {call_counts['write']})")
    
    state, failures, _, _ = backend_breaker.get_state()
    print(f"\n  Circuit state: {state.value}")
    print(f"  Total failures: {failures}")
    
    # Both operations are now blocked
    print("\nBoth operations now blocked:")
    for func_name, func in [("read", read_from_backend), ("write", write_to_backend)]:
        try:
            func("test")
        except CircuitBreakerError:
            print(f"  ❌ {func_name} blocked by circuit breaker")
    
    print("\n✓ One circuit protects multiple operations")
    print("  This prevents overwhelming a shared backend")


def demo_6_integration_with_retry():
    """Demo 6: Circuit breaker with retry logic."""
    print("\n" + "="*70)
    print("Demo 6: Circuit Breaker + Retry Logic Integration")
    print("="*70)
    
    from amorsize import with_retry, RetryPolicy
    
    # Combine circuit breaker with retry for robust error handling
    breaker = CircuitBreaker(
        CircuitBreakerPolicy(failure_threshold=5, timeout=0.5)
    )
    
    call_count = [0]
    
    # Apply both decorators: retry first, then circuit breaker
    @with_circuit_breaker(breaker)
    @with_retry(policy=RetryPolicy(max_retries=2, initial_delay=0.1))
    def robust_api_call(item):
        """API with both retry and circuit breaker protection."""
        call_count[0] += 1
        
        # Fail occasionally
        if call_count[0] % 4 == 0:
            raise TimeoutError(f"Timeout for {item}")
        
        return f"Success: {item}"
    
    print("\nProcessing items with layered protection:")
    print("  Layer 1: Retry (up to 2 retries per item)")
    print("  Layer 2: Circuit breaker (opens after 5 failures)")
    
    results = []
    for i in range(15):
        try:
            result = robust_api_call(i)
            results.append(result)
            print(f"  {i}: ✅ {result}")
        except TimeoutError:
            print(f"  {i}: ❌ Failed after retries")
        except CircuitBreakerError:
            print(f"  {i}: 🔴 Circuit breaker open")
            break
    
    print(f"\n✓ Processed {len(results)} items before circuit opened")
    print("  Retry handles transient failures")
    print("  Circuit breaker prevents cascade failures")


def demo_7_benefits_summary():
    """Demo 7: Summary of circuit breaker benefits."""
    print("\n" + "="*70)
    print("Demo 7: Circuit Breaker Benefits Summary")
    print("="*70)
    
    print("""
Circuit Breaker Pattern Benefits:

1. 🛡️  PREVENTS CASCADE FAILURES
   • Stops calling failing services
   • Prevents resource exhaustion
   • Protects downstream systems

2. ⚡ FASTER FAILURE DETECTION
   • Immediate failure when circuit is open
   • No waiting for timeouts
   • Better user experience

3. 🔄 AUTOMATIC RECOVERY
   • Tests service recovery periodically
   • Closes circuit when service recovers
   • No manual intervention needed

4. 📊 BUILT-IN MONITORING
   • State transition callbacks
   • Failure counting
   • Recovery tracking

5. 🎯 CONFIGURABLE BEHAVIOR
   • Custom thresholds
   • Selective exception handling
   • Shared or isolated circuits

6. 🤝 INTEGRATES WITH RETRY
   • Retry for transient failures
   • Circuit breaker for persistent failures
   • Layered fault tolerance

Key Metrics:
  • failure_threshold: When to open circuit (default: 5)
  • timeout: How long to wait before retry (default: 60s)
  • success_threshold: Successes needed to close (default: 2)

Usage Patterns:
  • @with_circuit_breaker() - Simple decorator
  • Shared breaker - Multiple services
  • + @with_retry - Layered protection
""")


if __name__ == "__main__":
    print("\n" + "🔴 CIRCUIT BREAKER PATTERN DEMONSTRATIONS 🔴".center(70))
    
    demo_1_basic_circuit_breaker()
    demo_2_custom_policy()
    demo_3_integration_with_parallel()
    demo_4_selective_exceptions()
    demo_5_shared_circuit_breaker()
    demo_6_integration_with_retry()
    demo_7_benefits_summary()
    
    print("\n" + "="*70)
    print("✅ All circuit breaker demos completed!")
    print("="*70)
