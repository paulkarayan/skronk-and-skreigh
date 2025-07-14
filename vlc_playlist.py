#!/usr/bin/env python3
"""
VLC playlist generation utilities.
Supports M3U and XSPF formats.
"""

import os
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import List, Optional
from urllib.parse import quote


def create_m3u_playlist(
    file_paths: List[Path],
    output_file: str,
    playlist_name: Optional[str] = None,
    use_absolute_paths: bool = True
) -> Path:
    """
    Create an M3U playlist file.
    
    Args:
        file_paths: List of audio file paths
        output_file: Output playlist filename
        playlist_name: Optional playlist name
        use_absolute_paths: Use absolute paths (True) or relative paths (False)
    
    Returns:
        Path to the created playlist file
    """
    output_path = Path(output_file)
    
    with open(output_path, 'w', encoding='utf-8') as f:
        # Write M3U header
        f.write("#EXTM3U\n")
        
        if playlist_name:
            f.write(f"#PLAYLIST:{playlist_name}\n")
        
        for file_path in file_paths:
            # Get file info
            if file_path.exists():
                # Write extended info (duration is -1 for unknown)
                filename = file_path.stem
                f.write(f"#EXTINF:-1,{filename}\n")
            
            # Write file path
            if use_absolute_paths:
                f.write(f"{file_path.absolute()}\n")
            else:
                # Try to make relative to playlist location
                try:
                    rel_path = file_path.relative_to(output_path.parent)
                    f.write(f"{rel_path}\n")
                except ValueError:
                    # Can't make relative, use absolute
                    f.write(f"{file_path.absolute()}\n")
    
    return output_path.absolute()


def create_xspf_playlist(
    file_paths: List[Path],
    output_file: str,
    playlist_title: Optional[str] = None,
    use_absolute_paths: bool = True
) -> Path:
    """
    Create an XSPF (XML Shareable Playlist Format) playlist file.
    
    Args:
        file_paths: List of audio file paths
        output_file: Output playlist filename
        playlist_title: Optional playlist title
        use_absolute_paths: Use absolute paths (True) or relative paths (False)
    
    Returns:
        Path to the created playlist file
    """
    output_path = Path(output_file)
    
    # Create root element
    playlist = ET.Element('playlist')
    playlist.set('version', '1')
    playlist.set('xmlns', 'http://xspf.org/ns/0/')
    
    # Add title if provided
    if playlist_title:
        title = ET.SubElement(playlist, 'title')
        title.text = playlist_title
    
    # Create trackList
    track_list = ET.SubElement(playlist, 'trackList')
    
    for file_path in file_paths:
        track = ET.SubElement(track_list, 'track')
        
        # Add location (file URI)
        location = ET.SubElement(track, 'location')
        
        if use_absolute_paths:
            # Convert to file URI
            abs_path = file_path.absolute()
            path_str = str(abs_path).replace('\\', '/')
            file_uri = f"file:///{quote(path_str)}"
        else:
            # Try to make relative
            try:
                rel_path = file_path.relative_to(output_path.parent)
                path_str = str(rel_path).replace('\\', '/')
                file_uri = quote(path_str)
            except ValueError:
                # Can't make relative, use absolute
                abs_path = file_path.absolute()
                path_str = str(abs_path).replace('\\', '/')
            file_uri = f"file:///{quote(path_str)}"
        
        location.text = file_uri
        
        # Add title (filename without extension)
        if file_path.exists():
            title = ET.SubElement(track, 'title')
            title.text = file_path.stem
    
    # Create the tree and write to file
    tree = ET.ElementTree(playlist)
    tree.write(output_path, encoding='utf-8', xml_declaration=True)
    
    return output_path.absolute()


def create_playlist_from_sets(
    sets_data: List[dict],
    file_results: dict,
    output_file: str,
    playlist_format: str = "m3u",
    use_absolute_paths: bool = True
) -> Optional[Path]:
    """
    Create a playlist from Irish music sets data.
    
    Args:
        sets_data: List of set dictionaries with tunes
        file_results: Dictionary mapping tune names to file paths
        output_file: Output playlist filename
        playlist_format: Format - "m3u" or "xspf"
        use_absolute_paths: Use absolute paths in playlist
    
    Returns:
        Path to created playlist or None if no files found
    """
    # Collect all file paths in order
    all_files = []
    
    for set_data in sets_data:
        set_name = set_data.get('set_name', 'Unknown Set')
        tunes = set_data.get('tunes', [])
        
        for tune in tunes:
            if tune in file_results and file_results[tune]:
                # Add ALL matches for each tune
                all_files.extend(file_results[tune])
    
    if not all_files:
        return None
    
    # Create playlist
    if playlist_format == "xspf":
        return create_xspf_playlist(
            all_files,
            output_file,
            playlist_title="Irish Music Practice Sets",
            use_absolute_paths=use_absolute_paths
        )
    else:
        return create_m3u_playlist(
            all_files,
            output_file,
            playlist_name="Irish Music Practice Sets",
            use_absolute_paths=use_absolute_paths
        )


if __name__ == "__main__":
    # Test playlist creation
    test_files = [
        Path("/Users/pk/Dropbox/Dreadlap/03 The Butterfly.m4a"),
        Path("/Users/pk/Dropbox/Dreadlap/drowsy maggie.m4a"),
        Path("/Users/pk/Dropbox/Dreadlap/05 Harvest Home.m4a")
    ]
    
    print("Creating test playlists...")
    
    # Test M3U
    m3u_path = create_m3u_playlist(
        test_files,
        "test_playlist.m3u",
        playlist_name="Test Irish Tunes"
    )
    print(f"Created M3U: {m3u_path}")
    
    # Test XSPF
    xspf_path = create_xspf_playlist(
        test_files,
        "test_playlist.xspf",
        playlist_title="Test Irish Tunes"
    )
    print(f"Created XSPF: {xspf_path}")