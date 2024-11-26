# Intelligent File Organizer

A Python-based intelligent file organization tool that uses Ollama LLM for content analysis and smart file categorization.

## Features

- GUI interface for easy interaction
- Intelligent file analysis using Ollama LLM
- Content-based file organization
- File type and extension-based sorting
- Date-based organization
- Pattern recognition in file names
- Safe file operations with backup functionality
- Real-time progress tracking
- Customizable organization rules

## Prerequisites

- Python 3.8 or higher
- Ollama installed and running locally
- Windows 10 or higher

## Installation

1. Clone this repository
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Ensure Ollama is installed and running with the Mistral model:
   ```bash
   ollama pull mistral
   ```

## Usage

1. Run the application:
   ```bash
   python main.py
   ```
2. Select source directory
3. Configure organization rules
4. Start the organization process

## Configuration

- Default model: Mistral
- Supported file types: Documents, Images, Videos, Audio, Archives
- Backup: Automatic backup before reorganization
- Custom rules: Can be configured through the GUI

## License

MIT License
