#!/usr/bin/env python3
"""
DNS Log Entropy Analysis Example

This example demonstrates using Amorsize to optimize parallel processing
of a large DNS log file (>100MB) for calculating domain name entropy.

Domain name entropy is useful for detecting:
- DGA (Domain Generation Algorithm) domains
- Random subdomains used by malware
- Legitimate vs suspicious DNS queries

Shannon entropy formula:
H(X) = -Σ p(xi) * log2(p(xi))

Higher entropy indicates more randomness in character distribution.
"""

import os
import math
import random
import string
import time
from collections import Counter
from datetime import datetime, timedelta
from multiprocessing import Pool
from amorsize import optimize


# ============================================================================
# DNS Log Generation
# ============================================================================

def generate_legitimate_domains():
    """Generate a list of legitimate-looking domain names."""
    # Common TLDs
    tlds = ['com', 'org', 'net', 'edu', 'gov', 'io', 'co', 'us', 'uk', 'de']
    
    # Common domain patterns
    base_domains = [
        'google', 'facebook', 'amazon', 'microsoft', 'apple', 'twitter',
        'linkedin', 'github', 'stackoverflow', 'youtube', 'netflix', 'reddit',
        'wikipedia', 'instagram', 'pinterest', 'dropbox', 'slack', 'zoom',
        'cloudflare', 'aws', 'azure', 'salesforce', 'oracle', 'adobe',
        'ibm', 'cisco', 'intel', 'nvidia', 'paypal', 'ebay', 'yahoo',
        'wordpress', 'medium', 'tumblr', 'blogger', 'mailchimp', 'shopify',
        'squarespace', 'wix', 'godaddy', 'namecheap', 'digitalocean'
    ]
    
    # Common subdomains
    subdomains = ['www', 'mail', 'api', 'cdn', 'static', 'images', 'media',
                  'blog', 'forum', 'shop', 'store', 'app', 'mobile', 'dev',
                  'staging', 'prod', 'admin', 'dashboard', 'portal', 'docs']
    
    domains = []
    
    # Generate legitimate domains
    for base in base_domains:
        for tld in tlds[:3]:  # Use first 3 TLDs per base
            domains.append(f"{base}.{tld}")
            # Add some with subdomains
            if random.random() > 0.7:
                subdomain = random.choice(subdomains)
                domains.append(f"{subdomain}.{base}.{tld}")
    
    return domains


def generate_dga_domain():
    """Generate a DGA-like (Domain Generation Algorithm) domain."""
    # DGA domains typically have high entropy - random characters
    length = random.randint(8, 20)
    chars = ''.join(random.choice(string.ascii_lowercase) for _ in range(length))
    tld = random.choice(['com', 'net', 'org', 'info', 'biz'])
    return f"{chars}.{tld}"


def generate_dns_log_entry(timestamp, domain, query_type='A', response_code='NOERROR'):
    """Generate a single DNS log entry in a realistic format."""
    client_ips = [f"192.168.{random.randint(1, 255)}.{random.randint(1, 255)}" 
                  for _ in range(100)]
    dns_servers = ['8.8.8.8', '8.8.4.4', '1.1.1.1', '1.0.0.1']
    
    client_ip = random.choice(client_ips)
    dns_server = random.choice(dns_servers)
    query_id = random.randint(10000, 65535)
    response_time = random.randint(1, 100)
    
    # Format: timestamp | query_id | client_ip | dns_server | domain | type | response_code | response_time_ms
    return (f"{timestamp.isoformat()} | {query_id:05d} | {client_ip} | {dns_server} | "
            f"{domain} | {query_type} | {response_code} | {response_time}ms")


