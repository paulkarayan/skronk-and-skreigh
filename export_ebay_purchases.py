#!/usr/bin/env python3
"""
eBay Purchase History Exporter

This script helps export your eBay purchase history, focusing on vinyl/LP purchases.
It provides both automated and manual export options.
"""

import json
import csv
import time
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
import requests
from bs4 import BeautifulSoup

def manual_export_instructions():
    """Provide instructions for manual export."""
    print("\n" + "="*60)
    print("MANUAL EXPORT INSTRUCTIONS")
    print("="*60)
    print("\n1. Go to: https://www.ebay.com/mye/myebay/purchase")
    print("2. Sign in to your eBay account")
    print("3. Use browser's Developer Tools (F12)")
    print("4. Go to Network tab")
    print("5. Look for API calls that contain your purchase data")
    print("6. Right-click on the response and save as JSON")
    print("\nAlternatively:")
    print("1. Use eBay's Download Purchase History:")
    print("   - Go to My eBay > Purchase History")
    print("   - Look for 'Download report' option")
    print("   - Select date range (Jan 2024 - Present)")
    print("   - Download as CSV")

def scrape_with_selenium():
    """Attempt to scrape eBay purchase history using Selenium."""
    print("\nAutomated Scraping Method")
    print("-" * 30)
    print("\nNOTE: This will open a browser window.")
    print("You'll need to manually sign in to eBay.")
    print("After signing in, the script will attempt to scrape your purchases.")
    
    input("\nPress Enter to continue...")
    
    # Set up Chrome driver
    options = webdriver.ChromeOptions()
    options.add_argument('--disable-blink-features=AutomationControlled')
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option('useAutomationExtension', False)
    
    driver = webdriver.Chrome(options=options)
    
    try:
        # Navigate to eBay purchase history
        driver.get("https://www.ebay.com/mye/myebay/purchase")
        
        print("\nPlease sign in to your eBay account in the browser window.")
        print("After signing in, press Enter here to continue...")
        input()
        
        # Wait for purchase history to load
        wait = WebDriverWait(driver, 30)
        
        # Try to find purchase items
        purchases = []
        
        # Look for purchase cards/items
        try:
            # Wait for purchase items to load
            wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "[data-testid*='purchase'], .m-purchase-card, .purchase-card")))
            
            # Find all purchase items
            purchase_elements = driver.find_elements(By.CSS_SELECTOR, "[data-testid*='purchase'], .m-purchase-card, .purchase-card")
            
            print(f"\nFound {len(purchase_elements)} purchase items")
            
            for element in purchase_elements:
                try:
                    # Extract purchase details
                    title = element.find_element(By.CSS_SELECTOR, "h3, .item-title, [data-testid*='title']").text
                    
                    # Check if it's a vinyl/LP purchase
                    if any(keyword in title.lower() for keyword in ['vinyl', 'lp', 'record', '12"', '7"', '45 rpm', '33 rpm']):
                        purchase = {
                            'title': title,
                            'date': 'N/A',
                            'price': 'N/A',
                            'seller': 'N/A',
                            'order_number': 'N/A'
                        }
                        
                        # Try to extract more details
                        try:
                            purchase['price'] = element.find_element(By.CSS_SELECTOR, ".price, [data-testid*='price']").text
                        except:
                            pass
                        
                        try:
                            purchase['date'] = element.find_element(By.CSS_SELECTOR, ".purchase-date, [data-testid*='date']").text
                        except:
                            pass
                        
                        try:
                            purchase['seller'] = element.find_element(By.CSS_SELECTOR, ".seller-name, [data-testid*='seller']").text
                        except:
                            pass
                        
                        purchases.append(purchase)
                        print(f"Found vinyl purchase: {title[:50]}...")
                
                except Exception as e:
                    print(f"Error extracting purchase details: {e}")
                    continue
            
            # Scroll to load more items
            last_height = driver.execute_script("return document.body.scrollHeight")
            while True:
                driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                time.sleep(2)
                new_height = driver.execute_script("return document.body.scrollHeight")
                if new_height == last_height:
                    break
                last_height = new_height
        
        except TimeoutException:
            print("\nCouldn't find purchase items. The page structure might have changed.")
            print("Falling back to manual export instructions...")
            manual_export_instructions()
            return []
        
        return purchases
    
    finally:
        input("\nPress Enter to close the browser...")
        driver.quit()

def parse_ebay_json(json_file):
    """Parse eBay JSON export file."""
    try:
        with open(json_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        purchases = []
        
        # The structure depends on how eBay exports data
        # This is a general parser that tries different structures
        
        # Try to find purchase array in data
        if isinstance(data, list):
            items = data
        elif isinstance(data, dict):
            # Look for common keys
            for key in ['purchases', 'items', 'transactions', 'orders']:
                if key in data:
                    items = data[key]
                    break
            else:
                items = []
        
        for item in items:
            # Extract relevant fields for vinyl purchases
            title = item.get('title', item.get('itemTitle', ''))
            
            if any(keyword in title.lower() for keyword in ['vinyl', 'lp', 'record', '12"', '7"', '45 rpm', '33 rpm']):
                purchase = {
                    'title': title,
                    'date': item.get('purchaseDate', item.get('date', 'N/A')),
                    'price': item.get('price', item.get('totalPrice', 'N/A')),
                    'seller': item.get('seller', item.get('sellerName', 'N/A')),
                    'order_number': item.get('orderId', item.get('transactionId', 'N/A'))
                }
                purchases.append(purchase)
        
        return purchases
    
    except Exception as e:
        print(f"Error parsing JSON file: {e}")
        return []

def save_purchases(purchases, filename='ebay_vinyl_purchases.csv'):
    """Save purchases to CSV file."""
    if not purchases:
        print("\nNo vinyl purchases found to save.")
        return
    
    with open(filename, 'w', newline='', encoding='utf-8') as f:
        fieldnames = ['title', 'date', 'price', 'seller', 'order_number']
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        
        writer.writeheader()
        writer.writerows(purchases)
    
    print(f"\n✓ Saved {len(purchases)} vinyl purchases to {filename}")

def main():
    """Main function."""
    print("eBay Vinyl/LP Purchase Exporter")
    print("=" * 40)
    
    print("\nOptions:")
    print("1. Automated scraping (requires Chrome)")
    print("2. Parse exported JSON file")
    print("3. Manual export instructions")
    
    choice = input("\nSelect option (1-3): ").strip()
    
    purchases = []
    
    if choice == '1':
        try:
            purchases = scrape_with_selenium()
        except Exception as e:
            print(f"\nError during automated scraping: {e}")
            print("\nFalling back to manual instructions...")
            manual_export_instructions()
    
    elif choice == '2':
        json_file = input("\nEnter path to eBay JSON export file: ").strip()
        purchases = parse_ebay_json(json_file)
        
        if purchases:
            print(f"\nFound {len(purchases)} vinyl purchases")
            for i, p in enumerate(purchases[:5], 1):
                print(f"{i}. {p['title'][:60]}... - {p['date']}")
            
            if len(purchases) > 5:
                print(f"... and {len(purchases) - 5} more")
    
    else:
        manual_export_instructions()
    
    if purchases:
        save_purchases(purchases)
        
        # Display summary
        print("\nSummary:")
        print(f"Total vinyl purchases: {len(purchases)}")
        
        # Try to calculate total spent
        total = 0
        for p in purchases:
            try:
                price = p['price'].replace('$', '').replace(',', '')
                total += float(price)
            except:
                pass
        
        if total > 0:
            print(f"Approximate total spent: ${total:.2f}")

if __name__ == '__main__':
    main()