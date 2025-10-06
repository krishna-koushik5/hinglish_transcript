# 🌐 Hinglish Transcription Service - Hosting Guide

This guide will help you host your Hinglish Transcription Service as a live website. Choose the deployment method that best fits your needs.

## 🚀 Quick Start Options

### Option 1: Docker Deployment (Recommended)
**Best for**: VPS, dedicated servers, or local development

```bash
# 1. Clone the repository
git clone <your-repository-url>
cd hinglish-service

# 2. Configure environment
cp env.example .env
# Edit .env file with your Google API key

# 3. Deploy with Docker
docker-compose up -d

# 4. Access your website
# Open http://localhost:8000 in your browser
```

### Option 2: Cloud Platform Deployment
**Best for**: Easy deployment without server management

#### Railway (Easiest)
1. Go to [Railway.app](https://railway.app)
2. Connect your GitHub repository
3. Add environment variables:
   - `GOOGLE_API_KEY`: Your Gemini API key
   - `MAX_CHUNK_DURATION`: 600
4. Deploy automatically

#### Render
1. Go to [Render.com](https://render.com)
2. Create new Web Service
3. Connect your GitHub repository
4. Set build command: `pip install -r requirements.txt`
5. Set start command: `python start_production.py`
6. Add environment variables in dashboard

#### Heroku
1. Install [Heroku CLI](https://devcenter.heroku.com/articles/heroku-cli)
2. Create app: `heroku create your-app-name`
3. Add buildpacks:
   ```bash
   heroku buildpacks:add heroku/python
   heroku buildpacks:add https://github.com/jonathanong/heroku-buildpack-ffmpeg.git
   ```
4. Set environment variables:
   ```bash
   heroku config:set GOOGLE_API_KEY=your-key
   ```
5. Deploy: `git push heroku main`

### Option 3: VPS/Server Deployment
**Best for**: Full control, custom domains, production use

#### Using the deployment script:
```bash
# Make script executable (Linux/Mac)
chmod +x deploy.sh

# Deploy as system service
sudo ./deploy.sh systemd

# Or deploy with Docker
./deploy.sh docker
```

#### Manual deployment:
```bash
# 1. Install dependencies
sudo apt update
sudo apt install python3.11 python3.11-pip python3.11-venv ffmpeg nginx

# 2. Setup application
git clone <your-repository>
cd hinglish-service
python3.11 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# 3. Configure environment
cp env.example .env
nano .env  # Add your API key

# 4. Run the service
python start_production.py
```

## 🔧 Configuration

### Environment Variables
Create a `.env` file with these variables:

```bash
# Required for real transcription
GOOGLE_API_KEY=your-google-gemini-api-key

# Optional settings
MAX_CHUNK_DURATION=600
HOST=0.0.0.0
PORT=8000
```

### Getting Google API Key
1. Go to [Google AI Studio](https://makersuite.google.com/app/apikey)
2. Create a new API key
3. Copy the key to your `.env` file

## 🌍 Domain and SSL Setup

### Using Nginx as Reverse Proxy
1. Install Nginx: `sudo apt install nginx`
2. Create configuration:
   ```bash
   sudo nano /etc/nginx/sites-available/hinglish-service
   ```
3. Add this configuration:
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
4. Enable site: `sudo ln -s /etc/nginx/sites-available/hinglish-service /etc/nginx/sites-enabled/`
5. Test and reload: `sudo nginx -t && sudo systemctl reload nginx`

### SSL Certificate with Let's Encrypt
1. Install Certbot: `sudo apt install certbot python3-certbot-nginx`
2. Get certificate: `sudo certbot --nginx -d your-domain.com`
3. Auto-renewal: `sudo crontab -e` and add:
   ```bash
   0 12 * * * /usr/bin/certbot renew --quiet
   ```

## 📊 Monitoring and Maintenance

### Health Checks
Your service provides a health endpoint at `/health` that returns:
- Service status
- Version information
- API key configuration status
- Active job count

### Logs
```bash
# Docker logs
docker-compose logs -f

# System service logs
sudo journalctl -u hinglish-service -f

# Application logs
tail -f /var/log/hinglish-service.log
```

### Performance Monitoring
- Monitor memory usage (jobs are stored in memory)
- Restart service periodically to clear completed jobs
- Consider implementing job cleanup for production

## 🔒 Security Best Practices

### Environment Security
- Never commit `.env` files to version control
- Use strong, unique API keys
- Rotate API keys regularly
- Use environment-specific configurations

### Server Security
```bash
# Configure firewall
sudo ufw allow 22    # SSH
sudo ufw allow 80    # HTTP
sudo ufw allow 443   # HTTPS
sudo ufw enable

# Update system regularly
sudo apt update && sudo apt upgrade -y
```

### Application Security
- The service runs with CORS enabled for all origins (suitable for development)
- For production, consider restricting CORS origins
- Implement rate limiting for API endpoints
- Add authentication if needed

## 🚨 Troubleshooting

### Common Issues

1. **Service won't start**
   - Check if port 8000 is available: `sudo lsof -i :8000`
   - Verify Python dependencies: `pip install -r requirements.txt`
   - Check logs for specific errors

2. **FFmpeg not found**
   - Install FFmpeg: `sudo apt install ffmpeg`
   - For Docker: FFmpeg is included in the image

3. **API key not working**
   - Verify key format in `.env` file
   - Check if key has proper permissions
   - Test with a simple API call

4. **Memory issues**
   - Service uses in-memory job tracking
   - Restart service to clear completed jobs
   - Monitor memory usage with `htop` or `free -h`

5. **File upload issues**
   - Check file size limits
   - Verify supported audio formats
   - Check disk space in temp directory

### Performance Optimization

1. **Use a reverse proxy** (Nginx) for better performance
2. **Enable gzip compression** in Nginx
3. **Use a CDN** for static assets
4. **Implement caching** for frequently accessed data
5. **Monitor resource usage** and scale accordingly

## 📈 Scaling for Production

For high-traffic scenarios:

1. **Implement persistent storage** (Redis/PostgreSQL)
2. **Use a load balancer** (HAProxy, Nginx)
3. **Deploy multiple instances**
4. **Implement job queuing** (Celery, RQ)
5. **Add monitoring** (Prometheus, Grafana)
6. **Use container orchestration** (Kubernetes, Docker Swarm)

## 🔄 Updates and Maintenance

### Updating the Service
```bash
# Pull latest changes
git pull origin main

# Rebuild and restart (Docker)
docker-compose down
docker-compose up -d --build

# Restart service (Systemd)
sudo systemctl restart hinglish-service
```

### Backup Strategy
- Backup your `.env` file
- Backup any custom configurations
- Consider backing up completed job data if needed

## 📞 Support

If you encounter issues:

1. Check the logs for error messages
2. Verify all dependencies are installed
3. Test with a simple audio file
4. Check the health endpoint: `http://your-domain.com/health`
5. Review the troubleshooting section above

## 🎯 Next Steps

After successful deployment:

1. **Test the service** with sample audio files
2. **Configure monitoring** and alerts
3. **Set up backups** for important data
4. **Implement security measures** for production
5. **Consider scaling** based on usage patterns

Your Hinglish Transcription Service is now ready to serve users worldwide! 🌍
