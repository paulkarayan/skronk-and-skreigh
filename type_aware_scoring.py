#!/usr/bin/env python3
"""
Type-aware scoring for tune matching when multiple tune types exist.
"""

from pathlib import Path
from typing import List, Tuple, Optional


def score_by_type(
    file_path: Path,
    base_score: float,
    tune_types: List[dict],
    preferred_type: Optional[str] = None
) -> float:
    """
    Adjust score based on tune type detection in filename/path.
    
    Args:
        file_path: The audio file path
        base_score: The original match score
        tune_types: List of tune type info from TheSession
        preferred_type: User-specified preferred type
    
    Returns:
        Adjusted score
    """
    if len(tune_types) <= 1:
        # No ambiguity, return original score
        return base_score
    
    path_str = str(file_path).lower()
    filename = file_path.name.lower()
    
    # Type keywords and their boost values
    type_keywords = {
        'reel': ['reel', 'reels', '120bpm', '116bpm', 'fast'],
        'jig': ['jig', 'jigs', '6/8'],
        'slip jig': ['slip', 'slip jig', 'slip-jig', '9/8', 'hop jig'],
        'slide': ['slide', 'slides', '12/8'],
        'hornpipe': ['hornpipe', 'hornpipes'],
        'polka': ['polka', 'polkas'],
        'waltz': ['waltz', 'waltzes', '3/4'],
        'mazurka': ['mazurka', 'mazurkas'],
        'barndance': ['barndance', 'barn dance'],
        'strathspey': ['strathspey', 'strathspeys']
    }
    
    # If user specified a type, boost matches for that type
    if preferred_type:
        preferred_type_lower = preferred_type.lower()
        
        # Check if this file matches the preferred type
        if preferred_type_lower in type_keywords:
            keywords = type_keywords[preferred_type_lower]
            for keyword in keywords:
                if keyword in path_str:
                    # Strong boost for matching preferred type
                    return min(base_score * 1.2, 1.0)
        
        # Check if it matches a different type (penalty)
        for tune_info in tune_types:
            if tune_info['type'].lower() != preferred_type_lower:
                other_type = tune_info['type'].lower()
                if other_type in type_keywords:
                    keywords = type_keywords[other_type]
                    for keyword in keywords:
                        if keyword in path_str:
                            # Penalty for matching wrong type
                            return base_score * 0.8
    
    else:
        # No preferred type - boost files that have ANY type indicator
        max_boost = 1.0
        
        for tune_info in tune_types:
            tune_type = tune_info['type'].lower()
            if tune_type in type_keywords:
                keywords = type_keywords[tune_type]
                for keyword in keywords:
                    if keyword in path_str:
                        # Mild boost for having type info
                        max_boost = max(max_boost, 1.1)
                        break
        
        return min(base_score * max_boost, 1.0)
    
    return base_score


def filter_by_type(
    matches: List[Tuple[Path, float, Optional[str]]],
    tune_types: List[dict],
    preferred_type: Optional[str] = None
) -> List[Tuple[Path, float, Optional[str]]]:
    """
    Re-score matches based on tune type detection.
    
    Args:
        matches: List of (path, score, reason) tuples
        tune_types: List of tune type info from TheSession
        preferred_type: User-specified preferred type
    
    Returns:
        Re-scored and sorted matches
    """
    if len(tune_types) <= 1:
        # No ambiguity
        return matches
    
    # Re-score all matches
    rescored = []
    for path, score, reason in matches:
        new_score = score_by_type(path, score, tune_types, preferred_type)
        
        # Add type info to reason if detected
        if new_score != score and reason:
            if new_score > score:
                reason = f"{reason} [type match]"
            else:
                reason = f"{reason} [type mismatch]"
        
        rescored.append((path, new_score, reason))
    
    # Re-sort by new scores
    rescored.sort(key=lambda x: x[1], reverse=True)
    
    return rescored