def generate_large_dns_log(filename, target_size_mb=100, progress_interval=10):
    """
    Generate a large DNS log file.
    
    Args:
        filename: Output filename
        target_size_mb: Target file size in megabytes
        progress_interval: Print progress every N MB
    """
    print(f"Generating DNS log file: {filename}")
    print(f"Target size: {target_size_mb} MB")
    print("-" * 70)
    
    target_size_bytes = target_size_mb * 1024 * 1024
    legitimate_domains = generate_legitimate_domains()
    
    # Mix of legitimate and suspicious domains (80% legitimate, 20% DGA)
    start_time = datetime.now() - timedelta(hours=24)
    
    with open(filename, 'w') as f:
        # Write header
        header = "# DNS Query Log\n"
        header += "# Format: timestamp | query_id | client_ip | dns_server | domain | type | response_code | response_time\n"
        f.write(header)
        
        current_size = len(header.encode('utf-8'))
        last_progress = 0
        entry_count = 0
        
        while current_size < target_size_bytes:
            # Increment timestamp
            timestamp = start_time + timedelta(seconds=entry_count * 0.1)
            
            # Choose domain type
            if random.random() < 0.8:
                # Legitimate domain
                domain = random.choice(legitimate_domains)
            else:
                # DGA domain (suspicious)
                domain = generate_dga_domain()
            
            # Generate log entry
            entry = generate_dns_log_entry(timestamp, domain)
            f.write(entry + '\n')
            
            # Update size
            current_size += len(entry.encode('utf-8')) + 1
            entry_count += 1
            
            # Progress reporting
            current_mb = current_size / (1024 * 1024)
            if current_mb - last_progress >= progress_interval:
                print(f"  Generated: {current_mb:.1f} MB ({entry_count:,} entries)")
                last_progress = current_mb
    
    final_size_mb = current_size / (1024 * 1024)
    print(f"\n✓ DNS log generated successfully!")
    print(f"  File: {filename}")
    print(f"  Size: {final_size_mb:.2f} MB")
    print(f"  Entries: {entry_count:,}")
    
    return filename, entry_count


# ============================================================================
# Entropy Calculation
# ============================================================================

def calculate_shannon_entropy(text):
    """
    Calculate Shannon entropy of a string.
    
    H(X) = -Σ p(xi) * log2(p(xi))
    
    Higher values indicate more randomness.
    Typical ranges:
    - Legitimate domains: 2.5 - 4.0
    - DGA domains: 3.5 - 5.0
    """
    if not text:
        return 0.0
    
    # Count character frequencies
    counter = Counter(text.lower())
    length = len(text)
    
    # Calculate entropy
    entropy = 0.0
    for count in counter.values():
        probability = count / length
        entropy -= probability * math.log2(probability)
    
    return entropy


def extract_domain_from_log_line(line):
    """Extract domain name from a DNS log line."""
    if line.startswith('#'):
        return None
    
    try:
        parts = line.split('|')
        if len(parts) >= 5:
            domain = parts[4].strip()
            return domain
    except:
        return None
    
    return None


def analyze_domain_entropy(log_line):
    """
    Analyze a single DNS log line and return domain with its entropy.
    
    This is the expensive function we'll optimize with Amorsize.
    
    The function includes multiple security checks and pattern detection
    algorithms to make it computationally expensive enough to benefit
    from parallelization. In a real-world scenario, this might include:
    - Regex pattern matching against known malware signatures
    - Machine learning model inference
    - External reputation database lookups (simulated here)
    - Advanced statistical analysis
    """
    domain = extract_domain_from_log_line(log_line)
    
    if domain is None:
        return None
    
    # Calculate entropy for the domain name (without TLD)
    # Remove TLD for better analysis
    parts = domain.split('.')
    if len(parts) > 1:
        base_domain = '.'.join(parts[:-1])
    else:
        base_domain = domain
    
    entropy = calculate_shannon_entropy(base_domain)
    
    # Additional metrics
    length = len(base_domain)
    digit_ratio = sum(c.isdigit() for c in base_domain) / length if length > 0 else 0
    
    # Simulate expensive security analysis
    # (In production, this might be ML model inference, regex matching, etc.)
    suspicious_score = 0.0
    for i in range(500):  # Multiple passes for pattern detection (more expensive)
        # Check for patterns that might indicate malicious domains
        if entropy > 3.5:
            suspicious_score += 0.01
        if length > 15:
            suspicious_score += 0.005
        if digit_ratio > 0.3:
            suspicious_score += 0.008
        # Additional pattern checks
        for char in base_domain:
            suspicious_score += 0.0001 if char.isdigit() else 0.00005
    
    return {
        'domain': domain,
        'entropy': entropy,
        'length': length,
        'digit_ratio': digit_ratio,
        'suspicious_score': suspicious_score,
        'suspicious': entropy > 4.0  # High entropy threshold
    }


