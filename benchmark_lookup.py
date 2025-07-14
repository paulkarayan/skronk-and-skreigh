#!/usr/bin/env python3
"""
Benchmark TheSession data lookup performance
"""

import time
import random
from thesession_data import get_tune_aliases, load_aliases_data, get_aliases_map


def benchmark_csv_load():
    """Benchmark loading the CSV file"""
    start = time.time()
    data = load_aliases_data()
    end = time.time()
    
    print(f"CSV Load Performance:")
    print(f"  - File size: ~1.3MB")
    print(f"  - Lines: ~29,020")
    print(f"  - Load time: {(end - start)*1000:.2f}ms")
    print(f"  - Unique keys in map: {len(data)}")
    
    return data


def benchmark_lookups(data, num_lookups=10000):
    """Benchmark dictionary lookups"""
    keys = list(data.keys())
    
    # Test existing keys (best/average case)
    existing_keys = random.sample(keys, min(num_lookups, len(keys)))
    start = time.time()
    for key in existing_keys:
        _ = data.get(key, [])
    end = time.time()
    avg_existing = (end - start) / len(existing_keys) * 1_000_000  # microseconds
    
    # Test non-existing keys (worst case for lookup)
    non_existing_keys = [f"nonexistent_tune_{i}" for i in range(num_lookups)]
    start = time.time()
    for key in non_existing_keys:
        _ = data.get(key, [])
    end = time.time()
    avg_non_existing = (end - start) / num_lookups * 1_000_000  # microseconds
    
    print(f"\nLookup Performance (after loading):")
    print(f"  - Average lookup (existing key): {avg_existing:.3f} microseconds")
    print(f"  - Average lookup (non-existing key): {avg_non_existing:.3f} microseconds")
    print(f"  - Lookups per second: ~{1_000_000/avg_existing:,.0f}")


def benchmark_with_cache():
    """Benchmark with caching"""
    # First call loads from disk
    start = time.time()
    aliases1 = get_tune_aliases("The Butterfly")
    end = time.time()
    first_call = (end - start) * 1000
    
    # Second call uses cache
    start = time.time()
    aliases2 = get_tune_aliases("The Harvest Home")
    end = time.time()
    cached_call = (end - start) * 1000
    
    print(f"\nWith Caching:")
    print(f"  - First call (loads CSV): {first_call:.2f}ms")
    print(f"  - Subsequent calls (cached): {cached_call:.3f}ms")


def analyze_complexity():
    """Analyze the complexity"""
    print("\nComplexity Analysis:")
    print("  - CSV Loading: O(n) where n = number of lines (~29k)")
    print("  - Memory usage: O(n) for storing the dictionary")
    print("  - Lookup time: O(1) average case (Python dict)")
    print("  - Cache benefit: Amortizes load cost across many lookups")
    
    print("\nPractical implications:")
    print("  - Initial load: ~50-100ms (acceptable for CLI tool)")
    print("  - Each lookup: <1 microsecond (negligible)")
    print("  - Memory: ~5-10MB (minimal for modern systems)")


if __name__ == "__main__":
    print("TheSession CSV Lookup Performance Analysis")
    print("=" * 50)
    
    # Load and benchmark
    data = benchmark_csv_load()
    benchmark_lookups(data)
    benchmark_with_cache()
    analyze_complexity()