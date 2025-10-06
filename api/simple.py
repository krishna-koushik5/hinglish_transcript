"""
Ultra-simple Vercel function for debugging
"""

from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from mangum import Mangum

app = FastAPI()

@app.get("/", response_class=HTMLResponse)
async def root():
    return """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Hinglish Service - Debug</title>
    </head>
    <body>
        <h1>🎵 Hinglish Transcription Service</h1>
        <p>This is a debug version to test Vercel deployment.</p>
        <p>If you can see this, the basic deployment is working!</p>
        <p>Updated: This should trigger a new deployment.</p>
    </body>
    </html>
    """

@app.get("/health")
async def health():
    return {"status": "ok", "message": "Debug version working"}

# Vercel handler
handler = Mangum(app)
