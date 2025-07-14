#!/usr/bin/env python3
"""
Integration with TheSession data files for fetching tune aliases.
Uses the weekly updated data from https://github.com/adactio/TheSession-data
"""

import csv
import json
import os
import subprocess
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Set, Optional
from collections import defaultdict


DATA_DIR = Path("TheSession-data")
ALIASES_FILE = DATA_DIR / "csv" / "aliases.csv"
TUNES_FILE = DATA_DIR / "csv" / "tunes.csv"


def update_thesession_data() -> bool:
    """
    Update TheSession data from GitHub.
    Returns True if successful, False otherwise.
    """
    try:
        if DATA_DIR.exists():
            # Pull latest changes
            print("Updating TheSession data...")
            result = subprocess.run(
                ["git", "pull"], 
                cwd=DATA_DIR,
                capture_output=True,
                text=True
            )
            if result.returncode != 0:
                print(f"Error updating: {result.stderr}")
                return False
        else:
            # Clone the repository
            print("Downloading TheSession data...")
            result = subprocess.run(
                ["git", "clone", "https://github.com/adactio/TheSession-data.git"],
                capture_output=True,
                text=True
            )
            if result.returncode != 0:
                print(f"Error cloning: {result.stderr}")
                return False
        
        print("TheSession data updated successfully")
        return True
        
    except Exception as e:
        print(f"Error updating TheSession data: {e}")
        return False


def load_aliases_data() -> Dict[str, List[str]]:
    """
    Load the aliases data from CSV file.
    Returns a dictionary mapping tune names to lists of aliases.
    """
    if not ALIASES_FILE.exists():
        print("Aliases file not found. Attempting to download TheSession data...")
        if not update_thesession_data():
            return {}
    
    # Build a map from tune names (and aliases) to all aliases
    name_to_aliases = defaultdict(set)
    
    try:
        with open(ALIASES_FILE, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            
            # Group aliases by tune_id first
            tune_aliases = defaultdict(set)
            for row in reader:
                tune_id = row['tune_id']
                alias = row['alias']
                name = row['name']
                
                # Add both alias and canonical name
                tune_aliases[tune_id].add(alias)
                tune_aliases[tune_id].add(name)
            
            # Now create mappings from any name to all aliases
            for tune_id, aliases in tune_aliases.items():
                alias_list = list(aliases)
                for alias in alias_list:
                    # Normalize the key for case-insensitive lookup
                    key = alias.lower().strip()
                    name_to_aliases[key].update(alias_list)
        
        # Convert sets to lists
        return {k: list(v) for k, v in name_to_aliases.items()}
        
    except Exception as e:
        print(f"Error loading aliases data: {e}")
        return {}


# Cache the loaded data
_aliases_cache = None
_cache_time = None
CACHE_DURATION = timedelta(hours=1)  # Reload data every hour


def get_aliases_map() -> Dict[str, List[str]]:
    """
    Get the aliases map, using cache if available.
    """
    global _aliases_cache, _cache_time
    
    now = datetime.now()
    if (_aliases_cache is None or 
        _cache_time is None or 
        now - _cache_time > CACHE_DURATION):
        
        _aliases_cache = load_aliases_data()
        _cache_time = now
    
    return _aliases_cache


def get_tune_aliases(tune_name: str) -> List[str]:
    """
    Get all known aliases for a tune name.
    
    Args:
        tune_name: The tune name to look up
    
    Returns:
        List of alternative names for the tune, including the original
    """
    aliases_map = get_aliases_map()
    
    # Normalize for lookup
    key = tune_name.lower().strip()
    
    if key in aliases_map:
        aliases = aliases_map[key].copy()
        # Ensure the searched name is included
        if tune_name not in aliases:
            aliases.append(tune_name)
        return aliases
    else:
        # Return just the original name if not found
        return [tune_name]


def get_all_tune_variations(tune_name: str) -> Set[str]:
    """
    Get all variations of a tune name, including aliases and common variations.
    Returns a set to avoid duplicates.
    """
    from fuzzy_match import find_common_variations
    
    variations = set()
    
    # Get aliases from TheSession data
    aliases = get_tune_aliases(tune_name)
    variations.update(aliases)
    
    # Get common variations for each alias
    for alias in aliases:
        variations.update(find_common_variations(alias))
    
    return variations


def search_tunes(query: str, max_results: int = 10) -> List[Dict[str, str]]:
    """
    Search for tunes by name in TheSession data.
    Returns a list of matching tunes with their IDs and names.
    """
    if not TUNES_FILE.exists():
        print("Tunes file not found. Attempting to download TheSession data...")
        if not update_thesession_data():
            return []
    
    results = []
    query_lower = query.lower()
    
    try:
        with open(TUNES_FILE, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            
            for row in reader:
                if query_lower in row['name'].lower():
                    results.append({
                        'id': row['tune_id'],
                        'name': row['name'],
                        'type': row.get('type', 'unknown')
                    })
                    
                    if len(results) >= max_results:
                        break
        
        return results
        
    except Exception as e:
        print(f"Error searching tunes: {e}")
        return []


if __name__ == "__main__":
    # Test the new implementation
    print("Testing TheSession data integration:")
    print("-" * 50)
    
    # Ensure we have the latest data
    update_thesession_data()
    
    test_tunes = [
        "The Harvest Home",
        "The Butterfly",
        "Drowsy Maggie",
        "The Silver Spear",
        "Cooley's"
    ]
    
    for tune in test_tunes:
        print(f"\nLooking up: {tune}")
        aliases = get_tune_aliases(tune)
        print(f"Found {len(aliases)} names:")
        for alias in aliases[:5]:  # Show first 5
            print(f"  - {alias}")
        if len(aliases) > 5:
            print(f"  ... and {len(aliases) - 5} more")
    
    print("\n\nSearching for 'butterfly':")
    results = search_tunes("butterfly")
    for result in results[:5]:
        print(f"  {result['id']}: {result['name']} ({result['type']})")