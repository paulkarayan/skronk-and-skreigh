# Discogs Album Search Tool Usage

This tool searches Discogs for specific albums and provides marketplace URLs where you can buy them.

## Basic Usage

```bash
python discogs_album_search.py [options]
```

## Options

- `-q, --query`: General search query
- `-a, --artist`: Artist name
- `-t, --title`: Album/release title  
- `-f, --format`: Format filter (e.g., "Vinyl", "LP", "12\"", "7\"")
- `-m, --max-results`: Maximum number of results (default: 20)
- `-o, --output`: Output CSV filename
- `-d, --details`: Show detailed release URLs

## Examples

### Search for a specific album on LP
```bash
python discogs_album_search.py -a "Pink Floyd" -t "Dark Side of the Moon" -f "LP"
```

### Search for all vinyl by an artist
```bash
python discogs_album_search.py -a "The Beatles" -f "Vinyl" -m 50
```

### Search for 12" singles
```bash
python discogs_album_search.py -q "disco" -f "12\"" -m 30
```

### Search and save to CSV
```bash
python discogs_album_search.py -a "Miles Davis" -t "Kind of Blue" -f "LP" -o miles_davis_results.csv
```

### General text search
```bash
python discogs_album_search.py -q "blue note jazz" -f "LP" -m 25
```

## Format Options

Common format filters:
- `"Vinyl"` - All vinyl records
- `"LP"` - Full-length albums
- `"12\""` - 12-inch singles
- `"7\""` - 7-inch singles
- `"10\""` - 10-inch records
- `"CD"` - Compact discs
- `"Cassette"` - Cassette tapes

## Output

The tool provides:
1. Artist and album title
2. Format, label, and country
3. Community stats (how many people have/want it)
4. Number of copies for sale and lowest price
5. Direct marketplace URL to view all sellers

The CSV output includes all this information for easy sorting and filtering.