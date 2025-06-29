import os
import spotipy
from spotipy.oauth2 import SpotifyOAuth
from irish_playlist_manager import IrishPlaylistManager
import time
from dotenv import load_dotenv

class SpotifyPlaylistCreator:
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
        
    def search_tune(self, tune_name):
        """Search for a tune on Spotify"""
        # Try different search strategies
        searches = [
            f'"{tune_name}" irish traditional',
            f'{tune_name} irish traditional',
            f'{tune_name} irish',
            tune_name
        ]
        
        for search_query in searches:
            results = self.sp.search(q=search_query, type='track', limit=10)
            
            if results['tracks']['items']:
                # Look for traditional/irish music in results
                for track in results['tracks']['items']:
                    # Check if it's likely traditional Irish music
                    track_name = track['name'].lower()
                    artist_name = track['artists'][0]['name'].lower() if track['artists'] else ""
                    
                    # Prioritize tracks that mention the tune name
                    if tune_name.lower() in track_name:
                        return track['uri']
                
                # If no exact match, return first result
                return results['tracks']['items'][0]['uri']
                
        return None
    
    def create_playlist(self, playlist_name, matching_sets):
        """Create a Spotify playlist from the matching sets"""
        # Get current user ID
        user_id = self.sp.current_user()['id']
        
        # Create playlist
        playlist = self.sp.user_playlist_create(
            user_id, 
            playlist_name,
            public=False,
            description="Irish traditional music sets for practice"
        )
        
        print(f"\nCreated playlist: {playlist_name}")
        print(f"Playlist URL: {playlist['external_urls']['spotify']}")
        
        # Search and add tracks
        track_uris = []
        not_found = []
        
        for i, tune_set in enumerate(matching_sets, 1):
            print(f"\nProcessing {tune_set}...")
            
            for tune in tune_set.tunes:
                print(f"  Searching for: {tune.name}")
                uri = self.search_tune(tune.name)
                
                if uri:
                    track_uris.append(uri)
                    track_info = self.sp.track(uri)
                    print(f"    ✓ Found: {track_info['name']} by {track_info['artists'][0]['name']}")
                else:
                    not_found.append(f"{tune_set.set_type} set {tune_set.set_number}: {tune.name}")
                    print(f"    ✗ Not found: {tune.name}")
                
                time.sleep(0.1)  # Be nice to Spotify API
        
        # Add tracks to playlist in batches
        if track_uris:
            for i in range(0, len(track_uris), 100):
                batch = track_uris[i:i+100]
                self.sp.playlist_add_items(playlist['id'], batch)
            
            print(f"\nAdded {len(track_uris)} tracks to playlist")
        
        if not_found:
            print(f"\nCould not find {len(not_found)} tunes:")
            for tune in not_found:
                print(f"  - {tune}")
                
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
    
    # Initialize managers
    irish_manager = IrishPlaylistManager()
    spotify_creator = SpotifyPlaylistCreator(CLIENT_ID, CLIENT_SECRET)
    
    # Parse target sets
    target_sets = irish_manager.parse_target_file("target.md")
    
    if not target_sets:
        print("No target sets found in target.md")
        return
        
    # Find matching sets
    matching_sets = irish_manager.find_matching_sets(target_sets)
    
    print(f"Found {len(matching_sets)} matching sets to add to Spotify")
    
    # Create playlist
    playlist_name = f"Irish Session Practice - {time.strftime('%Y-%m-%d')}"
    playlist_url = spotify_creator.create_playlist(playlist_name, matching_sets)
    
    print(f"\n✓ Done! Your playlist is ready:")
    print(f"  {playlist_url}")

if __name__ == "__main__":
    main()