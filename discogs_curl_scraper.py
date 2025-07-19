#!/usr/bin/env python3
import subprocess
import json
import csv
import time
import re
from html.parser import HTMLParser

class DiscogsParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.records = []
        self.current_record = {}
        self.in_listing = False
        self.in_artist = False
        self.in_title = False
        self.in_label = False
        self.in_price = False
        self.in_condition = False
        self.current_tag = None
        self.condition_count = 0
        
    def handle_starttag(self, tag, attrs):
        attrs_dict = dict(attrs)
        
        # Check for listing row
        if tag == 'tr' and 'class' in attrs_dict and 'shortcut_navigable' in attrs_dict['class']:
            self.in_listing = True
            self.current_record = {
                'artist': '',
                'title': '',
                'label': '',
                'catalog_number': '',
                'format': 'Vinyl LP',
                'media_condition': '',
                'sleeve_condition': '',
                'price': ''
            }
            self.condition_count = 0
        
        # Check for artist link
        elif self.in_listing and tag == 'a' and 'class' in attrs_dict and 'artist_name' in attrs_dict['class']:
            self.in_artist = True
        
        # Check for title link
        elif self.in_listing and tag == 'a' and 'class' in attrs_dict and 'item_title' in attrs_dict['class']:
            self.in_title = True
        
        # Check for label info
        elif self.in_listing and tag == 'span' and 'class' in attrs_dict and 'item_label_and_cat' in attrs_dict['class']:
            self.in_label = True
        
        # Check for price
        elif self.in_listing and tag == 'span' and 'class' in attrs_dict and 'price' in attrs_dict['class']:
            self.in_price = True
        
        # Check for condition
        elif self.in_listing and tag == 'span' and 'class' in attrs_dict and 'condition_text' in attrs_dict['class']:
            self.in_condition = True
    
    def handle_endtag(self, tag):
        if tag == 'tr' and self.in_listing:
            self.in_listing = False
            if self.current_record['artist'] or self.current_record['title']:
                self.records.append(self.current_record)
        
        elif self.in_artist:
            self.in_artist = False
        elif self.in_title:
            self.in_title = False
        elif self.in_label:
            self.in_label = False
        elif self.in_price:
            self.in_price = False
        elif self.in_condition:
            self.in_condition = False
            self.condition_count += 1
    
    def handle_data(self, data):
        data = data.strip()
        if not data:
            return
        
        if self.in_artist:
            self.current_record['artist'] = data
        elif self.in_title:
            self.current_record['title'] = data
        elif self.in_label:
            # Parse label and catalog number
            parts = data.split(' - ')
            self.current_record['label'] = parts[0] if parts else data
            self.current_record['catalog_number'] = parts[1] if len(parts) > 1 else ''
        elif self.in_price:
            self.current_record['price'] = data
        elif self.in_condition:
            if self.condition_count == 0:
                self.current_record['media_condition'] = data
            else:
                self.current_record['sleeve_condition'] = data

def fetch_with_curl(url):
    """Use curl to fetch the page content"""
    cmd = [
        'curl', '-s', '-L',
        '-H', 'User-Agent: Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        '-H', 'Accept: text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        '-H', 'Accept-Language: en-US,en;q=0.9',
        '-H', 'Accept-Encoding: gzip, deflate, br',
        '-H', 'Connection: keep-alive',
        '-H', 'Upgrade-Insecure-Requests: 1',
        '-H', 'Sec-Fetch-Dest: document',
        '-H', 'Sec-Fetch-Mode: navigate',
        '-H', 'Sec-Fetch-Site: none',
        '-H', 'Sec-Fetch-User: ?1',
        '--compressed',
        url
    ]
    
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        return result.stdout
    except subprocess.CalledProcessError as e:
        print(f"Error fetching URL: {e}")
        return None

def extract_total_pages(html_content):
    """Extract the total number of pages from the pagination"""
    # Look for pagination patterns
    page_pattern = r'page=(\d+)'
    pages = re.findall(page_pattern, html_content)
    if pages:
        return max(int(p) for p in pages)
    return 1

def scrape_all_pages(base_url):
    """Scrape all pages of vinyl records"""
    all_records = []
    page = 1
    max_pages = None
    
    while True:
        url = f"{base_url}&page={page}"
        print(f"Fetching page {page}...")
        
        html_content = fetch_with_curl(url)
        if not html_content:
            break
        
        # Check if we're blocked
        if "Enable JavaScript and cookies to continue" in html_content:
            print("Website requires JavaScript. Trying alternative approach...")
            return None
        
        # Parse the HTML
        parser = DiscogsParser()
        parser.feed(html_content)
        
        if not parser.records:
            print(f"No records found on page {page}")
            break
        
        all_records.extend(parser.records)
        print(f"Extracted {len(parser.records)} records from page {page}")
        
        # Check for total pages on first page
        if page == 1 and max_pages is None:
            max_pages = extract_total_pages(html_content)
            print(f"Total pages detected: {max_pages}")
        
        # Check if we've reached the last page
        if max_pages and page >= max_pages:
            print(f"Reached last page ({page})")
            break
        
        # Also check for "Next" button
        if 'Next' not in html_content or 'class="pagination_next disabled"' in html_content:
            print("No next page found")
            break
        
        page += 1
        time.sleep(2)  # Be polite to the server
    
    return all_records

def save_to_csv(records, filename='discogs_vinyl_records.csv'):
    """Save records to CSV file"""
    if not records:
        print("No records to save")
        return
    
    fieldnames = ['artist', 'title', 'label', 'catalog_number', 'format', 
                  'media_condition', 'sleeve_condition', 'price']
    
    with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(records)
    
    print(f"Saved {len(records)} records to {filename}")

if __name__ == "__main__":
    base_url = "https://www.discogs.com/seller/The_Record_Cellar/profile?format=Vinyl&format_desc=LP"
    
    print("Starting Discogs scraper using curl...")
    
    # First, let's test if we can access the site
    test_content = fetch_with_curl(base_url)
    if test_content and "Enable JavaScript and cookies to continue" in test_content:
        print("\nThe website requires JavaScript and is blocking automated access.")
        print("Unfortunately, we cannot scrape this site directly.")
        print("\nAlternative options:")
        print("1. Use the Discogs API (requires API key)")
        print("2. Use a browser automation tool like Selenium")
        print("3. Manually export the data from the website")
        print("4. Use a proxy service that can handle JavaScript")
    else:
        records = scrape_all_pages(base_url)
        
        if records:
            save_to_csv(records)
            print(f"\nSuccessfully scraped {len(records)} vinyl records!")
            print("Check discogs_vinyl_records.csv for the results")
        else:
            print("No records were scraped")