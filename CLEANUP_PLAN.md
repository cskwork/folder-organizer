# Cleanup Plan - Remove Duplicates and Unused Files

## Analysis of Current Files

### Duplicate Implementations Found:
1. **GUI**: `main.py` (sync) vs `async_gui.py` (async)
2. **File Analyzer**: `file_analyzer.py` (sync) vs `async_file_analyzer.py` (async)
3. **Content Analyzer**: `content_analyzer.py` (sync) vs `async_content_analyzer.py` (async)  
4. **File Organizer**: `file_organizer.py` (sync) vs `async_file_organizer.py` (async)

### Usage Analysis:
- **main.py**: Currently used as main entry point, uses sync versions
- **async_gui.py**: Alternative implementation with dependency injection
- **service_configuration.py**: Uses async versions
- **business_logic_service.py**: Modern service layer
- **tests/**: Has tests for both sync and async versions

## Recommended Cleanup Strategy:

### Keep (Modern Architecture):
- ✅ `async_*.py` files (more modern, better performance)
- ✅ `business_logic_service.py` (clean service layer)
- ✅ `di_container.py` (dependency injection)
- ✅ `service_configuration.py` (modern service setup)
- ✅ `interfaces.py` (clean abstractions)
- ✅ `design_tokens.py` (modern UI system)

### Remove (Legacy/Duplicate):
- ❌ `file_analyzer.py` (duplicate of async version)
- ❌ `content_analyzer.py` (duplicate of async version)
- ❌ `file_organizer.py` (duplicate of async version)
- ❌ `main.py` (replace with modern entry point)

### Keep and Reorganize:
- ✅ `config_manager.py` → `src/services/config_service.py`
- ✅ `korean_utils.py` → `src/utils/`
- ✅ `error_handler.py` → `src/utils/`
- ✅ `logging_config.py` → `src/services/logging_service.py`
- ✅ `file_renamer.py` → `src/core/`
- ✅ `settings_dialog.py` → `src/ui/`

### Unused Files to Remove:
- ❌ `ui_service.py` (seems unused)
- ❌ `install_mecab.bat` (MeCab was removed)
- ❌ `PHASE2_IMPLEMENTATION_SUMMARY.md` (development doc)

## New Entry Point Strategy:
Create a simple `main.py` that uses the modern async architecture but provides a simple sync interface for users.