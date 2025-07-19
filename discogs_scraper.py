import requests
from bs4 import BeautifulSoup
import csv
import time
from urllib.parse import urljoin, urlparse, parse_qs
import re

def scrape_discogs_seller(base_url):
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
        'Accept-Language': 'en-US,en;q=0.9',
        'Accept-Encoding': 'gzip, deflate, br',
        'Connection': 'keep-alive',
        'Upgrade-Insecure-Requests': '1',
        'Sec-Fetch-Dest': 'document',
        'Sec-Fetch-Mode': 'navigate',
        'Sec-Fetch-Site': 'none',
        'Sec-Fetch-User': '?1',
        'Cache-Control': 'max-age=0'
    }
    
    session = requests.Session()
    session.headers.update(headers)
    
    all_records = []
    page = 1
    
    while True:
        url = f"{base_url}&page={page}"
        print(f"Fetching page {page}...")
        
        try:
            response = session.get(url)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Find the table with listings
            listings_table = soup.find('table', class_='table_block mpitems push_down')
            if not listings_table:
                print("No listings table found")
                break
            
            rows = listings_table.find_all('tr', class_='shortcut_navigable')
            if not rows:
                print("No more records found")
                break
            
            for row in rows:
                record = {}
                
                # Extract artist and title
                title_cell = row.find('td', class_='item_description')
                if title_cell:
                    artist_elem = title_cell.find('a', class_='artist_name')
                    record['artist'] = artist_elem.text.strip() if artist_elem else ''
                    
                    title_elem = title_cell.find('a', class_='item_title')
                    record['title'] = title_elem.text.strip() if title_elem else ''
                    
                    # Extract label info
                    label_info = title_cell.find('span', class_='item_label_and_cat')
                    if label_info:
                        label_text = label_info.text.strip()
                        # Parse label and catalog number
                        parts = label_text.split(' - ')
                        record['label'] = parts[0] if parts else ''
                        record['catalog_number'] = parts[1] if len(parts) > 1 else ''
                
                # Extract format
                format_cell = row.find('td', class_='item_format')
                record['format'] = format_cell.text.strip() if format_cell else ''
                
                # Extract condition
                condition_cell = row.find('td', class_='item_condition')
                if condition_cell:
                    condition_spans = condition_cell.find_all('span', class_='condition_text')
                    if len(condition_spans) >= 2:
                        record['media_condition'] = condition_spans[0].text.strip()
                        record['sleeve_condition'] = condition_spans[1].text.strip()
                    else:
                        record['media_condition'] = ''
                        record['sleeve_condition'] = ''
                
                # Extract price
                price_cell = row.find('td', class_='item_price')
                if price_cell:
                    price_span = price_cell.find('span', class_='price')
                    record['price'] = price_span.text.strip() if price_span else ''
                
                # Extract listing ID
                listing_id = row.get('data-release-id', '')
                record['listing_id'] = listing_id
                
                all_records.append(record)
            
            # Check if there's a next page
            pagination = soup.find('div', class_='pagination')
            if pagination:
                next_link = pagination.find('a', string='Next')
                if not next_link or 'disabled' in next_link.get('class', []):
                    print(f"Reached last page (page {page})")
                    break
            else:
                print("No pagination found")
                break
            
            page += 1
            time.sleep(2)  # Be polite to the server
            
        except requests.RequestException as e:
            print(f"Error fetching page {page}: {e}")
            break
    
    return all_records

def save_to_csv(records, filename='discogs_records.csv'):
    if not records:
        print("No records to save")
        return
    
    fieldnames = ['artist', 'title', 'label', 'catalog_number', 'format', 
                  'media_condition', 'sleeve_condition', 'price', 'listing_id']
    
    with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(records)
    
    print(f"Saved {len(records)} records to {filename}")

if __name__ == "__main__":
    base_url = "https://www.discogs.com/seller/The_Record_Cellar/profile?format=Vinyl&format_desc=LP"
    
    print("Starting Discogs scraper...")
    records = scrape_discogs_seller(base_url)
    
    if records:
        save_to_csv(records)
        print(f"Successfully scraped {len(records)} vinyl records")
    else:
        print("No records were scraped")