# Intelligent File Organizer (IFO)

A sophisticated file organization tool that leverages AI to automatically categorize and organize files using the PARA method (Projects, Areas, Resources, Archives). Built with Python and featuring a modern GUI interface.

## Key Features

- 🤖 **AI-Powered Analysis**: Uses Ollama LLM for intelligent content analysis and file categorization
- 📁 **PARA Methodology**: Organizes files according to the PARA system:
  - Projects: Active and upcoming work
  - Areas: Ongoing responsibilities
  - Resources: Reference materials and tools
  - Archives: Completed or inactive items
- 🎨 **Modern GUI Interface**: Built with CustomTkinter for a clean, modern look
- 🌏 **Multilingual Support**: Full support for English and Korean interfaces
- 📊 **Rich File Analysis**:
  - Comprehensive metadata extraction
  - Content-based categorization
  - File type detection
  - Document analysis (PDF, Office files, emails, images)
- ⚙️ **Advanced Features**:
  - Undo/Redo operations
  - Preview organization before applying
  - Progress tracking
  - Batch processing
  - Empty folder cleanup
  - Automatic backups

## System Requirements

- Python 3.10 or higher
- Windows 10/11
- 8GB RAM recommended
- [Ollama](https://ollama.ai/) installed and running locally

## Installation

1. Clone the repository:
```bash
git clone https://github.com/yourusername/intelligent-file-organizer.git
cd intelligent-file-organizer
```

2. Create and activate a virtual environment:
```bash
# Windows
python -m venv venv
venv\Scripts\activate

# Linux/macOS
python -m venv venv
source venv/bin/activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Install and start Ollama:
- Download from [ollama.ai](https://ollama.ai)
- Install the required model:
```bash
ollama pull mistral
```

## Quick Start

1. Run the application:
```bash
# Windows
run.bat

# Linux/macOS
./run.sh
```

2. Using the interface:
- Select your source directory
- Choose organization options:
  - Content Analysis: Uses AI to analyze file contents
  - File Type Organization: Groups by file types
  - Date Organization: Organizes by creation/modification date
  - Remove Empty Folders: Cleans up empty directories
- Click "Analyze" to scan files
- Use "Preview" to see the proposed organization
- Click "Organize" to execute the organization

## Configuration

Edit `config.json` to customize:

- Language settings (english/korean)
- AI model configuration
- File size limits
- Backup preferences
- PARA category names and paths
- Supported file extensions
- Organization rules and thresholds

## File Type Support

- Documents: .txt, .doc, .docx, .pdf, .rtf, .odt, .md, .csv, .json, .xml
- Images: .jpg, .jpeg, .png, .gif, .bmp, .tiff, .webp, .svg
- Videos: .mp4, .avi, .mov, .wmv, .flv, .mkv, .webm
- Audio: .mp3, .wav, .ogg, .m4a, .flac, .aac
- Archives: .zip, .rar, .7z, .tar, .gz, .bz2
- Code: .py, .js, .html, .css, .java, .cpp, .h, .cs, .php
- Data: .xlsx, .xls, .db, .sqlite, .sql

## Error Handling

The application includes comprehensive error handling:
- Automatic retries for failed operations
- Detailed error logging
- User-friendly error messages
- Operation rollback capability

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Acknowledgments

- [CustomTkinter](https://github.com/TomSchimansky/CustomTkinter) for the modern GUI framework
- [Ollama](https://ollama.ai/) for the AI model integration
- The PARA method by Tiago Forte