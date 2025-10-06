#!/usr/bin/env python3
"""
Simple runner for the Hinglish Transcription Service
"""

import os
import sys
import subprocess
from pathlib import Path


def check_ffmpeg():
    """Check if FFmpeg is installed"""
    # Check different locations for FFmpeg
    ffmpeg_paths = [
        "ffmpeg",  # System PATH
        "api/ffmpeg.exe",  # API directory
        "ffmpeg.exe",  # Root directory
    ]

    for path in ffmpeg_paths:
        try:
            subprocess.run([path, "-version"], capture_output=True, check=True)
            print(f"✅ FFmpeg found at: {path}")
            return True
        except (subprocess.CalledProcessError, FileNotFoundError):
            continue

    print("❌ FFmpeg is not installed or not in PATH")
    print("Please install FFmpeg:")
    print("  - Windows: Download from https://ffmpeg.org/download.html")
    print("  - macOS: brew install ffmpeg")
    print("  - Ubuntu/Debian: sudo apt install ffmpeg")
    print("  - Or place ffmpeg.exe and ffprobe.exe in the api/ directory")
    return False


def install_requirements():
    """Install Python requirements"""
    print("📦 Installing Python requirements...")
    try:
        subprocess.run(
            [sys.executable, "-m", "pip", "install", "-r", "requirements.txt"],
            check=True,
        )
        print("✅ Requirements installed successfully")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to install requirements: {e}")
        return False


def run_service():
    """Run the FastAPI service"""
    print("🚀 Starting Hinglish Transcription Service...")
    print("📱 Web interface: http://localhost:8000")
    print("🔍 Health check: http://localhost:8000/health")
    print("📚 API docs: http://localhost:8000/docs")
    print("\nPress Ctrl+C to stop the service\n")

    # Change to api directory
    os.chdir("api")

    # Run the service
    try:
        subprocess.run([sys.executable, "main.py"], check=True)
    except KeyboardInterrupt:
        print("\n👋 Service stopped by user")
    except subprocess.CalledProcessError as e:
        print(f"❌ Service failed to start: {e}")
        return False

    return True


def main():
    """Main entry point"""
    print("🎵 Hinglish Transcription Service")
    print("=" * 40)

    # Check if we're in the right directory
    if not Path("api/main.py").exists():
        print("❌ Please run this script from the project root directory")
        sys.exit(1)

    # Check FFmpeg
    if not check_ffmpeg():
        sys.exit(1)

    # Install requirements
    if not install_requirements():
        sys.exit(1)

    # Run the service
    run_service()


if __name__ == "__main__":
    main()
