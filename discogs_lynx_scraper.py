#!/usr/bin/env python3
import subprocess
import re
import csv
import time
import os

def extract_with_lynx(url):
    """Use lynx to dump the page content"""
    try:
        # Use lynx to dump the page in a readable format
        result = subprocess.run(
            ['lynx', '-dump', '-nolist', '-width=200', url],
            capture_output=True,
            text=True,
            check=True
        )
        return result.stdout
    except subprocess.CalledProcessError as e:
        print(f"Error running lynx: {e}")
        return None
    except FileNotFoundError:
        print("Lynx not found. Please install lynx: brew install lynx")
        return None

def parse_lynx_output(content):
    """Parse the lynx dump output to extract record information"""
    records = []
    
    # Split content into lines
    lines = content.split('\n')
    
    # Look for patterns that indicate a record listing
    current_record = {}
    in_record = False
    
    for i, line in enumerate(lines):
        line = line.strip()
        
        # Skip empty lines
        if not line:
            continue
        
        # Look for artist - title pattern
        # Usually appears as "Artist - Title"
        if ' - ' in line and not line.startswith('$') and not line.startswith('£'):
            # Check if this looks like an artist-title line
            parts = line.split(' - ', 1)
            if len(parts) == 2 and not any(x in line.lower() for x in ['page', 'next', 'previous', 'login', 'register']):
                # Start a new record
                if current_record:
                    records.append(current_record)
                
                current_record = {
                    'artist': parts[0].strip(),
                    'title': parts[1].strip(),
                    'label': '',
                    'catalog_number': '',
                    'format': 'Vinyl LP',
                    'media_condition': '',
                    'sleeve_condition': '',
                    'price': ''
                }
                in_record = True
        
        # Look for price (lines starting with $ or £)
        elif in_record and (line.startswith('$') or line.startswith('£') or 'USD' in line):
            current_record['price'] = line.strip()
        
        # Look for condition information (VG+, NM, etc.)
        elif in_record and any(cond in line for cond in ['VG+', 'VG', 'NM', 'M', 'G+', 'G', 'F', 'P']):
            # Extract conditions
            condition_pattern = r'\b(M|NM|VG\+|VG|G\+|G|F|P)\b'
            conditions = re.findall(condition_pattern, line)
            if conditions:
                current_record['media_condition'] = conditions[0] if len(conditions) > 0 else ''
                current_record['sleeve_condition'] = conditions[1] if len(conditions) > 1 else conditions[0]
        
        # Look for label information
        elif in_record and i > 0 and 'cat#' in line.lower():
            # Extract catalog number
            cat_match = re.search(r'cat#?\s*:?\s*(\S+)', line, re.IGNORECASE)
            if cat_match:
                current_record['catalog_number'] = cat_match.group(1)
    
    # Don't forget the last record
    if current_record:
        records.append(current_record)
    
    return records

def scrape_all_pages(base_url):
    """Scrape all pages of vinyl records"""
    all_records = []
    page = 1
    
    while True:
        url = f"{base_url}&page={page}"
        print(f"Fetching page {page}...")
        
        content = extract_with_lynx(url)
        if not content:
            break
        
        # Check if we've reached the end (no records or "no items found")
        if "no items found" in content.lower() or "0 items" in content:
            print(f"No more records found at page {page}")
            break
        
        records = parse_lynx_output(content)
        if not records:
            print(f"No records extracted from page {page}")
            break
        
        all_records.extend(records)
        print(f"Extracted {len(records)} records from page {page}")
        
        # Check if there's a next page by looking for "Next" in the content
        if "Next »" not in content and "Next" not in content:
            print("No next page link found, assuming last page")
            break
        
        page += 1
        time.sleep(1)  # Be polite to the server
    
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
    # Check if lynx is installed
    if subprocess.run(['which', 'lynx'], capture_output=True).returncode != 0:
        print("Lynx is not installed. Please install it first:")
        print("  macOS: brew install lynx")
        print("  Ubuntu/Debian: sudo apt-get install lynx")
        print("  CentOS/RHEL: sudo yum install lynx")
        exit(1)
    
    base_url = "https://www.discogs.com/seller/The_Record_Cellar/profile?format=Vinyl&format_desc=LP"
    
    print("Starting Discogs scraper using Lynx...")
    records = scrape_all_pages(base_url)
    
    if records:
        save_to_csv(records)
        print(f"\nSuccessfully scraped {len(records)} vinyl records!")
        print("Check discogs_vinyl_records.csv for the results")
    else:
        print("No records were scraped")