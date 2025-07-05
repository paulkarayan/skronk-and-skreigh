#!/usr/bin/python3
"""
Multi-method BPM Detection Tool

Uses multiple BPM detection methods and outputs results to separate JSON files.
Supports librosa (multiple variants) and essentia.
"""

import argparse
import os
import sys
import json
from pathlib import Path
import warnings
warnings.filterwarnings('ignore')


def get_bpm_librosa_standard(file_path, duration=None, offset=None):
    """Standard librosa beat tracking."""
    try:
        import librosa
        import numpy as np
        
        y, sr = librosa.load(str(file_path), duration=duration, offset=offset)
        tempo, _ = librosa.beat.beat_track(y=y, sr=sr)
        
        if isinstance(tempo, np.ndarray):
            tempo = tempo.item()
        
        return float(tempo)
    except Exception as e:
        print(f"Error with librosa_standard on {file_path}: {e}", file=sys.stderr)
        return None


def get_bpm_librosa_percussive(file_path, duration=None, offset=None):
    """Librosa with percussive separation."""
    try:
        import librosa
        import numpy as np
        
        y, sr = librosa.load(str(file_path), duration=duration, offset=offset)
        y_percussive = librosa.effects.percussive(y, margin=3.0)
        tempo, _ = librosa.beat.beat_track(y=y_percussive, sr=sr)
        
        if isinstance(tempo, np.ndarray):
            tempo = tempo.item()
        
        return float(tempo)
    except Exception as e:
        print(f"Error with librosa_percussive on {file_path}: {e}", file=sys.stderr)
        return None


def get_bpm_librosa_onset(file_path, duration=None, offset=None):
    """Librosa with onset-based detection."""
    try:
        import librosa
        import numpy as np
        
        y, sr = librosa.load(str(file_path), duration=duration, offset=offset)
        
        # Calculate onset strength with specific parameters
        onset_env = librosa.onset.onset_strength(
            y=y, 
            sr=sr,
            aggregate=np.median,
            fmax=8000
        )
        
        tempo, _ = librosa.beat.beat_track(
            onset_envelope=onset_env,
            sr=sr,
            hop_length=512
        )
        
        if isinstance(tempo, np.ndarray):
            tempo = tempo.item()
        
        return float(tempo)
    except Exception as e:
        print(f"Error with librosa_onset on {file_path}: {e}", file=sys.stderr)
        return None


def get_bpm_librosa_tempogram(file_path, duration=None, offset=None):
    """Librosa using tempogram method."""
    try:
        import librosa
        import numpy as np
        
        y, sr = librosa.load(str(file_path), duration=duration, offset=offset)
        hop_length = 512
        
        onset_env = librosa.onset.onset_strength(y=y, sr=sr, hop_length=hop_length)
        tempo = librosa.beat.tempo(onset_envelope=onset_env, sr=sr, hop_length=hop_length)
        
        if isinstance(tempo, np.ndarray):
            tempo = tempo[0]
        
        return float(tempo)
    except Exception as e:
        print(f"Error with librosa_tempogram on {file_path}: {e}", file=sys.stderr)
        return None


def get_bpm_essentia(file_path, duration=None, offset=None):
    """Essentia RhythmExtractor2013 method."""
    try:
        import essentia.standard as es
        
        # Load audio
        if duration or offset:
            # Load full audio first
            loader = es.MonoLoader(filename=str(file_path), sampleRate=44100)
            audio = loader()
            
            # Calculate sample indices
            sr = 44100
            start_sample = int(offset * sr) if offset else 0
            end_sample = int((offset + duration) * sr) if duration and offset else (
                int(duration * sr) if duration else len(audio)
            )
            
            # Slice audio
            audio = audio[start_sample:end_sample]
        else:
            audio = es.MonoLoader(filename=str(file_path), sampleRate=44100)()
        
        # Use RhythmExtractor2013
        rhythm_extractor = es.RhythmExtractor2013(method="multifeature")
        bpm, beats, beats_confidence, _, beats_intervals = rhythm_extractor(audio)
        
        return float(bpm)
    except Exception as e:
        print(f"Error with essentia on {file_path}: {e}", file=sys.stderr)
        return None


