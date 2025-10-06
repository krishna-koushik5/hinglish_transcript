#!/bin/bash
# Quick setup script for Hinglish Transcription Service

set -e

echo "🚀 Setting up Hinglish Transcription Service..."

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    echo "❌ Docker is not installed. Please install Docker first."
    exit 1
fi

# Check if Docker Compose is installed
if ! command -v docker-compose &> /dev/null; then
    echo "❌ Docker Compose is not installed. Please install Docker Compose first."
    exit 1
fi

# Create .env file if it doesn't exist
if [ ! -f ".env" ]; then
    echo "📝 Creating .env file..."
    cat > .env << 'EOF'
# Google Cloud Configuration
GCS_BUCKET=hinglish-service-audios
GCP_PROJECT_ID=your-project-id
GOOGLE_API_KEY=your-google-api-key-here

# Redis/Valkey Configuration  
VALKEY_URL=redis://valkey:6379/0

# Worker Configuration
WORKER_CONCURRENCY=5
MAX_CHUNK_DURATION=600
EOF
    echo "✅ .env file created! Please edit it with your Google Cloud credentials."
    echo ""
    echo "Required:"
    echo "  - GOOGLE_API_KEY: Your Google Gemini API key"
    echo "  - GCS_BUCKET: Your Google Cloud Storage bucket name"
    echo "  - GCP_PROJECT_ID: Your Google Cloud project ID"
    echo ""
    echo "To get started:"
    echo "  1. Edit .env with your credentials"
    echo "  2. Run: docker-compose up -d"
    echo "  3. Visit: http://localhost:8000/docs"
else
    echo "✅ .env file already exists"
fi

# Create necessary directories
echo "📁 Creating directories..."
mkdir -p temp

# Check if Google credentials are set
if [ -f ".env" ]; then
    source .env
    if [ "$GOOGLE_API_KEY" = "your-google-api-key-here" ]; then
        echo ""
        echo "⚠️  WARNING: Please update your GOOGLE_API_KEY in .env file"
        echo "   You can get one at: https://aistudio.google.com/app/apikey"
    fi
    
    if [ "$GCS_BUCKET" = "hinglish-service-audios" ]; then
        echo "⚠️  WARNING: Please update your GCS_BUCKET in .env file"
    fi
    
    if [ "$GCP_PROJECT_ID" = "your-project-id" ]; then
        echo "⚠️  WARNING: Please update your GCP_PROJECT_ID in .env file"
    fi
fi

echo ""
echo "🎉 Setup complete!"
echo ""
echo "Next steps:"
echo "  1. Update .env with your Google Cloud credentials"
echo "  2. Start the service: docker-compose up -d"
echo "  3. Check status: docker-compose ps"
echo "  4. View logs: docker-compose logs -f"
echo "  5. Access API docs: http://localhost:8000/docs"
echo ""
echo "To test the API:"
echo "  curl http://localhost:8000/health"