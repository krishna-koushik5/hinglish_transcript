#!/bin/bash

# Hinglish Transcription Service Deployment Script
# This script helps deploy the service to various platforms

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if running as root
check_root() {
    if [[ $EUID -eq 0 ]]; then
        print_warning "Running as root. Consider using a non-root user for production."
    fi
}

# Check prerequisites
check_prerequisites() {
    print_status "Checking prerequisites..."
    
    # Check Python
    if ! command -v python3 &> /dev/null; then
        print_error "Python 3 is not installed"
        exit 1
    fi
    
    # Check pip
    if ! command -v pip3 &> /dev/null; then
        print_error "pip3 is not installed"
        exit 1
    fi
    
    # Check FFmpeg
    if ! command -v ffmpeg &> /dev/null; then
        print_warning "FFmpeg is not installed. Installing..."
        install_ffmpeg
    fi
    
    print_success "Prerequisites check completed"
}

# Install FFmpeg
install_ffmpeg() {
    if [[ "$OSTYPE" == "linux-gnu"* ]]; then
        if command -v apt-get &> /dev/null; then
            sudo apt-get update
            sudo apt-get install -y ffmpeg
        elif command -v yum &> /dev/null; then
            sudo yum install -y ffmpeg
        else
            print_error "Cannot install FFmpeg automatically. Please install manually."
            exit 1
        fi
    elif [[ "$OSTYPE" == "darwin"* ]]; then
        if command -v brew &> /dev/null; then
            brew install ffmpeg
        else
            print_error "Homebrew not found. Please install FFmpeg manually."
            exit 1
        fi
    else
        print_error "Unsupported OS. Please install FFmpeg manually."
        exit 1
    fi
}

# Setup environment
setup_environment() {
    print_status "Setting up environment..."
    
    # Create .env file if it doesn't exist
    if [ ! -f .env ]; then
        print_status "Creating .env file from template..."
        cp env.example .env
        print_warning "Please edit .env file and add your Google API key"
    fi
    
    # Create virtual environment
    if [ ! -d "venv" ]; then
        print_status "Creating virtual environment..."
        python3 -m venv venv
    fi
    
    # Activate virtual environment
    source venv/bin/activate
    
    # Install requirements
    print_status "Installing Python dependencies..."
    pip install -r requirements.txt
    
    print_success "Environment setup completed"
}

# Deploy with Docker
deploy_docker() {
    print_status "Deploying with Docker..."
    
    # Check if Docker is installed
    if ! command -v docker &> /dev/null; then
        print_error "Docker is not installed. Please install Docker first."
        exit 1
    fi
    
    # Check if Docker Compose is installed
    if ! command -v docker-compose &> /dev/null; then
        print_error "Docker Compose is not installed. Please install Docker Compose first."
        exit 1
    fi
    
    # Build and start containers
    docker-compose up -d --build
    
    print_success "Docker deployment completed"
    print_status "Service is running at http://localhost:8000"
}

# Deploy manually
deploy_manual() {
    print_status "Deploying manually..."
    
    # Setup environment
    setup_environment
    
    # Activate virtual environment
    source venv/bin/activate
    
    # Start the service
    print_status "Starting the service..."
    python start_production.py
}

# Deploy to production with systemd
deploy_systemd() {
    print_status "Deploying with systemd..."
    
    # Check if running as root
    if [[ $EUID -ne 0 ]]; then
        print_error "This option requires root privileges. Please run with sudo."
        exit 1
    fi
    
    # Get current directory
    CURRENT_DIR=$(pwd)
    USER=$(logname)
    
    # Create systemd service file
    print_status "Creating systemd service file..."
    cat > /etc/systemd/system/hinglish-service.service << EOF
[Unit]
Description=Hinglish Transcription Service
After=network.target

[Service]
Type=simple
User=$USER
WorkingDirectory=$CURRENT_DIR
Environment=PATH=$CURRENT_DIR/venv/bin
ExecStart=$CURRENT_DIR/venv/bin/python start_production.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF
    
    # Reload systemd and enable service
    systemctl daemon-reload
    systemctl enable hinglish-service
    systemctl start hinglish-service
    
    print_success "Systemd deployment completed"
    print_status "Service is running. Check status with: sudo systemctl status hinglish-service"
}

# Main function
main() {
    echo "🎵 Hinglish Transcription Service Deployment Script"
    echo "=================================================="
    
    check_root
    check_prerequisites
    
    # Parse command line arguments
    case "${1:-}" in
        "docker")
            deploy_docker
            ;;
        "manual")
            deploy_manual
            ;;
        "systemd")
            deploy_systemd
            ;;
        "setup")
            setup_environment
            ;;
        *)
            echo "Usage: $0 {docker|manual|systemd|setup}"
            echo ""
            echo "Options:"
            echo "  docker   - Deploy using Docker Compose"
            echo "  manual   - Deploy manually (for development)"
            echo "  systemd  - Deploy as systemd service (production)"
            echo "  setup    - Setup environment only"
            echo ""
            echo "Examples:"
            echo "  $0 docker     # Deploy with Docker"
            echo "  $0 manual     # Run manually for development"
            echo "  sudo $0 systemd  # Deploy as system service"
            exit 1
            ;;
    esac
}

# Run main function
main "$@"
