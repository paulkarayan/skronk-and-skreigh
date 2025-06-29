#!/usr/bin/env python3
"""
Simple Spotify playlist creator with manual auth URL handling
"""

import os
import sys
import webbrowser
from dotenv import load_dotenv
import spotipy
from spotipy.oauth2 import SpotifyOAuth
from irish_playlist_manager import IrishPlaylistManager
from spotify_integration import SpotifyPlaylistCreator

def main():
    load_dotenv()
    
    CLIENT_ID = os.getenv('SPOTIFY_CLIENT_ID')
    CLIENT_SECRET = os.getenv('SPOTIFY_CLIENT_SECRET')
    REDIRECT_URI = "http://127.0.0.1:8888/callback"
    
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
        print("\n✓ Authentication successful!")
        
        # Now run the playlist creation
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