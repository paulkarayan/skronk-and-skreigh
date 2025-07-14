#!/usr/bin/env python3
"""
Create a local file playlist from target.md
"""

import argparse
import sys
from pathlib import Path
from irish_playlist_manager import IrishPlaylistManager
from local_file_search import find_tunes_for_set
from vlc_playlist import create_playlist_from_sets
from album_search import print_album_info
from tune_disambiguation import get_tune_types, format_tune_type_info


def main():
    parser = argparse.ArgumentParser(
        description="Create a local file playlist from target.md"
    )
    parser.add_argument(
        "directories",
        nargs="+",
        help="Directories to search for music files"
    )
    parser.add_argument(
        "--target",
        default="target.md",
        help="Target file with sets to include (default: target.md)"
    )
    parser.add_argument(
        "--source",
        default="foinn1-sets.md",
        help="Source file with all sets (default: foinn1-sets.md)"
    )
    parser.add_argument(
        "--playlist",
        choices=["m3u", "xspf"],
        default="m3u",
        help="Playlist format (default: m3u)"
    )
    parser.add_argument(
        "--output", "-o",
        help="Output filename (default: irish_tunes.m3u/xspf)"
    )
    parser.add_argument(
        "--show-albums",
        action="store_true",
        help="Show which albums contain each tune"
    )
    parser.add_argument(
        "--show-types",
        action="store_true",
        help="Show tune type information"
    )
    parser.add_argument(
        "--overload",
        type=int,
        help="Find up to N versions of each tune"
    )
    parser.add_argument(
        "--threshold",
        type=float,
        default=0.85,
        help="Minimum match score (default: 0.85)"
    )
    
    args = parser.parse_args()
    
    # Initialize playlist manager
    manager = IrishPlaylistManager(args.source)
    
    # Read target file
    print(f"Reading target file: {args.target}")
    target_tune_lists = manager.parse_target_file(args.target)
    
    if not target_tune_lists:
        print("No sets found in target file")
        sys.exit(1)
    
    print(f"Found {len(target_tune_lists)} sets in target file")
    
    # Find matching sets from source
    matched_tune_sets = manager.find_matching_sets(target_tune_lists)
    
    # Get all unique tunes from matched sets
    all_tunes = set()
    matched_sets = []
    
    for tune_set in matched_tune_sets:
        matched_sets.append({
            'set_name': str(tune_set),
            'tunes': tune_set.get_tune_names()
        })
        all_tunes.update(tune_set.get_tune_names())
    
    print(f"\nMatched {len(matched_sets)} sets containing {len(all_tunes)} unique tunes")
    
    # Show album and type info if requested
    if args.show_albums or args.show_types:
        print("\n" + "="*60)
        for tune in sorted(all_tunes):
            print(f"\n{tune}:")
            
            if args.show_types:
                tune_types = get_tune_types(tune)
                if tune_types:
                    if len(tune_types) > 1:
                        print("  Types:")
                        for tune_info in tune_types:
                            print(f"    - {format_tune_type_info(tune_info)}")
                    else:
                        print(f"  Type: {format_tune_type_info(tune_types[0])}")
            
            if args.show_albums:
                print_album_info(tune)
        
        print("\n" + "="*60)
    
    # Search for files
    print(f"\nSearching for audio files in: {', '.join(args.directories)}")
    
    file_results = find_tunes_for_set(
        list(all_tunes),
        args.directories,
        use_aliases=True,
        threshold=args.threshold,
        overload=args.overload
    )
    
    # Count found files
    total_found = sum(len(files) for files in file_results.values())
    print(f"\nFound {total_found} audio files for {len([t for t, f in file_results.items() if f])} tunes")
    
    # Show missing tunes
    missing = [tune for tune, files in file_results.items() if not files]
    if missing:
        print(f"\nMissing {len(missing)} tunes:")
        for tune in missing:
            print(f"  - {tune}")
    
    # Create playlist
    if args.output:
        output_file = args.output
    else:
        output_file = f"irish_tunes.{args.playlist}"
    
    playlist_path = create_playlist_from_sets(
        matched_sets,
        file_results,
        output_file,
        playlist_format=args.playlist
    )
    
    if playlist_path:
        print(f"\nPlaylist created: {playlist_path}")
        print("\nYou can open this with:")
        # Keep command on one line
        cmd = f'vlc "{playlist_path}"'
        print(cmd)
    else:
        print("\nNo playlist created (no files found)")
        
    # Add warning if no tunes were found at all
    if len(all_tunes) == 0:
        print("\n\033[93m" + "="*60)
        print("WARNING: You may have used the wrong script!")
        print("="*60)
        print("\nDifference between scripts:")
        print("- create_local_playlist.py: Requires tunes to match sets in foinn1-sets.md")
        print("- create_local_playlist_direct.py: Works directly with any tunes in target.md")
        print("\nTry using: python create_local_playlist_direct.py " + " ".join(args.directories))
        print("\033[0m")  # Reset color


if __name__ == "__main__":
    main()