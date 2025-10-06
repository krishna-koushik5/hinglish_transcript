"""
Simplified Vercel-compatible version of the Hinglish Transcription Service
"""

from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import os
import uuid
import tempfile
from typing import Dict, Any
from datetime import datetime
import json
from dotenv import load_dotenv
from mangum import Mangum

# Load environment variables
load_dotenv()

# Environment variables
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
MAX_CHUNK_DURATION = int(os.getenv("MAX_CHUNK_DURATION", "600"))

# In-memory job tracking
jobs: Dict[str, Dict[str, Any]] = {}

app = FastAPI(
    title="Hindi/English Transcription Service",
    description="Simplified service for Hindi and English audio transcription",
    version="4.2.0",
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/", response_class=HTMLResponse)
async def upload_page():
    """Simple upload page"""
    return """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Hinglish Transcription Service</title>
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <style>
            body { font-family: Arial, sans-serif; max-width: 800px; margin: 0 auto; padding: 20px; }
            .upload-area { border: 2px dashed #ccc; padding: 40px; text-align: center; margin: 20px 0; }
            .upload-area.dragover { border-color: #007bff; background-color: #f8f9fa; }
            input[type="file"] { margin: 10px 0; }
            button { background: #007bff; color: white; padding: 10px 20px; border: none; border-radius: 4px; cursor: pointer; }
            button:hover { background: #0056b3; }
            .status { margin: 20px 0; padding: 10px; border-radius: 4px; }
            .status.queued { background: #fff3cd; border: 1px solid #ffeaa7; }
            .status.processing { background: #d1ecf1; border: 1px solid #bee5eb; }
            .status.completed { background: #d4edda; border: 1px solid #c3e6cb; }
            .status.failed { background: #f8d7da; border: 1px solid #f5c6cb; }
            .download-link { display: inline-block; margin: 10px 0; padding: 10px 20px; background: #28a745; color: white; text-decoration: none; border-radius: 4px; }
        </style>
    </head>
    <body>
        <h1>🎵 Hinglish Transcription Service</h1>
        <p>Upload an audio file to get transcription with SRT subtitles.</p>
        <p><strong>Note: This is a demo version. For full functionality, deploy with FFmpeg support.</strong></p>
        
        <div class="upload-area" id="uploadArea">
            <p>Drag and drop your audio file here, or click to select</p>
            <input type="file" id="audioFile" accept=".mp3,.wav,.m4a,.aac,.mp4" style="display: none;">
        </div>
        
        <div id="status"></div>
        
        <script>
            const uploadArea = document.getElementById('uploadArea');
            const fileInput = document.getElementById('audioFile');
            const statusDiv = document.getElementById('status');
            
            uploadArea.addEventListener('click', () => fileInput.click());
            uploadArea.addEventListener('dragover', (e) => {
                e.preventDefault();
                uploadArea.classList.add('dragover');
            });
            uploadArea.addEventListener('dragleave', () => uploadArea.classList.remove('dragover'));
            uploadArea.addEventListener('drop', (e) => {
                e.preventDefault();
                uploadArea.classList.remove('dragover');
                const files = e.dataTransfer.files;
                if (files.length > 0) {
                    fileInput.files = files;
                    uploadFile(files[0]);
                }
            });
            
            fileInput.addEventListener('change', (e) => {
                if (e.target.files.length > 0) {
                    uploadFile(e.target.files[0]);
                }
            });
            
            async function uploadFile(file) {
                const formData = new FormData();
                formData.append('audio_file', file);
                formData.append('user_id', 'web_user');
                
                statusDiv.innerHTML = '<div class="status queued">Uploading file...</div>';
                
                try {
                    const response = await fetch('/api/transcribe', {
                        method: 'POST',
                        body: formData
                    });
                    
                    const result = await response.json();
                    
                    if (response.ok) {
                        statusDiv.innerHTML = `<div class="status queued">Job submitted: ${result.job_id}<br>Status: ${result.status}</div>`;
                        pollJobStatus(result.job_id);
                    } else {
                        statusDiv.innerHTML = `<div class="status failed">Error: ${result.detail}</div>`;
                    }
                } catch (error) {
                    statusDiv.innerHTML = `<div class="status failed">Error: ${error.message}</div>`;
                }
            }
            
            async function pollJobStatus(jobId) {
                const interval = setInterval(async () => {
                    try {
                        const response = await fetch(`/api/status/${jobId}`);
                        const status = await response.json();
                        
                        if (status.status === 'completed') {
                            clearInterval(interval);
                            statusDiv.innerHTML = `
                                <div class="status completed">
                                    Job completed!<br>
                                    <a href="/api/download/${jobId}" class="download-link">Download SRT File</a>
                                </div>
                            `;
                        } else if (status.status === 'failed') {
                            clearInterval(interval);
                            statusDiv.innerHTML = `<div class="status failed">Job failed: ${status.error || 'Unknown error'}</div>`;
                        } else {
                            statusDiv.innerHTML = `<div class="status processing">Processing... ${status.progress || 0}%</div>`;
                        }
                    } catch (error) {
                        clearInterval(interval);
                        statusDiv.innerHTML = `<div class="status failed">Error checking status: ${error.message}</div>`;
                    }
                }, 2000);
            }
        </script>
    </body>
    </html>
    """

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "hindi-english-transcription",
        "version": "4.2.0-simplified",
        "api_key_configured": bool(GOOGLE_API_KEY and GOOGLE_API_KEY != "your-google-gemini-api-key"),
        "note": "This is a simplified version for Vercel deployment"
    }

