@echo off
REM Hinglish Transcription Service Deployment Script for Windows
REM This script helps deploy the service on Windows

setlocal enabledelayedexpansion

echo 🎵 Hinglish Transcription Service Deployment Script
echo ==================================================

REM Check if Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python is not installed or not in PATH
    exit /b 1
)

REM Check if pip is installed
pip --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] pip is not installed
    exit /b 1
)

REM Parse command line arguments
if "%1"=="docker" goto deploy_docker
if "%1"=="manual" goto deploy_manual
if "%1"=="setup" goto setup_env
goto show_help

:show_help
echo Usage: deploy.bat {docker^|manual^|setup}
echo.
echo Options:
echo   docker   - Deploy using Docker Compose
echo   manual   - Deploy manually (for development)
echo   setup    - Setup environment only
echo.
echo Examples:
echo   deploy.bat docker     # Deploy with Docker
echo   deploy.bat manual     # Run manually for development
echo   deploy.bat setup      # Setup environment only
exit /b 1

:setup_env
echo [INFO] Setting up environment...

REM Create .env file if it doesn't exist
if not exist .env (
    echo [INFO] Creating .env file from template...
    copy env.example .env
    echo [WARNING] Please edit .env file and add your Google API key
)

REM Create virtual environment
if not exist venv (
    echo [INFO] Creating virtual environment...
    python -m venv venv
)

REM Activate virtual environment and install requirements
echo [INFO] Installing Python dependencies...
call venv\Scripts\activate.bat
pip install -r requirements.txt

echo [SUCCESS] Environment setup completed
goto end

:deploy_docker
echo [INFO] Deploying with Docker...

REM Check if Docker is installed
docker --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Docker is not installed. Please install Docker Desktop first.
    exit /b 1
)

REM Check if Docker Compose is installed
docker-compose --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Docker Compose is not installed. Please install Docker Compose first.
    exit /b 1
)

REM Build and start containers
docker-compose up -d --build

echo [SUCCESS] Docker deployment completed
echo [INFO] Service is running at http://localhost:8000
goto end

:deploy_manual
echo [INFO] Deploying manually...

REM Setup environment first
call :setup_env

REM Activate virtual environment and start service
echo [INFO] Starting the service...
call venv\Scripts\activate.bat
python start_production.py
goto end

:end
echo.
echo Deployment completed!
