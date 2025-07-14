#!/usr/bin/env python3
"""
Album-aware search functionality using TheSession recordings data.
Helps find tunes that might be on albums under different names.
"""

import csv
from pathlib import Path
from collections import defaultdict
from typing import List, Dict, Set, Tuple, Optional
from thesession_data import get_tune_aliases
from local_file_search import search_local_files, find_audio_files
from fuzzy_match import fuzzy_match_tune, normalize_tune_name


RECORDINGS_FILE = Path("TheSession-data/csv/recordings.csv")


def load_recordings_data() -> Dict[str, List[Dict]]:
    """
    Load recordings data and create mappings.
    Returns dict mapping artist_album to list of tunes.
    """
    if not RECORDINGS_FILE.exists():
        print("Recordings file not found. Run: python thesession_data.py to download data.")
        return {}
    
    # Map from "artist - album" to list of tunes on that album
    album_tunes = defaultdict(list)
    
    try:
        with open(RECORDINGS_FILE, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            
            for row in reader:
                artist = row.get('artist', '').strip()
                album = row.get('recording', '').strip()
                tune = row.get('tune', '').strip()
                tune_id = row.get('tune_id', '').strip()
                track = row.get('track', '').strip()
                
                if artist and album and tune:
                    # Create album key
                    album_key = f"{artist} - {album}"
                    
                    album_tunes[album_key].append({
                        'tune': tune,
                        'tune_id': tune_id,
                        'track': track,
                        'artist': artist,
                        'album': album
                    })
        
        return dict(album_tunes)
        
    except Exception as e:
        print(f"Error loading recordings data: {e}")
        return {}


def find_albums_with_tune(tune_name: str, use_aliases: bool = True) -> List[Dict]:
    """
    Find all albums that contain a specific tune.
    
    Returns list of dicts with album info.
    """
    album_data = load_recordings_data()
    
    # Get all variations of the tune name
    if use_aliases:
        search_names = set(get_tune_aliases(tune_name))
    else:
        search_names = {tune_name}
    
    # Normalize search names
    normalized_search = {normalize_tune_name(name) for name in search_names}
    
    matching_albums = []
    
    for album_key, tunes in album_data.items():
        for tune_info in tunes:
            tune_on_album = normalize_tune_name(tune_info['tune'])
            
            # Check if any search name matches
            for search_name in normalized_search:
                if search_name == tune_on_album:
                    matching_albums.append({
                        'artist': tune_info['artist'],
                        'album': tune_info['album'],
                        'track': tune_info['track'],
                        'album_key': album_key,
                        'tune_as_listed': tune_info['tune']
                    })
                    break
    
    return matching_albums


def search_by_album_context(
    tune_name: str,
    directories: List[str],
    threshold: float = 0.85,
    use_aliases: bool = True
) -> List[Tuple[Path, float, str]]:
    """
    Search for files that might contain a tune based on album context.
    
    Returns list of (file_path, score, reason) tuples.
    """
    # First, find albums containing this tune
    albums = find_albums_with_tune(tune_name, use_aliases)
    
    if not albums:
        return []
    
    # Get all audio files
    all_files = []
    for directory in directories:
        all_files.extend(find_audio_files(directory, recursive=True))
    
    matches = []
    
    for album_info in albums:
        artist = album_info['artist']
        album = album_info['album']
        
        # Look for files that might be from this album
        for file_path in all_files:
            # Check if artist name appears in path
            path_str = str(file_path).lower()
            
            artist_match = False
            album_match = False
            
            # Fuzzy match artist in path
            if artist.lower() in path_str:
                artist_match = True
            else:
                # Try fuzzy matching on directory names
                for part in file_path.parts:
                    if fuzzy_match_tune(artist, [part], threshold=0.8):
                        artist_match = True
                        break
            
            # Fuzzy match album in path
            if album.lower() in path_str:
                album_match = True
            else:
                # Try fuzzy matching on directory names
                for part in file_path.parts:
                    if fuzzy_match_tune(album, [part], threshold=0.8):
                        album_match = True
                        break
            
            # If we have a good match, add it
            if artist_match and album_match:
                reason = f"Album: {artist} - {album}"
                # Check if it's the specific track
                track_num = album_info.get('track', '')
                if track_num and track_num.isdigit() and f"{int(track_num):02d}" in file_path.name:
                    score = 0.95  # High confidence
                else:
                    score = 0.85  # Good confidence
                
                matches.append((file_path, score, reason))
            elif artist_match or album_match:
                # Partial match
                reason = f"Possible album: {artist} - {album}"
                score = 0.75
                matches.append((file_path, score, reason))
    
    # Remove duplicates and sort by score
    unique_matches = {}
    for path, score, reason in matches:
        if path not in unique_matches or unique_matches[path][0] < score:
            unique_matches[path] = (score, reason)
    
    return [(path, score, reason) for path, (score, reason) in unique_matches.items()]


def print_album_info(tune_name: str):
    """Print information about albums containing a tune."""
    albums = find_albums_with_tune(tune_name)
    
    if not albums:
        print(f"No albums found containing '{tune_name}'")
        return
    
    print(f"\nAlbums containing '{tune_name}':")
    print("-" * 60)
    
    # Group by artist
    by_artist = defaultdict(list)
    for album in albums:
        by_artist[album['artist']].append(album)
    
    for artist, artist_albums in sorted(by_artist.items()):
        print(f"\n{artist}:")
        for album_info in artist_albums:
            track = album_info.get('track', '?')
            listed_as = album_info['tune_as_listed']
            print(f"  - {album_info['album']} (Track {track}: \"{listed_as}\")")


if __name__ == "__main__":
    # Test the album search
    test_tune = "The Boys of Ballisodare"
    
    print(f"Testing album search for: {test_tune}")
    print_album_info(test_tune)
    
    # Test file search with album context
    print(f"\n\nSearching for files based on album context:")
    print("-" * 60)
    
    matches = search_by_album_context(
        test_tune,
        ["/Users/pk/Dropbox/Dreadlap"],
        use_aliases=True
    )
    
    if matches:
        for path, score, reason in matches[:10]:  # Show first 10
            print(f"{path.name} (score: {score:.2f})")
            print(f"  Reason: {reason}")
            print(f"  Path: {path.parent}")