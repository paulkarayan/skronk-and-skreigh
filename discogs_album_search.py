#!/usr/bin/env python3
"""
Discogs Album Search Tool
Search for specific albums on Discogs and get seller URLs
Supports filtering by format (vinyl, LP, etc.)
"""

import requests
import argparse
import os
import time
from dotenv import load_dotenv
from urllib.parse import quote

# Load environment variables
load_dotenv()

class DiscogsSearcher:
    def __init__(self, user_token):
        self.base_url = "https://api.discogs.com"
        self.headers = {
            "User-Agent": "DiscogsAlbumSearcher/1.0",
            "Authorization": f"Discogs token={user_token}"
        }
        self.session = requests.Session()
        self.session.headers.update(self.headers)
    
    def search_releases(self, query, artist=None, title=None, format_filter=None, page=1, per_page=50):
        """Search for releases on Discogs"""
        url = f"{self.base_url}/database/search"
        
        params = {
            "page": page,
            "per_page": per_page,
            "type": "release"
        }
        
        # Build search query
        if query:
            params["q"] = query
        if artist:
            params["artist"] = artist
        if title:
            params["release_title"] = title
        if format_filter:
            params["format"] = format_filter
        
        print(f"Searching with params: {params}")
        
        try:
            response = self.session.get(url, params=params, timeout=30)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            print(f"Search error: {e}")
            return None
    
    def get_release_details(self, release_id):
        """Get detailed release information"""
        url = f"{self.base_url}/releases/{release_id}"
        
        try:
            response = self.session.get(url, timeout=30)
            if response.status_code == 200:
                return response.json()
            else:
                return None
        except Exception as e:
            print(f"Release details error: {e}")
            return None
    
    def search_and_get_sellers(self, query=None, artist=None, title=None, format_filter=None, max_results=50):
        """Search for releases and get seller information"""
        all_results = []
        page = 1
        
        while len(all_results) < max_results:
            print(f"\nSearching page {page}...")
            data = self.search_releases(query, artist, title, format_filter, page)
            
            if not data or not data.get('results'):
                break
            
            results = data.get('results', [])
            print(f"Found {len(results)} releases on page {page}")
            
            for i, release in enumerate(results):
                if len(all_results) >= max_results:
                    break
                
                release_info = {
                    'id': release.get('id'),
                    'artist': release.get('title', '').split(' - ')[0] if ' - ' in release.get('title', '') else '',
                    'title': release.get('title', '').split(' - ')[1] if ' - ' in release.get('title', '') else release.get('title', ''),
                    'year': release.get('year'),
                    'format': ', '.join(release.get('format', [])),
                    'label': ', '.join(release.get('label', [])),
                    'country': release.get('country'),
                    'release_url': f"https://www.discogs.com/release/{release.get('id')}",
                    'marketplace_url': f"https://www.discogs.com/sell/release/{release.get('id')}",
                    'master_id': release.get('master_id'),
                    'community': {}
                }
                
                # Get additional release details
                print(f"  Getting details for: {release_info['artist']} - {release_info['title']}")
                release_details = self.get_release_details(release.get('id'))
                
                if release_details:
                    # Get community stats (how many have, want)
                    community = release_details.get('community', {})
                    release_info['community'] = {
                        'have': community.get('have', 0),
                        'want': community.get('want', 0)
                    }
                    
                    # Get lowest price if available
                    if 'lowest_price' in release_details and release_details.get('lowest_price') is not None:
                        release_info['lowest_price'] = f"{float(release_details.get('lowest_price', 0)):.2f}"
                        release_info['num_for_sale'] = release_details.get('num_for_sale', 0)
                    else:
                        release_info['lowest_price'] = 'N/A'
                        release_info['num_for_sale'] = 0
                    
                    print(f"    {release_info['num_for_sale']} copies for sale, lowest: {release_info['lowest_price']}")
                
                all_results.append(release_info)
                
                # Rate limiting
                time.sleep(0.5)
            
            # Check if there are more pages
            pagination = data.get('pagination', {})
            if page >= pagination.get('pages', 1):
                break
            
            page += 1
            time.sleep(1)  # Rate limiting between pages
        
        return all_results

