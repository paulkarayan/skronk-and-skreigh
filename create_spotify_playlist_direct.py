#!/usr/bin/env python3
"""
Create a Spotify playlist directly from target.md without requiring source file matches.
Uses fuzzy matching and TheSession.org aliases.
"""

import os
import sys
import time
import argparse
from pathlib import Path
from typing import List, Dict, Optional
from dotenv import load_dotenv

import spotipy
from spotipy.oauth2 import SpotifyOAuth

from fuzzy_match import normalize_tune_name, calculate_similarity
from thesession_data import get_tune_aliases
from tune_disambiguation import get_tune_types, format_tune_type_info


class DirectSpotifyPlaylistCreator:
    def __init__(self, client_id, client_secret, redirect_uri="http://127.0.0.1:8888/callback"):
        self.client_id = client_id
        self.client_secret = client_secret
        self.redirect_uri = redirect_uri
        self.scope = "playlist-modify-public playlist-modify-private"
        
        self.sp = spotipy.Spotify(auth_manager=SpotifyOAuth(
            client_id=self.client_id,
            client_secret=self.client_secret,
            redirect_uri=self.redirect_uri,
            scope=self.scope,
            open_browser=True
        ))
        
    def fuzzy_match_track(self, tune_name: str, track_name: str, threshold: float = 0.85) -> bool:
        """Check if a track name matches the tune name using fuzzy matching."""
        norm_tune = normalize_tune_name(tune_name)
        norm_track = normalize_tune_name(track_name)
        
        # Direct substring match
        if norm_tune in norm_track or norm_track in norm_tune:
            return True
        
        # Check similarity
        return calculate_similarity(norm_tune, norm_track) >= threshold
    
    def search_tune_with_context(self, tune_name: str, tune_type: Optional[str] = None, 
                                overload: int = 1, threshold: float = 0.85) -> List[Dict]:
        """
        Search for a tune on Spotify using fuzzy matching, aliases, and type hints.
        Returns list of track info dicts with URIs and metadata.
        """
        # Get all aliases for this tune
        aliases = get_tune_aliases(tune_name)
        
        found_tracks = []
        seen_tracks = set()
        
        # If we have tune type info, use it in search
        type_keywords = []
        if tune_type:
            type_keywords = [tune_type.lower()]
            # Add variations
            if tune_type.lower() == 'reel':
                type_keywords.extend(['reels'])
            elif tune_type.lower() == 'jig':
                type_keywords.extend(['jigs'])
        
        # Try each alias
        for alias in aliases:
            # Build search queries
            searches = []
            
            # If we have type, include it
            if type_keywords:
                for tk in type_keywords:
                    searches.append(f'"{alias}" {tk} irish')
                    searches.append(f'{alias} {tk} irish')
            
            # Standard searches
            searches.extend([
                f'"{alias}" irish traditional',
                f'{alias} irish traditional',
                f'{alias} irish trad',
                f'{alias} irish',
                alias
            ])
            
            for search_query in searches:
                if len(found_tracks) >= overload:
                    break
                    
                try:
                    results = self.sp.search(q=search_query, type='track', limit=30)
                    
                    if results['tracks']['items']:
                        # Score and rank results
                        scored_tracks = []
                        
                        for track in results['tracks']['items']:
                            track_name = track['name']
                            artist_name = track['artists'][0]['name'] if track['artists'] else ""
                            track_uri = track['uri']
                            album_name = track['album']['name'] if track.get('album') else ""
                            
                            # Skip if we've already found this track
                            if track_uri in seen_tracks:
                                continue
                            
                            # Calculate match score
                            score = 0
                            
                            # Check if tune name matches using fuzzy matching
                            if self.fuzzy_match_track(alias, track_name, threshold):
                                score += 10
                            
                            # Bonus for tune type in track/album name
                            if type_keywords:
                                for tk in type_keywords:
                                    if tk in track_name.lower() or tk in album_name.lower():
                                        score += 3
                            
                            # Bonus for Irish/traditional keywords
                            lower_track = track_name.lower()
                            lower_artist = artist_name.lower()
                            lower_album = album_name.lower()
                            
                            irish_keywords = ['irish', 'traditional', 'trad', 'celtic', 'session']
                            for keyword in irish_keywords:
                                if keyword in lower_track or keyword in lower_artist or keyword in lower_album:
                                    score += 2
                            
                            # Penalty for non-traditional indicators
                            modern_keywords = ['remix', 'cover', 'rock', 'pop', 'jazz', 'metal', 'techno']
                            for keyword in modern_keywords:
                                if keyword in lower_track or keyword in lower_artist:
                                    score -= 3
                            
                            if score > 0:
                                scored_tracks.append((score, track))
                        
                        # Sort by score and add best matches
                        scored_tracks.sort(key=lambda x: x[0], reverse=True)
                        
                        for score, track in scored_tracks[:overload - len(found_tracks)]:
                            if track['uri'] not in seen_tracks:
                                found_tracks.append({
                                    'uri': track['uri'],
                                    'name': track['name'],
                                    'artist': track['artists'][0]['name'] if track['artists'] else 'Unknown',
                                    'album': track['album']['name'] if track.get('album') else 'Unknown',
                                    'score': score,
                                    'matched_alias': alias
                                })
                                seen_tracks.add(track['uri'])
                                
                except Exception as e:
                    print(f"    Search error: {e}")
                    time.sleep(1)
                
                time.sleep(0.1)  # Be nice to Spotify API
                
            if len(found_tracks) >= overload:
                break
        
        return found_tracks[:overload]


