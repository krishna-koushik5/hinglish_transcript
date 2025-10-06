# 🚀 Deploy to Vercel - Hinglish Transcription Service

This guide will help you deploy your Hinglish Transcription Service to Vercel, a modern serverless platform perfect for FastAPI applications.

## 📋 Prerequisites

- GitHub account
- Vercel account (free at [vercel.com](https://vercel.com))
- Google Gemini API key (optional, service works in demo mode without it)

## 🚀 Quick Deployment

### Method 1: Deploy from GitHub (Recommended)

1. **Push your code to GitHub**
   ```bash
   git add .
   git commit -m "Add Vercel deployment configuration"
   git push origin main
   ```

2. **Connect to Vercel**
   - Go to [vercel.com](https://vercel.com)
   - Sign in with your GitHub account
   - Click "New Project"
   - Import your GitHub repository

3. **Configure the project**
   - Framework Preset: **Other**
   - Root Directory: **Leave as is** (or set to project root)
   - Build Command: **Leave empty** (Vercel will auto-detect)
   - Output Directory: **Leave empty**

4. **Add Environment Variables**
   - Go to Project Settings → Environment Variables
   - Add these variables:
     ```
     GOOGLE_API_KEY=your-google-gemini-api-key
     MAX_CHUNK_DURATION=600
     ```

5. **Deploy**
   - Click "Deploy"
   - Wait for deployment to complete
   - Your service will be available at `https://your-project-name.vercel.app`

### Method 2: Deploy with Vercel CLI

1. **Install Vercel CLI**
   ```bash
   npm install -g vercel
   ```

2. **Login to Vercel**
   ```bash
   vercel login
   ```

3. **Deploy from your project directory**
   ```bash
   vercel
   ```

4. **Follow the prompts**
   - Link to existing project or create new
   - Set up environment variables
   - Deploy

## ⚙️ Configuration Files

### `vercel.json`
```json
{
  "version": 2,
  "builds": [
    {
      "src": "api/vercel_handler.py",
      "use": "@vercel/python"
    }
  ],
  "routes": [
    {
      "src": "/(.*)",
      "dest": "api/vercel_handler.py"
    }
  ],
  "env": {
    "PYTHON_VERSION": "3.11"
  },
  "functions": {
    "api/vercel_handler.py": {
      "maxDuration": 300
    }
  }
}
```

### `requirements-vercel.txt`
```
fastapi>=0.115.12,<0.116.0
uvicorn[standard]>=0.32.0,<0.33.0
python-dotenv>=1.1.0,<2.0.0
python-multipart>=0.0.17,<0.1.0
google-genai>=1.17.0,<2.0.0
openai-whisper>=20240930
mangum>=0.17.0
```

## 🔧 Environment Variables

Set these in your Vercel project dashboard:

| Variable | Description | Required | Default |
|----------|-------------|----------|---------|
| `GOOGLE_API_KEY` | Your Google Gemini API key | No | Demo mode without it |
| `MAX_CHUNK_DURATION` | Max audio chunk duration in seconds | No | 600 |
| `HOST` | Server host | No | 0.0.0.0 |
| `PORT` | Server port | No | 8000 |

### Getting Google API Key
1. Go to [Google AI Studio](https://makersuite.google.com/app/apikey)
2. Create a new API key
3. Copy the key to your Vercel environment variables

## 📁 Project Structure

```
your-project/
├── api/
│   ├── main.py              # Main FastAPI application
│   ├── vercel_handler.py    # Vercel serverless handler
│   └── temp_audio/          # Temporary audio storage
├── static/
│   └── style.css            # Custom styles
├── vercel.json              # Vercel configuration
├── requirements-vercel.txt  # Python dependencies
├── env.example              # Environment variables template
└── README.md
```

## 🌐 Accessing Your Service

After deployment, your service will be available at:
- **Web Interface**: `https://your-project-name.vercel.app`
- **Health Check**: `https://your-project-name.vercel.app/health`
- **API Documentation**: `https://your-project-name.vercel.app/docs`

## 🔍 Testing Your Deployment

1. **Health Check**
   ```bash
   curl https://your-project-name.vercel.app/health
   ```

2. **Upload Audio File**
   - Visit the web interface
   - Upload a sample audio file
   - Wait for processing
   - Download the SRT file

3. **API Test**
   ```bash
   curl -X POST https://your-project-name.vercel.app/api/transcribe \
     -F "audio_file=@sample.mp3" \
     -F "user_id=test_user"
   ```

## 🚨 Important Considerations

### Vercel Limitations
- **Function timeout**: 300 seconds (5 minutes) maximum
- **Memory limit**: 1024 MB
- **File size limit**: 50 MB for uploads
- **Cold starts**: First request may be slower

### Audio Processing
- Large audio files may timeout on Vercel
- Consider chunking very long audio files
- The service automatically handles chunking for files > 10 minutes

### Storage
- Vercel is serverless, so files are temporary
- Audio files are processed and then cleaned up
- SRT files are generated on-demand

## 🔄 Updates and Maintenance

### Updating Your Service
1. Make changes to your code
2. Push to GitHub: `git push origin main`
3. Vercel automatically redeploys

### Environment Variables
- Update in Vercel dashboard
- Changes take effect on next deployment

### Monitoring
- Check Vercel dashboard for logs
- Monitor function execution time
- Watch for timeout errors

## 🛠️ Troubleshooting

### Common Issues

1. **Build Failures**
   - Check Python version (should be 3.11)
   - Verify all dependencies in `requirements-vercel.txt`
   - Check build logs in Vercel dashboard

2. **Function Timeouts**
   - Reduce `MAX_CHUNK_DURATION` environment variable
   - Split large audio files before upload
   - Check function logs for specific errors

3. **Import Errors**
   - Ensure all dependencies are in `requirements-vercel.txt`
   - Check that `mangum` is included for Vercel compatibility

4. **File Upload Issues**
   - Check file size limits (50MB max)
   - Verify supported audio formats
   - Check function logs for errors

### Debug Mode
Enable debug logging by setting environment variable:
```
DEBUG=true
```

## 📊 Performance Optimization

### For Better Performance
1. **Use smaller audio chunks** (reduce `MAX_CHUNK_DURATION`)
2. **Optimize audio files** before upload
3. **Monitor function execution time**
4. **Consider upgrading** to Vercel Pro for higher limits

### Monitoring
- Check Vercel dashboard for metrics
- Monitor function invocations
- Watch for cold start times
- Track error rates

## 🔒 Security

### Current Setup
- CORS enabled for all origins
- No authentication required
- Public API access

### For Production
- Consider adding API authentication
- Implement rate limiting
- Restrict CORS origins
- Add input validation

## 🎯 Next Steps

1. **Deploy your service** using one of the methods above
2. **Test with sample audio files**
3. **Configure custom domain** (optional)
4. **Set up monitoring** and alerts
5. **Optimize performance** based on usage

## 📞 Support

If you encounter issues:
1. Check Vercel dashboard logs
2. Verify environment variables
3. Test with simple audio files
4. Check the health endpoint
5. Review this troubleshooting guide

## 🎉 You're All Set!

Your Hinglish Transcription Service is now ready to run on Vercel! The serverless architecture means:
- ✅ Automatic scaling
- ✅ No server management
- ✅ Global CDN
- ✅ Automatic HTTPS
- ✅ Easy deployments

Happy transcribing! 🎵
