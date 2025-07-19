# Discogs Seller Data Extraction

Unfortunately, Discogs has strong anti-scraping measures (Cloudflare protection) that prevent automated extraction of the data. Here are your options:

## Option 1: Use Discogs API (Recommended)

1. Sign up for a Discogs account
2. Get an API token from https://www.discogs.com/settings/developers
3. Use the API to fetch seller inventory

## Option 2: Browser Extension

Use a browser extension like:
- Web Scraper (Chrome)
- Data Miner (Chrome)
- Instant Data Scraper (Chrome)

## Option 3: Manual Browser Console Script

1. Open the seller page in your browser
2. Open Developer Console (F12)
3. Use this script to extract data from the current page:

```javascript
// Run this in the browser console on each page
const records = [];
document.querySelectorAll('tr.shortcut_navigable').forEach(row => {
    const record = {
        artist: row.querySelector('.artist_name')?.textContent.trim() || '',
        title: row.querySelector('.item_title')?.textContent.trim() || '',
        label: row.querySelector('.item_label_and_cat')?.textContent.split(' - ')[0]?.trim() || '',
        catalog: row.querySelector('.item_label_and_cat')?.textContent.split(' - ')[1]?.trim() || '',
        format: row.querySelector('.item_format')?.textContent.trim() || '',
        mediaCondition: row.querySelectorAll('.condition_text')[0]?.textContent.trim() || '',
        sleeveCondition: row.querySelectorAll('.condition_text')[1]?.textContent.trim() || '',
        price: row.querySelector('.price')?.textContent.trim() || ''
    };
    records.push(record);
});

// Convert to CSV
const csv = [
    ['Artist', 'Title', 'Label', 'Catalog', 'Format', 'Media Condition', 'Sleeve Condition', 'Price'],
    ...records.map(r => [r.artist, r.title, r.label, r.catalog, r.format, r.mediaCondition, r.sleeveCondition, r.price])
].map(row => row.map(cell => `"${cell}"`).join(',')).join('\n');

// Download CSV
const blob = new Blob([csv], { type: 'text/csv' });
const url = URL.createObjectURL(blob);
const a = document.createElement('a');
a.href = url;
a.download = 'discogs_records_page.csv';
a.click();
```

You'll need to run this script on each page and then combine the CSV files.

## Option 4: Use Discogs CSV Export (If Available)

Some Discogs seller accounts offer a CSV export feature. Check if The Record Cellar has this option enabled on their profile.

## Python Script to Combine Multiple CSV Files

If you extract multiple CSV files (one per page), use this script to combine them:

```python
import pandas as pd
import glob

# Get all CSV files
csv_files = glob.glob('discogs_records_page*.csv')

# Read and combine
dfs = []
for file in csv_files:
    df = pd.read_csv(file)
    dfs.append(df)

# Combine all dataframes
combined_df = pd.concat(dfs, ignore_index=True)

# Remove duplicates if any
combined_df = combined_df.drop_duplicates()

# Save to final CSV
combined_df.to_csv('all_discogs_records.csv', index=False)
print(f"Combined {len(csv_files)} files into all_discogs_records.csv")
print(f"Total records: {len(combined_df)}")
```