#!/usr/bin/env python3
"""
Simple Spotify playlist creator with manual auth URL handling
"""

import os
import sys
import webbrowser
import argparse
from dotenv import load_dotenv
import spotipy
from spotipy.oauth2 import SpotifyOAuth
from irish_playlist_manager import IrishPlaylistManager
from spotify_integration import SpotifyPlaylistCreator

def write_songs_to_file(matching_sets, filename="single-songs.md"):
    """Write all individual song names to a file"""
    with open(filename, 'w') as f:
        f.write("# Individual Songs from Matching Sets\n\n")
        seen_songs = set()
        for tune_set in matching_sets:
            for tune in tune_set.tunes:
                if tune.name not in seen_songs:
                    f.write(f"- {tune.name}\n")
                    seen_songs.add(tune.name)
    print(f"\n✓ Wrote {len(seen_songs)} unique songs to {filename}")

def read_songs_from_file(filename="single-songs.md"):
    """Read song names from the markdown file"""
    import re
    songs = []
    if os.path.exists(filename):
        with open(filename, 'r') as f:
            content = f.read()
        
        # Remove HTML comments (<!-- ... -->)
        content = re.sub(r'<!--.*?-->', '', content, flags=re.DOTALL)
        
        lines = content.split('\n')
        
        for line in lines:
            line = line.strip()
            # Skip lines starting with # (comments)
            if line.startswith('#'):
                continue
            # Process lines starting with '-' (list items)
            if line.startswith('- '):
                songs.append(line[2:])
    return songs

def create_overload_playlist(songs, n_versions=3, auth_manager=None, client_id=None, client_secret=None, redirect_uri=None):
    """Create a playlist with N versions of each song"""
    import time
    
    # Create SpotifyOAuth if not provided
    if not auth_manager:
        auth_manager = SpotifyOAuth(
            client_id=client_id,
            client_secret=client_secret,
            redirect_uri=redirect_uri,
            scope="playlist-modify-public playlist-modify-private",
            cache_path=".spotify_cache",
            open_browser=False
        )
    
    # Create Spotify client
    sp = spotipy.Spotify(auth_manager=auth_manager)
    
    # Create playlist
    user_id = sp.current_user()['id']
    playlist_name = f"Irish Practice Overload - {time.strftime('%Y-%m-%d')}"
    playlist = sp.user_playlist_create(
        user_id,
        playlist_name,
        public=False,
        description=f"Multiple versions of Irish traditional tunes ({n_versions} versions each)"
    )
    
    print(f"\nCreated playlist: {playlist_name}")
    print(f"Playlist URL: {playlist['external_urls']['spotify']}")
    
    track_uris = []
    
    for song in songs:
        print(f"\nSearching for {n_versions} versions of: {song}")
        
        # Search for multiple versions
        search_queries = [
            f'"{song}" irish traditional',
            f'{song} irish traditional',
            f'{song} irish trad',
            f'{song} celtic',
            song
        ]
        
        found_versions = []
        seen_artists = set()
        
        for query in search_queries:
            if len(found_versions) >= n_versions:
                break
                
            results = sp.search(q=query, type='track', limit=50)
            
            for track in results['tracks']['items']:
                if len(found_versions) >= n_versions:
                    break
                    
                track_name = track['name'].lower()
                artist_name = track['artists'][0]['name'] if track['artists'] else "Unknown"
                
                # Check if this song name matches and we haven't used this artist yet
                if song.lower() in track_name and artist_name not in seen_artists:
                    found_versions.append(track)
                    seen_artists.add(artist_name)
                    track_uris.append(track['uri'])
                    print(f"  ✓ Found: {track['name']} by {artist_name}")
            
            time.sleep(0.1)  # Be nice to Spotify API
        
        if len(found_versions) < n_versions:
            print(f"  ⚠ Only found {len(found_versions)} versions of {song}")
    
    # Add tracks to playlist
    if track_uris:
        for i in range(0, len(track_uris), 100):
            batch = track_uris[i:i+100]
            sp.playlist_add_items(playlist['id'], batch)
        
        print(f"\n✓ Added {len(track_uris)} tracks to playlist")
    
    return playlist['external_urls']['spotify']

