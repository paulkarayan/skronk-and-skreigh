#!/usr/bin/env python3
"""
Convert top-session-tunes.csv to target.md format for playlist creation
Groups tunes by type into sets of 3
"""

import csv
import sys
from collections import defaultdict

def read_top_tunes(csv_file):
    """Read the CSV and organize tunes by type"""
    tunes_by_type = defaultdict(list)
    
    with open(csv_file, 'r') as f:
        reader = csv.DictReader(f)
        for row in reader:
            tune_type = row['Type']
            tune_name = row['Name']
            
            # Skip recording entries for now (avoid duplicates)
            if '(recordings)' not in tune_type:
                tunes_by_type[tune_type].append(tune_name)
    
    return tunes_by_type

def create_sets_from_tunes(tunes_by_type, tunes_per_set=3):
    """Create sets of tunes, grouping by type"""
    all_sets = []
    
    # Process each type
    for tune_type, tunes in tunes_by_type.items():
        # Remove duplicates while preserving order
        seen = set()
        unique_tunes = []
        for tune in tunes:
            if tune not in seen:
                seen.add(tune)
                unique_tunes.append(tune)
        
        # Create sets of N tunes
        for i in range(0, len(unique_tunes), tunes_per_set):
            tune_set = unique_tunes[i:i+tunes_per_set]
            if tune_set:  # Don't add empty sets
                all_sets.append(' / '.join(tune_set))
    
    return all_sets

def main():
    if len(sys.argv) < 2:
        print("Usage: python convert_top_tunes_to_target.py <csv_file> [output_file]")
        sys.exit(1)
    
    csv_file = sys.argv[1]
    output_file = sys.argv[2] if len(sys.argv) > 2 else 'top_tunes_target.md'
    
    # Read and process tunes
    print(f"Reading {csv_file}...")
    tunes_by_type = read_top_tunes(csv_file)
    
    # Show summary
    print("\nTunes by type:")
    for tune_type, tunes in sorted(tunes_by_type.items()):
        unique_tunes = list(dict.fromkeys(tunes))  # Remove duplicates
        print(f"  {tune_type}: {len(unique_tunes)} unique tunes")
    
    # Create sets
    print("\nCreating sets...")
    all_sets = create_sets_from_tunes(tunes_by_type)
    
    # Write to output file
    with open(output_file, 'w') as f:
        for tune_set in all_sets:
            f.write(tune_set + '\n')
    
    print(f"\nCreated {len(all_sets)} sets")
    print(f"Output written to: {output_file}")
    
    # Show first few sets as preview
    print("\nFirst 5 sets:")
    for i, tune_set in enumerate(all_sets[:5]):
        print(f"  {i+1}. {tune_set}")

if __name__ == "__main__":
    main()