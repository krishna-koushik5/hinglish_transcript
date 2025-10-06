# Hinglish Transcription Service Makefile

.PHONY: help setup run test clean install

help: ## Show this help message
	@echo "Hinglish Transcription Service"
	@echo "=============================="
	@echo ""
	@echo "Available commands:"
	@echo ""
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-15s\033[0m %s\n", $$1, $$2}'

setup: ## Run setup script to install dependencies
	@echo "Setting up Hinglish Transcription Service..."
	python setup.py

install: ## Install Python dependencies only
	@echo "Installing Python dependencies..."
	pip install -r requirements.txt

run: ## Start the service
	@echo "Starting Hinglish Transcription Service..."
	python run.py

test: ## Run tests
	@echo "Running tests..."
	python test_simple_api.py

clean: ## Clean up temporary files
	@echo "Cleaning up..."
	find . -type f -name "*.pyc" -delete
	find . -type d -name "__pycache__" -delete
	find . -type f -name "*.log" -delete
	rm -rf .pytest_cache
	rm -rf .coverage

dev: ## Run in development mode with auto-reload
	@echo "Starting in development mode..."
	cd api && uvicorn main:app --host 0.0.0.0 --port 8000 --reload

check: ## Check if FFmpeg is installed
	@echo "Checking FFmpeg installation..."
	@ffmpeg -version > /dev/null 2>&1 && echo "✅ FFmpeg is installed" || echo "❌ FFmpeg is not installed"

status: ## Check service status
	@echo "Checking service status..."
	@curl -s http://localhost:8000/health > /dev/null 2>&1 && echo "✅ Service is running" || echo "❌ Service is not running"

stop: ## Stop the service (if running in background)
	@echo "Stopping service..."
	@pkill -f "python.*main.py" || echo "No service running"

# Default target
.DEFAULT_GOAL := help