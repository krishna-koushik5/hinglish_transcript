# Hinglish Transcription Service - Deployment Guide

This guide covers different ways to deploy the Hinglish Transcription Service as a website.

## 🚀 Quick Start (Docker)

### Prerequisites
- Docker and Docker Compose installed
- Google Gemini API key (optional, service works in demo mode without it)

### 1. Clone and Setup
```bash
git clone <your-repository>
cd hinglish-service
```

### 2. Configure Environment
```bash
# Copy the example environment file
cp env.example .env

# Edit .env file with your API key
nano .env
```

### 3. Deploy with Docker Compose
```bash
# Build and start the service
docker-compose up -d

# Check logs
docker-compose logs -f

# Stop the service
docker-compose down
```

### 4. Access the Service
- Web Interface: http://localhost:8000
- Health Check: http://localhost:8000/health
- API Documentation: http://localhost:8000/docs

## 🌐 Cloud Deployment Options

### Option 1: Railway
1. Connect your GitHub repository to Railway
2. Add environment variables in Railway dashboard:
   - `GOOGLE_API_KEY`: Your Gemini API key
   - `MAX_CHUNK_DURATION`: 600 (optional)
3. Deploy automatically

### Option 2: Render
1. Create a new Web Service on Render
2. Connect your GitHub repository
3. Set build command: `pip install -r requirements.txt`
4. Set start command: `python start_production.py`
5. Add environment variables in Render dashboard

### Option 3: Heroku
1. Install Heroku CLI
2. Create a new app: `heroku create your-app-name`
3. Add buildpack: `heroku buildpacks:add heroku/python`
4. Add FFmpeg buildpack: `heroku buildpacks:add https://github.com/jonathanong/heroku-buildpack-ffmpeg.git`
5. Set environment variables: `heroku config:set GOOGLE_API_KEY=your-key`
6. Deploy: `git push heroku main`

### Option 4: DigitalOcean App Platform
1. Connect your GitHub repository
2. Select "Docker" as the source type
3. Add environment variables in the dashboard
4. Deploy

### Option 5: AWS EC2
1. Launch an EC2 instance (Ubuntu 20.04+)
2. Install Docker: `sudo apt update && sudo apt install docker.io docker-compose`
3. Clone your repository
4. Run `docker-compose up -d`
5. Configure security groups to allow port 8000

## 🔧 Manual Deployment (VPS/Dedicated Server)

### Prerequisites
- Ubuntu 20.04+ or similar Linux distribution
- Python 3.11+
- FFmpeg installed
- Nginx (optional, for reverse proxy)

### 1. Install Dependencies
```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install Python 3.11
sudo apt install python3.11 python3.11-pip python3.11-venv

# Install FFmpeg
sudo apt install ffmpeg

# Install Nginx (optional)
sudo apt install nginx
```

### 2. Setup Application
```bash
# Clone repository
git clone <your-repository>
cd hinglish-service

# Create virtual environment
python3.11 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Configure environment
cp env.example .env
nano .env  # Add your API key
```

### 3. Run with Systemd (Production)
```bash
# Create systemd service file
sudo nano /etc/systemd/system/hinglish-service.service
```

Add this content:
```ini
[Unit]
Description=Hinglish Transcription Service
After=network.target

[Service]
Type=simple
User=www-data
WorkingDirectory=/path/to/hinglish-service
Environment=PATH=/path/to/hinglish-service/venv/bin
ExecStart=/path/to/hinglish-service/venv/bin/python start_production.py
Restart=always

[Install]
WantedBy=multi-user.target
```

```bash
# Enable and start service
sudo systemctl daemon-reload
sudo systemctl enable hinglish-service
sudo systemctl start hinglish-service

# Check status
sudo systemctl status hinglish-service
```

### 4. Configure Nginx (Optional)
```bash
sudo nano /etc/nginx/sites-available/hinglish-service
```

Add this configuration:
```nginx
server {
    listen 80;
    server_name your-domain.com;

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

```bash
# Enable site
sudo ln -s /etc/nginx/sites-available/hinglish-service /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx
```

## 🔒 Security Considerations

### Environment Variables
- Never commit `.env` files to version control
- Use strong, unique API keys
- Rotate API keys regularly

### Firewall
```bash
# Allow only necessary ports
sudo ufw allow 22    # SSH
sudo ufw allow 80    # HTTP
sudo ufw allow 443   # HTTPS
sudo ufw enable
```

### SSL Certificate (Let's Encrypt)
```bash
# Install Certbot
sudo apt install certbot python3-certbot-nginx

# Get certificate
sudo certbot --nginx -d your-domain.com
```

## 📊 Monitoring

### Health Checks
The service provides a health endpoint at `/health` that returns:
- Service status
- Version information
- API key configuration status
- Active job count

### Logs
```bash
# Docker logs
docker-compose logs -f

# Systemd logs
sudo journalctl -u hinglish-service -f
```

## 🚨 Troubleshooting

### Common Issues

1. **FFmpeg not found**
   - Ensure FFmpeg is installed and in PATH
   - For Docker: FFmpeg is included in the image

2. **API key not working**
   - Verify the key is correct in `.env` file
   - Check if the key has proper permissions

3. **Port already in use**
   - Change the port in `.env` file
   - Kill the process using the port: `sudo lsof -ti:8000 | xargs kill -9`

4. **Memory issues**
   - The service uses in-memory job tracking
   - Restart the service to clear completed jobs
   - Consider implementing persistent storage for production

### Performance Tips
- Use a reverse proxy (Nginx) for better performance
- Monitor memory usage for long-running jobs
- Consider implementing job cleanup for completed tasks
- Use a CDN for static assets if needed

## 📈 Scaling

For high-traffic scenarios:
1. Implement persistent storage (Redis/PostgreSQL)
2. Use a load balancer
3. Deploy multiple instances
4. Implement job queuing (Celery/RQ)
5. Add caching layers

## 🔄 Updates

To update the service:
```bash
# Pull latest changes
git pull origin main

# Rebuild Docker image (if using Docker)
docker-compose down
docker-compose build --no-cache
docker-compose up -d

# Or restart systemd service (if using manual deployment)
sudo systemctl restart hinglish-service
```