def get_bpm_essentia_percival(file_path, duration=None, offset=None):
    """Essentia using Percival method."""
    try:
        import essentia.standard as es
        
        # Load audio
        if duration or offset:
            loader = es.MonoLoader(filename=str(file_path), sampleRate=44100)
            audio = loader()
            
            sr = 44100
            start_sample = int(offset * sr) if offset else 0
            end_sample = int((offset + duration) * sr) if duration and offset else (
                int(duration * sr) if duration else len(audio)
            )
            
            audio = audio[start_sample:end_sample]
        else:
            audio = es.MonoLoader(filename=str(file_path), sampleRate=44100)()
        
        # Use PercivalBpmEstimator
        bpm_estimator = es.PercivalBpmEstimator()
        bpm = bpm_estimator(audio)
        
        return float(bpm)
    except Exception as e:
        print(f"Error with essentia_percival on {file_path}: {e}", file=sys.stderr)
        return None


# Define all available methods
METHODS = {
    'librosa_standard': get_bpm_librosa_standard,
    'librosa_percussive': get_bpm_librosa_percussive,
    'librosa_onset': get_bpm_librosa_onset,
    'librosa_tempogram': get_bpm_librosa_tempogram,
    'essentia': get_bpm_essentia,
    'essentia_percival': get_bpm_essentia_percival
}


def check_dependencies():
    """Check which dependencies are available."""
    available_methods = []
    
    # Check librosa
    try:
        import librosa
        available_methods.extend(['librosa_standard', 'librosa_percussive', 
                                'librosa_onset', 'librosa_tempogram'])
    except ImportError:
        print("Warning: librosa not found. Install with: pip install librosa", file=sys.stderr)
    
    # Check essentia
    try:
        import essentia
        available_methods.extend(['essentia', 'essentia_percival'])
    except (ImportError, AttributeError) as e:
        print(f"Warning: essentia not available. {type(e).__name__}: {e}", file=sys.stderr)
        print("Note: essentia may have compatibility issues with NumPy 2.x", file=sys.stderr)
    
    return available_methods


def process_file(file_path, methods, duration=None, offset=None):
    """Process a single file with multiple methods."""
    file_path = Path(file_path)
    if not file_path.exists():
        return None
    
    results = {
        'file': str(file_path),
        'filename': file_path.name,
        'duration': duration,
        'offset': offset
    }
    
    for method_name in methods:
        if method_name in METHODS:
            bpm = METHODS[method_name](file_path, duration=duration, offset=offset)
            results[method_name] = round(bpm, 2) if bpm else None
    
    return results


def process_directory(directory, extensions=None, methods=None, duration=None, offset=None):
    """Process all audio files in a directory."""
    if extensions is None:
        extensions = ['.mp3', '.wav', '.flac', '.m4a', '.ogg']
    
    directory = Path(directory)
    results = []
    
    for file_path in sorted(directory.rglob('*')):
        if file_path.is_file() and file_path.suffix.lower() in extensions:
            print(f"Processing {file_path.name}...", file=sys.stderr)
            result = process_file(file_path, methods, duration=duration, offset=offset)
            if result:
                results.append(result)
    
    return results


