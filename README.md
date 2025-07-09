# Irish Session Playlist Manager

A Python tool for creating practice playlists of Irish traditional music sets from various sources (Spotify, YouTube, local audio files).

## Overview

Irish traditional music is often played in "sets" - groups of 2-4 tunes played consecutively. This tool helps musicians:
1. Extract specific sets they want to learn from longer recordings
2. Create focused practice playlists containing only the sets they need
3. Maintain the traditional set groupings when practicing

## How It Works

1. **Source Material**: The tool reads `foinn1-sets.md` which contains timestamps and tune names from a comprehensive YouTube video/audio file
2. **Target Selection**: You specify which sets to learn in `target.md`
3. **Output Generation**:
   - For Spotify: Generates a text file with the exact order of tunes to add to your playlist
   - For Audio Files: Extracts the specific time segments and combines them into a single practice file

## Usage

### quick start for pk
<add your stuff to target.md>
source .venv/bin/activate
python create_spotify_playlist.py

python create_spotify_playlist.py --dry-run
python create_spotify_playlist.py --overload --versions 3


### Basic Setup

1. Edit `target.md` to list the sets you want to learn:
```
Jim Ward's Jig / Blarney Pilgrim / The Cook in the Kitchen
Jerry's Beaver Hat (Returned Yank) / Kesh / Rambling Pitchfolk
Out on the Ocean / The Connaughtman's Rambles / Geese in the Bog
```

2. Run the main script:
```bash
python irish_playlist_manager.py
```

This generates `spotify_playlist_order.txt` with the tunes in order.

### Audio Extraction

When you have the MP3 file from the YouTube video:

```bash
python extract_audio.py foinn1_audio.mp3
```

This will:
- Create `extracted_sets/` directory with individual set recordings
- Generate `my_practice_sets.mp3` combining all your target sets

### Example Output

For the target sets above, the tool will:
1. Find "Jig set 5" starting at 1:31:36
2. Find "Jig set 3" starting at 1:23:34
3. Extract these segments and combine them in order

## File Structure

- `foinn1-sets.md` - Source file with all available sets and timestamps
- `target.md` - Your list of sets to learn
- `irish_playlist_manager.py` - Main script
- `extract_audio.py` - Audio extraction utility
- `spotify_playlist_order.txt` - Generated Spotify playlist order

## Requirements

- Python 3.7+
- ffmpeg (for audio extraction)
- spotipy and python-dotenv (for Spotify integration)

```bash
# Install ffmpeg
# macOS: brew install ffmpeg
# Ubuntu: sudo apt install ffmpeg

# Install Python dependencies
uv venv
source .venv/bin/activate
uv pip install spotipy python-dotenv
```

## Spotify Integration

### Setup

1. **Create Spotify App**: 
   - Go to https://developer.spotify.com/dashboard
   - Create a new app
   - In app settings, add this exact redirect URI: `http://127.0.0.1:8888/callback`
   - Save your Client ID and Client Secret

2. **Configure Credentials**:
   Create a `.env` file with:
   ```
   SPOTIFY_CLIENT_ID=your_client_id_here
   SPOTIFY_CLIENT_SECRET=your_client_secret_here
   ```

3. **Install Dependencies**:
   ```bash
   source .venv/bin/activate
   uv pip install spotipy python-dotenv
   ```

4. **Run Spotify Integration**:
   ```bash
   source .venv/bin/activate
   python create_spotify_playlist.py
   ```

   - Your browser will open for Spotify login
   - After login, you'll see an error page saying "This site can't be reached" - **this is normal!**
   - Look at the URL in your browser's address bar - it will contain `?code=...`
   - Copy the ENTIRE URL (including http://127.0.0.1:8888/callback?code=...)
   - Paste it when the script prompts you
   - The playlist will be created automatically

## On tempo adjustment

Tempo adjustment for practice (Note: Spotify doesn't have built-in tempo control. You can either download MP3s of the songs or use the [Spotify Playback Speed Chrome extension](https://chromewebstore.google.com/detail/spotify-playback-speed/bgehnoihoklmofgehcefiaicdcdgppck) for the web player)


## what i use

python extract_audio.py "Fionn Seisiun Book 1 - hatao.mp3"