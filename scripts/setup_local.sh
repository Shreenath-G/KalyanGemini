#!/bin/bash

# Local development setup script

set -e

echo "Setting up Adaptive Ad Intelligence Platform for local development"

# Check Python version
python_version=$(python --version 2>&1 | awk '{print $2}')
echo "Python version: $python_version"

# Create virtual environment
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python -m venv venv
else
    echo "Virtual environment already exists"
fi

# Activate virtual environment
echo "Activating virtual environment..."
source venv/bin/activate || . venv/Scripts/activate

# Upgrade pip
echo "Upgrading pip..."
pip install --upgrade pip

# Install dependencies
echo "Installing dependencies..."
pip install -r requirements.txt

# Create .env file if it doesn't exist
if [ ! -f ".env" ]; then
    echo "Creating .env file from template..."
    cp .env.example .env
    echo "Please edit .env file with your configuration"
else
    echo ".env file already exists"
fi

# Create necessary directories
echo "Creating directory structure..."
mkdir -p src/agents
mkdir -p src/models
mkdir -p src/services
mkdir -p src/api
mkdir -p tests
mkdir -p logs

# Create __init__.py files
touch src/agents/__init__.py
touch src/models/__init__.py
touch src/services/__init__.py
touch src/api/__init__.py
touch tests/__init__.py

echo ""
echo "Setup complete!"
echo ""
echo "Next steps:"
echo "1. Edit .env file with your Google Cloud configuration"
echo "2. Set GOOGLE_APPLICATION_CREDENTIALS to your service account key path"
echo "3. Run: source venv/bin/activate (or venv\\Scripts\\activate on Windows)"
echo "4. Run: python -m src.main"
echo ""
echo "The API will be available at http://localhost:8080"
echo "API documentation: http://localhost:8080/docs"
