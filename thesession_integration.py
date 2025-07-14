#!/usr/bin/env python3
"""
Integration with TheSession.org for fetching tune aliases and alternative names.
Includes local caching to minimize API calls and support offline usage.
"""

import json
import os
import re
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Set
from urllib.parse import quote_plus
import requests
from bs4 import BeautifulSoup


CACHE_FILE = "tune_aliases_cache.json"
CACHE_EXPIRY_DAYS = 30  # Refresh cache entries older than this


def load_cache() -> Dict:
    """Load the local cache of tune aliases."""
    if os.path.exists(CACHE_FILE):
        try:
            with open(CACHE_FILE, 'r') as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError):
            return {}
    return {}


def save_cache(cache: Dict) -> None:
    """Save the cache to disk."""
    with open(CACHE_FILE, 'w') as f:
        json.dump(cache, f, indent=2)


def is_cache_entry_valid(entry: Dict) -> bool:
    """Check if a cache entry is still valid."""
    if 'timestamp' not in entry:
        return False
    
    entry_time = datetime.fromisoformat(entry['timestamp'])
    expiry_time = datetime.now() - timedelta(days=CACHE_EXPIRY_DAYS)
    return entry_time > expiry_time


def search_thesession(tune_name: str) -> Optional[str]:
    """
    Search for a tune on TheSession.org and return the URL of the first result.
    """
    search_url = f"https://thesession.org/tunes/search?q={quote_plus(tune_name)}"
    
    try:
        response = requests.get(search_url, timeout=10)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Find the first tune link in search results
        # TheSession.org search results have tune links like /tunes/123
        tune_links = soup.find_all('a', href=re.compile(r'^/tunes/\d+$'))
        
        if tune_links:
            # Get the first result
            first_link = tune_links[0]
            tune_id = first_link['href'].split('/')[-1]
            return f"https://thesession.org/tunes/{tune_id}"
        
        return None
        
    except (requests.RequestException, Exception) as e:
        print(f"Error searching TheSession.org: {e}")
        return None


def fetch_tune_aliases(tune_url: str) -> List[str]:
    """
    Fetch the aliases for a tune from its TheSession.org page.
    """
    try:
        response = requests.get(tune_url, timeout=10)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Find the "Also known as" section
        info_paragraphs = soup.find_all('p', class_='info')
        
        aliases = []
        for p in info_paragraphs:
            text = p.get_text()
            if text.startswith('Also known as'):
                # Extract the aliases - they're typically comma-separated
                alias_text = text.replace('Also known as', '').strip()
                # Split by comma and clean up each alias
                aliases = [alias.strip() for alias in alias_text.split(',')]
                aliases = [a for a in aliases if a]  # Remove empty strings
                break
        
        # Also get the main title of the tune
        title_elem = soup.find('h1')
        if title_elem:
            main_title = title_elem.get_text().strip()
            if main_title and main_title not in aliases:
                aliases.insert(0, main_title)
        
        return aliases
        
    except (requests.RequestException, Exception) as e:
        print(f"Error fetching tune info from {tune_url}: {e}")
        return []


def get_tune_aliases(tune_name: str, use_cache: bool = True) -> List[str]:
    """
    Get all known aliases for a tune name.
    
    Args:
        tune_name: The tune name to look up
        use_cache: Whether to use cached results (default True)
    
    Returns:
        List of alternative names for the tune, including the original
    """
    # Always check cache first
    cache = load_cache()
    cache_key = tune_name.lower().strip()
    
    if use_cache and cache_key in cache:
        entry = cache[cache_key]
        if is_cache_entry_valid(entry):
            return entry['aliases']
    
    # Search TheSession.org
    print(f"Searching TheSession.org for '{tune_name}'...")
    tune_url = search_thesession(tune_name)
    
    if not tune_url:
        # If no results, return just the original name
        aliases = [tune_name]
    else:
        # Fetch aliases from the tune page
        aliases = fetch_tune_aliases(tune_url)
        if not aliases:
            aliases = [tune_name]
        elif tune_name not in aliases:
            # Ensure the searched name is included
            aliases.append(tune_name)
    
    # Update cache
    cache[cache_key] = {
        'aliases': aliases,
        'timestamp': datetime.now().isoformat(),
        'url': tune_url
    }
    save_cache(cache)
    
    # Small delay to be respectful to TheSession.org
    time.sleep(0.5)
    
    return aliases


def get_all_tune_variations(tune_name: str) -> Set[str]:
    """
    Get all variations of a tune name, including aliases and common variations.
    Returns a set to avoid duplicates.
    """
    from fuzzy_match import find_common_variations
    
    variations = set()
    
    # Get aliases from TheSession.org
    aliases = get_tune_aliases(tune_name)
    variations.update(aliases)
    
    # Get common variations for each alias
    for alias in aliases:
        variations.update(find_common_variations(alias))
    
    return variations


def preload_cache(tune_names: List[str]) -> None:
    """
    Preload the cache with multiple tune names.
    Useful for batch processing.
    """
    for tune_name in tune_names:
        get_tune_aliases(tune_name)
        print(f"Cached aliases for: {tune_name}")


if __name__ == "__main__":
    # Test the integration
    test_tunes = [
        "The Harvest Home",
        "The Butterfly",
        "Drowsy Maggie",
        "The Silver Spear"
    ]
    
    print("Testing TheSession.org integration:")
    print("-" * 50)
    
    for tune in test_tunes:
        print(f"\nLooking up: {tune}")
        aliases = get_tune_aliases(tune)
        print(f"Found {len(aliases)} names:")
        for alias in aliases:
            print(f"  - {alias}")
    
    print("\n\nAll variations for 'The Harvest Home':")
    print("-" * 50)
    variations = get_all_tune_variations("The Harvest Home")
    for var in sorted(variations):
        print(f"  - {var}")