@app.post("/api/transcribe")
async def submit_transcription(
    audio_file: UploadFile = File(...), 
    user_id: str = Form(default="anonymous")
):
    """Submit audio file for transcription (simplified version)"""
    try:
        # Generate job ID
        job_id = str(uuid.uuid4())
        
        # Create job entry
        jobs[job_id] = {
            "id": job_id,
            "user_id": user_id,
            "filename": audio_file.filename,
            "status": "queued",
            "created_at": datetime.now().isoformat(),
            "progress": 0,
            "error": None
        }
        
        # Simulate processing (since we don't have FFmpeg on Vercel)
        jobs[job_id]["status"] = "processing"
        jobs[job_id]["progress"] = 50
        
        # For demo purposes, create a simple SRT file
        demo_srt = f"""1
00:00:00,000 --> 00:00:05,000
Demo transcription for {audio_file.filename}

2
00:00:05,000 --> 00:00:10,000
This is a simplified version for Vercel deployment.

3
00:00:10,000 --> 00:00:15,000
For full functionality, deploy with FFmpeg support.
"""
        
        jobs[job_id]["status"] = "completed"
        jobs[job_id]["progress"] = 100
        jobs[job_id]["srt_content"] = demo_srt
        
        return {
            "job_id": job_id,
            "status": "completed",
            "message": "Demo transcription completed (simplified version)"
        }
        
    except Exception as e:
        if job_id in jobs:
            jobs[job_id]["status"] = "failed"
            jobs[job_id]["error"] = str(e)
        
        raise HTTPException(status_code=500, detail=f"Transcription failed: {str(e)}")

@app.get("/api/status/{job_id}")
async def get_job_status(job_id: str):
    """Get job status"""
    if job_id not in jobs:
        raise HTTPException(status_code=404, detail="Job not found")
    
    return jobs[job_id]

@app.get("/api/download/{job_id}")
async def download_srt(job_id: str):
    """Download SRT file"""
    if job_id not in jobs:
        raise HTTPException(status_code=404, detail="Job not found")
    
    job = jobs[job_id]
    if job["status"] != "completed":
        raise HTTPException(status_code=400, detail="Job not completed")
    
    srt_content = job.get("srt_content", "")
    filename = f"{job['filename']}.srt" if job['filename'] else f"{job_id}.srt"
    
    return JSONResponse(
        content={"srt_content": srt_content, "filename": filename},
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )

# Vercel handler
handler = Mangum(app)
