#!/usr/bin/python3
"""
BPM Detection CLI Tool

A wrapper around aubio or librosa for detecting BPM (beats per minute) 
in audio files. Supports both individual files and directory processing.
"""

import argparse
import os
import sys
import json
import csv
from pathlib import Path
import subprocess
import re


def check_aubio():
    """Check if aubio is installed."""
    try:
        subprocess.run(['aubiotempo', '--help'], capture_output=True, check=True)
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        return False


def get_bpm_with_aubio(file_path):
    """Get BPM using aubio Python library or command line tool."""
    # Try Python aubio first
    try:
        import aubio
        import numpy as np
        
        # Read audio file
        samplerate = 44100
        hop_size = 512
        
        # Create aubio source
        s = aubio.source(str(file_path), samplerate, hop_size)
        samplerate = s.samplerate
        
        # Create tempo detection
        tempo = aubio.tempo("default", 1024, hop_size, samplerate)
        
        # Process file
        beats = []
        total_frames = 0
        while True:
            samples, read = s()
            is_beat = tempo(samples)
            if is_beat:
                this_beat = tempo.get_last_s()
                beats.append(this_beat)
            total_frames += read
            if read < hop_size:
                break
        
        # Calculate BPM
        if len(beats) > 1:
            # Calculate average interval between beats
            intervals = np.diff(beats)
            avg_interval = np.mean(intervals)
            bpm = 60.0 / avg_interval
            return float(bpm)
        return None
        
    except ImportError:
        # Fall back to command line tool
        try:
            result = subprocess.run(
                ['aubiotempo', str(file_path)],
                capture_output=True,
                text=True,
                check=True
            )
            # aubiotempo outputs beat timestamps, one per line
            lines = result.stdout.strip().split('\n')
            beats = [float(line) for line in lines if line.strip()]
            
            if len(beats) > 1:
                # Calculate average interval between beats
                intervals = [beats[i+1] - beats[i] for i in range(len(beats)-1)]
                avg_interval = sum(intervals) / len(intervals)
                bpm = 60.0 / avg_interval
                return float(bpm)
            return None
        except (subprocess.CalledProcessError, FileNotFoundError):
            return None


def get_bpm_with_librosa(file_path):
    """Get BPM using librosa library."""
    try:
        import librosa
        import numpy as np
        y, sr = librosa.load(file_path)
        tempo, _ = librosa.beat.beat_track(y=y, sr=sr)
        # Handle numpy array to scalar conversion
        if isinstance(tempo, np.ndarray):
            tempo = tempo.item()
        return float(tempo)
    except ImportError:
        print("Error: librosa not installed. Install with: pip install librosa")
        sys.exit(1)
    except Exception as e:
        print(f"Error processing {file_path}: {e}", file=sys.stderr)
        return None


def process_file(file_path, use_aubio=True):
    """Process a single audio file and return BPM info."""
    file_path = Path(file_path)
    if not file_path.exists():
        return None
    
    if use_aubio:
        bpm = get_bpm_with_aubio(file_path)
    else:
        bpm = get_bpm_with_librosa(file_path)
    
    return {
        'file': str(file_path),
        'filename': file_path.name,
        'bpm': round(bpm, 2) if bpm else None
    }


def process_directory(directory, extensions=None, use_aubio=True):
    """Process all audio files in a directory."""
    if extensions is None:
        extensions = ['.mp3', '.wav', '.flac', '.m4a', '.ogg']
    
    directory = Path(directory)
    results = []
    
    for file_path in directory.rglob('*'):
        if file_path.is_file() and file_path.suffix.lower() in extensions:
            result = process_file(file_path, use_aubio)
            if result:
                results.append(result)
    
    return results


def output_results(results, format='plain', output_file=None):
    """Output results in the specified format."""
    if format == 'json':
        output = json.dumps(results, indent=2)
    elif format == 'csv':
        if results:
            from io import StringIO
            output_buffer = StringIO()
            writer = csv.DictWriter(output_buffer, fieldnames=['filename', 'bpm', 'file'])
            writer.writeheader()
            writer.writerows(results)
            output = output_buffer.getvalue()
        else:
            output = ""
    else:  # plain
        output_lines = []
        for result in results:
            if result['bpm']:
                output_lines.append(f"{result['bpm']:6.2f} BPM - {result['filename']}")
            else:
                output_lines.append(f"   N/A BPM - {result['filename']}")
        output = '\n'.join(output_lines)
    
    if output_file:
        with open(output_file, 'w') as f:
            f.write(output)
    else:
        print(output)


def main():
    parser = argparse.ArgumentParser(
        description='Detect BPM (beats per minute) in audio files',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s song.mp3                    # Analyze single file
  %(prog)s -d music/                   # Analyze all files in directory
  %(prog)s -d music/ -f json           # Output as JSON
  %(prog)s *.mp3 -o results.csv -f csv # Save multiple files to CSV
        """
    )
    
    parser.add_argument('files', nargs='*', help='Audio file(s) to analyze')
    parser.add_argument('-d', '--directory', help='Process all audio files in directory')
    parser.add_argument('-f', '--format', choices=['plain', 'json', 'csv'], 
                        default='plain', help='Output format (default: plain)')
    parser.add_argument('-o', '--output', help='Save output to file')
    parser.add_argument('--librosa', action='store_true', 
                        help='Use librosa instead of aubio')
    parser.add_argument('-e', '--extensions', nargs='+', 
                        default=['.mp3', '.wav', '.flac', '.m4a', '.ogg'],
                        help='File extensions to process (default: .mp3 .wav .flac .m4a .ogg)')
    
    args = parser.parse_args()
    
    # Check if aubio is available
    use_aubio = not args.librosa
    if use_aubio and not check_aubio():
        print("Warning: aubio not found. Install with: brew install aubio")
        print("Falling back to librosa...")
        use_aubio = False
    
    results = []
    
    # Process directory if specified
    if args.directory:
        results.extend(process_directory(args.directory, args.extensions, use_aubio))
    
    # Process individual files
    for file_path in args.files:
        # Handle wildcards
        from glob import glob
        matched_files = glob(file_path)
        if matched_files:
            for matched_file in matched_files:
                result = process_file(matched_file, use_aubio)
                if result:
                    results.append(result)
        else:
            result = process_file(file_path, use_aubio)
            if result:
                results.append(result)
    
    if not results:
        print("No audio files found or processed.", file=sys.stderr)
        sys.exit(1)
    
    # Sort by BPM
    results.sort(key=lambda x: x['bpm'] if x['bpm'] else 0)
    
    output_results(results, args.format, args.output)


if __name__ == '__main__':
    main()