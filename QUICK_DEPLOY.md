# 🚀 Quick Vercel Deployment Guide

Your Hinglish Transcription Service is now ready to be hosted on Vercel! Follow these simple steps:

## ✅ What's Ready

- ✅ Clean git repository with all Vercel configuration
- ✅ `vercel.json` - Vercel deployment configuration
- ✅ `api/vercel_handler.py` - Serverless handler
- ✅ `requirements-vercel.txt` - Python dependencies
- ✅ Modern web interface with professional styling
- ✅ All deployment files created

## 🚀 Deploy to Vercel (3 Easy Steps)

### Step 1: Push to GitHub
```bash
# Create a new repository on GitHub first, then:
git remote add origin https://github.com/YOUR_USERNAME/YOUR_REPO_NAME.git
git push -u origin main
```

### Step 2: Deploy on Vercel
1. Go to [vercel.com](https://vercel.com)
2. Sign in with your GitHub account
3. Click "New Project"
4. Import your GitHub repository
5. Vercel will auto-detect it's a Python project

### Step 3: Configure Environment Variables
In your Vercel project dashboard, go to Settings → Environment Variables and add:

| Variable | Value | Description |
|----------|-------|-------------|
| `GOOGLE_API_KEY` | `your-google-gemini-api-key` | Get from [Google AI Studio](https://makersuite.google.com/app/apikey) |
| `MAX_CHUNK_DURATION` | `600` | Max audio chunk duration (seconds) |

## 🌐 Your Live Website

After deployment, your service will be available at:
- **Web Interface**: `https://your-project-name.vercel.app`
- **Health Check**: `https://your-project-name.vercel.app/health`
- **API Docs**: `https://your-project-name.vercel.app/docs`

## 🎯 Features

- 🎤 **Drag & drop audio upload**
- 📊 **Real-time processing status**
- 📝 **Download SRT files**
- 📱 **Mobile-responsive design**
- 🌐 **Multi-language support** (Hindi → Hinglish, English → English)
- 🤖 **AI-powered transcription** with Whisper + Gemini

## 🔧 Getting Your Google API Key

1. Go to [Google AI Studio](https://makersuite.google.com/app/apikey)
2. Sign in with your Google account
3. Click "Create API Key"
4. Copy the key and add it to Vercel environment variables

**Note**: The service works in demo mode without an API key, but for real transcription, you need the Google API key.

## 🎉 You're All Set!

Your Hinglish Transcription Service will be live and ready to serve users worldwide! The serverless architecture means:
- ✅ Automatic scaling
- ✅ No server management
- ✅ Global CDN
- ✅ Automatic HTTPS
- ✅ Easy updates

**Start deploying now!** 🚀
