# Intelligent File Organizer (PARA)

An AI-powered file organization tool that automatically categorizes files using the PARA method (Projects, Areas, Resources, Archives) and content analysis.

## Features

- 🤖 AI-powered content analysis using Ollama LLM
- 📁 PARA methodology-based organization
- 🌏 Multilingual support (English/Korean)
- 📄 Rich metadata extraction
- 🎨 Modern GUI interface
- 🔍 Intelligent content-based categorization

## Prerequisites

- Python 3.10 or higher
- Windows 10/11
- [Ollama](https://ollama.ai/) installed and running locally
- At least 8GB RAM recommended

## Installation

1. Clone this repository
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Install and start Ollama:
   - Download from [ollama.ai](https://ollama.ai)
   - Pull the required model:
     ```bash
     ollama pull llama2:3.1
     ```

## Usage

1. Start the application:
   ```bash
   python main.py
   ```

2. Using the application:
   - Select source directory
   - Click "Analyze" to start file analysis
   - Review results
   - Click "Organize" to begin file organization

## Configuration

Edit `config.json` to configure:
- Language (english/korean)
- AI model settings
- File size limits
- Backup options

## License

MIT License
