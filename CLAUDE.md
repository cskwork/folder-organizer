# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Intelligent File Organizer (IFO) is a Python desktop application that uses AI to automatically organize files using the PARA methodology (Projects, Areas, Resources, Archives). It features a modern GUI built with CustomTkinter and integrates with LLM providers (OpenRouter/Ollama) for intelligent content analysis and smart file renaming.

## Key Commands

### Development
```bash
# Run the application
python3 main.py
# or use platform-specific scripts:
./run.sh        # Linux/macOS  
run.bat         # Windows

# Install dependencies
pip install -r requirements.txt

# Check Python version (requires 3.10+)
python3 --version
```

### Testing
The project does not currently have automated tests. Manual testing is done through the GUI.

## Current State & Known Issues

### Code Quality Concerns
- **No type hints**: Entire codebase lacks static typing, making maintenance difficult
- **Missing tests**: No unit tests, integration tests, or test infrastructure
- **Thread safety**: Uses basic threading instead of async/await patterns
- **Configuration validation**: No validation of config.json structure or values
- **Error handling**: Basic error handling without structured logging

### UI/UX Limitations
- **Hardcoded styling**: UI colors and spacing scattered throughout code without design system
- **Poor responsiveness**: Fixed layouts don't adapt to different screen sizes
- **Limited accessibility**: No keyboard navigation, screen reader support, or ARIA labels
- **Basic interactions**: No drag-and-drop, no modern file dialogs, limited user feedback

### Architecture Issues
- **Tight coupling**: Components directly instantiate dependencies without injection
- **Singleton misuse**: ConfigManager uses singleton pattern inappropriately
- **Mixed responsibilities**: GUI class handles both UI and business logic
- **No separation of concerns**: File operations mixed with UI updates

### Performance Bottlenecks
- **Synchronous file operations**: Large directories can freeze the UI
- **No caching**: File type detection and content analysis repeated unnecessarily
- **Memory usage**: Large files loaded entirely into memory for analysis
- **No batch processing**: Files processed individually without optimization

## Improvement Priorities

### Phase 1: Foundation (High Priority)
1. Add comprehensive type hints throughout codebase
2. Implement structured logging with proper error handling
3. Add configuration validation using Pydantic
4. Extract design tokens and create consistent styling system

### Phase 2: Architecture (Medium Priority)
1. Refactor to dependency injection pattern
2. Implement async/await for file operations
3. Add comprehensive test suite (pytest)
4. Separate business logic from UI components

### Phase 3: Features (Lower Priority)
1. Add drag-and-drop file support
2. Implement real-time file watching
3. Add cloud storage integration
4. Create plugin architecture for extensibility

## Architecture

### Core Components

**Main Application Flow**: `main.py` → GUI setup → User selects directory → File analysis → Preview/Organization

**Key Classes**:
- `FileOrganizerGUI` (main.py): Main application window and UI logic
- `FileAnalyzer` (file_analyzer.py): Scans directories and extracts file metadata
- `ContentAnalyzer` (content_analyzer.py): LLM integration for content analysis and smart renaming
- `FileOrganizer` (file_organizer.py): Handles actual file movement and PARA categorization
- `ConfigManager` (config_manager.py): Manages JSON configuration and settings
- `FileRenamer` (file_renamer.py): Safe file renaming operations
- `SettingsDialog` (settings_dialog.py): Configuration UI

### Data Flow
1. User selects source directory via GUI
2. `FileAnalyzer` scans directory and collects file metadata
3. `ContentAnalyzer` sends file content to LLM for categorization and naming suggestions
4. `FileOrganizer` determines PARA categories and destination paths
5. Preview shows proposed organization before execution
6. Files are moved/renamed according to PARA structure

### LLM Integration
- Primary provider: OpenRouter (default model: google/gemini-flash-1.5-8b)
- Fallback: Local Ollama
- Configuration in `config.json` under `llm_config`
- Content analysis includes smart renaming suggestions

### PARA Organization Structure
Files are organized into:
- `1_프로젝트/` (Projects): Active work
- `2_영역/` (Areas): Ongoing responsibilities  
- `3_자료/` (Resources): Reference materials
- `4_보관/` (Archives): Completed items
- `5_기타/` (Other): Uncategorized

Language-specific folder names are configured in `config.json` under `category_names`.

### Configuration System
- Main config: `config.json` - contains LLM settings, PARA categories, file extensions, organization rules
- Smart rename feature controlled by `organization_rules.smart_rename_enabled`
- Multilingual support (English/Korean) via `language` setting

### Error Handling
- `ErrorHandler` class provides retry logic and graceful failure handling
- Operations support undo/redo functionality
- Progress tracking and cancellation support

## Development Notes

### Technology Stack
- **UI Framework**: CustomTkinter for modern appearance
- **Language Processing**: KoreanTextHandler for Korean text romanization
- **File Operations**: Threading with stop flags (needs async refactor)
- **Platform Integration**: win32com for Windows Office file analysis
- **LLM Integration**: OpenRouter/Ollama for content analysis
- **Configuration**: JSON-based with observer pattern

### File Type Support
Supports 60+ file extensions across categories:
- Documents: .txt, .doc, .docx, .pdf, .rtf, .odt, .md, .csv, .json, .xml
- Images: .jpg, .jpeg, .png, .gif, .bmp, .tiff, .webp, .svg
- Videos: .mp4, .avi, .mov, .wmv, .flv, .mkv, .webm
- Audio: .mp3, .wav, .ogg, .m4a, .flac, .aac
- Archives: .zip, .rar, .7z, .tar, .gz, .bz2
- Code: .py, .js, .html, .css, .java, .cpp, .h, .cs, .php
- Data: .xlsx, .xls, .db, .sqlite, .sql

### Common Development Patterns

**Configuration Access**:
```python
config_manager = ConfigManager()
rules = config_manager.get_organization_rules()
smart_rename_enabled = rules.get("smart_rename_enabled", True)
```

**Error Handling**:
```python
try:
    result = self.error_handler.retry_operation(operation, *args)
except RetryableError as e:
    self.logger.warning(f"Operation failed: {e}")
```

**UI Styling**:
```python
button_style = {
    "height": 38,
    "corner_radius": 8,
    "font": ("Segoe UI", 12),
    "hover_color": self.colors["accent"]
}
```

### Critical Implementation Details
- **Observer Pattern**: ConfigManager notifies components of setting changes
- **PARA Structure**: Language-specific folder names from config.json
- **Smart Renaming**: LLM-generated suggestions preserved with original extensions
- **Undo/Redo**: File operation history tracked for rollback
- **Progress Tracking**: Callback-based progress updates with cancellation support

### Development Workflow Issues
- No linting (ruff/black) configured
- No pre-commit hooks for code quality
- No CI/CD pipeline
- No dependency management (poetry/pipenv)
- No development/production environment separation