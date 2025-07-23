#!/usr/bin/env python3
"""
MP3 Metadata Updater

Updates ID3 tags (metadata) in MP3 files to match their filenames.
"""

import os
import sys
from pathlib import Path
from mutagen.mp3 import MP3
from mutagen.id3 import ID3, TIT2, TPE1, TALB, APIC, ID3NoHeaderError

def update_mp3_metadata(file_path, new_title=None, new_artist=None, new_album=None):
    """
    Update MP3 metadata (ID3 tags).
    
    Args:
        file_path: Path to the MP3 file
        new_title: New title (if None, uses filename without extension)
        new_artist: New artist name
        new_album: New album name
    """
    try:
        # Load the MP3 file
        audio = MP3(file_path, ID3=ID3)
        
        # Add ID3 tag if it doesn't exist
        if audio.tags is None:
            audio.add_tags()
        
        # Update title
        if new_title is None:
            # Use filename without extension as title
            new_title = Path(file_path).stem
        
        audio.tags["TIT2"] = TIT2(encoding=3, text=new_title)
        
        # Update artist if provided
        if new_artist:
            audio.tags["TPE1"] = TPE1(encoding=3, text=new_artist)
        
        # Update album if provided
        if new_album:
            audio.tags["TALB"] = TALB(encoding=3, text=new_album)
        
        # Save the changes
        audio.save()
        
        return True, f"Updated: {Path(file_path).name} - Title: '{new_title}'"
    
    except Exception as e:
        return False, f"Error updating {file_path}: {str(e)}"

def update_mutiny_files():
    """Update all Mutiny on the Mary Jane files."""
    base_dir = "/Users/pk/Desktop/occupant8"
    
    # Define files to update
    files_to_update = [
        # Main files
        ("Mutiny on the Mary Jane.mp3", "Mutiny on the Mary Jane", "occupant8", "Mutiny on the Mary Jane"),
        ("Mutiny on the Mary Jane - v2.mp3", "Mutiny on the Mary Jane (v2)", "occupant8", "Mutiny on the Mary Jane"),
        
        # Stems folder
        ("Mutiny on the Mary Jane Stems/Mutiny on the Mary Jane (Bass).mp3", "Mutiny on the Mary Jane (Bass)", "occupant8", "Mutiny on the Mary Jane Stems"),
        ("Mutiny on the Mary Jane Stems/Mutiny on the Mary Jane (Drums).mp3", "Mutiny on the Mary Jane (Drums)", "occupant8", "Mutiny on the Mary Jane Stems"),
        ("Mutiny on the Mary Jane Stems/Mutiny on the Mary Jane (FX).mp3", "Mutiny on the Mary Jane (FX)", "occupant8", "Mutiny on the Mary Jane Stems"),
        ("Mutiny on the Mary Jane Stems/Mutiny on the Mary Jane (Guitar).mp3", "Mutiny on the Mary Jane (Guitar)", "occupant8", "Mutiny on the Mary Jane Stems"),
        ("Mutiny on the Mary Jane Stems/Mutiny on the Mary Jane (Synth).mp3", "Mutiny on the Mary Jane (Synth)", "occupant8", "Mutiny on the Mary Jane Stems"),
        
        # Stems v2 folder
        ("Mutiny on the Mary Jane Stems - v2/Mutiny on the Mary Jane (Bass).mp3", "Mutiny on the Mary Jane (Bass) v2", "occupant8", "Mutiny on the Mary Jane Stems v2"),
        ("Mutiny on the Mary Jane Stems - v2/Mutiny on the Mary Jane (Drums).mp3", "Mutiny on the Mary Jane (Drums) v2", "occupant8", "Mutiny on the Mary Jane Stems v2"),
        ("Mutiny on the Mary Jane Stems - v2/Mutiny on the Mary Jane (FX).mp3", "Mutiny on the Mary Jane (FX) v2", "occupant8", "Mutiny on the Mary Jane Stems v2"),
        ("Mutiny on the Mary Jane Stems - v2/Mutiny on the Mary Jane (Synth).mp3", "Mutiny on the Mary Jane (Synth) v2", "occupant8", "Mutiny on the Mary Jane Stems v2"),
    ]
    
    print("Updating MP3 metadata for Mutiny on the Mary Jane files...")
    print("=" * 60)
    
    success_count = 0
    for relative_path, title, artist, album in files_to_update:
        full_path = os.path.join(base_dir, relative_path)
        
        if os.path.exists(full_path):
            success, message = update_mp3_metadata(full_path, title, artist, album)
            print(message)
            if success:
                success_count += 1
        else:
            print(f"File not found: {relative_path}")
    
    print(f"\nSuccessfully updated {success_count}/{len(files_to_update)} files")

def update_single_file(file_path, title=None, artist=None, album=None):
    """Update a single MP3 file's metadata."""
    if not os.path.exists(file_path):
        print(f"Error: File not found - {file_path}")
        return
    
    success, message = update_mp3_metadata(file_path, title, artist, album)
    print(message)
    
    # Show current metadata
    try:
        audio = MP3(file_path, ID3=ID3)
        print("\nCurrent metadata:")
        print(f"  Title: {audio.tags.get('TIT2', 'None')}")
        print(f"  Artist: {audio.tags.get('TPE1', 'None')}")
        print(f"  Album: {audio.tags.get('TALB', 'None')}")
    except:
        pass

def main():
    """Main function."""
    if len(sys.argv) == 1:
        # No arguments - update all Mutiny files
        update_mutiny_files()
    
    elif len(sys.argv) == 2:
        # Single file path - update with filename as title
        update_single_file(sys.argv[1])
    
    elif len(sys.argv) >= 3:
        # File path + title (+ optional artist and album)
        file_path = sys.argv[1]
        title = sys.argv[2]
        artist = sys.argv[3] if len(sys.argv) > 3 else None
        album = sys.argv[4] if len(sys.argv) > 4 else None
        update_single_file(file_path, title, artist, album)
    
    else:
        print("Usage:")
        print("  python update_mp3_metadata.py                    # Update all Mutiny files")
        print("  python update_mp3_metadata.py <file>             # Update single file")
        print("  python update_mp3_metadata.py <file> <title> [artist] [album]")

if __name__ == '__main__':
    main()