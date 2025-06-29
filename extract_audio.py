#!/usr/bin/env python3
"""
Extract audio segments from the YouTube MP3 based on target.md sets
Usage: python extract_audio.py <input_mp3_file>
"""

import sys
from irish_playlist_manager import IrishPlaylistManager

def main():
    if len(sys.argv) < 2:
        print("Usage: python extract_audio.py <input_mp3_file>")
        print("Example: python extract_audio.py foinn1_audio.mp3")
        return
        
    input_file = sys.argv[1]
    
    manager = IrishPlaylistManager()
    
    # Parse target sets
    target_sets = manager.parse_target_file("target.md")
    
    if not target_sets:
        print("No target sets found in target.md")
        return
        
    # Find matching sets
    matching_sets = manager.find_matching_sets(target_sets)
    
    print(f"\nExtracting {len(matching_sets)} sets from {input_file}...")
    
    # Extract audio segments
    manager.extract_audio_segments(input_file, "extracted_sets", matching_sets)
    
    # Combine into single file
    manager.create_combined_audio("extracted_sets", "my_practice_sets.mp3")
    
    print("\n✓ Done! Created:")
    print("  - Individual sets in extracted_sets/")
    print("  - Combined file: my_practice_sets.mp3")

if __name__ == "__main__":
    main()