#!/usr/bin/env python3
"""
Interactive Spotify playlist creator
This script will open your browser for authentication
"""

import webbrowser
from spotify_integration import main

if __name__ == "__main__":
    print("Starting Spotify playlist creation...")
    print("\nIMPORTANT: Your browser will open for Spotify authentication.")
    print("After logging in, you'll be redirected to a URL starting with http://127.0.0.1:8888/callback")
    print("Copy the ENTIRE URL from your browser and paste it when prompted.\n")
    
    input("Press Enter to continue...")
    
    main()