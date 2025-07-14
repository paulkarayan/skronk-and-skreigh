#!/usr/bin/env python3
"""
Interactive duplicate removal tool for playlists.
Shows files with the same name but different paths and lets user choose which to keep.
"""

import os
import sys
from pathlib import Path
from collections import defaultdict


def get_files_from_playlist(playlist_file: str) -> list:
    """
    Extract file paths and their corresponding info from playlist.
    Returns list of tuples: (line_number, extinf_line, file_path)
    """
    files = []
    
    with open(playlist_file, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    
    i = 0
    while i < len(lines):
        line = lines[i].strip()
        
        # Check if this is an #EXTINF line
        if line.startswith('#EXTINF'):
            # Look at the next line (should be the file path)
            if i + 1 < len(lines):
                path_line = lines[i + 1].strip()
                if path_line and not path_line.startswith('#'):
                    files.append((i, lines[i], path_line))
                    i += 2
                    continue
        i += 1
    
    return files


def group_by_filename(file_entries: list) -> dict:
    """
    Group file entries by their basename.
    Returns dict mapping basename -> list of (line_num, extinf, full_path)
    """
    groups = defaultdict(list)
    
    for line_num, extinf, file_path in file_entries:
        basename = os.path.basename(file_path)
        groups[basename].append((line_num, extinf, file_path))
    
    return groups


def show_duplicate_group(basename: str, entries: list) -> list:
    """
    Show a group of duplicates and let user choose which to keep.
    Returns list of entries to keep.
    """
    print(f"\n{'='*80}")
    print(f"Found {len(entries)} copies of: {basename}")
    print(f"{'='*80}")
    
    # Show all options
    for i, (line_num, extinf, file_path) in enumerate(entries):
        print(f"\n[{i+1}] {file_path}")
        
        # Show file info if it exists
        if os.path.exists(file_path):
            size = os.path.getsize(file_path) / (1024 * 1024)
            mtime = os.path.getmtime(file_path)
            from datetime import datetime
            mod_date = datetime.fromtimestamp(mtime).strftime('%Y-%m-%d %H:%M')
            print(f"    Size: {size:.1f} MB, Modified: {mod_date}")
        else:
            print(f"    FILE NOT FOUND")
    
    # Ask user what to do
    print(f"\nOptions:")
    print(f"  1-{len(entries)}: Keep only that file")
    print(f"  a: Keep all files")
    print(f"  n: Remove all files")
    print(f"  q: Quit without saving")
    
    while True:
        choice = input("\nYour choice: ").strip().lower()
        
        if choice == 'q':
            return None  # Signal to quit
        elif choice == 'a':
            return entries  # Keep all
        elif choice == 'n':
            return []  # Remove all
        elif choice.isdigit():
            num = int(choice)
            if 1 <= num <= len(entries):
                return [entries[num-1]]  # Keep only selected
        
        print("Invalid choice. Please try again.")


def create_filtered_playlist(original_file: str, entries_to_keep: set, output_file: str = None):
    """
    Create a new playlist with only the entries to keep.
    """
    if output_file is None:
        base = os.path.splitext(original_file)[0]
        output_file = f"{base}_deduped.m3u"
    
    with open(original_file, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    
    # Build set of line numbers to keep
    lines_to_keep = set()
    for line_num, _, _ in entries_to_keep:
        lines_to_keep.add(line_num)      # EXTINF line
        lines_to_keep.add(line_num + 1)  # File path line
    
    # Write filtered playlist
    with open(output_file, 'w', encoding='utf-8') as f:
        i = 0
        while i < len(lines):
            if lines[i].strip().startswith('#EXTINF'):
                # This is a track entry
                if i in lines_to_keep:
                    f.write(lines[i])
                    if i + 1 < len(lines):
                        f.write(lines[i + 1])
                    i += 2
                else:
                    # Skip this entry
                    i += 2
            else:
                # Keep all other lines (headers, comments, etc.)
                f.write(lines[i])
                i += 1
    
    return output_file


def main():
    if len(sys.argv) < 2:
        print("Usage: python interactive_dupe_remover.py <playlist.m3u> [output.m3u]")
        print("\nThis tool will interactively help you remove duplicate files")
        print("(files with the same name but different paths) from your playlist.")
        sys.exit(1)
    
    playlist_file = sys.argv[1]
    output_file = sys.argv[2] if len(sys.argv) > 2 else None
    
    if not os.path.exists(playlist_file):
        print(f"Error: Playlist file '{playlist_file}' not found")
        sys.exit(1)
    
    # Extract files from playlist
    print(f"Reading playlist: {playlist_file}")
    file_entries = get_files_from_playlist(playlist_file)
    print(f"Found {len(file_entries)} tracks")
    
    # Group by filename
    groups = group_by_filename(file_entries)
    
    # Find actual duplicates (same filename, different paths)
    duplicates = {}
    for basename, entries in groups.items():
        if len(entries) > 1:
            # Check if paths are actually different
            paths = set(entry[2] for entry in entries)
            if len(paths) > 1:
                duplicates[basename] = entries
    
    if not duplicates:
        print("\nNo duplicate filenames found in playlist!")
        return
    
    print(f"\nFound {len(duplicates)} filenames with multiple paths")
    print("Let's go through them one by one...\n")
    
    # Process each duplicate group
    entries_to_keep = []
    
    for basename in sorted(duplicates.keys()):
        entries = duplicates[basename]
        
        # Let user choose what to keep
        result = show_duplicate_group(basename, entries)
        
        if result is None:  # User chose to quit
            print("\nQuitting without saving changes.")
            return
        
        entries_to_keep.extend(result)
    
    # Also keep all non-duplicate entries
    for basename, entries in groups.items():
        if basename not in duplicates:
            entries_to_keep.extend(entries)
    
    # Create new playlist
    print(f"\nCreating filtered playlist...")
    output_path = create_filtered_playlist(playlist_file, set(entries_to_keep), output_file)
    
    print(f"\nDone! Created: {output_path}")
    print(f"Original tracks: {len(file_entries)}")
    print(f"Remaining tracks: {len(entries_to_keep)}")
    print(f"Removed: {len(file_entries) - len(entries_to_keep)}")


if __name__ == "__main__":
    main()