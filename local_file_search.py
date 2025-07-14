#!/usr/bin/env python3
"""
Local file search functionality with fuzzy matching for audio files.
Searches directories for audio files that match tune names.
"""

import os
import re
from pathlib import Path
from typing import List, Dict, Optional, Set, Tuple
from fuzzy_match import fuzzy_match_tune, normalize_tune_name
from thesession_data import get_all_tune_variations


# Supported audio file extensions
AUDIO_EXTENSIONS = {'.mp3', '.mp4', '.m4a', '.flac', '.wav', '.ogg', '.opus', '.aac', '.wma'}


def find_audio_files(directory: str, recursive: bool = True) -> List[Path]:
    """
    Find all audio files in a directory.
    
    Args:
        directory: Directory path to search
        recursive: Whether to search subdirectories
    
    Returns:
        List of Path objects for audio files
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


def extract_tune_name_from_path(file_path: Path) -> str:
    """
    Extract a potential tune name from a file path.
    Removes file extension and common prefixes/suffixes.
    """
    # Get just the filename without extension
    name = file_path.stem
    
    # Remove common prefixes/suffixes
    # e.g., "01_The_Butterfly" -> "The_Butterfly"
    name = re.sub(r'^\d+[-_\s]*', '', name)  # Remove leading numbers
    name = re.sub(r'[-_]', ' ', name)  # Replace underscores/hyphens with spaces
    name = re.sub(r'\s+', ' ', name)  # Normalize whitespace
    
    return name.strip()


def is_tune_in_composite_name(tune_name: str, composite_name: str, threshold: float = 0.85) -> bool:
    """
    Check if a tune name appears within a composite track name.
    Handles cases like "Carraroe Jig _ Kesh Jig _ Leaf Reel" containing "Kesh Jig".
    """
    # Common separators in composite track names
    separators = [' _ ', ' / ', ' - ', ', ', ' & ', ' and ']
    
    # First check if tune name appears directly (case insensitive)
    if tune_name.lower() in composite_name.lower():
        return True
    
    # Split composite name by common separators
    parts = [composite_name]
    for sep in separators:
        new_parts = []
        for part in parts:
            new_parts.extend(part.split(sep))
        parts = new_parts
    
    # Clean up parts
    parts = [p.strip() for p in parts if p.strip()]
    
    # Check each part against the tune name
    from fuzzy_match import calculate_similarity
    for part in parts:
        if calculate_similarity(tune_name, part) >= threshold:
            return True
    
    return False


def search_local_files(
    tune_name: str,
    directories: List[str],
    use_aliases: bool = True,
    threshold: float = 0.85,
    recursive: bool = True,
    max_results: Optional[int] = None
) -> List[Tuple[Path, float]]:
    """
    Search for audio files matching a tune name in specified directories.
    
    Args:
        tune_name: The tune name to search for
        directories: List of directory paths to search
        use_aliases: Whether to use TheSession.org aliases
        threshold: Minimum fuzzy match score (0-1)
        recursive: Whether to search subdirectories
        max_results: Maximum number of results to return
    
    Returns:
        List of (file_path, match_score) tuples, sorted by score
    """
    # Get all variations of the tune name
    if use_aliases:
        search_terms = get_all_tune_variations(tune_name)
    else:
        from fuzzy_match import find_common_variations
        search_terms = set(find_common_variations(tune_name))
    
    # Collect all audio files
    all_files = []
    for directory in directories:
        all_files.extend(find_audio_files(directory, recursive))
    
    # Remove duplicates by converting paths to absolute and using a set
    unique_files = []
    seen_paths = set()
    for file_path in all_files:
        abs_path = file_path.absolute()
        if abs_path not in seen_paths:
            seen_paths.add(abs_path)
            unique_files.append(file_path)
    all_files = unique_files
    
    # Extract filenames for matching
    file_candidates = [(f, extract_tune_name_from_path(f)) for f in all_files]
    
    # Find matches
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
    
    # Remove duplicate files (same file path appearing multiple times)
    unique_matches = {}
    for file_path, score in matches:
        abs_path = file_path.absolute()
        if abs_path not in unique_matches or unique_matches[abs_path][1] < score:
            unique_matches[abs_path] = (file_path, score)
    
    # Convert back to list
    matches = [(path, score) for path, score in unique_matches.values()]
    
    # Sort by score (highest first)
    matches.sort(key=lambda x: x[1], reverse=True)
    
    if max_results:
        matches = matches[:max_results]
    
    return matches


def find_tunes_for_set(
    tunes: List[str],
    directories: List[str],
    use_aliases: bool = True,
    threshold: float = 0.85,
    overload: Optional[int] = None
) -> Dict[str, List[Path]]:
    """
    Find local files for a set of tunes.
    
    Args:
        tunes: List of tune names to search for
        directories: List of directories to search
        use_aliases: Whether to use TheSession.org aliases
        threshold: Minimum fuzzy match score
        overload: If set, find up to N versions of each tune
    
    Returns:
        Dictionary mapping tune names to lists of matching file paths
    """
    results = {}
    
    for tune in tunes:
        print(f"Searching for: {tune}")
        max_results = overload if overload else 1
        
        matches = search_local_files(
            tune,
            directories,
            use_aliases=use_aliases,
            threshold=threshold,
            max_results=max_results
        )
        
        if matches:
            results[tune] = [match[0] for match in matches]
            # Show how many were found vs requested
            if overload and len(matches) < overload:
                print(f"  Found {len(matches)} match(es) (requested up to {overload})")
            else:
                print(f"  Found {len(matches)} match(es)")
            for path, score in matches[:3]:  # Show first 3
                print(f"    - {path.name} (score: {score:.2f})")
            if len(matches) > 3:
                print(f"    ... and {len(matches) - 3} more")
        else:
            results[tune] = []
            print(f"  No matches found")
    
    return results


def test_local_search():
    """Test the local file search functionality."""
    test_dir = "/Users/pk/Dropbox/Dreadlap"
    
    print(f"Testing local file search in: {test_dir}")
    print("-" * 50)
    
    # First, let's see what files are in there
    print("\nSample audio files found:")
    audio_files = find_audio_files(test_dir, recursive=True)
    for i, file in enumerate(audio_files[:10]):  # Show first 10
        print(f"  {file.name}")
    print(f"  ... ({len(audio_files)} total audio files)")
    
    # Test searching for specific tunes
    test_tunes = [
        "The Harvest Home",
        "The Butterfly", 
        "Drowsy Maggie",
        "The Silver Spear"
    ]
    
    print("\n\nSearching for test tunes:")
    print("-" * 50)
    
    for tune in test_tunes:
        print(f"\nSearching for: {tune}")
        matches = search_local_files(
            tune,
            [test_dir],
            use_aliases=True,
            threshold=0.7,  # Lower threshold for testing
            max_results=3
        )
        
        if matches:
            for path, score in matches:
                print(f"  Found: {path.name} (score: {score:.2f})")
        else:
            print("  No matches found")


if __name__ == "__main__":
    import re  # Import needed for extract_tune_name_from_path
    test_local_search()