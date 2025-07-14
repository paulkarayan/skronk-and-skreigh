#!/usr/bin/env python3
"""
Remove files from Unknown Artist/Unknown Album directories listed in a playlist.
WITH CONFIRMATION - shows files before deleting.
"""

import os
import sys
from pathlib import Path


def get_unknown_files_from_playlist(playlist_file: str) -> list:
    """
    Extract Unknown Artist/Unknown Album file paths from playlist.
    """
    unknown_files = []
    
    with open(playlist_file, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    
    for i, line in enumerate(lines):
        line = line.strip()
        if line and not line.startswith('#') and '/Unknown Artist/Unknown Album/' in line:
            unknown_files.append(line)
    
    return unknown_files


def remove_files_with_confirmation(files_to_remove: list):
    """
    Remove files after showing them and getting confirmation.
    """
    if not files_to_remove:
        print("No Unknown Artist/Unknown Album files found.")
        return
    
    print(f"\nFound {len(files_to_remove)} files to remove:")
    print("-" * 60)
    
    for file_path in files_to_remove:
        if os.path.exists(file_path):
            size_mb = os.path.getsize(file_path) / (1024 * 1024)
            print(f"{file_path} ({size_mb:.1f} MB)")
        else:
            print(f"{file_path} (NOT FOUND)")
    
    print("-" * 60)
    
    # Calculate total size
    total_size = 0
    for file_path in files_to_remove:
        if os.path.exists(file_path):
            total_size += os.path.getsize(file_path)
    
    total_size_mb = total_size / (1024 * 1024)
    print(f"\nTotal size: {total_size_mb:.1f} MB")
    
    # Ask for confirmation
    response = input("\nAre you SURE you want to permanently delete these files? (yes/no): ")
    
    if response.lower() == 'yes':
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
        
        print(f"\nRemoved {removed_count} files")
        if failed_count > 0:
            print(f"Failed to remove {failed_count} files")
    else:
        print("\nCancelled. No files were removed.")


def main():
    if len(sys.argv) < 2:
        print("Usage: python remove_unknown_files.py <playlist.m3u>")
        print("\nThis will remove all files in Unknown Artist/Unknown Album directories")
        print("referenced in the playlist. BE CAREFUL - this permanently deletes files!")
        sys.exit(1)
    
    playlist_file = sys.argv[1]
    
    if not os.path.exists(playlist_file):
        print(f"Error: Playlist file '{playlist_file}' not found")
        sys.exit(1)
    
    # Get list of files to remove
    unknown_files = get_unknown_files_from_playlist(playlist_file)
    
    # Remove with confirmation
    remove_files_with_confirmation(unknown_files)


if __name__ == "__main__":
    main()