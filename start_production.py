#!/usr/bin/env python3
"""
Production startup script for Hinglish Transcription Service
"""

import os
import sys
import uvicorn
from pathlib import Path


def main():
    """Start the service in production mode"""
    print("🚀 Starting Hinglish Transcription Service (Production Mode)")
    print("=" * 60)

    # Check if we're in the right directory
    if not Path("api/main.py").exists():
        print("❌ Please run this script from the project root directory")
        sys.exit(1)

    # Load environment variables
    from dotenv import load_dotenv

    load_dotenv()

    # Get configuration
    host = os.getenv("HOST", "0.0.0.0")
    port = int(os.getenv("PORT", "8000"))

    print(f"🌐 Server will be available at: http://{host}:{port}")
    print(f"📱 Web interface: http://{host}:{port}")
    print(f"🔍 Health check: http://{host}:{port}/health")
    print(f"📚 API docs: http://{host}:{port}/docs")
    print("\nPress Ctrl+C to stop the service\n")

    # Start the server
    try:
        uvicorn.run(
            "api.main:app",
            host=host,
            port=port,
            log_level="info",
            access_log=True,
            workers=1,
            reload=False,  # Disable reload in production
        )
    except KeyboardInterrupt:
        print("\n👋 Service stopped by user")
    except Exception as e:
        print(f"❌ Service failed to start: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