def generate_summary_report(results, methods, output_file):
    """Generate a summary report of BPM detection results."""
    with open(output_file, 'w') as f:
        f.write("BPM Detection Summary Report\n")
        f.write("=" * 80 + "\n\n")
        
        f.write(f"Total files analyzed: {len(results)}\n")
        f.write(f"Methods used: {', '.join(sorted(methods))}\n\n")
        
        # Calculate statistics for each method
        f.write("Method Statistics:\n")
        f.write("-" * 40 + "\n")
        for method in sorted(methods):
            bpms = [r[method] for r in results if method in r and r[method] is not None]
            if bpms:
                avg_bpm = sum(bpms) / len(bpms)
                min_bpm = min(bpms)
                max_bpm = max(bpms)
                f.write(f"{method}:\n")
                f.write(f"  Average BPM: {avg_bpm:.1f}\n")
                f.write(f"  Range: {min_bpm:.1f} - {max_bpm:.1f}\n")
                f.write(f"  Files processed: {len(bpms)}/{len(results)}\n\n")
        
        # Show files with high variance between methods
        f.write("\nFiles with High Variance (>20 BPM difference):\n")
        f.write("-" * 60 + "\n")
        high_variance_count = 0
        for result in results:
            bpms = [result[m] for m in methods if m in result and result[m] is not None]
            if len(bpms) > 1:
                variance = max(bpms) - min(bpms)
                if variance > 20:
                    high_variance_count += 1
                    f.write(f"\n{result['filename']}:\n")
                    for method in sorted(methods):
                        if method in result and result[method] is not None:
                            f.write(f"  {method}: {result[method]:.1f} BPM\n")
                    f.write(f"  Variance: {variance:.1f} BPM\n")
        
        if high_variance_count == 0:
            f.write("No files with high variance found.\n")
        
        # Show method agreement
        f.write("\n\nMethod Agreement Analysis:\n")
        f.write("-" * 40 + "\n")
        
        # Check which methods tend to agree
        if len(methods) > 1:
            agreement_threshold = 5  # BPM difference threshold for "agreement"
            method_pairs = []
            method_list = sorted(methods)
            
            for i in range(len(method_list)):
                for j in range(i + 1, len(method_list)):
                    m1, m2 = method_list[i], method_list[j]
                    agreements = 0
                    total = 0
                    
                    for result in results:
                        if m1 in result and m2 in result and result[m1] and result[m2]:
                            total += 1
                            if abs(result[m1] - result[m2]) <= agreement_threshold:
                                agreements += 1
                    
                    if total > 0:
                        agreement_pct = (agreements / total) * 100
                        method_pairs.append((m1, m2, agreement_pct, agreements, total))
            
            # Sort by agreement percentage
            method_pairs.sort(key=lambda x: x[2], reverse=True)
            
            for m1, m2, pct, agreements, total in method_pairs:
                f.write(f"{m1} vs {m2}: {pct:.1f}% agreement ({agreements}/{total} files)\n")
        
        f.write("\n" + "=" * 80 + "\n")
        f.write("Report generated successfully.\n")
    
    print(f"\nSummary report saved to {output_file}")
    
    # Also print key findings to console
    print("\n" + "=" * 60)
    print("BPM DETECTION SUMMARY")
    print("=" * 60)
    print(f"Files analyzed: {len(results)}")
    print(f"Methods used: {', '.join(sorted(methods))}")
    
    # Count high variance files
    high_var_files = []
    for result in results:
        bpms = [result[m] for m in methods if m in result and result[m] is not None]
        if len(bpms) > 1 and (max(bpms) - min(bpms)) > 20:
            high_var_files.append((result['filename'], max(bpms) - min(bpms)))
    
    if high_var_files:
        print(f"\nFiles with high BPM variance (>20 BPM): {len(high_var_files)}")
        high_var_files.sort(key=lambda x: x[1], reverse=True)
        for filename, variance in high_var_files[:5]:  # Show top 5
            print(f"  - {filename}: {variance:.1f} BPM difference")
    
    print("\nAll results saved to bpm-results/")
    print("=" * 60)


def save_results_by_method(results, output_prefix):
    """Save results to separate JSON files for each method."""
    if not results:
        return
    
    # Ensure bpm-results directory exists
    output_dir = Path('bpm-results')
    output_dir.mkdir(exist_ok=True)
    
    # Get all methods present in results
    all_methods = set()
    for result in results:
        all_methods.update([k for k in result.keys() 
                          if k not in ['file', 'filename', 'duration', 'offset']])
    
    # Save combined results
    combined_file = output_dir / f"{output_prefix}_all_methods.json"
    with open(combined_file, 'w') as f:
        json.dump(results, f, indent=2)
    print(f"Saved combined results to {combined_file}")
    
    # Save per-method results
    for method in sorted(all_methods):
        method_results = []
        for result in results:
            if method in result and result[method] is not None:
                method_results.append({
                    'file': result['file'],
                    'filename': result['filename'],
                    'bpm': result[method]
                })
        
        if method_results:
            # Sort by BPM
            method_results.sort(key=lambda x: x['bpm'])
            
            method_file = output_dir / f"{output_prefix}_{method}.json"
            with open(method_file, 'w') as f:
                json.dump(method_results, f, indent=2)
            print(f"Saved {method} results to {method_file}")
    
    # Generate and save summary report
    summary_file = output_dir / f"{output_prefix}_summary.txt"
    generate_summary_report(results, all_methods, summary_file)


