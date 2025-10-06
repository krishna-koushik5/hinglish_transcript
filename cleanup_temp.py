#!/usr/bin/env python3
"""
Cleanup script for temporary audio files
"""

import os
import shutil
import glob


def cleanup_temp_files():
    """Clean up all temporary audio files"""
    temp_dir = "temp_audio"

    if not os.path.exists(temp_dir):
        print("✅ No temp directory found - nothing to clean up!")
        return

    # Count files before cleanup
    temp_files = glob.glob(os.path.join(temp_dir, "*"))
    file_count = len(temp_files)

    if file_count == 0:
        print("✅ No temporary files found - nothing to clean up!")
        return

    print(f"🧹 Found {file_count} temporary files to clean up...")

    # Show files that will be deleted
    for file_path in temp_files:
        file_size = os.path.getsize(file_path) / (1024 * 1024)  # Size in MB
        print(f"  📁 {file_path} ({file_size:.2f} MB)")

    # Ask for confirmation
    response = input(f"\n❓ Delete all {file_count} temporary files? (y/N): ")

    if response.lower() in ["y", "yes"]:
        try:
            shutil.rmtree(temp_dir)
            print(f"✅ Successfully cleaned up {file_count} temporary files!")
            print(f"🗑️ Removed directory: {temp_dir}")
        except Exception as e:
            print(f"❌ Error cleaning up files: {e}")
    else:
        print("🚫 Cleanup cancelled.")


def show_temp_status():
    """Show status of temporary files"""
    temp_dir = "temp_audio"

    if not os.path.exists(temp_dir):
        print("✅ No temporary files directory found")
        return

    temp_files = glob.glob(os.path.join(temp_dir, "*"))
    file_count = len(temp_files)

    if file_count == 0:
        print("✅ No temporary files found")
        return

    total_size = 0
    print(f"📊 Temporary files status:")
    print(f"   Directory: {temp_dir}")
    print(f"   Files: {file_count}")

    for file_path in temp_files:
        file_size = os.path.getsize(file_path)
        total_size += file_size
        size_mb = file_size / (1024 * 1024)
        print(f"   📁 {os.path.basename(file_path)} ({size_mb:.2f} MB)")

    total_mb = total_size / (1024 * 1024)
    print(f"   💾 Total size: {total_mb:.2f} MB")


if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1 and sys.argv[1] == "--status":
        show_temp_status()
    else:
        cleanup_temp_files()