# ============================================================================
# Main Analysis Pipeline
# ============================================================================

def read_log_lines(filename):
    """Read DNS log file and yield lines."""
    with open(filename, 'r') as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith('#'):
                yield line


def analyze_dns_log_serial(filename):
    """Serial analysis (baseline for comparison)."""
    print("\n[Serial Analysis]")
    print("-" * 70)
    
    start_time = time.time()
    
    results = []
    for line in read_log_lines(filename):
        result = analyze_domain_entropy(line)
        if result:
            results.append(result)
    
    elapsed = time.time() - start_time
    
    print(f"  Processed: {len(results):,} domains")
    print(f"  Time: {elapsed:.2f} seconds")
    
    return results, elapsed


def analyze_dns_log_optimized(filename):
    """Optimized parallel analysis using Amorsize."""
    print("\n[Optimized Parallel Analysis with Amorsize]")
    print("-" * 70)
    
    # Read log lines into memory (for this example)
    print("  Loading log file...")
    log_lines = list(read_log_lines(filename))
    print(f"  Loaded: {len(log_lines):,} log lines")
    
    # Optimize with Amorsize
    print("\n  Analyzing optimal parallelization...")
    opt_result = optimize(analyze_domain_entropy, log_lines, verbose=True)
    
    print(f"\n  Amorsize Recommendations:")
    print(f"    n_jobs: {opt_result.n_jobs}")
    print(f"    chunksize: {opt_result.chunksize}")
    print(f"    estimated_speedup: {opt_result.estimated_speedup:.2f}x")
    print(f"    reason: {opt_result.reason}")
    
    # Execute with recommendations
    print(f"\n  Processing with {opt_result.n_jobs} workers...")
    start_time = time.time()
    
    if opt_result.n_jobs > 1:
        with Pool(processes=opt_result.n_jobs) as pool:
            results = pool.map(analyze_domain_entropy, log_lines, 
                             chunksize=opt_result.chunksize)
    else:
        results = [analyze_domain_entropy(line) for line in log_lines]
    
    # Filter out None results
    results = [r for r in results if r is not None]
    
    elapsed = time.time() - start_time
    
    print(f"\n  Processed: {len(results):,} domains")
    print(f"  Time: {elapsed:.2f} seconds")
    
    return results, elapsed, opt_result


def print_analysis_summary(results):
    """Print summary statistics of the entropy analysis."""
    print("\n" + "=" * 70)
    print("DNS Log Entropy Analysis Summary")
    print("=" * 70)
    
    if not results:
        print("No results to analyze.")
        return
    
    # Calculate statistics
    entropies = [r['entropy'] for r in results]
    suspicious_domains = [r for r in results if r['suspicious']]
    
    avg_entropy = sum(entropies) / len(entropies)
    min_entropy = min(entropies)
    max_entropy = max(entropies)
    
    print(f"\nTotal domains analyzed: {len(results):,}")
    print(f"Suspicious domains (entropy > 4.0): {len(suspicious_domains):,} "
          f"({100*len(suspicious_domains)/len(results):.1f}%)")
    
    print(f"\nEntropy Statistics:")
    print(f"  Average: {avg_entropy:.3f}")
    print(f"  Minimum: {min_entropy:.3f}")
    print(f"  Maximum: {max_entropy:.3f}")
    
    # Show examples of suspicious domains
    print(f"\nTop 10 Most Suspicious Domains (highest entropy):")
    sorted_results = sorted(results, key=lambda x: x['entropy'], reverse=True)
    for i, result in enumerate(sorted_results[:10], 1):
        print(f"  {i:2d}. {result['domain']:40s} "
              f"entropy={result['entropy']:.3f} "
              f"length={result['length']:2d}")
    
    # Show examples of legitimate domains
    print(f"\nTop 10 Most Legitimate Domains (lowest entropy):")
    for i, result in enumerate(sorted_results[-10:][::-1], 1):
        print(f"  {i:2d}. {result['domain']:40s} "
              f"entropy={result['entropy']:.3f} "
              f"length={result['length']:2d}")


