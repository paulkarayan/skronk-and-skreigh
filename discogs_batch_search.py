#!/usr/bin/env python3
"""
Discogs Batch Search Tool
Reads a list of records from CSV or JSON and searches for each one
Uses the discogs_album_search module to find marketplace listings
"""

import csv
import json
import os
import time
import argparse
from datetime import datetime
from dotenv import load_dotenv

# Import our existing search functionality
from discogs_album_search import DiscogsSearcher

# Load environment variables
load_dotenv()

def read_csv_wishlist(filename):
    """Read wishlist from CSV file"""
    wishlist = []
    
    with open(filename, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            # Handle different possible column names
            item = {
                'artist': row.get('artist') or row.get('Artist') or row.get('ARTIST', ''),
                'title': row.get('title') or row.get('Title') or row.get('album') or row.get('Album') or row.get('TITLE', ''),
                'format': row.get('format') or row.get('Format') or row.get('FORMAT', 'Vinyl'),
                'year': row.get('year') or row.get('Year') or row.get('YEAR', ''),
                'notes': row.get('notes') or row.get('Notes') or row.get('NOTES', '')
            }
            
            # Only add if we have at least artist or title
            if item['artist'] or item['title']:
                wishlist.append(item)
    
    return wishlist

def read_json_wishlist(filename):
    """Read wishlist from JSON file"""
    with open(filename, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    # Handle both array of objects and object with array
    if isinstance(data, list):
        wishlist = data
    elif isinstance(data, dict) and 'records' in data:
        wishlist = data['records']
    elif isinstance(data, dict) and 'wishlist' in data:
        wishlist = data['wishlist']
    else:
        raise ValueError("JSON format not recognized. Expected array or object with 'records' or 'wishlist' key")
    
    # Normalize the data
    normalized = []
    for item in wishlist:
        normalized.append({
            'artist': item.get('artist', ''),
            'title': item.get('title', '') or item.get('album', ''),
            'format': item.get('format', 'Vinyl'),
            'year': item.get('year', ''),
            'notes': item.get('notes', '')
        })
    
    return normalized

def search_single_record(searcher, record, max_results_per_item=5):
    """Search for a single record"""
    print(f"\nSearching for: {record['artist']} - {record['title']}")
    if record.get('year'):
        print(f"  Year: {record['year']}")
    if record.get('format'):
        print(f"  Format: {record['format']}")
    
    # Build search query
    query = None
    if record['artist'] and record['title']:
        # Use specific artist and title search
        artist = record['artist']
        title = record['title']
    elif record['artist'] or record['title']:
        # Use general query if only one is provided
        query = f"{record['artist']} {record['title']}".strip()
        artist = None
        title = None
    else:
        print("  Skipping - no artist or title provided")
        return None
    
    # Perform search
    try:
        results = searcher.search_and_get_sellers(
            query=query,
            artist=artist,
            title=title,
            format_filter=record.get('format'),
            max_results=max_results_per_item
        )
        
        if results:
            print(f"  Found {len(results)} matching releases")
            # Add wishlist info to results
            for result in results:
                result['wishlist_artist'] = record['artist']
                result['wishlist_title'] = record['title']
                result['wishlist_notes'] = record.get('notes', '')
        else:
            print("  No results found")
            
        return results
        
    except Exception as e:
        print(f"  Error searching: {e}")
        return None

def save_batch_results(all_results, output_filename):
    """Save all batch search results to CSV"""
    if not all_results:
        print("\nNo results to save")
        return
    
    with open(output_filename, 'w', newline='', encoding='utf-8') as csvfile:
        fieldnames = [
            'wishlist_artist', 'wishlist_title', 'wishlist_notes',
            'found_artist', 'found_title', 'year', 'format', 'label', 'country',
            'num_for_sale', 'lowest_price', 'community_have', 'community_want',
            'release_url', 'marketplace_url'
        ]
        
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        
        for result in all_results:
            row = {
                'wishlist_artist': result.get('wishlist_artist', ''),
                'wishlist_title': result.get('wishlist_title', ''),
                'wishlist_notes': result.get('wishlist_notes', ''),
                'found_artist': result.get('artist', ''),
                'found_title': result.get('title', ''),
                'year': result.get('year', ''),
                'format': result.get('format', ''),
                'label': result.get('label', ''),
                'country': result.get('country', ''),
                'num_for_sale': result.get('num_for_sale', 0),
                'lowest_price': result.get('lowest_price', 'N/A'),
                'community_have': result.get('community', {}).get('have', 0),
                'community_want': result.get('community', {}).get('want', 0),
                'release_url': result.get('release_url', ''),
                'marketplace_url': result.get('marketplace_url', '')
            }
            writer.writerow(row)
    
    print(f"\nResults saved to {output_filename}")

def print_summary(wishlist, all_results):
    """Print summary of search results"""
    print("\n" + "="*80)
    print("SEARCH SUMMARY")
    print("="*80)
    print(f"Total items searched: {len(wishlist)}")
    print(f"Total releases found: {len(all_results)}")
    
    # Count items with available copies
    available_count = sum(1 for r in all_results if r.get('num_for_sale', 0) > 0)
    print(f"Releases with copies for sale: {available_count}")
    
    # Group by wishlist item
    wishlist_results = {}
    for result in all_results:
        key = f"{result.get('wishlist_artist', '')} - {result.get('wishlist_title', '')}"
        if key not in wishlist_results:
            wishlist_results[key] = []
        wishlist_results[key].append(result)
    
    print(f"\nItems with matches: {len(wishlist_results)}")
    print(f"Items with no matches: {len(wishlist) - len(wishlist_results)}")
    
    # Show items with available copies
    print("\n" + "-"*80)
    print("AVAILABLE NOW:")
    print("-"*80)
    
    for result in all_results:
        if result.get('num_for_sale', 0) > 0:
            print(f"{result['artist']} - {result['title']} ({result['year']})")
            print(f"  {result['num_for_sale']} copies from {result['lowest_price']}")
            print(f"  {result['marketplace_url']}")
            print()

def main():
    parser = argparse.ArgumentParser(description='Batch search Discogs for multiple records')
    parser.add_argument('input_file', help='CSV or JSON file with records to search')
    parser.add_argument('-o', '--output', help='Output CSV filename (default: batch_search_results_[timestamp].csv)')
    parser.add_argument('-m', '--max-results', type=int, default=5, 
                       help='Maximum results per item (default: 5)')
    parser.add_argument('-d', '--delay', type=float, default=1.0,
                       help='Delay between searches in seconds (default: 1.0)')
    parser.add_argument('-s', '--summary', action='store_true',
                       help='Show summary only, no detailed results')
    
    args = parser.parse_args()
    
    # Check API token
    api_token = os.environ.get('DISCOGS_TOKEN')
    if not api_token:
        print("Error: DISCOGS_TOKEN not found in environment variables")
        return
    
    # Determine file type and read wishlist
    if args.input_file.lower().endswith('.csv'):
        print(f"Reading CSV file: {args.input_file}")
        wishlist = read_csv_wishlist(args.input_file)
    elif args.input_file.lower().endswith('.json'):
        print(f"Reading JSON file: {args.input_file}")
        wishlist = read_json_wishlist(args.input_file)
    else:
        print("Error: Input file must be .csv or .json")
        return
    
    print(f"Loaded {len(wishlist)} items to search")
    
    # Initialize searcher
    searcher = DiscogsSearcher(api_token)
    
    # Search for each item
    all_results = []
    for i, record in enumerate(wishlist, 1):
        print(f"\n[{i}/{len(wishlist)}]", end='')
        results = search_single_record(searcher, record, args.max_results)
        
        if results:
            all_results.extend(results)
        
        # Rate limiting
        if i < len(wishlist):
            time.sleep(args.delay)
    
    # Print summary
    print_summary(wishlist, all_results)
    
    # Save results
    if not args.summary:
        if args.output:
            output_filename = args.output
        else:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            output_filename = f"batch_search_results_{timestamp}.csv"
        
        save_batch_results(all_results, output_filename)

if __name__ == "__main__":
    main()