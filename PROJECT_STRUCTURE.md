# Project Reorganization Plan

## Current Issues
- Mixed async/sync implementations in root directory
- Core business logic scattered across multiple files
- No clear separation between UI, business logic, and utilities
- Configuration and documentation mixed with source code
- Test structure is good but could be better organized

## Proposed New Structure

```
intelligent-file-organizer/
├── 📁 src/                          # All source code
│   ├── 📁 core/                     # Core business logic
│   │   ├── __init__.py
│   │   ├── file_analyzer.py         # File analysis engine
│   │   ├── content_analyzer.py      # AI content analysis
│   │   ├── file_organizer.py        # Organization logic
│   │   ├── file_renamer.py          # Smart renaming
│   │   └── business_logic.py        # Main workflow orchestration
│   ├── 📁 ui/                       # User interface components
│   │   ├── __init__.py
│   │   ├── main_window.py           # Main GUI application
│   │   ├── settings_dialog.py       # Settings interface
│   │   ├── components/              # Reusable UI components
│   │   └── themes/                  # Design tokens and themes
│   ├── 📁 services/                 # Service layer
│   │   ├── __init__.py
│   │   ├── ai_service.py            # LLM integration
│   │   ├── config_service.py        # Configuration management
│   │   └── logging_service.py       # Logging utilities
│   ├── 📁 utils/                    # Utility modules
│   │   ├── __init__.py
│   │   ├── korean_utils.py          # Korean text processing
│   │   ├── error_handler.py         # Error handling
│   │   └── di_container.py          # Dependency injection
│   └── 📁 interfaces/               # Type definitions and interfaces
│       ├── __init__.py
│       └── types.py                 # All interface definitions
├── 📁 config/                       # Configuration files
│   ├── config.json                  # Main configuration
│   ├── logging.yaml                 # Logging configuration
│   └── defaults/                    # Default configurations
├── 📁 tests/                        # Test suite (current structure is good)
│   ├── unit/
│   ├── integration/
│   └── fixtures/
├── 📁 docs/                         # Documentation
│   ├── README.md                    # Main documentation
│   ├── SETUP.md                     # Installation guide
│   ├── USAGE.md                     # User guide
│   ├── API.md                       # Developer API docs
│   └── ARCHITECTURE.md              # System architecture
├── 📁 scripts/                      # Utility scripts
│   ├── run.py                       # Main entry point
│   ├── setup.py                     # Setup and installation
│   ├── test.py                      # Test runner
│   └── build/                       # Build scripts
├── 📁 assets/                       # Static assets
│   ├── icons/
│   ├── themes/
│   └── examples/
├── 📁 logs/                         # Log files
├── .env.example                     # Environment template
├── .gitignore                       # Git ignore rules
├── requirements.txt                 # Python dependencies
├── requirements-dev.txt             # Development dependencies
├── pyproject.toml                   # Modern Python project config
├── Makefile                         # Common commands
└── main.py                          # Simple entry point
```

## Key Improvements

### 1. Clear Separation of Concerns
- **src/core/**: Pure business logic, no UI dependencies
- **src/ui/**: All user interface code
- **src/services/**: External integrations and services
- **src/utils/**: Reusable utilities
- **config/**: All configuration separate from code

### 2. Simplified Entry Points
- **main.py**: Simple entry point that imports from src/
- **scripts/run.py**: Advanced runner with options
- **Makefile**: Common commands (run, test, build, etc.)

### 3. Better Configuration Management
- Environment-based configuration
- Separate dev/prod configs
- Centralized in config/ directory

### 4. Enhanced Documentation
- Clear separation of user vs developer docs
- Step-by-step guides
- Architecture documentation

### 5. Modern Python Practices
- pyproject.toml for modern dependency management
- Type hints throughout
- Proper package structure