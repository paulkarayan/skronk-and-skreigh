#!/usr/bin/env python3
"""
Find all instances of a single tune in local directories.
Can output as a list or generate a playlist.
"""

import argparse
import os
import sys
from pathlib import Path
from typing import List, Tuple, Optional
from datetime import datetime

from local_file_search import search_local_files
from vlc_playlist import create_m3u_playlist, create_xspf_playlist
from album_search import search_by_album_context, print_album_info
from tune_disambiguation import get_tune_types, format_tune_type_info
from type_aware_scoring import filter_by_type


def format_file_info(file_path: Path, score: float, verbose: bool = False) -> str:
    """Format file information for display."""
    if verbose:
        size = file_path.stat().st_size / (1024 * 1024)  # MB
        modified = datetime.fromtimestamp(file_path.stat().st_mtime).strftime('%Y-%m-%d')
        return f"{file_path} (score: {score:.2f}, size: {size:.1f}MB, modified: {modified})"
    else:
        # Show relative path if in current directory tree
        try:
            rel_path = file_path.relative_to(Path.cwd())
            return f"{rel_path} (score: {score:.2f})"
        except ValueError:
            return f"{file_path} (score: {score:.2f})"


def find_tune_instances(
    tune_name: str,
    directories: List[str],
    threshold: float = 0.8,
    use_aliases: bool = True,
    recursive: bool = True,
    verbose: bool = False,
    use_album_search: bool = True,
    overload: Optional[int] = None
) -> List[Tuple[Path, float, Optional[str]]]:
    """
    Find all instances of a tune in the specified directories.
    Returns list of (path, score, reason) tuples.
    """
    # Get direct matches
    direct_matches = search_local_files(
        tune_name,
        directories,
        use_aliases=use_aliases,
        threshold=threshold,
        recursive=recursive,
        max_results=overload  # Use overload parameter
    )
    
    # Convert to include reason
    matches_with_reason = [(path, score, None) for path, score in direct_matches]
    
    # Add album-based matches if enabled
    if use_album_search:
        album_matches = search_by_album_context(
            tune_name,
            directories,
            threshold=threshold,
            use_aliases=use_aliases
        )
        
        # Merge with direct matches, avoiding duplicates
        existing_paths = {path for path, _, _ in matches_with_reason}
        for path, score, reason in album_matches:
            if path not in existing_paths:
                matches_with_reason.append((path, score, reason))
    
    # Sort by score
    matches_with_reason.sort(key=lambda x: x[1], reverse=True)
    
    return matches_with_reason


def main():
    parser = argparse.ArgumentParser(
        description="Find all instances of a single tune in your music collection"
    )
    parser.add_argument(
        "tune",
        help="Name of the tune to search for"
    )
    parser.add_argument(
        "directories",
        nargs="*",
        default=["."],
        help="Directories to search (default: current directory)"
    )
    parser.add_argument(
        "--playlist",
        choices=["m3u", "xspf"],
        help="Create a playlist file with all matches"
    )
    parser.add_argument(
        "--output", "-o",
        help="Output filename for playlist (default: tune_name.m3u/xspf)"
    )
    parser.add_argument(
        "--threshold", "-t",
        type=float,
        default=0.8,
        help="Minimum match score 0-1 (default: 0.8)"
    )
    parser.add_argument(
        "--no-aliases",
        action="store_true",
        help="Don't use TheSession aliases"
    )
    parser.add_argument(
        "--no-recursive",
        action="store_true",
        help="Don't search subdirectories"
    )
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Show additional file information"
    )
    parser.add_argument(
        "--absolute-paths",
        action="store_true",
        help="Use absolute paths in playlist"
    )
    parser.add_argument(
        "--show-albums",
        action="store_true",
        help="Show which albums contain this tune"
    )
    parser.add_argument(
        "--no-album-search",
        action="store_true",
        help="Don't search for files based on album context"
    )
    parser.add_argument(
        "--type",
        help="Specify tune type (e.g., reel, jig, slip jig) for disambiguation"
    )
    parser.add_argument(
        "--overload",
        type=int,
        help="Find up to N versions of the tune"
    )
    
    args = parser.parse_args()
    
    # Expand directory paths
    directories = [os.path.expanduser(d) for d in args.directories]
    
    # Show albums if requested
    if args.show_albums:
        print_album_info(args.tune)
        print()
    
    # Check for tune type ambiguity
    tune_types = get_tune_types(args.tune)
    if len(tune_types) > 1:
        print(f"\nWARNING: Multiple tune types found for '{args.tune}':")
        for tune_info in tune_types:
            print(f"  - {format_tune_type_info(tune_info)}")
        
        if args.type:
            print(f"\nFiltering for type: {args.type}")
        else:
            print("\nSearching for all types. Use --type to specify a particular type.")
            print("Results will be scored higher if type keywords appear in the filename.\n")
    
    # Find all instances
    print(f"Searching for: {args.tune}")
    if not args.no_aliases:
        from thesession_data import get_tune_aliases
        aliases = get_tune_aliases(args.tune)
        if len(aliases) > 1:
            print(f"Also searching for aliases: {', '.join(aliases[1:])}")
    
    print(f"Searching in: {', '.join(directories)}")
    print("-" * 60)
    
    matches = find_tune_instances(
        args.tune,
        directories,
        threshold=args.threshold,
        use_aliases=not args.no_aliases,
        recursive=not args.no_recursive,
        verbose=args.verbose,
        use_album_search=not args.no_album_search,
        overload=args.overload
    )
    
    if not matches:
        print("No matches found.")
        sys.exit(1)
    
    # Apply type-aware scoring if there are multiple tune types
    if len(tune_types) > 1:
        matches = filter_by_type(matches, tune_types, args.type)
    
    # Display results
    print(f"\nFound {len(matches)} match{'es' if len(matches) != 1 else ''}:\n")
    for file_path, score, reason in matches:
        info = format_file_info(file_path, score, args.verbose)
        if reason:
            print(f"  {info} [{reason}]")
        else:
            print(f"  {info}")
    
    # Create playlist if requested
    if args.playlist:
        # Generate output filename if not provided
        if args.output:
            output_file = args.output
        else:
            safe_name = args.tune.replace('/', '_').replace('\\', '_')
            output_file = f"{safe_name}.{args.playlist}"
        
        # Get just the file paths
        file_paths = [match[0] for match in matches]
        
        # Create playlist
        if args.playlist == "m3u":
            playlist_path = create_m3u_playlist(
                file_paths,
                output_file,
                playlist_name=args.tune,
                use_absolute_paths=args.absolute_paths
            )
        else:  # xspf
            playlist_path = create_xspf_playlist(
                file_paths,
                output_file,
                playlist_title=args.tune,
                use_absolute_paths=args.absolute_paths
            )
        
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


if __name__ == "__main__":
    main()