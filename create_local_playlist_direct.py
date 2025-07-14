#!/usr/bin/env python3
"""
Create a local file playlist directly from target.md without requiring source file matches
"""

import argparse
import sys
from pathlib import Path
from local_file_search import find_tunes_for_set
from vlc_playlist import create_playlist_from_sets
from album_search import print_album_info
from tune_disambiguation import get_tune_types, format_tune_type_info


def read_target_file_direct(target_file: str):
    """Read target.md directly to get tune sets"""
    sets = []
    
    with open(target_file, 'r') as f:
        lines = f.readlines()
    
    for line in lines:
        line = line.strip()
        # Skip empty lines and comments
        if line and not line.startswith('#'):
            # Split by ' / ' to get individual tunes
            tunes = [tune.strip() for tune in line.split(' / ')]
            if tunes:
                sets.append({
                    'set_name': ' / '.join(tunes),
                    'tunes': tunes
                })
    
    return sets


def main():
    parser = argparse.ArgumentParser(
        description="Create a local file playlist directly from target.md"
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
        default=0.8,
        help="Minimum match score (default: 0.8)"
    )
    parser.add_argument(
        "--async",
        action="store_true",
        dest="use_async",
        help="Use parallel/async search for better performance"
    )
    parser.add_argument(
        "--max-workers",
        type=int,
        help="Maximum number of parallel workers (default: CPU count)"
    )
    parser.add_argument(
        "--exclude-unknown",
        action="store_true",
        help="Exclude files from Unknown Artist/Unknown Album directories"
    )
    
    args = parser.parse_args()
    
    # Read target file directly
    print(f"Reading target file: {args.target}")
    matched_sets = read_target_file_direct(args.target)
    
    if not matched_sets:
        print("No sets found in target file")
        sys.exit(1)
    
    # Get all unique tunes
    all_tunes = set()
    for set_data in matched_sets:
        all_tunes.update(set_data['tunes'])
    
    print(f"Found {len(matched_sets)} sets containing {len(all_tunes)} unique tunes")
    
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
    
    if args.use_async:
        from local_file_search_async import find_tunes_for_set_optimized
        file_results = find_tunes_for_set_optimized(
            list(all_tunes),
            args.directories,
            use_aliases=True,
            threshold=args.threshold,
            overload=args.overload,
            use_async=True,
            max_workers=args.max_workers
        )
    else:
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
        
        # Verify no duplicates
        from vlc_playlist import verify_playlist_no_duplicates
        total, unique, duplicates = verify_playlist_no_duplicates(playlist_path)
        
        if duplicates:
            print(f"\n⚠️  WARNING: Playlist contains {len(duplicates)} duplicate files!")
            print("Duplicates found:")
            for dup in duplicates[:5]:  # Show first 5
                print(f"  - {dup}")
            if len(duplicates) > 5:
                print(f"  ... and {len(duplicates) - 5} more")
        else:
            print(f"✓ Verified: {total} unique files in playlist")
        
        print("\nYou can open this with:")
        # Keep command on one line
        cmd = f'vlc "{playlist_path}"'
        print(cmd)
    else:
        print("\nNo playlist created (no files found)")


if __name__ == "__main__":
    main()