def main():
    """Main execution function."""
    print("=" * 70)
    print("DNS Log Entropy Analysis with Amorsize")
    print("=" * 70)
    print("\nThis example demonstrates:")
    print("  1. Generating a large DNS log file (>100MB)")
    print("  2. Calculating entropy of domain names to detect suspicious activity")
    print("  3. Using Amorsize to optimize parallel processing")
    print("=" * 70)
    
    # Configuration
    log_filename = "/tmp/dns_log_large.txt"
    target_size_mb = 120  # Generate 120MB file
    
    # Step 1: Generate DNS log if it doesn't exist
    if not os.path.exists(log_filename):
        print("\n[Step 1] Generating large DNS log file...")
        generate_large_dns_log(log_filename, target_size_mb=target_size_mb)
    else:
        file_size_mb = os.path.getsize(log_filename) / (1024 * 1024)
        print(f"\n[Step 1] Using existing DNS log file:")
        print(f"  File: {log_filename}")
        print(f"  Size: {file_size_mb:.2f} MB")
    
    # Step 2: Analyze with Amorsize optimization
    print("\n[Step 2] Analyzing DNS log with Amorsize optimization...")
    results, parallel_time, opt_result = analyze_dns_log_optimized(log_filename)
    
    # Step 3: Optional - Compare with serial execution (on subset for speed)
    if opt_result.n_jobs > 1 and opt_result.estimated_speedup > 1.5:
        print("\n[Step 3] Comparing with serial execution (small subset)...")
        print("  (Using first 10,000 lines for fair comparison)")
        
        # Create temporary subset file
        subset_filename = "/tmp/dns_log_subset.txt"
        with open(log_filename, 'r') as f_in, open(subset_filename, 'w') as f_out:
            for i, line in enumerate(f_in):
                if i < 10000:
                    f_out.write(line)
                else:
                    break
        
        # Serial processing
        start = time.time()
        serial_results = []
        for line in read_log_lines(subset_filename):
            result = analyze_domain_entropy(line)
            if result:
                serial_results.append(result)
        serial_time = time.time() - start
        
        # Parallel processing
        subset_lines = list(read_log_lines(subset_filename))
        start = time.time()
        with Pool(processes=opt_result.n_jobs) as pool:
            parallel_results = pool.map(analyze_domain_entropy, subset_lines,
                                       chunksize=opt_result.chunksize)
        parallel_subset_time = time.time() - start
        
        actual_speedup = serial_time / parallel_subset_time
        
        print(f"\n  Subset Performance Comparison:")
        print(f"    Serial time: {serial_time:.3f}s")
        print(f"    Parallel time: {parallel_subset_time:.3f}s")
        print(f"    Actual speedup: {actual_speedup:.2f}x")
        print(f"    Estimated speedup: {opt_result.estimated_speedup:.2f}x")
        
        # Clean up
        os.remove(subset_filename)
    
    # Step 4: Print analysis summary
    print_analysis_summary(results)
    
    # Final summary
    print("\n" + "=" * 70)
    print("Analysis Complete!")
    print("=" * 70)
    print(f"\nKey Takeaways:")
    print(f"  • Processed {len(results):,} DNS queries")
    print(f"  • Used {opt_result.n_jobs} parallel workers")
    print(f"  • Chunksize: {opt_result.chunksize}")
    print(f"  • Processing time: {parallel_time:.2f} seconds")
    
    if opt_result.n_jobs > 1:
        print(f"  • Amorsize optimization enabled parallel processing!")
        print(f"    Estimated speedup: {opt_result.estimated_speedup:.2f}x")
    else:
        print(f"  • Amorsize recommended serial processing")
        print(f"    Reason: {opt_result.reason}")
    
    print("\nThis demonstrates how Amorsize automatically determines")
    print("whether parallelization is beneficial for your specific workload.")
    print("=" * 70)


if __name__ == "__main__":
    main()
