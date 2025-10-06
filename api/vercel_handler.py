"""
Vercel serverless handler for Hinglish Transcription Service
"""

import os
import sys
from pathlib import Path

# Add the parent directory to Python path
sys.path.append(str(Path(__file__).parent.parent))

# Import the FastAPI app
from api.main import app

# Vercel expects the app to be available as 'handler'
handler = app