def format_results(results, show_details=False):
    """Format search results for display"""
    if not results:
        print("\nNo results found.")
        return
    
    print(f"\n{'='*80}")
    print(f"Found {len(results)} releases:")
    print(f"{'='*80}\n")
    
    for i, release in enumerate(results, 1):
        print(f"{i}. {release['artist']} - {release['title']} ({release['year']})")
        print(f"   Format: {release['format']}")
        print(f"   Label: {release['label']}")
        print(f"   Country: {release['country']}")
        
        # Show community stats
        community = release.get('community', {})
        if community:
            print(f"   Community: {community.get('have', 0)} have, {community.get('want', 0)} want")
        
        # Show marketplace info
        num_for_sale = release.get('num_for_sale', 0)
        if num_for_sale > 0:
            print(f"   For Sale: {num_for_sale} copies starting at {release.get('lowest_price', 'N/A')}")
            print(f"   Marketplace URL: {release['marketplace_url']}")
        else:
            print(f"   For Sale: None currently available")
        
        if show_details:
            print(f"   Release URL: {release['release_url']}")
            if release.get('master_id'):
                print(f"   Master Release URL: https://www.discogs.com/master/{release['master_id']}")
        
        print(f"\n{'-'*80}\n")

def save_results_to_csv(results, filename='discogs_search_results.csv'):
    """Save search results to CSV file"""
    import csv
    
    with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
        fieldnames = ['artist', 'title', 'year', 'format', 'label', 'country', 
                      'num_for_sale', 'lowest_price', 'community_have', 'community_want',
                      'release_url', 'marketplace_url']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        
        for release in results:
            row = {
                'artist': release['artist'],
                'title': release['title'],
                'year': release['year'],
                'format': release['format'],
                'label': release['label'],
                'country': release['country'],
                'num_for_sale': release.get('num_for_sale', 0),
                'lowest_price': release.get('lowest_price', 'N/A'),
                'community_have': release.get('community', {}).get('have', 0),
                'community_want': release.get('community', {}).get('want', 0),
                'release_url': release['release_url'],
                'marketplace_url': release['marketplace_url']
            }
            writer.writerow(row)
    
    print(f"\nResults saved to {filename}")

def main():
    parser = argparse.ArgumentParser(description='Search Discogs for albums and get seller URLs')
    parser.add_argument('-q', '--query', help='General search query')
    parser.add_argument('-a', '--artist', help='Artist name')
    parser.add_argument('-t', '--title', help='Album/release title')
    parser.add_argument('-f', '--format', help='Format filter (e.g., "Vinyl", "LP", "12\\"", "7\\"")')
    parser.add_argument('-m', '--max-results', type=int, default=20, help='Maximum number of results (default: 20)')
    parser.add_argument('-o', '--output', help='Output CSV filename')
    parser.add_argument('-d', '--details', action='store_true', help='Show detailed listing URLs')
    
    args = parser.parse_args()
    
    # Get API token
    api_token = os.environ.get('DISCOGS_TOKEN')
    if not api_token:
        print("Error: DISCOGS_TOKEN not found in environment variables")
        print("Please set it in your .env file")
        return
    
    # Ensure at least one search parameter is provided
    if not any([args.query, args.artist, args.title]):
        print("Error: Please provide at least one search parameter (-q, -a, or -t)")
        parser.print_help()
        return
    
    # Format examples
    print("\nFormat examples: Vinyl, LP, CD, Cassette, 12\", 7\", 10\"")
    print("You can combine: -f \"LP\" for LPs only, -f \"12\\\"\" for 12-inch singles\n")
    
    # Initialize searcher
    searcher = DiscogsSearcher(api_token)
    
    # Perform search
    results = searcher.search_and_get_sellers(
        query=args.query,
        artist=args.artist,
        title=args.title,
        format_filter=args.format,
        max_results=args.max_results
    )
    
    # Display results
    format_results(results, show_details=args.details)
    
    # Save to CSV if requested
    if args.output:
        save_results_to_csv(results, args.output)
    elif results and os.isatty(0):  # Only prompt if running interactively
        save_option = input("\nSave results to CSV? (y/n): ")
        if save_option.lower() == 'y':
            filename = input("Enter filename (default: discogs_search_results.csv): ").strip()
            if not filename:
                filename = "discogs_search_results.csv"
            save_results_to_csv(results, filename)

if __name__ == "__main__":
    main()