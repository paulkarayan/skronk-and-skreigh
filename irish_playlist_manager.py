import re
import os
from dataclasses import dataclass
from typing import List
import subprocess

@dataclass
class Tune:
    name: str
    
@dataclass
class TuneSet:
    set_type: str  # Reel, Jig, Hornpipe, etc.
    set_number: int
    tunes: List[Tune]
    start_time: str
    
    def get_tune_names(self) -> List[str]:
        return [tune.name for tune in self.tunes]
    
    def __str__(self) -> str:
        return f"{self.set_type} set {self.set_number}: {' / '.join(self.get_tune_names())}"

class IrishPlaylistManager:
    def __init__(self, source_file: str = "foinn1-sets.md"):
        self.source_file = source_file
        self.all_sets = self.parse_source_file()
        
    def parse_time_to_seconds(self, time_str: str) -> int:
        """Convert MM:SS or H:MM:SS to seconds"""
        parts = time_str.split(':')
        if len(parts) == 2:
            return int(parts[0]) * 60 + int(parts[1])
        elif len(parts) == 3:
            return int(parts[0]) * 3600 + int(parts[1]) * 60 + int(parts[2])
        return 0
    
    def parse_source_file(self) -> List[TuneSet]:
        """Parse the foinn1-sets.md file to extract all tune sets"""
        sets = []
        
        with open(self.source_file, 'r') as f:
            lines = f.readlines()
            
        for line in lines:
            # Match pattern like: 21→1:31:36 Jig set 5 Jim Ward's Jig / Blarney Pilgrim / The Cook in the Kitchen
            # Strip the line number and arrow first
            clean_line = re.sub(r'^\d+→', '', line.strip())
            match = re.match(r'^(\d+:\d+(?::\d+)?)\s+(\w+)\s+set\s+(\d+)\s+(.+)$', clean_line)
            if match:
                time_str = match.group(1)
                set_type = match.group(2)
                set_number = int(match.group(3))
                tunes_str = match.group(4)
                
                # Split tunes by ' / '
                tune_names = [name.strip() for name in tunes_str.split(' / ')]
                tunes = [Tune(name) for name in tune_names]
                
                tune_set = TuneSet(
                    set_type=set_type,
                    set_number=set_number,
                    tunes=tunes,
                    start_time=time_str
                )
                sets.append(tune_set)
                
        return sets
    
    def parse_target_file(self, target_file: str = "target.md") -> List[List[str]]:
        """Parse target.md to get the sets we want to learn"""
        target_sets = []
        
        if not os.path.exists(target_file):
            print(f"Target file {target_file} not found. Creating example...")
            self.create_example_target_file(target_file)
            return []
            
        with open(target_file, 'r') as f:
            lines = f.readlines()
            
        for line in lines:
            line = line.strip()
            if line and not line.startswith('#'):  # Skip empty lines and comments
                # Split by ' / ' to get individual tunes
                tunes = [tune.strip() for tune in line.split(' / ')]
                target_sets.append(tunes)
                
        return target_sets
    
    def create_example_target_file(self, filename: str = "target.md"):
        """Create an example target.md file"""
        example_content = """# Target Tune Sets to Learn

# Example format: List each set on its own line
# Tunes within a set are separated by ' / '

Jim Ward's Jig / Blarney Pilgrim / The Cook in the Kitchen
Maid Behind the Bar / Kilmaley / Green Mountain
Out on the Ocean / The Connaughtman's Rambles / Geese in the Bog
"""
        with open(filename, 'w') as f:
            f.write(example_content)
        print(f"Created example {filename}")
    
    def find_matching_sets(self, target_sets: List[List[str]]) -> List[TuneSet]:
        """Find the TuneSet objects that match our target sets"""
        matching_sets = []
        
        for target_set in target_sets:
            for tune_set in self.all_sets:
                # Check if all tunes in the target set match the tune set
                tune_names = tune_set.get_tune_names()
                
                # Normalize names for comparison (case insensitive, remove extra spaces)
                normalized_target = [t.lower().strip() for t in target_set]
                normalized_source = [t.lower().strip() for t in tune_names]
                
                if normalized_target == normalized_source:
                    matching_sets.append(tune_set)
                    break
                    
        return matching_sets
    
    def extract_audio_segments(self, input_file: str, output_dir: str, matching_sets: List[TuneSet]):
        """Extract audio segments from MP3/audio file based on timestamps"""
        os.makedirs(output_dir, exist_ok=True)
        
        # Get duration of each set by looking at the next set's start time
        for i, tune_set in enumerate(matching_sets):
            start_seconds = self.parse_time_to_seconds(tune_set.start_time)
            
            # Find the end time by looking for the next set in the original list
            end_seconds = None
            original_index = self.all_sets.index(tune_set)
            if original_index + 1 < len(self.all_sets):
                end_seconds = self.parse_time_to_seconds(self.all_sets[original_index + 1].start_time)
            
            # Create filename
            safe_name = re.sub(r'[^\w\s-]', '', str(tune_set))
            safe_name = re.sub(r'[-\s]+', '-', safe_name)
            output_file = os.path.join(output_dir, f"{i+1:02d}_{safe_name}.mp3")
            
            # Build ffmpeg command
            cmd = ['ffmpeg', '-i', input_file, '-ss', str(start_seconds)]
            
            if end_seconds:
                duration = end_seconds - start_seconds
                cmd.extend(['-t', str(duration)])
                
            cmd.extend(['-acodec', 'copy', output_file, '-y'])
            
            print(f"Extracting: {tune_set}")
            subprocess.run(cmd, capture_output=True)
            
    def create_combined_audio(self, output_dir: str, final_output: str = "combined_sets.mp3"):
        """Combine all extracted audio segments into one file"""
        # Get all MP3 files in order
        mp3_files = sorted([f for f in os.listdir(output_dir) if f.endswith('.mp3')])
        
        if not mp3_files:
            print("No MP3 files found to combine")
            return
            
        # Create concat file for ffmpeg
        concat_file = os.path.join(output_dir, 'concat_list.txt')
        with open(concat_file, 'w') as f:
            for mp3_file in mp3_files:
                f.write(f"file '{mp3_file}'\n")
                
        # Combine using ffmpeg
        cmd = ['ffmpeg', '-f', 'concat', '-safe', '0', '-i', concat_file, 
               '-c', 'copy', final_output, '-y']
        
        print(f"Creating combined audio file: {final_output}")
        subprocess.run(cmd, cwd=output_dir, capture_output=True)
        
        # Clean up concat file
        os.remove(concat_file)
        
    def generate_spotify_playlist_info(self, matching_sets: List[TuneSet]) -> str:
        """Generate information for creating Spotify playlist"""
        playlist_info = "Spotify Playlist Order:\n\n"
        
        for i, tune_set in enumerate(matching_sets, 1):
            playlist_info += f"{i}. {tune_set}\n"
            for tune in tune_set.tunes:
                playlist_info += f"   - {tune.name}\n"
            playlist_info += "\n"
            
        return playlist_info

def main():
    manager = IrishPlaylistManager()
    
    # Parse target sets
    target_sets = manager.parse_target_file("target.md")
    
    if not target_sets:
        print("No target sets found. Please add sets to target.md")
        return
        
    # Find matching sets
    matching_sets = manager.find_matching_sets(target_sets)
    
    print(f"\nFound {len(matching_sets)} matching sets:")
    for tune_set in matching_sets:
        print(f"  - {tune_set}")
        
    # Generate Spotify playlist info
    spotify_info = manager.generate_spotify_playlist_info(matching_sets)
    
    with open("spotify_playlist_order.txt", "w") as f:
        f.write(spotify_info)
    print(f"\nSpotify playlist order saved to spotify_playlist_order.txt")
    
    # For audio extraction (when you provide the MP3)
    # Uncomment and modify when you have the audio file:
    # manager.extract_audio_segments("foinn1_audio.mp3", "extracted_sets", matching_sets)
    # manager.create_combined_audio("extracted_sets", "my_practice_sets.mp3")

if __name__ == "__main__":
    main()