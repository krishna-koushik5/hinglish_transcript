#!/usr/bin/env python3
"""
Helper script to set up Google Gemini API key
"""

import os
from pathlib import Path

def setup_api_key():
    """Set up the Google Gemini API key"""
    print("🔑 Google Gemini API Key Setup")
    print("=" * 40)
    
    # Check if .env file exists
    env_file = Path(".env")
    
    if env_file.exists():
        print("✅ .env file found")
        
        # Read current content
        with open(".env", "r") as f:
            content = f.read()
        
        if "your-google-gemini-api-key" in content:
            print("⚠️  API key not set yet")
            print("\n📝 To set your API key:")
            print("1. Get your API key from: https://makersuite.google.com/app/apikey")
            print("2. Edit the .env file")
            print("3. Replace 'your-google-gemini-api-key' with your actual key")
        else:
            print("✅ API key appears to be set")
            print("Current .env content:")
            print("-" * 20)
            print(content)
            print("-" * 20)
    else:
        print("❌ .env file not found")
        print("Creating .env file...")
        
        # Create .env file
        with open(".env", "w") as f:
            f.write("# Hinglish Transcription Service Configuration\n")
            f.write("# Get your Google Gemini API key from: https://makersuite.google.com/app/apikey\n")
            f.write("GOOGLE_API_KEY=your-google-gemini-api-key\n")
            f.write("MAX_CHUNK_DURATION=600\n")
        
        print("✅ .env file created")
        print("\n📝 Next steps:")
        print("1. Get your API key from: https://makersuite.google.com/app/apikey")
        print("2. Edit the .env file")
        print("3. Replace 'your-google-gemini-api-key' with your actual key")
    
    print("\n🚀 After setting the API key, restart the service with:")
    print("   python run.py")

if __name__ == "__main__":
    setup_api_key()