def main():
    parser = argparse.ArgumentParser(description='Create Spotify playlists for Irish traditional music')
    parser.add_argument('--overload', action='store_true', help='Create overload playlist from single-songs.md')
    parser.add_argument('--versions', type=int, default=3, help='Number of versions per song (default: 3)')
    parser.add_argument('--dry-run', action='store_true', help='Process songs without creating Spotify playlist')
    args = parser.parse_args()
    
    load_dotenv()
    
    CLIENT_ID = os.getenv('SPOTIFY_CLIENT_ID')
    CLIENT_SECRET = os.getenv('SPOTIFY_CLIENT_SECRET')
    REDIRECT_URI = "http://127.0.0.1:8888/callback"
    
    # In dry-run mode, skip authentication
    if args.dry_run:
        print("Running in dry-run mode (no Spotify playlist will be created)")
        token = True
        auth_manager = None
    else:
        # Create cache file path
        cache_path = ".spotify_cache"
        
        # Create auth manager
        auth_manager = SpotifyOAuth(
            client_id=CLIENT_ID,
            client_secret=CLIENT_SECRET,
            redirect_uri=REDIRECT_URI,
            scope="playlist-modify-public playlist-modify-private",
            cache_path=cache_path,
            open_browser=False  # We'll handle browser opening manually
        )
        
        # Get the auth URL
        auth_url = auth_manager.get_authorize_url()
        
        print("Opening Spotify authorization in your browser...")
        print(f"\nIf browser doesn't open, visit this URL:\n{auth_url}\n")
        
        webbrowser.open(auth_url)
        
        print("After authorizing, you'll be redirected to a URL that starts with:")
        print("http://127.0.0.1:8888/callback?code=...")
        print("\nYour browser will show an error page - this is normal!")
        print("Copy the ENTIRE URL from your browser's address bar.\n")
        
        response_url = input("Paste the URL here: ").strip()
        
        # Extract the code from the response URL
        code = auth_manager.parse_response_code(response_url)
        
        # Get the token
        token = auth_manager.get_access_token(code, as_dict=False)
    
    if token:
        if not args.dry_run:
            print("\n✓ Authentication successful!")
        
        if args.overload:
            # Create overload playlist from single-songs.md
            if not os.path.exists("single-songs.md"):
                print("Error: single-songs.md not found!")
                print("Please run the script without --overload first to generate single-songs.md")
                print("Example: python create_spotify_playlist.py")
                return
                
            songs = read_songs_from_file("single-songs.md")
            if not songs:
                print("No songs found in single-songs.md")
                return
                
            print(f"\nFound {len(songs)} songs in single-songs.md")
            
            if args.dry_run:
                print(f"\nDry-run mode: Would create playlist with {args.versions} versions of each song:")
                for i, song in enumerate(songs, 1):
                    print(f"  {i}. {song}")
                print(f"\nTotal tracks: ~{len(songs) * args.versions}")
            else:
                playlist_url = create_overload_playlist(songs, args.versions, auth_manager, CLIENT_ID, CLIENT_SECRET, REDIRECT_URI)
                
                print(f"\n✓ Done! Your overload playlist is ready:")
                print(f"  {playlist_url}")
        else:
            # Original functionality
            irish_manager = IrishPlaylistManager()
            spotify_creator = SpotifyPlaylistCreator(CLIENT_ID, CLIENT_SECRET, REDIRECT_URI)
            
            # Parse target sets
            target_sets = irish_manager.parse_target_file("target.md")
            
            if not target_sets:
                print("No target sets found in target.md")
                return
                
            # Find matching sets
            matching_sets = irish_manager.find_matching_sets(target_sets)
            
            print(f"\nFound {len(matching_sets)} matching sets to add to Spotify")
            
            # Write individual songs to file
            write_songs_to_file(matching_sets)
            
            if args.dry_run:
                print(f"\nDry-run mode: Would create playlist with {len(matching_sets)} sets:")
                for i, tune_set in enumerate(matching_sets, 1):
                    print(f"  {i}. {tune_set}")
                total_songs = sum(len(tune_set.tunes) for tune_set in matching_sets)
                print(f"\nTotal songs: {total_songs}")
            else:
                # Create playlist
                import time
                playlist_name = f"Irish Session Practice - {time.strftime('%Y-%m-%d')}"
                playlist_url = spotify_creator.create_playlist(playlist_name, matching_sets)
                
                print(f"\n✓ Done! Your playlist is ready:")
                print(f"  {playlist_url}")
    else:
        print("\n✗ Authentication failed. Please try again.")

if __name__ == "__main__":
    main()