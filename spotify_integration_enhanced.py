import os
import spotipy
from spotipy.oauth2 import SpotifyOAuth
from irish_playlist_manager import IrishPlaylistManager
import time
from dotenv import load_dotenv
from fuzzy_match import normalize_tune_name, calculate_similarity
from thesession_data import get_tune_aliases
from typing import List, Optional, Dict, Tuple


class EnhancedSpotifyPlaylistCreator:
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
        # Normalize both names
        norm_tune = normalize_tune_name(tune_name)
        norm_track = normalize_tune_name(track_name)
        
        # Direct substring match
        if norm_tune in norm_track or norm_track in norm_tune:
            return True
        
        # Check similarity
        return calculate_similarity(norm_tune, norm_track) >= threshold
    
    def search_tune_with_aliases(self, tune_name: str, overload: int = 1) -> List[str]:
        """
        Search for a tune on Spotify using fuzzy matching and aliases.
        Returns up to 'overload' number of track URIs.
        """
        # Get all aliases for this tune
        aliases = get_tune_aliases(tune_name)
        
        found_tracks = []
        seen_tracks = set()  # Avoid duplicates
        
        # Try each alias
        for alias in aliases:
            # Try different search strategies
            searches = [
                f'"{alias}" irish traditional',
                f'{alias} irish traditional',
                f'{alias} irish trad',
                f'{alias} irish',
                alias
            ]
            
            for search_query in searches:
                if len(found_tracks) >= overload:
                    break
                    
                try:
                    results = self.sp.search(q=search_query, type='track', limit=20)
                    
                    if results['tracks']['items']:
                        # Score and rank results
                        scored_tracks = []
                        
                        for track in results['tracks']['items']:
                            track_name = track['name']
                            artist_name = track['artists'][0]['name'] if track['artists'] else ""
                            track_uri = track['uri']
                            
                            # Skip if we've already found this track
                            if track_uri in seen_tracks:
                                continue
                            
                            # Calculate match score
                            score = 0
                            
                            # Check if tune name matches using fuzzy matching
                            if self.fuzzy_match_track(alias, track_name):
                                score += 10
                            
                            # Bonus for Irish/traditional keywords
                            lower_track = track_name.lower()
                            lower_artist = artist_name.lower()
                            
                            irish_keywords = ['irish', 'traditional', 'trad', 'celtic', 'reel', 'jig', 'hornpipe']
                            for keyword in irish_keywords:
                                if keyword in lower_track or keyword in lower_artist:
                                    score += 2
                            
                            # Penalty for non-traditional indicators
                            modern_keywords = ['remix', 'cover', 'rock', 'pop', 'jazz', 'metal']
                            for keyword in modern_keywords:
                                if keyword in lower_track or keyword in lower_artist:
                                    score -= 3
                            
                            if score > 0:
                                scored_tracks.append((score, track))
                        
                        # Sort by score and add best matches
                        scored_tracks.sort(key=lambda x: x[0], reverse=True)
                        
                        for score, track in scored_tracks[:overload - len(found_tracks)]:
                            if track['uri'] not in seen_tracks:
                                found_tracks.append(track['uri'])
                                seen_tracks.add(track['uri'])
                                
                except Exception as e:
                    print(f"    Search error: {e}")
                    time.sleep(1)  # Back off on error
                
                time.sleep(0.1)  # Be nice to Spotify API
                
            if len(found_tracks) >= overload:
                break
        
        return found_tracks[:overload]
    
    def create_playlist(self, playlist_name: str, matching_sets: List, overload: int = 1):
        """Create a Spotify playlist from the matching sets with fuzzy matching"""
        # Get current user ID
        user_id = self.sp.current_user()['id']
        
        # Create playlist
        playlist = self.sp.user_playlist_create(
            user_id, 
            playlist_name,
            public=False,
            description=f"Irish traditional music sets for practice (overload={overload})"
        )
        
        print(f"\nCreated playlist: {playlist_name}")
        print(f"Playlist URL: {playlist['external_urls']['spotify']}")
        
        # Search and add tracks
        all_track_uris = []
        not_found = []
        stats = {'exact': 0, 'fuzzy': 0, 'alias': 0}
        
        for i, tune_set in enumerate(matching_sets, 1):
            print(f"\nProcessing {tune_set}...")
            
            for tune in tune_set.tunes:
                print(f"  Searching for: {tune.name}")
                
                # Search with aliases and fuzzy matching
                uris = self.search_tune_with_aliases(tune.name, overload)
                
                if uris:
                    all_track_uris.extend(uris)
                    
                    # Show what we found
                    for uri in uris:
                        track_info = self.sp.track(uri)
                        track_name = track_info['name']
                        artist = track_info['artists'][0]['name']
                        
                        # Determine match type
                        if tune.name.lower() in track_name.lower():
                            match_type = "exact"
                            stats['exact'] += 1
                        elif any(alias.lower() in track_name.lower() for alias in get_tune_aliases(tune.name)):
                            match_type = "alias"
                            stats['alias'] += 1
                        else:
                            match_type = "fuzzy"
                            stats['fuzzy'] += 1
                        
                        print(f"    ✓ Found ({match_type}): {track_name} by {artist}")
                else:
                    not_found.append(f"{tune_set.set_type} set {tune_set.set_number}: {tune.name}")
                    print(f"    ✗ Not found: {tune.name}")
        
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
                self.sp.playlist_add_items(playlist['id'], batch)
            
            print(f"\nAdded {len(unique_uris)} unique tracks to playlist")
            print(f"Match statistics:")
            print(f"  - Exact matches: {stats['exact']}")
            print(f"  - Alias matches: {stats['alias']}")
            print(f"  - Fuzzy matches: {stats['fuzzy']}")
        
        if not_found:
            print(f"\nCould not find {len(not_found)} tunes:")
            for tune in not_found[:10]:  # Show first 10
                print(f"  - {tune}")
            if len(not_found) > 10:
                print(f"  ... and {len(not_found) - 10} more")
                
        return playlist['external_urls']['spotify']


