import time
import csv
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import NoSuchElementException, TimeoutException

def scrape_with_selenium(base_url):
    # Setup Chrome options
    options = webdriver.ChromeOptions()
    options.add_argument('--headless')  # Run in background
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument('--disable-blink-features=AutomationControlled')
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option('useAutomationExtension', False)
    
    driver = webdriver.Chrome(options=options)
    driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
    
    all_records = []
    page = 1
    
    try:
        while True:
            url = f"{base_url}&page={page}"
            print(f"Fetching page {page}...")
            
            driver.get(url)
            time.sleep(3)  # Wait for page to load
            
            # Check if we have listings
            try:
                # Wait for the table to load
                WebDriverWait(driver, 10).until(
                    EC.presence_of_element_located((By.CLASS_NAME, "mpitems"))
                )
                
                # Find all item rows
                rows = driver.find_elements(By.CSS_SELECTOR, "tr.shortcut_navigable")
                
                if not rows:
                    print("No more records found")
                    break
                
                for row in rows:
                    record = {}
                    
                    try:
                        # Artist and Title
                        artist_elem = row.find_element(By.CSS_SELECTOR, "a.artist_name")
                        record['artist'] = artist_elem.text.strip()
                    except:
                        record['artist'] = ''
                    
                    try:
                        title_elem = row.find_element(By.CSS_SELECTOR, "a.item_title")
                        record['title'] = title_elem.text.strip()
                    except:
                        record['title'] = ''
                    
                    try:
                        # Label and catalog
                        label_elem = row.find_element(By.CSS_SELECTOR, "span.item_label_and_cat")
                        label_text = label_elem.text.strip()
                        parts = label_text.split(' - ')
                        record['label'] = parts[0] if parts else ''
                        record['catalog_number'] = parts[1] if len(parts) > 1 else ''
                    except:
                        record['label'] = ''
                        record['catalog_number'] = ''
                    
                    try:
                        # Format
                        format_elem = row.find_element(By.CSS_SELECTOR, "td.item_format")
                        record['format'] = format_elem.text.strip()
                    except:
                        record['format'] = ''
                    
                    try:
                        # Conditions
                        condition_elems = row.find_elements(By.CSS_SELECTOR, "span.condition_text")
                        if len(condition_elems) >= 2:
                            record['media_condition'] = condition_elems[0].text.strip()
                            record['sleeve_condition'] = condition_elems[1].text.strip()
                        else:
                            record['media_condition'] = ''
                            record['sleeve_condition'] = ''
                    except:
                        record['media_condition'] = ''
                        record['sleeve_condition'] = ''
                    
                    try:
                        # Price
                        price_elem = row.find_element(By.CSS_SELECTOR, "span.price")
                        record['price'] = price_elem.text.strip()
                    except:
                        record['price'] = ''
                    
                    all_records.append(record)
                
                # Check for next page
                try:
                    next_button = driver.find_element(By.LINK_TEXT, "Next")
                    if 'disabled' in next_button.get_attribute('class'):
                        print(f"Reached last page (page {page})")
                        break
                except:
                    print(f"No next button found, assuming last page (page {page})")
                    break
                
                page += 1
                time.sleep(2)  # Be polite
                
            except TimeoutException:
                print(f"Timeout on page {page}, possibly no more pages")
                break
            
    finally:
        driver.quit()
    
    return all_records

def save_to_csv(records, filename='discogs_records.csv'):
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
    
    print("Starting Discogs Selenium scraper...")
    print("Note: This requires Chrome and ChromeDriver to be installed")
    
    try:
        records = scrape_with_selenium(base_url)
        
        if records:
            save_to_csv(records)
            print(f"Successfully scraped {len(records)} vinyl records")
        else:
            print("No records were scraped")
    except Exception as e:
        print(f"Error: {e}")
        print("Make sure you have Chrome and ChromeDriver installed")