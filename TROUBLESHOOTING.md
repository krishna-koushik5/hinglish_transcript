# Troubleshooting Guide

## Common Issues and Solutions

### 1. Services Won't Start

**Problem**: Docker containers fail to start
```bash
docker-compose up -d
# Shows errors or containers keep restarting
```

**Solutions**:
- Check if ports are already in use:
  ```bash
  sudo lsof -i :8000
  sudo lsof -i :6379
  ```
- Check Docker logs:
  ```bash
  docker-compose logs api
  docker-compose logs worker
  docker-compose logs valkey
  ```
- Rebuild containers:
  ```bash
  docker-compose down
  docker-compose build --no-cache
  docker-compose up -d
  ```

### 2. API Not Responding

**Problem**: `curl http://localhost:8000/health` returns connection refused

**Solutions**:
- Check if API container is running:
  ```bash
  docker-compose ps
  ```
- Check API logs:
  ```bash
  docker-compose logs api
  ```
- Restart API service:
  ```bash
  docker-compose restart api
  ```

### 3. Valkey/Redis Connection Issues

**Problem**: API logs show "Failed to connect to Valkey/Redis"

**Solutions**:
- Check if Valkey is running:
  ```bash
  docker-compose ps valkey
  ```
- Test Valkey connection:
  ```bash
  docker-compose exec valkey valkey-cli ping
  ```
- Check network connectivity:
  ```bash
  docker-compose exec api ping valkey
  ```

### 4. Google API Authentication Errors

**Problem**: Transcription fails with authentication errors

**Solutions**:
- Verify your Google API key:
  ```bash
  # Check if key is set
  grep GOOGLE_API_KEY .env
  
  # Test API key manually
  curl -H "Authorization: Bearer YOUR_API_KEY" \
    https://generativelanguage.googleapis.com/v1/models
  ```
- Ensure Gemini API is enabled in Google Cloud Console
- Check API quotas and billing in Google Cloud Console

### 5. Google Cloud Storage Issues

**Problem**: File upload/download fails

**Solutions**:
- Verify GCS bucket exists and is accessible
- Check service account permissions
- Test bucket access:
  ```bash
  gsutil ls gs://your-bucket-name
  ```

### 6. Worker Not Processing Jobs

**Problem**: Jobs stay in "queued" status

**Solutions**:
- Check if workers are running:
  ```bash
  docker-compose ps worker
  curl http://localhost:8000/api/stats
  ```
- Check worker logs:
  ```bash
  docker-compose logs worker
  ```
- Restart workers:
  ```bash
  docker-compose restart worker
  ```

### 7. FFmpeg Issues

**Problem**: Audio processing fails with FFmpeg errors

**Solutions**:
- Test FFmpeg in container:
  ```bash
  docker-compose exec api ffmpeg -version
  docker-compose exec worker ffmpeg -version
  ```
- Check audio file format:
  ```bash
  file your_audio_file.mp3
  ```
- Try with a simple audio file first

### 8. Memory Issues

**Problem**: Containers are killed due to memory issues

**Solutions**:
- Check system memory:
  ```bash
  free -h
  docker stats
  ```
- Reduce worker concurrency in .env:
  ```bash
  WORKER_CONCURRENCY=2
  ```
- Increase Docker memory limits

### 9. Permission Issues

**Problem**: File permission errors in containers

**Solutions**:
- Check file permissions:
  ```bash
  ls -la /tmp
  ```
- Fix permissions:
  ```bash
  chmod 755 setup.sh test_api.sh
  sudo chown -R $USER:$USER .
  ```

### 10. Port Conflicts

**Problem**: Port 8000 or 6379 already in use

**Solutions**:
- Find process using the port:
  ```bash
  sudo lsof -i :8000
  sudo lsof -i :6379
  ```
- Kill the process or change ports in docker-compose.yml:
  ```yaml
  ports:
    - "8001:8000"  # Use different external port
  ```

## Debugging Commands

### Check Service Health
```bash
# Overall status
make status

# Individual service health
curl http://localhost:8000/health
curl http://localhost:8000/api/stats

# Container logs
docker-compose logs --tail=50 api
docker-compose logs --tail=50 worker
docker-compose logs --tail=50 valkey
```

### Check Configuration
```bash
# Environment variables
cat .env

# Docker compose config
docker-compose config

# Container environment
docker-compose exec api env | grep -E "(VALKEY|GOOGLE|GCS)"
```

### Network Debugging
```bash
# Test internal connectivity
docker-compose exec api ping valkey
docker-compose exec worker ping valkey

# Check DNS resolution
docker-compose exec api nslookup valkey
```

### Resource Monitoring
```bash
# Container resource usage
docker stats

# System resources
top
htop
free -h
df -h
```

## Getting Help

If you're still having issues:

1. **Check the logs**: Most issues are revealed in the container logs
2. **Test incrementally**: Start with basic health checks, then move to complex operations
3. **Isolate the problem**: Test each component individually
4. **Check dependencies**: Ensure all external services (Google APIs, GCS) are properly configured

### Useful Log Commands
```bash
# All logs
docker-compose logs

# Specific service logs
docker-compose logs api
docker-compose logs worker
docker-compose logs valkey

# Follow logs in real-time
docker-compose logs -f

# Last N lines
docker-compose logs --tail=100 api
```

### Clean Restart
```bash
# Complete clean restart
docker-compose down -v
docker system prune -f
docker-compose build --no-cache
docker-compose up -d
```