def main():
    parser = argparse.ArgumentParser(
        description='Multi-method BPM detection tool',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s song.mp3                     # Analyze with all methods
  %(prog)s -d music/                    # Analyze directory
  %(prog)s -d music/ --methods librosa_percussive essentia
  %(prog)s song.mp3 --middle            # Use middle 30 seconds
  %(prog)s song.mp3 --duration 60 --offset 30  # Custom segment
        """
    )
    
    parser.add_argument('files', nargs='*', help='Audio file(s) to analyze')
    parser.add_argument('-d', '--directory', help='Process all audio files in directory')
    parser.add_argument('-o', '--output', default='bpm_results', 
                        help='Output file prefix (default: bpm_results)')
    parser.add_argument('--methods', nargs='+', choices=list(METHODS.keys()),
                        help='Specific methods to use')
    parser.add_argument('--middle', action='store_true',
                        help='Use middle 30 seconds of file')
    parser.add_argument('--duration', type=float,
                        help='Duration in seconds to analyze')
    parser.add_argument('--offset', type=float,
                        help='Offset in seconds from start')
    parser.add_argument('-e', '--extensions', nargs='+', 
                        default=['.mp3', '.wav', '.flac', '.m4a', '.ogg'],
                        help='File extensions to process')
    
    args = parser.parse_args()
    
    # Check available methods
    available_methods = check_dependencies()
    if not available_methods:
        print("Error: No BPM detection libraries found. Install librosa or essentia.", 
              file=sys.stderr)
        sys.exit(1)
    
    # Determine which methods to use
    if args.methods:
        methods_to_use = [m for m in args.methods if m in available_methods]
        if not methods_to_use:
            print("Error: None of the specified methods are available.", file=sys.stderr)
            sys.exit(1)
    else:
        methods_to_use = available_methods
    
    print(f"Using methods: {', '.join(methods_to_use)}", file=sys.stderr)
    
    # Handle middle flag
    duration = args.duration
    offset = args.offset
    if args.middle:
        duration = 30  # 30 seconds
        # Note: We'll calculate the actual offset per file when we know its length
        # For now, we'll use a placeholder
        offset = -1  # Special value to indicate "calculate middle"
    
    results = []
    
    # Process directory if specified
    if args.directory:
        results.extend(process_directory(
            args.directory, 
            args.extensions, 
            methods_to_use,
            duration=duration,
            offset=offset
        ))
    
    # Process individual files
    for file_path in args.files:
        from glob import glob
        matched_files = glob(file_path)
        if matched_files:
            for matched_file in matched_files:
                # Handle middle calculation if needed
                actual_offset = offset
                if offset == -1:  # Middle flag
                    try:
                        import librosa
                        file_duration = librosa.get_duration(filename=str(matched_file))
                        actual_offset = max(0, (file_duration - 30) / 2)
                    except:
                        actual_offset = 30  # Default to 30 seconds if can't determine
                
                print(f"Processing {matched_file}...", file=sys.stderr)
                result = process_file(
                    matched_file, 
                    methods_to_use,
                    duration=duration,
                    offset=actual_offset if actual_offset != -1 else None
                )
                if result:
                    results.append(result)
        else:
            print(f"Warning: No files matched pattern: {file_path}", file=sys.stderr)
    
    if not results:
        print("No audio files processed.", file=sys.stderr)
        sys.exit(1)
    
    # Save results
    save_results_by_method(results, args.output)


if __name__ == '__main__':
    main()