def read_target_file_direct(target_file: str):
    """Read target.md directly to get tune sets"""
    sets = []
    
    with open(target_file, 'r') as f:
        lines = f.readlines()
    
    for line in lines:
        line = line.strip()
        # Skip empty lines and comments
        if line and not line.startswith('#'):
            # Split by ' / ' to get individual tunes
            tunes = [tune.strip() for tune in line.split(' / ')]
            if tunes:
                sets.append({
                    'set_name': ' / '.join(tunes),
                    'tunes': tunes
                })
    
    return sets


def main():
    load_dotenv()
    
    parser = argparse.ArgumentParser(
        description="Create a Spotify playlist directly from target.md"
    )
    parser.add_argument(
        "--target",
        default="target.md",
        help="Target file with sets to include (default: target.md)"
    )
    parser.add_argument(
        "--overload",
        type=int,
        default=1,
        help="Find up to N versions of each tune (default: 1)"
    )
    parser.add_argument(
        "--threshold",
        type=float,
        default=0.85,
        help="Minimum match score (default: 0.85)"
    )
    parser.add_argument(
        "--playlist-name",
        help="Custom playlist name"
    )
    parser.add_argument(
        "--show-types",
        action="store_true",
        help="Show tune type information"
    )
    
    args = parser.parse_args()
    
    # Get Spotify credentials
    CLIENT_ID = os.getenv('SPOTIFY_CLIENT_ID')
    CLIENT_SECRET = os.getenv('SPOTIFY_CLIENT_SECRET')
    
    if not CLIENT_ID or not CLIENT_SECRET:
        print("Please set SPOTIFY_CLIENT_ID and SPOTIFY_CLIENT_SECRET in .env file")
        print("Example .env file:")
        print("SPOTIFY_CLIENT_ID=your_client_id")
        print("SPOTIFY_CLIENT_SECRET=your_client_secret")
        sys.exit(1)
    
    # Read target file
    print(f"Reading target file: {args.target}")
    matched_sets = read_target_file_direct(args.target)
    
    if not matched_sets:
        print("No sets found in target file")
        sys.exit(1)
    
    # Get all unique tunes
    all_tunes = set()
    for set_data in matched_sets:
        all_tunes.update(set_data['tunes'])
    
    print(f"Found {len(matched_sets)} sets containing {len(all_tunes)} unique tunes")
    
    # Initialize Spotify client
    spotify_creator = DirectSpotifyPlaylistCreator(CLIENT_ID, CLIENT_SECRET)
    
    # Get current user ID
    user_id = spotify_creator.sp.current_user()['id']
    
    # Create playlist
    playlist_name = args.playlist_name or f"Irish Session Practice - {time.strftime('%Y-%m-%d')}"
    playlist = spotify_creator.sp.user_playlist_create(
        user_id, 
        playlist_name,
        public=False,
        description=f"Irish traditional music sets (threshold={args.threshold}, overload={args.overload})"
    )
    
    print(f"\nCreated playlist: {playlist_name}")
    print(f"Playlist URL: {playlist['external_urls']['spotify']}")
    
    # Search for tunes
    print(f"\nSearching for tunes on Spotify...")
    
    all_track_uris = []
    not_found = []
    stats = {'exact': 0, 'alias': 0, 'fuzzy': 0, 'total': 0}
    
    # Process each set
    for set_idx, set_data in enumerate(matched_sets):
        print(f"\nSet {set_idx + 1}: {set_data['set_name']}")
        
        for tune in set_data['tunes']:
            # Get tune type if available
            tune_type = None
            if args.show_types:
                tune_types = get_tune_types(tune)
                if tune_types and len(tune_types) == 1:
                    tune_type = tune_types[0]['type']
            
            print(f"  Searching: {tune}" + (f" ({tune_type})" if tune_type else ""))
            
            # Search with context
            tracks = spotify_creator.search_tune_with_context(
                tune, tune_type, args.overload, args.threshold
            )
            
            if tracks:
                for track_info in tracks:
                    all_track_uris.append(track_info['uri'])
                    
                    # Determine match type
                    if tune.lower() in track_info['name'].lower():
                        match_type = "exact"
                        stats['exact'] += 1
                    elif track_info['matched_alias'].lower() != tune.lower():
                        match_type = "alias"
                        stats['alias'] += 1
                    else:
                        match_type = "fuzzy"
                        stats['fuzzy'] += 1
                    
                    stats['total'] += 1
                    
                    print(f"    ✓ {match_type}: {track_info['name']} - {track_info['artist']}")
            else:
                not_found.append(tune)
                print(f"    ✗ Not found")
    
    # Add tracks to playlist in batches
    if all_track_uris:
        # Remove duplicates while preserving order
        seen = set()
        unique_uris = []
        for uri in all_track_uris:
            if uri not in seen:
                seen.add(uri)
                unique_uris.append(uri)
        
        for i in range(0, len(unique_uris), 100):
            batch = unique_uris[i:i+100]
            spotify_creator.sp.playlist_add_items(playlist['id'], batch)
        
        print(f"\n✓ Added {len(unique_uris)} unique tracks to playlist")
        print(f"\nMatch statistics:")
        print(f"  Total matches: {stats['total']}")
        print(f"  - Exact: {stats['exact']}")
        print(f"  - Alias: {stats['alias']}")
        print(f"  - Fuzzy: {stats['fuzzy']}")
    
    if not_found:
        print(f"\n⚠️  Could not find {len(not_found)} tunes:")
        for tune in not_found[:10]:
            print(f"  - {tune}")
        if len(not_found) > 10:
            print(f"  ... and {len(not_found) - 10} more")
    
    print(f"\n✓ Done! Your playlist is ready:")
    print(f"  {playlist['external_urls']['spotify']}")


if __name__ == "__main__":
    main()