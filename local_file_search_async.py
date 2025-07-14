#!/usr/bin/env python3
"""
Async/parallel local file search functionality with performance optimizations.
"""

import os
import re
import asyncio
from pathlib import Path
from typing import List, Dict, Optional, Set, Tuple
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor
from functools import lru_cache
import multiprocessing

from fuzzy_match import fuzzy_match_tune, normalize_tune_name
from thesession_data import get_all_tune_variations


# Supported audio file extensions
AUDIO_EXTENSIONS = {'.mp3', '.mp4', '.m4a', '.flac', '.wav', '.ogg', '.opus', '.aac', '.wma'}


def find_audio_files(directory: str, recursive: bool = True) -> List[Path]:
    """
    Find all audio files in a directory.
    """
    audio_files = []
    path = Path(directory).expanduser()
    
    if not path.exists():
        print(f"Warning: Directory '{directory}' does not exist")
        return audio_files
    
    if recursive:
        for ext in AUDIO_EXTENSIONS:
            audio_files.extend(path.rglob(f"*{ext}"))
            audio_files.extend(path.rglob(f"*{ext.upper()}"))
    else:
        for ext in AUDIO_EXTENSIONS:
            audio_files.extend(path.glob(f"*{ext}"))
            audio_files.extend(path.glob(f"*{ext.upper()}"))
    
    return audio_files


@lru_cache(maxsize=10000)
def extract_tune_name_from_path_cached(file_path_str: str) -> str:
    """
    Cached version of extracting tune name from path.
    """
    file_path = Path(file_path_str)
    name = file_path.stem
    
    # Remove common prefixes/suffixes
    name = re.sub(r'^\d+[-_\s]*', '', name)  # Remove leading numbers
    name = re.sub(r'[-_]', ' ', name)  # Replace underscores/hyphens with spaces
    name = re.sub(r'\s+', ' ', name)  # Normalize whitespace
    
    return name.strip()


def search_single_tune(
    tune_data: Tuple[str, Set[str], List[Tuple[Path, str]], float, int]
) -> Tuple[str, List[Tuple[Path, float]]]:
    """
    Search for a single tune. Designed to be run in parallel.
    
    Args:
        tune_data: Tuple of (tune_name, search_terms, file_candidates, threshold, max_results)
    
    Returns:
        Tuple of (tune_name, matches)
    """
    tune_name, search_terms, file_candidates, threshold, max_results = tune_data
    
    # Import here to avoid issues with multiprocessing
    from local_file_search import is_tune_in_composite_name
    
    matches = []
    for file_path, extracted_name in file_candidates:
        best_score = 0.0
        
        # Try matching against all search terms
        for search_term in search_terms:
            # First try exact matching
            candidates = [extracted_name]
            results = fuzzy_match_tune(search_term, candidates, threshold=0)
            
            if results:
                score = results[0][1]
                best_score = max(best_score, score)
            
            # Also check if this tune appears within a composite track name
            if is_tune_in_composite_name(search_term, extracted_name, threshold):
                # Give a slightly lower score for composite matches
                best_score = max(best_score, 0.9)
        
        if best_score >= threshold:
            matches.append((file_path, best_score))
    
    # Remove duplicate files
    unique_matches = {}
    for file_path, score in matches:
        abs_path = file_path.absolute()
        if abs_path not in unique_matches or unique_matches[abs_path][1] < score:
            unique_matches[abs_path] = (file_path, score)
    
    # Convert back to list and sort
    matches = [(path, score) for path, score in unique_matches.values()]
    matches.sort(key=lambda x: x[1], reverse=True)
    
    if max_results:
        matches = matches[:max_results]
    
    return tune_name, matches


