#!/usr/bin/env python3
"""
Process rowan22-2025.txt into target.md format
"""

def process_rowan_file(input_file: str, output_file: str):
    """
    Convert Rowan's tune list into target.md format.
    
    Input format:
    Type
    - Tune 1
    - Tune 2
    
    Output format:
    Tune 1 / Tune 2
    """
    with open(input_file, 'r') as f:
        lines = f.readlines()
    
    sets = []
    current_set = []
    current_type = None
    
    for line in lines:
        line = line.strip()
        
        if not line:
            # Empty line - end of current set if we have tunes
            if current_set:
                sets.append(current_set)
                current_set = []
            continue
        
        if line.startswith('- '):
            # This is a tune
            tune_name = line[2:].strip()
            current_set.append(tune_name)
        else:
            # This is a tune type header
            # Save previous set if exists
            if current_set:
                sets.append(current_set)
                current_set = []
            current_type = line
    
    # Don't forget the last set
    if current_set:
        sets.append(current_set)
    
    # Write to target.md
    with open(output_file, 'w') as f:
        f.write("# Target Tune Sets from Rowan 2022-2025\n\n")
        f.write("# Format: Each line is a set, tunes separated by ' / '\n\n")
        
        for set_tunes in sets:
            set_line = " / ".join(set_tunes)
            f.write(f"{set_line}\n")
    
    print(f"Processed {len(sets)} sets containing {sum(len(s) for s in sets)} tunes total")
    print(f"Output written to {output_file}")


if __name__ == "__main__":
    process_rowan_file("rowan22-2025.txt", "target.md")