def main():
    # Load environment variables
    load_dotenv()
    
    # Get Spotify credentials from .env
    CLIENT_ID = os.getenv('SPOTIFY_CLIENT_ID')
    CLIENT_SECRET = os.getenv('SPOTIFY_CLIENT_SECRET')
    
    if not CLIENT_ID or not CLIENT_SECRET:
        print("Please set SPOTIFY_CLIENT_ID and SPOTIFY_CLIENT_SECRET in .env file")
        print("Example .env file:")
        print("SPOTIFY_CLIENT_ID=your_client_id")
        print("SPOTIFY_CLIENT_SECRET=your_client_secret")
        return
    
    # Parse arguments
    import argparse
    parser = argparse.ArgumentParser(description="Create Spotify playlist with fuzzy matching")
    parser.add_argument("--overload", type=int, default=1, 
                       help="Number of versions per tune (default: 1)")
    parser.add_argument("--playlist-name", type=str,
                       help="Custom playlist name")
    args = parser.parse_args()
    
    # Initialize managers
    irish_manager = IrishPlaylistManager()
    spotify_creator = EnhancedSpotifyPlaylistCreator(CLIENT_ID, CLIENT_SECRET)
    
    # Parse target sets
    target_sets = irish_manager.parse_target_file("target.md")
    
    if not target_sets:
        print("No target sets found in target.md")
        return
        
    # Find matching sets
    matching_sets = irish_manager.find_matching_sets(target_sets)
    
    print(f"Found {len(matching_sets)} matching sets to add to Spotify")
    
    # Create playlist
    playlist_name = args.playlist_name or f"Irish Session Practice - {time.strftime('%Y-%m-%d')}"
    playlist_url = spotify_creator.create_playlist(playlist_name, matching_sets, args.overload)
    
    print(f"\n✓ Done! Your playlist is ready:")
    print(f"  {playlist_url}")


if __name__ == "__main__":
    main()