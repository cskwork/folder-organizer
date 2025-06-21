"""
Pytest configuration and shared fixtures.
"""

import pytest
import asyncio
import tempfile
import shutil
import os
from pathlib import Path
from typing import Dict, Any
from unittest.mock import Mock, AsyncMock

# Add src to path
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(__file__)), 'src'))

# Import the interfaces and implementations
from IService import IFileAnalyzer, IFileOrganizer
from Utils.config_manager import ConfigManager

@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()

@pytest.fixture
def mock_container():
    """Create a simple mock container for testing."""
    return Mock()

@pytest.fixture
def temp_directory():
    """Create a temporary directory for testing."""
    temp_dir = tempfile.mkdtemp()
    yield temp_dir
    shutil.rmtree(temp_dir, ignore_errors=True)

@pytest.fixture
def sample_files(temp_directory):
    """Create sample files for testing."""
    files = {}
    
    # Create various file types
    test_files = [
        ("document.txt", "This is a test document about project management."),
        ("image.jpg", b"fake_image_data"),
        ("code.py", "print('Hello, world!')"),
        ("data.json", '{"key": "value", "number": 42}'),
        ("archive.zip", b"fake_zip_data"),
        ("presentation.pdf", b"fake_pdf_data"),
    ]
    
    for filename, content in test_files:
        file_path = os.path.join(temp_directory, filename)
        if isinstance(content, str):
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
        else:
            with open(file_path, 'wb') as f:
                f.write(content)
        files[filename] = file_path
    
    return files

@pytest.fixture
def mock_config_manager():
    """Create a mock configuration manager."""
    mock = Mock()

    def get_setting_se(key, default=None):
        if key == "llm_config":
            return {
                "default_provider": "openrouter",
                "providers": {
                    "openrouter": {
                        "url": "https://openrouter.ai/api/v1/chat/completions",
                        "default_model": "google/gemini-pro"
                    }
                }
            }
        if key == "content_analysis":
            return {}
        return default if default is not None else True

    mock.get_setting.side_effect = get_setting_se
    mock.get_organization_rules.return_value = {
        "use_content_analysis": True,
        "use_file_type": True,
        "use_date": True,
        "smart_rename_enabled": True
    }
    mock.observers = []
    mock.add_observer = Mock()
    mock.remove_observer = Mock()
    return mock

@pytest.fixture
def mock_file_analyzer():
    """Create a mock file analyzer."""
    mock = AsyncMock()
    mock.analyze_directory_async.return_value = {
        "/path/to/file1.txt": {
            "file_type": "txt",
            "category": "documents",
            "content_analysis": {
                "success": True,
                "category": "projects",
                "suggested_name": "project_notes",
                "confidence": 0.8
            }
        }
    }
    mock.analyze_file_async.return_value = {
        "file_type": "txt",
        "category": "documents"
    }
    mock.stop = Mock()
    return mock

@pytest.fixture
def mock_content_analyzer():
    """Create a mock content analyzer."""
    mock = AsyncMock()
    mock.analyze_content_async.return_value = {
        "success": True,
        "category": "projects",
        "suggested_name": "project_notes",
        "confidence": 0.8,
        "keywords": ["project", "management", "notes"]
    }
    mock.suggest_name_async.return_value = "suggested_filename"
    return mock

@pytest.fixture
def mock_file_organizer():
    """Create a mock file organizer."""
    mock = AsyncMock()
    mock.organize_files_async.return_value = None
    mock.determine_para_category.return_value = ("projects", "development")
    mock.get_stats.return_value = {
        "processed": 5,
        "succeeded": 4,
        "failed": 1,
        "skipped": 0
    }
    mock.undo.return_value = True
    mock.redo.return_value = True
    mock.stop = Mock()
    return mock

@pytest.fixture
def mock_file_renamer():
    """Create a mock file renamer."""
    mock = AsyncMock()
    mock.rename_file_async.return_value = "/new/path/to/file.txt"
    mock.generate_safe_name.return_value = "safe_filename.txt"
    return mock

@pytest.fixture
def mock_error_handler():
    """Create a mock error handler."""
    mock = AsyncMock()
    mock.retry_operation_async.side_effect = lambda op, *args, **kwargs: op(*args, **kwargs)
    mock.log_error = Mock()
    return mock

@pytest.fixture
def mock_ui_service():
    """Create a mock UI service."""
    mock = Mock()
    mock.show_message = Mock()
    mock.show_error = Mock()
    mock.show_success = Mock()
    mock.ask_confirmation.return_value = True
    mock.select_directory.return_value = "/selected/directory"
    return mock

@pytest.fixture
def mock_progress_reporter():
    """Create a mock progress reporter."""
    mock = Mock()
    mock.report_progress = Mock()
    mock.is_cancelled.return_value = False
    mock.cancel = Mock()
    return mock

@pytest.fixture
def real_config_manager(temp_directory):
    """Create a real configuration manager with temporary config file."""
    config_path = os.path.join(temp_directory, "test_config.json")
    
    # Clear any existing singleton
    ConfigManager._instance = None
    
    config_manager = ConfigManager(config_path)
    yield config_manager
    
    # Clean up
    ConfigManager._instance = None

@pytest.fixture
def analysis_results():
    """Sample analysis results for testing."""
    return {
        "/path/to/document.txt": {
            "file_type": "txt",
            "category": "documents",
            "file_size": 1024,
            "content_analysis": {
                "success": True,
                "category": "projects",
                "suggested_name": "project_notes",
                "confidence": 0.8
            }
        },
        "/path/to/image.jpg": {
            "file_type": "jpg",
            "category": "images",
            "file_size": 2048,
            "content_analysis": {
                "success": False,
                "error": "Binary file not analyzed"
            }
        }
    }

@pytest.fixture
def organization_options():
    """Default organization options for testing."""
    return {
        "use_content_analysis": True,
        "use_file_type": True,
        "use_date": True,
        "remove_empty_folders": True
    }