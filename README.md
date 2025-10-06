# Hinglish Transcription Service (Simplified)

A simple, self-contained service for transcribing Hinglish (Hindi-English mix) audio content with automatic SRT file generation using Google's Gemini API.

## What's New in v3.0

- **No external dependencies** - Removed Valkey/Redis, GCS bucket requirements
- **In-memory job tracking** - Simple, fast, and self-contained
- **Built-in web interface** - Upload and process audio directly from your browser
- **No API key protection** - Simplified for easy testing and development
- **Single service** - No complex microservice architecture
- **No Docker required** - Run directly with Python

## Features

- Simple web interface for audio upload
- Real-time job progress tracking
- SRT file generation
- Support for multiple audio formats (MP3, WAV, M4A, AAC, MP4)
- In-memory job management
- No external database or storage requirements
- Cross-platform Python support

## Prerequisites

- Python 3.11 or higher
- FFmpeg (for audio processing)
- Google Gemini API key (for real transcription - service works in demo mode without it)

## Quick Start

### Option 1: Deploy to Vercel (Recommended for Web Hosting)
1. **Push to GitHub**
   ```bash
   git add .
   git commit -m "Initial commit"
   git push origin main
   ```

2. **Deploy to Vercel**
   - Go to [vercel.com](https://vercel.com)
   - Connect your GitHub repository
   - Add environment variables: `GOOGLE_API_KEY=your-key`
   - Deploy automatically

3. **Access your live website**
   - Your service will be available at `https://your-project-name.vercel.app`

### Option 2: Local Development
1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd hinglish-service
   ```

2. **Run the setup script**
   ```bash
   python setup.py
   ```
   This will:
   - Install FFmpeg (on macOS/Linux)
   - Install Python dependencies
   - Create a `.env` file for configuration

3. **Start the service**
   ```bash
   python run.py
   ```

4. **Access the service**
   - Web interface: http://localhost:8000
   - Health check: http://localhost:8000/health
   - API docs: http://localhost:8000/docs

## Manual Setup

If you prefer to set up manually:

### 1. Install FFmpeg

**Windows:**
- Download from https://ffmpeg.org/download.html
- Extract and add to PATH
- Or use: `choco install ffmpeg` or `scoop install ffmpeg`

**macOS:**
```bash
brew install ffmpeg
```

**Ubuntu/Debian:**
```bash
sudo apt update
sudo apt install ffmpeg
```

### 2. Install Python Dependencies
```bash
pip install -r requirements.txt
```

### 3. Configure Environment (Optional)
```bash
# Create .env file
echo "GOOGLE_API_KEY=your-google-gemini-api-key" > .env
```

### 4. Run the Service
```bash
cd api
python main.py
```

## Usage

### Web Interface

1. Open http://localhost:8000 in your browser
2. Drag and drop an audio file or click to select
3. Wait for processing to complete
4. Download the generated SRT file

### API Usage

#### Submit Transcription Job
```bash
curl -X POST http://localhost:8000/api/transcribe \
  -F "audio_file=@your_audio.mp3" \
  -F "user_id=your_user_id"
```

#### Check Job Status
```bash
curl http://localhost:8000/api/status/{job_id}
```

#### Download SRT File
```bash
curl http://localhost:8000/api/download/{job_id} -o output.srt
```

## API Endpoints

- `GET /` - Web upload interface
- `GET /health` - Health check
- `POST /api/transcribe` - Submit audio file
- `GET /api/status/{job_id}` - Check job status
- `GET /api/download/{job_id}` - Download SRT file
- `GET /api/jobs` - List all jobs (debug)

## Environment Variables

Create a `.env` file with:

```bash
# Required for real transcription (get from https://makersuite.google.com/app/apikey)
GOOGLE_API_KEY=your-google-gemini-api-key

# Optional
MAX_CHUNK_DURATION=600  # Maximum chunk duration in seconds
```

**Note:** Without a valid Google API key, the service will run in demo mode and generate placeholder SRT files.

## Development

### Local Development
```bash
# Install dependencies
pip install -r requirements.txt

# Run locally
cd api
python main.py
```

### Testing

Run the test script to verify the service:
```bash
python test_simple_api.py
```

## Architecture

The simplified service uses:
- **FastAPI** - Web framework
- **In-memory storage** - Job tracking without external dependencies
- **FFmpeg** - Audio processing
- **Google Gemini API** - AI transcription (optional)

## Limitations

- Jobs are stored in memory and will be lost on restart
- No persistent storage
- Single instance only (no horizontal scaling)
- No authentication or API key protection

## Production Considerations

For production use, consider:
- Adding persistent storage for job data
- Implementing proper authentication
- Adding rate limiting
- Setting up monitoring and logging
- Using a proper database for job tracking

## Troubleshooting

### Common Issues

1. **FFmpeg Not Found**
   - Make sure FFmpeg is installed and in your PATH
   - Test with: `ffmpeg -version`

2. **Audio Processing Errors**
   - Check audio file format compatibility
   - Verify FFmpeg can process the file

3. **Port Already in Use**
   - Change the port in `api/main.py` (line 394)
   - Or kill the process using port 8000

4. **Python Dependencies**
   - Make sure you're using Python 3.11+
   - Try: `pip install --upgrade -r requirements.txt`

### Logs
The service logs to the console. For production, consider redirecting to a log file:
```bash
python run.py > service.log 2>&1
```

## File Structure

```
hinglish-service/
├── api/
│   └── main.py          # Main FastAPI application
├── requirements.txt     # Python dependencies
├── setup.py            # Setup script
├── run.py              # Run script
├── test_simple_api.py  # Test script
├── .env                # Environment variables (created by setup)
└── README.md           # This file
```

## License

MIT License