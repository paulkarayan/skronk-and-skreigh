# BPM Detection Tools

## Usage

### Simple BPM Detection (`bpm.py`)
```bash
# Single file
./bpm.py song.mp3

# Directory
./bpm.py -d music/

# Output as JSON
./bpm.py -d music/ -f json
```

### Multi-Method BPM Detection (`bpm_multi.py`)
```bash
# Analyze directory using middle 30 seconds of each file
./bpm_multi.py -d ROWAN --middle

# Analyze with specific methods
./bpm_multi.py -d music/ --methods librosa_percussive librosa_tempogram

# Custom duration and offset
./bpm_multi.py song.mp3 --duration 60 --offset 30

# Specify output prefix
./bpm_multi.py -d music/ -o my_music_analysis
```

All results are saved to `bpm-results/` directory.

## Tips

1. Use `--middle` flag to analyze the middle portion of songs (avoids intros/outros)
2. Check the summary report for files with high variance
3. When in doubt, listen to the song and tap along to verify
4. Traditional Irish tunes often show as either ~100 BPM or ~200 BPM (half/double time)