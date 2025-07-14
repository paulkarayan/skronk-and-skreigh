#!/usr/bin/env python3
"""
Handle disambiguation of tunes with the same name but different types.
"""

import csv
from pathlib import Path
from typing import List, Dict, Optional, Tuple
from collections import defaultdict


TUNES_FILE = Path("TheSession-data/csv/tunes.csv")


def get_tune_types(tune_name: str) -> List[Dict[str, str]]:
    """
    Get all tune types for a given tune name.
    Returns list of dicts with tune_id, name, and type.
    """
    if not TUNES_FILE.exists():
        return []
    
    matches = []
    tune_name_lower = tune_name.lower().strip()
    
    # Also try with "The" moved to the end
    tune_name_alt = None
    if tune_name_lower.startswith('the '):
        tune_name_alt = tune_name_lower[4:] + ', the'
    elif not tune_name_lower.endswith(', the'):
        # Try adding ", the" if it might need it
        tune_name_alt = tune_name_lower + ', the'
    
    try:
        with open(TUNES_FILE, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            
            for row in reader:
                # Normalize both for comparison
                row_name = row['name'].lower().strip()
                # Remove "the" at beginning for comparison
                if row_name.startswith('the '):
                    row_name_alt = row_name[4:] + ', the'
                else:
                    row_name_alt = row_name
                
                if row_name == tune_name_lower or row_name_alt == tune_name_lower or \
                   (tune_name_alt and (row_name == tune_name_alt or row_name_alt == tune_name_alt)):
                    # Get unique tune IDs (first column is the unique ID)
                    tune_id = row['tune_id']
                    
                    # Check if we already have this tune_id
                    if not any(m['tune_id'] == tune_id for m in matches):
                        matches.append({
                            'tune_id': tune_id,
                            'name': row['name'],
                            'type': row['type'],
                            'meter': row.get('meter', ''),
                            'key': row.get('key', '')
                        })
        
        return matches
        
    except Exception as e:
        print(f"Error reading tunes data: {e}")
        return []


def format_tune_type_info(tune_info: Dict[str, str]) -> str:
    """Format tune type information for display."""
    parts = [tune_info['type']]
    
    if tune_info.get('meter'):
        parts.append(f"in {tune_info['meter']}")
    
    if tune_info.get('key'):
        parts.append(f"({tune_info['key']})")
    
    return " ".join(parts)


def disambiguate_tune(tune_name: str, preferred_type: Optional[str] = None) -> Optional[str]:
    """
    Disambiguate a tune name that has multiple types.
    
    Args:
        tune_name: The tune name to disambiguate
        preferred_type: Preferred tune type (e.g., "reel", "jig", "slip jig")
    
    Returns:
        The disambiguated search string or None if no disambiguation needed
    """
    tune_types = get_tune_types(tune_name)
    
    if len(tune_types) <= 1:
        # No disambiguation needed
        return None
    
    if preferred_type:
        # Filter to preferred type
        matching_types = [t for t in tune_types if t['type'].lower() == preferred_type.lower()]
        if matching_types:
            return f"{tune_name} ({preferred_type})"
    
    # Return info about multiple types
    type_strs = []
    for tune_info in tune_types:
        type_strs.append(format_tune_type_info(tune_info))
    
    return f"{tune_name} - Multiple types found: {', '.join(type_strs)}"


def suggest_search_strategies(tune_name: str, tune_types: List[Dict[str, str]]) -> List[str]:
    """
    Suggest search strategies for disambiguating tunes.
    """
    strategies = []
    
    # Strategy 1: Search with type in filename/path
    for tune_info in tune_types:
        tune_type = tune_info['type']
        strategies.append(f"Files containing both '{tune_name}' and '{tune_type}'")
    
    # Strategy 2: Search by tempo/rhythm
    type_to_tempo = {
        'reel': ['reel', '116', '120', 'fast'],
        'slip jig': ['slip', 'jig', '9/8', 'slow'],
        'jig': ['jig', '6/8'],
        'hornpipe': ['hornpipe', 'dotted'],
        'polka': ['polka', 'quick']
    }
    
    for tune_info in tune_types:
        tune_type = tune_info['type']
        if tune_type in type_to_tempo:
            keywords = type_to_tempo[tune_type]
            strategies.append(f"For {tune_type}: look for keywords {keywords}")
    
    return strategies


if __name__ == "__main__":
    # Test with Boys of Ballisodare
    test_tune = "Boys of Ballisodare, The"
    
    print(f"Checking tune types for: {test_tune}")
    print("-" * 60)
    
    tune_types = get_tune_types(test_tune)
    
    if not tune_types:
        print("No tune found with this name")
    elif len(tune_types) == 1:
        print(f"Single type found: {format_tune_type_info(tune_types[0])}")
    else:
        print(f"Multiple types found for this tune name:")
        for tune_info in tune_types:
            print(f"  - ID {tune_info['tune_id']}: {format_tune_type_info(tune_info)}")
        
        print("\nSearch strategies:")
        strategies = suggest_search_strategies(test_tune, tune_types)
        for strategy in strategies:
            print(f"  - {strategy}")
        
        print("\nDisambiguation examples:")
        print(f"  - Searching for reel: {disambiguate_tune(test_tune, 'reel')}")
        print(f"  - Searching for slip jig: {disambiguate_tune(test_tune, 'slip jig')}")