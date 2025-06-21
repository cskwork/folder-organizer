"""
Unit tests for the file analyzer.
"""

import pytest
import os
import tempfile
import sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'src'))

from unittest.mock import Mock, patch
from Service.file_analyzer import FileAnalyzer


class TestFileAnalyzer:
    """Test cases for file analyzer."""
    
    @pytest.fixture
    def analyzer(self, mock_config_manager):
        """Create file analyzer with mocks."""
        return FileAnalyzer(mock_config_manager)
    
    def test_analyze_file_text_file(self, analyzer, temp_directory):
        """Test analyzing a text file."""
        # Create test file
        test_file = os.path.join(temp_directory, "test.txt")
        with open(test_file, 'w', encoding='utf-8') as f:
            f.write("This is a test file.")
        
        # Mock content analyzer
        with patch.object(analyzer.content_analyzer, '_query_llm') as mock_query:
            mock_query.return_value = "Category: documents\nSuggested name: test_document"
            
            result = analyzer.analyze_file(test_file)
            
            assert "metadata" in result
            assert result["metadata"]["name"] == "test.txt"
            assert result["metadata"]["extension"] == ".txt"
            assert result["metadata"]["size"] > 0
    
    def test_analyze_file_image_file(self, analyzer, temp_directory):
        """Test analyzing an image file."""
        # Create test image file
        test_file = os.path.join(temp_directory, "test.jpg")
        with open(test_file, 'wb') as f:
            f.write(b"fake_image_data")
        
        result = analyzer.analyze_file(test_file, use_content=False)
        
        assert "metadata" in result
        assert result["metadata"]["name"] == "test.jpg"
        assert result["metadata"]["extension"] == ".jpg"
        assert result["metadata"]["size"] > 0
    
    def test_analyze_directory(self, analyzer, temp_directory, sample_files):
        """Test analyzing a directory."""
        # Mock content analyzer
        with patch.object(analyzer.content_analyzer, '_query_llm') as mock_query:
            mock_query.return_value = "Category: documents"
            
            # Mock config manager
            analyzer.config_manager.get_setting.return_value = 5  # batch_size
            
            results = analyzer.analyze_directory(temp_directory)
            
            assert isinstance(results, dict)
            assert len(results) > 0
    
    def test_stop(self, analyzer):
        """Test stopping the analyzer."""
        analyzer.stop()
        assert analyzer.stop_flag.is_set() 