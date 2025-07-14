#!/usr/bin/env python3
"""
Fuzzy matching utilities for Irish tune names.
Handles common variations like capitalization, spacing, and minor spelling differences.
"""

import re
from difflib import SequenceMatcher
from typing import List, Tuple, Optional


def normalize_tune_name(name: str) -> str:
    """
    Normalize a tune name for comparison.
    - Convert to lowercase
    - Remove extra spaces
    - Remove common punctuation
    - Normalize "The" at the beginning
    """
    # Convert to lowercase
    name = name.lower().strip()
    
    # Remove apostrophes entirely
    name = re.sub(r"[''`']", '', name)  # Remove all apostrophes
    name = re.sub(r'[,\.\!\?;:]', '', name)  # Remove punctuation
    name = re.sub(r'[-_]', ' ', name)  # Replace hyphens and underscores with spaces
    name = re.sub(r'\s+', ' ', name)  # Normalize whitespace
    
    # Handle "The" at the beginning (common in Irish tune names)
    if name.startswith('the '):
        # Move "the" to the end for comparison
        name = name[4:] + ', the'
    
    return name


def calculate_similarity(str1: str, str2: str) -> float:
    """
    Calculate similarity score between two strings.
    Returns a float between 0 and 1, where 1 is identical.
    """
    # First try exact match after normalization
    norm1 = normalize_tune_name(str1)
    norm2 = normalize_tune_name(str2)
    
    if norm1 == norm2:
        return 1.0
    
    # Use SequenceMatcher for fuzzy matching
    return SequenceMatcher(None, norm1, norm2).ratio()


def fuzzy_match_tune(
    target: str, 
    candidates: List[str], 
    threshold: float = 0.85,
    max_results: Optional[int] = None
) -> List[Tuple[str, float]]:
    """
    Find fuzzy matches for a target tune name in a list of candidates.
    
    Args:
        target: The tune name to search for
        candidates: List of tune names to search in
        threshold: Minimum similarity score (0-1) to consider a match
        max_results: Maximum number of results to return (None for all)
    
    Returns:
        List of (candidate_name, similarity_score) tuples, sorted by score
    """
    matches = []
    
    for candidate in candidates:
        score = calculate_similarity(target, candidate)
        if score >= threshold:
            matches.append((candidate, score))
    
    # Sort by score (highest first)
    matches.sort(key=lambda x: x[1], reverse=True)
    
    if max_results:
        matches = matches[:max_results]
    
    return matches


def is_likely_match(name1: str, name2: str, threshold: float = 0.85) -> bool:
    """
    Quick check if two tune names are likely the same tune.
    """
    return calculate_similarity(name1, name2) >= threshold


def find_common_variations(tune_name: str) -> List[str]:
    """
    Generate common variations of a tune name that might appear in filenames.
    """
    variations = [tune_name]
    
    # Original normalized version
    normalized = normalize_tune_name(tune_name)
    variations.append(normalized)
    
    # Without "The" at the beginning
    if tune_name.lower().startswith('the '):
        variations.append(tune_name[4:])
    
    # With "The" at the beginning if not present
    if not tune_name.lower().startswith('the '):
        variations.append(f"The {tune_name}")
    
    # Common replacements
    replacements = [
        ('&', 'and'),
        ('and', '&'),
        ("'s", 's'),
        ('s', "'s"),
    ]
    
    for old, new in replacements:
        if old in tune_name.lower():
            variations.append(tune_name.replace(old, new))
            variations.append(tune_name.replace(old.title(), new.title()))
    
    # Remove duplicates while preserving order
    seen = set()
    unique_variations = []
    for v in variations:
        v_lower = v.lower()
        if v_lower not in seen:
            seen.add(v_lower)
            unique_variations.append(v)
    
    return unique_variations


if __name__ == "__main__":
    # Test the fuzzy matching
    test_tunes = [
        "The Harvest Home",
        "harvest home",
        "Harvest Homes",
        "The Cork Hornpipe",
        "Drowsy Maggie",
        "drowsy maggie"
    ]
    
    print("Testing fuzzy matching:")
    print("-" * 50)
    
    target = "Harvest Home"
    print(f"\nSearching for: '{target}'")
    matches = fuzzy_match_tune(target, test_tunes)
    for match, score in matches:
        print(f"  {match}: {score:.2f}")
    
    print("\nTesting variations:")
    print("-" * 50)
    for tune in ["The Harvest Home", "Drowsy Maggie's"]:
        print(f"\nVariations of '{tune}':")
        for var in find_common_variations(tune):
            print(f"  - {var}")