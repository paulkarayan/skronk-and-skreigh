#!/usr/bin/env python3
"""
Remove files from Unknown Artist/Unknown Album directories - CONFIRMED VERSION
"""

import os
import sys
from pathlib import Path


# List of files from the previous output
files_to_remove = [
    "/Users/pk/Dropbox/Dreadlap/Music/Unknown Artist/Unknown Album/boys of the town.mp3",
    "/Users/pk/Dropbox/Dreadlap/Music/Unknown Artist/Unknown Album/eddie kellys.mp3",
    "/Users/pk/Dropbox/Dreadlap/Music/Unknown Artist/Unknown Album/maid in the meadow.mp3",
    "/Users/pk/Dropbox/Dreadlap/Music/Unknown Artist/Unknown Album/ah surely.mp3",
    "/Users/pk/Dropbox/Dreadlap/Music/Unknown Artist/Unknown Album/musical priest.mp3",
    "/Users/pk/Dropbox/Dreadlap/Music/Unknown Artist/Unknown Album/jackie colemans.mp3",
    "/Users/pk/Dropbox/Dreadlap/Music/Unknown Artist/Unknown Album/last nights fun.mp3",
    "/Users/pk/Dropbox/Dreadlap/Unknown Artist/Unknown Album/15 Reels- Pinch Of Snuff, Last Nights Fun, Abbey Reel.wav",
    "/Users/pk/Dropbox/Dreadlap/Music/Unknown Artist/Unknown Album/my love is fair and handsome.mp3",
    "/Users/pk/Dropbox/Dreadlap/Music/Unknown Artist/Unknown Album/Boys of Ballycastle.mp3",
    "/Users/pk/Dropbox/Dreadlap/Music/Unknown Artist/Unknown Album/Stack of Wheat.mp3",
    "/Users/pk/Dropbox/Dreadlap/Music/Unknown Artist/Unknown Album/Patrick Doherty_s Barndance.mp3",
    "/Users/pk/Dropbox/Dreadlap/Music/Unknown Artist/Unknown Album/chaffpool post.mp3",
    "/Users/pk/Dropbox/Dreadlap/Music/Unknown Artist/Unknown Album/callopie house.mp3",
    "/Users/pk/Dropbox/Dreadlap/Music/Unknown Artist/Unknown Album/eavesdropper.mp3",
    "/Users/pk/Dropbox/Dreadlap/Music/Unknown Artist/Unknown Album/an paistin fionn.mp3",
    "/Users/pk/Dropbox/Dreadlap/Music/Unknown Artist/Unknown Album/marias waltz.mp3",
    "/Users/pk/Dropbox/Dreadlap/Music/Unknown Artist/Unknown Album/Marino Waltz.mp3",
    "/Users/pk/Dropbox/Dreadlap/Music/Unknown Artist/Unknown Album/Banshee.mp3"
]

print(f"Removing {len(files_to_remove)} Unknown Artist/Unknown Album files...")
print("-" * 60)

removed_count = 0
failed_count = 0

for file_path in files_to_remove:
    try:
        if os.path.exists(file_path):
            os.remove(file_path)
            removed_count += 1
            print(f"✓ Removed: {os.path.basename(file_path)}")
        else:
            print(f"⚠ Skipped (not found): {os.path.basename(file_path)}")
    except Exception as e:
        failed_count += 1
        print(f"✗ Failed to remove {os.path.basename(file_path)}: {e}")

print("-" * 60)
print(f"\nRemoved {removed_count} files ({57.7:.1f} MB freed)")
if failed_count > 0:
    print(f"Failed to remove {failed_count} files")