# Discogs Batch Search Tool Usage

This tool reads a wishlist of records from a CSV or JSON file and searches Discogs for all of them, showing you where to buy each one.

## Basic Usage

```bash
python discogs_batch_search.py <input_file> [options]
```

## Options

- `-o, --output`: Output CSV filename (default: batch_search_results_[timestamp].csv)
- `-m, --max-results`: Maximum results per item (default: 5)
- `-d, --delay`: Delay between searches in seconds (default: 1.0)
- `-s, --summary`: Show summary only, no detailed results

## Input File Formats

### CSV Format

The CSV file should have these columns (case-insensitive):
- `artist` - Artist name
- `title` (or `album`) - Album title
- `format` - Format type (optional, defaults to "Vinyl")
- `year` - Release year (optional)
- `notes` - Your notes (optional)

Example CSV:
```csv
artist,title,format,year,notes
Miles Davis,Kind of Blue,LP,1959,Classic modal jazz
The Beatles,Abbey Road,LP,1969,Looking for UK pressing
```

### JSON Format

The JSON file can be:
1. An array of records
2. An object with a "wishlist" or "records" key

Example JSON:
```json
{
  "wishlist": [
    {
      "artist": "Miles Davis",
      "title": "Kind of Blue",
      "format": "LP",
      "year": "1959",
      "notes": "Classic modal jazz"
    }
  ]
}
```

## Examples

### Search from CSV wishlist
```bash
python discogs_batch_search.py my_wishlist.csv
```

### Search from JSON with custom output
```bash
python discogs_batch_search.py wishlist.json -o found_records.csv
```

### Quick search with fewer results per item
```bash
python discogs_batch_search.py wishlist.csv -m 3 -d 0.5
```

### Summary only (no CSV output)
```bash
python discogs_batch_search.py wishlist.csv -s
```

## Output

The tool provides:
1. **Console output** showing:
   - Progress for each search
   - Number of matches found
   - Summary of all available copies
   - Direct marketplace URLs

2. **CSV output** containing:
   - Original wishlist info (artist, title, notes)
   - Found release details (format, year, label, country)
   - Marketplace data (number for sale, lowest price)
   - Direct URLs to buy

## Example Workflow

1. Create a wishlist CSV:
```csv
artist,title
Curtis Mayfield,Superfly
Marvin Gaye,What's Going On
Stevie Wonder,Songs in the Key of Life
```

2. Run the batch search:
```bash
python discogs_batch_search.py wishlist.csv -o results.csv
```

3. Open results.csv to see all available copies with prices and URLs

## Tips

- Use specific format filters (LP, 12", 7") to narrow results
- Add year to get more accurate matches
- The delay option helps avoid rate limiting on large lists
- Check the marketplace URLs for detailed condition info and seller ratings