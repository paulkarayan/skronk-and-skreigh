#!/usr/bin/env python3
"""
Fix metadata for Coil's Fancy files
"""

import os
from mutagen.mp3 import MP3
from mutagen.id3 import ID3, TIT2, TPE1, TALB

def update_metadata(file_path, title, artist="occupant8", album="Coil's Fancy"):
    """Update MP3 metadata."""
    try:
        audio = MP3(file_path, ID3=ID3)
        if audio.tags is None:
            audio.add_tags()
        
        audio.tags["TIT2"] = TIT2(encoding=3, text=title)
        audio.tags["TPE1"] = TPE1(encoding=3, text=artist)
        audio.tags["TALB"] = TALB(encoding=3, text=album)
        
        audio.save()
        print(f"✓ Updated: {os.path.basename(file_path)} -> Title: '{title}'")
        return True
    except Exception as e:
        print(f"✗ Error updating {file_path}: {e}")
        return False

def main():
    base_dir = "/Users/pk/Desktop/occupant8"
    
    # Define all files to update
    files_to_update = [
        ("Coil's Fancy.mp3", "Coil's Fancy", "Coil's Fancy"),
        ("Coil's Fancy - Stems/Coil's Fancy (Bass).mp3", "Coil's Fancy (Bass)", "Coil's Fancy - Stems"),
        ("Coil's Fancy - Stems/Coil's Fancy (Drums).mp3", "Coil's Fancy (Drums)", "Coil's Fancy - Stems"),
        ("Coil's Fancy - Stems/Coil's Fancy (FX).mp3", "Coil's Fancy (FX)", "Coil's Fancy - Stems"),
        ("Coil's Fancy - Stems/Coil's Fancy (Guitar).mp3", "Coil's Fancy (Guitar)", "Coil's Fancy - Stems"),
        ("Coil's Fancy - Stems/Coil's Fancy (Synth).mp3", "Coil's Fancy (Synth)", "Coil's Fancy - Stems"),
    ]
    
    print("Fixing metadata for Coil's Fancy files...")
    print("=" * 50)
    
    success_count = 0
    for relative_path, title, album in files_to_update:
        full_path = os.path.join(base_dir, relative_path)
        if os.path.exists(full_path):
            if update_metadata(full_path, title, album=album):
                success_count += 1
        else:
            print(f"✗ File not found: {relative_path}")
    
    print(f"\nSuccessfully updated {success_count}/{len(files_to_update)} files")
    
    # Show current metadata for verification
    print("\nVerifying metadata:")
    print("-" * 50)
    for relative_path, _, _ in files_to_update[:2]:  # Show first 2 files
        full_path = os.path.join(base_dir, relative_path)
        if os.path.exists(full_path):
            try:
                audio = MP3(full_path, ID3=ID3)
                print(f"\n{os.path.basename(full_path)}:")
                print(f"  Title: {audio.tags.get('TIT2', 'None')}")
                print(f"  Artist: {audio.tags.get('TPE1', 'None')}")
                print(f"  Album: {audio.tags.get('TALB', 'None')}")
            except:
                pass

if __name__ == "__main__":
    main()