async def find_tunes_for_set_async(
    tunes: List[str],
    directories: List[str],
    use_aliases: bool = True,
    threshold: float = 0.85,
    overload: Optional[int] = None,
    max_workers: Optional[int] = None
) -> Dict[str, List[Path]]:
    """
    Async version of find_tunes_for_set using parallel processing.
    """
    if max_workers is None:
        max_workers = min(multiprocessing.cpu_count(), len(tunes))
    
    print(f"Searching with {max_workers} parallel workers...")
    
    # Pre-collect all audio files (this is I/O bound, so do it once)
    print("Collecting audio files...")
    all_files = []
    for directory in directories:
        all_files.extend(find_audio_files(directory, recursive=True))
    
    # Remove duplicates
    unique_files = []
    seen_paths = set()
    for file_path in all_files:
        abs_path = file_path.absolute()
        if abs_path not in seen_paths:
            seen_paths.add(abs_path)
            unique_files.append(file_path)
    all_files = unique_files
    
    print(f"Found {len(all_files)} unique audio files")
    
    # Pre-extract all filenames (cache them)
    file_candidates = [(f, extract_tune_name_from_path_cached(str(f))) for f in all_files]
    
    # Prepare search data for each tune
    search_tasks = []
    for tune in tunes:
        print(f"Preparing search for: {tune}")
        
        # Get search terms
        if use_aliases:
            search_terms = get_all_tune_variations(tune)
        else:
            from fuzzy_match import find_common_variations
            search_terms = set(find_common_variations(tune))
        
        max_results = overload if overload else 1
        search_tasks.append((tune, search_terms, file_candidates, threshold, max_results))
    
    # Run searches in parallel
    print("\nSearching in parallel...")
    results = {}
    
    with ProcessPoolExecutor(max_workers=max_workers) as executor:
        # Submit all tasks
        future_to_tune = {
            executor.submit(search_single_tune, task): task[0] 
            for task in search_tasks
        }
        
        # Collect results as they complete
        import concurrent.futures
        for future in concurrent.futures.as_completed(future_to_tune):
            tune_name, matches = future.result()
            
            if matches:
                results[tune_name] = [match[0] for match in matches]
                print(f"  Found {len(matches)} match(es) for: {tune_name}")
                for path, score in matches[:3]:
                    print(f"    - {path.name} (score: {score:.2f})")
                if len(matches) > 3:
                    print(f"    ... and {len(matches) - 3} more")
            else:
                results[tune_name] = []
                print(f"  No matches found for: {tune_name}")
    
    return results


def find_tunes_for_set_optimized(
    tunes: List[str],
    directories: List[str],
    use_aliases: bool = True,
    threshold: float = 0.85,
    overload: Optional[int] = None,
    use_async: bool = False,
    max_workers: Optional[int] = None
) -> Dict[str, List[Path]]:
    """
    Optimized version with optional async support.
    """
    if use_async and len(tunes) > 1:
        # Use async version for multiple tunes
        return asyncio.run(find_tunes_for_set_async(
            tunes, directories, use_aliases, threshold, overload, max_workers
        ))
    else:
        # Fall back to synchronous version
        from local_file_search import find_tunes_for_set
        return find_tunes_for_set(tunes, directories, use_aliases, threshold, overload)


# Additional optimizations:

class FileIndexCache:
    """
    Cache for file index to avoid repeated directory scans.
    """
    def __init__(self):
        self.cache = {}
        self.cache_time = {}
    
    def get_files(self, directory: str, recursive: bool = True) -> List[Path]:
        """Get files from cache or scan directory."""
        import time
        cache_key = (directory, recursive)
        
        # Check if cache is valid (less than 5 minutes old)
        if cache_key in self.cache:
            if time.time() - self.cache_time[cache_key] < 300:  # 5 minutes
                return self.cache[cache_key]
        
        # Scan directory and cache results
        files = find_audio_files(directory, recursive)
        self.cache[cache_key] = files
        self.cache_time[cache_key] = time.time()
        
        return files


# Global file index cache
_file_index_cache = FileIndexCache()


def get_cached_audio_files(directories: List[str], recursive: bool = True) -> List[Path]:
    """Get audio files using cache."""
    all_files = []
    for directory in directories:
        all_files.extend(_file_index_cache.get_files(directory, recursive))
    return all_files


if __name__ == "__main__":
    import time
    
    # Test async vs sync performance
    test_tunes = [
        "The Butterfly",
        "Drowsy Maggie", 
        "The Silver Spear",
        "Out on the Ocean",
        "The Kesh Jig"
    ]
    
    test_dir = "/Users/pk/Dropbox/Dreadlap"
    
    print("Testing sync version...")
    start = time.time()
    from local_file_search import find_tunes_for_set
    sync_results = find_tunes_for_set(test_tunes, [test_dir], overload=3)
    sync_time = time.time() - start
    print(f"Sync time: {sync_time:.2f} seconds")
    
    print("\n" + "="*60 + "\n")
    
    print("Testing async version...")
    start = time.time()
    async_results = find_tunes_for_set_optimized(
        test_tunes, [test_dir], overload=3, use_async=True
    )
    async_time = time.time() - start
    print(f"Async time: {async_time:.2f} seconds")
    
    print(f"\nSpeedup: {sync_time/async_time:.2f}x")