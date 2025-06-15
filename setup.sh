#!/bin/bash

echo "Setting up Folder Organizer environment..."

# Create virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
echo "Activating virtual environment..."
source venv/bin/activate

# Upgrade pip
echo "Upgrading pip..."
pip install --upgrade pip

# Install dependencies (excluding problematic ones)
echo "Installing core dependencies..."
pip install \
    customtkinter==5.2.1 \
    CTkMessagebox==2.5 \
    requests==2.31.0 \
    langdetect \
    python-dateutil==2.8.2 \
    tqdm==4.66.1 \
    PyYAML \
    python-docx \
    PyPDF2 \
    watchdog==3.0.0 \
    jaconv \
    unidecode \
    packaging==23.0 \
    pydantic \
    typing-extensions \
    pytest \
    pytest-asyncio \
    pytest-mock \
    pytest-cov \
    aiofiles

echo "✅ Setup complete!"
echo "To run the application:"
echo "  source venv/bin/activate"
echo "  python3 main.py"