#!/usr/bin/env python3
"""
Discogs API Seller Inventory Fetcher
Fetches all vinyl/LP records from a Discogs seller using the official API
"""

import requests
import csv
import time
import os
from urllib.parse import urlparse
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class DiscogsAPI:
    def __init__(self, user_token):
        self.base_url = "https://api.discogs.com"
        self.headers = {
            "User-Agent": "DiscogsVinylFetcher/1.0",
            "Authorization": f"Discogs token={user_token}"
        }
        self.session = requests.Session()
        self.session.headers.update(self.headers)
    
    def get_seller_inventory(self, seller_username, format_filter="Vinyl", page=1, per_page=100):
        """Fetch a page of seller's inventory"""
        # Use the user inventory endpoint
        url = f"{self.base_url}/users/{seller_username}/inventory"
        params = {
            "page": page,
            "per_page": per_page
        }
        
        print(f"Requesting: {url} page {page}")
        try:
            response = self.session.get(url, params=params, timeout=30)
            print(f"Response status: {response.status_code}")
            response.raise_for_status()
            return response.json()
        except requests.exceptions.Timeout:
            print("Request timed out")
            return None
        except Exception as e:
            print(f"Request error: {e}")
            return None
    
    def get_all_vinyl_records(self, seller_username):
        """Fetch all vinyl records from a seller"""
        all_records = []
        page = 1
        
        while True:
            print(f"Fetching page {page}...")
            
            try:
                data = self.get_seller_inventory(seller_username, page=page)
                
                if data is None:
                    print("Failed to get data")
                    break
                
                # Check if we have listings
                listings = data.get('listings', [])
                if not listings:
                    print("No more listings found")
                    break
                
                # Filter for vinyl/LP records
                vinyl_count = 0
                for listing in listings:
                    release = listing.get('release', {})
                    
                    # Check format
                    format_str = release.get('format', '').upper()
                    
                    # Check if it's vinyl/LP - looking for LP, Album, 12", 10", 7" etc
                    is_vinyl = any(fmt in format_str for fmt in ['LP', '12"', '10"', '7"', 'VINYL'])
                    
                    if is_vinyl:
                        vinyl_count += 1
                        record = {
                            'listing_id': listing.get('id', ''),
                            'artist': release.get('artist', ''),
                            'title': release.get('title', ''),
                            'label': release.get('label', ''),
                            'catalog_number': release.get('catalog_number', ''),
                            'year': release.get('year', ''),
                            'format': release.get('format', ''),
                            'media_condition': listing.get('condition', ''),
                            'sleeve_condition': listing.get('sleeve_condition', ''),
                            'price': f"{listing.get('price', {}).get('currency', '')} {listing.get('price', {}).get('value', '')}",
                            'status': listing.get('status', ''),
                            'ships_from': listing.get('ships_from', ''),
                            'comments': listing.get('comments', '').replace('\n', ' ') if listing.get('comments') else ''
                        }
                        all_records.append(record)
                
                print(f"Found {vinyl_count} vinyl records on page {page}")
                
                # Check pagination
                pagination = data.get('pagination', {})
                total_pages = pagination.get('pages', 1)
                print(f"Progress: page {page} of {total_pages}")
                
                if page >= total_pages:
                    print(f"Reached last page ({page})")
                    break
                
                # Optional: limit pages for testing
                # if page >= 10:
                #     print("Limiting to first 10 pages for testing")
                #     break
                
                page += 1
                time.sleep(1)  # Rate limit: 60 requests per minute
                
            except requests.exceptions.HTTPError as e:
                if e.response.status_code == 429:
                    print("Rate limited. Waiting 60 seconds...")
                    time.sleep(60)
                    continue
                else:
                    print(f"Error: {e}")
                    break
            except Exception as e:
                print(f"Unexpected error: {e}")
                break
        
        return all_records

def extract_seller_username(url):
    """Extract seller username from Discogs URL"""
    # URL format: https://www.discogs.com/seller/USERNAME/profile
    path_parts = urlparse(url).path.split('/')
    if 'seller' in path_parts:
        seller_index = path_parts.index('seller')
        if seller_index + 1 < len(path_parts):
            return path_parts[seller_index + 1]
    return None

def save_to_csv(records, filename='discogs_vinyl_inventory.csv'):
    """Save records to CSV file"""
    if not records:
        print("No records to save")
        return
    
    fieldnames = [
        'listing_id', 'artist', 'title', 'label', 'catalog_number', 
        'year', 'format', 'format_details', 'media_condition', 
        'sleeve_condition', 'price', 'status', 'ships_from', 'comments'
    ]
    
    with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(records)
    
    print(f"Saved {len(records)} records to {filename}")

def main():
    # Get API token from environment
    api_token = os.environ.get('DISCOGS_TOKEN')
    
    if not api_token:
        print("Discogs API Token required!")
        print("\nTo get your token:")
        print("1. Log in to Discogs")
        print("2. Go to https://www.discogs.com/settings/developers")
        print("3. Click 'Generate new token'")
        print("4. Add it to your .env file as: DISCOGS_TOKEN='your_token_here'")
        return
    
    print(f"Token found: {api_token[:10]}...")
    
    # The seller URL
    seller_url = "https://www.discogs.com/seller/The_Record_Cellar/profile"
    seller_username = extract_seller_username(seller_url)
    
    if not seller_username:
        print("Could not extract seller username from URL")
        print("Using 'The_Record_Cellar' as username")
        seller_username = "The_Record_Cellar"
    
    print(f"\nFetching vinyl records from seller: {seller_username}")
    
    # Initialize API client
    api = DiscogsAPI(api_token)
    
    # Fetch all vinyl records
    records = api.get_all_vinyl_records(seller_username)
    
    if records:
        save_to_csv(records)
        print(f"\nSuccessfully fetched {len(records)} vinyl/LP records!")
        
        # Show sample of data
        print("\nSample of fetched records:")
        for i, record in enumerate(records[:5]):
            print(f"{i+1}. {record['artist']} - {record['title']} ({record['price']})")
    else:
        print("No records were fetched")

if __name__ == "__main__":
    main()