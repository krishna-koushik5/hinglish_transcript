@echo off
REM Vercel Deployment Script for Windows
REM This script helps deploy the Hinglish Transcription Service to Vercel

echo 🚀 Hinglish Transcription Service - Vercel Deployment
echo ==================================================

REM Check if Vercel CLI is installed
vercel --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Vercel CLI is not installed
    echo Please install it with: npm install -g vercel
    exit /b 1
)

REM Check if we're in a git repository
git status >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Not in a git repository
    echo Please initialize git and commit your code first
    exit /b 1
)

echo [INFO] Checking git status...
git status --porcelain | findstr /v "^$" >nul
if not errorlevel 1 (
    echo [WARNING] You have uncommitted changes
    echo Please commit your changes first:
    echo   git add .
    echo   git commit -m "Your commit message"
    pause
    exit /b 1
)

echo [INFO] All checks passed!
echo.
echo Choose deployment method:
echo 1. Deploy with Vercel CLI (recommended)
echo 2. Show GitHub deployment instructions
echo 3. Exit
echo.
set /p choice="Enter your choice (1-3): "

if "%choice%"=="1" goto deploy_cli
if "%choice%"=="2" goto show_github
if "%choice%"=="3" goto end
goto invalid_choice

:deploy_cli
echo.
echo [INFO] Starting Vercel deployment...
echo.
vercel
if errorlevel 1 (
    echo [ERROR] Deployment failed
    exit /b 1
)
echo.
echo [SUCCESS] Deployment completed!
echo Your service should be available at the URL shown above
goto end

:show_github
echo.
echo ========================================
echo GitHub Deployment Instructions
echo ========================================
echo.
echo 1. Push your code to GitHub:
echo    git push origin main
echo.
echo 2. Go to https://vercel.com
echo.
echo 3. Sign in with your GitHub account
echo.
echo 4. Click "New Project"
echo.
echo 5. Import your GitHub repository
echo.
echo 6. Configure the project:
echo    - Framework Preset: Other
echo    - Root Directory: (leave as is)
echo    - Build Command: (leave empty)
echo    - Output Directory: (leave empty)
echo.
echo 7. Add environment variables:
echo    - GOOGLE_API_KEY=your-google-gemini-api-key
echo    - MAX_CHUNK_DURATION=600
echo.
echo 8. Click "Deploy"
echo.
echo 9. Your service will be available at https://your-project-name.vercel.app
echo.
pause
goto end

:invalid_choice
echo [ERROR] Invalid choice. Please enter 1, 2, or 3.
goto end

:end
echo.
echo Deployment script completed!
pause
