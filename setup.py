#!/usr/bin/env python3
"""
Setup script for Hinglish Transcription Service
"""

import os
import sys
import subprocess
import platform
from pathlib import Path


def get_os():
    """Get the operating system"""
    return platform.system().lower()


def install_ffmpeg_windows():
    """Instructions for installing FFmpeg on Windows"""
    print("📥 To install FFmpeg on Windows:")
    print("1. Download FFmpeg from: https://ffmpeg.org/download.html")
    print("2. Extract the zip file")
    print("3. Add the 'bin' folder to your PATH environment variable")
    print("4. Restart your terminal/command prompt")
    print("\nOr use Chocolatey: choco install ffmpeg")
    print("Or use Scoop: scoop install ffmpeg")
    print("\nAlternatively, place ffmpeg.exe and ffprobe.exe in the api/ directory")


def install_ffmpeg_macos():
    """Install FFmpeg on macOS using Homebrew"""
    print("📥 Installing FFmpeg on macOS...")
    try:
        subprocess.run(["brew", "install", "ffmpeg"], check=True)
        print("✅ FFmpeg installed successfully")
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("❌ Homebrew not found. Please install Homebrew first:")
        print(
            '   /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"'
        )
        return False


def install_ffmpeg_linux():
    """Install FFmpeg on Linux"""
    print("📥 Installing FFmpeg on Linux...")
    try:
        # Try different package managers
        if subprocess.run(["which", "apt"], capture_output=True).returncode == 0:
            subprocess.run(["sudo", "apt", "update"], check=True)
            subprocess.run(["sudo", "apt", "install", "-y", "ffmpeg"], check=True)
        elif subprocess.run(["which", "yum"], capture_output=True).returncode == 0:
            subprocess.run(["sudo", "yum", "install", "-y", "ffmpeg"], check=True)
        elif subprocess.run(["which", "dnf"], capture_output=True).returncode == 0:
            subprocess.run(["sudo", "dnf", "install", "-y", "ffmpeg"], check=True)
        else:
            print(
                "❌ Could not detect package manager. Please install FFmpeg manually."
            )
            return False

        print("✅ FFmpeg installed successfully")
        return True
    except subprocess.CalledProcessError:
        print("❌ Failed to install FFmpeg. Please install manually.")
        return False


def install_ffmpeg():
    """Install FFmpeg based on the operating system"""
    os_name = get_os()

    if os_name == "windows":
        install_ffmpeg_windows()
        return False  # User needs to install manually
    elif os_name == "darwin":  # macOS
        return install_ffmpeg_macos()
    elif os_name == "linux":
        return install_ffmpeg_linux()
    else:
        print(f"❌ Unsupported operating system: {os_name}")
        return False


def install_python_requirements():
    """Install Python requirements"""
    print("📦 Installing Python requirements...")
    try:
        subprocess.run(
            [sys.executable, "-m", "pip", "install", "-r", "requirements.txt"],
            check=True,
        )
        print("✅ Python requirements installed successfully")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to install Python requirements: {e}")
        return False


def create_env_file():
    """Create a .env file if it doesn't exist"""
    env_file = Path(".env")
    if not env_file.exists():
        print("📝 Creating .env file...")
        with open(".env", "w") as f:
            f.write("# Hinglish Transcription Service Configuration\n")
            f.write(
                "# Get your Google Gemini API key from: https://makersuite.google.com/app/apikey\n"
            )
            f.write("GOOGLE_API_KEY=your-google-gemini-api-key\n")
            f.write("MAX_CHUNK_DURATION=600\n")
        print("✅ .env file created.")
        print("🔑 To enable real transcription:")
        print("   1. Get API key from: https://makersuite.google.com/app/apikey")
        print(
            "   2. Edit .env file and replace 'your-google-gemini-api-key' with your actual key"
        )
    else:
        print("✅ .env file already exists")
        # Check if API key is set
        with open(".env", "r") as f:
            content = f.read()
            if "your-google-gemini-api-key" in content:
                print("⚠️  Google API key not set. Service will run in demo mode.")
                print("   Edit .env file to add your API key for real transcription.")


def main():
    """Main setup function"""
    print("🎵 Hinglish Transcription Service Setup")
    print("=" * 40)

    # Check if we're in the right directory
    if not Path("api/main.py").exists():
        print("❌ Please run this script from the project root directory")
        sys.exit(1)

    # Install FFmpeg
    print("\n1. Installing FFmpeg...")
    ffmpeg_installed = install_ffmpeg()

    if not ffmpeg_installed and get_os() == "windows":
        print("\n⚠️  Please install FFmpeg manually and then run: python run.py")
        return

    # Install Python requirements
    print("\n2. Installing Python requirements...")
    if not install_python_requirements():
        sys.exit(1)

    # Create .env file
    print("\n3. Setting up configuration...")
    create_env_file()

    print("\n✅ Setup completed successfully!")
    print("\n🚀 To start the service, run:")
    print("   python run.py")
    print("\n📱 Then open http://localhost:8000 in your browser")


if __name__ == "__main__":
    main()
