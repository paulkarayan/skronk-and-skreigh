#!/usr/bin/env python3
"""
Filter out Unknown Artist/Unknown Album entries from a playlist.
"""

import sys
from pathlib import Path


def filter_playlist(input_file: str, output_file: str = None):
    """
    Remove Unknown Artist/Unknown Album entries from playlist.
    """
    if output_file is None:
        output_file = input_file.replace('.m3u', '_filtered.m3u')
    
    with open(input_file, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    
    filtered_lines = []
    i = 0
    removed_count = 0
    
    while i < len(lines):
        line = lines[i].strip()
        
        # Check if this is an #EXTINF line
        if line.startswith('#EXTINF'):
            # Look at the next line (should be the file path)
            if i + 1 < len(lines):
                path_line = lines[i + 1].strip()
                
                # Check if it's from Unknown Artist/Unknown Album
                if '/Unknown Artist/Unknown Album/' in path_line:
                    # Skip both the #EXTINF and the path line
                    removed_count += 1
                    i += 2
                    continue
                else:
                    # Keep both lines
                    filtered_lines.append(lines[i])
                    filtered_lines.append(lines[i + 1])
                    i += 2
            else:
                # Keep the line if there's no next line
                filtered_lines.append(lines[i])
                i += 1
        else:
            # Keep all other lines (headers, etc.)
            filtered_lines.append(lines[i])
            i += 1
    
    # Write filtered playlist
    with open(output_file, 'w', encoding='utf-8') as f:
        f.writelines(filtered_lines)
    
    print(f"Filtered playlist created: {output_file}")
    print(f"Removed {removed_count} Unknown Artist/Unknown Album entries")
    
    return output_file


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python filter_playlist.py <input.m3u> [output.m3u]")
        sys.exit(1)
    
    input_file = sys.argv[1]
    output_file = sys.argv[2] if len(sys.argv) > 2 else None
    
    filter_playlist(input_file, output_file)