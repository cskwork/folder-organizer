"""
Unit tests for the async file analyzer.
"""

import pytest
import os
import tempfile
from unittest.mock import Mock, AsyncMock, patch
from async_file_analyzer import AsyncFileAnalyzer


class TestAsyncFileAnalyzer:
    """Test cases for async file analyzer."""
    
    @pytest.fixture
    def analyzer(self, mock_config_manager, mock_content_analyzer):
        """Create file analyzer with mocks."""
        return AsyncFileAnalyzer(mock_config_manager, mock_content_analyzer)
    
    @pytest.mark.asyncio
    async def test_analyze_file_async_text_file(self, analyzer, temp_directory):
        """Test analyzing a text file."""
        # Create test file
        test_file = os.path.join(temp_directory, "test.txt")
        with open(test_file, 'w', encoding='utf-8') as f:
            f.write("This is a test file.")
        
        # Mock content analyzer
        analyzer.content_analyzer.analyze_content_async.return_value = {
            "success": True,
            "category": "documents",
            "suggested_name": "test_document"
        }
        
        result = await analyzer.analyze_file_async(test_file)
        
        assert result["file_name"] == "test.txt"
        assert result["file_type"] == "txt"
        assert result["category"] == "documents"
        assert result["file_size"] > 0
        assert "content_analysis" in result
    
    @pytest.mark.asyncio
    async def test_analyze_file_async_image_file(self, analyzer, temp_directory):
        """Test analyzing an image file."""
        # Create test image file
        test_file = os.path.join(temp_directory, "test.jpg")
        with open(test_file, 'wb') as f:
            f.write(b"fake_image_data")
        
        result = await analyzer.analyze_file_async(test_file, use_content=False)
        
        assert result["file_name"] == "test.jpg"
        assert result["file_type"] == "jpg"
        assert result["category"] == "images"
        assert result["file_size"] > 0
    
    @pytest.mark.asyncio
    async def test_analyze_directory_async(self, analyzer, temp_directory, sample_files):
        """Test analyzing a directory."""
        # Mock content analyzer
        analyzer.content_analyzer.analyze_content_async.return_value = {
            "success": True,
            "category": "documents"
        }
        
        # Mock config manager
        analyzer.config_manager.get_setting.return_value = 5  # batch_size
        
        results = await analyzer.analyze_directory_async(temp_directory)
        
        assert isinstance(results, dict)
        assert len(results) == len(sample_files)
        
        # Check that all files were analyzed
        for filename in sample_files:
            file_path = sample_files[filename]
            assert file_path in results
            assert "file_type" in results[file_path]
    
    @pytest.mark.asyncio
    async def test_analyze_directory_async_with_cancellation(self, analyzer, temp_directory):
        """Test directory analysis with cancellation."""
        # Cancel immediately
        analyzer._cancelled.set()
        
        results = await analyzer.analyze_directory_async(temp_directory)
        
        # Should return empty results due to cancellation
        assert isinstance(results, dict)
        assert len(results) == 0
    
    @pytest.mark.asyncio
    async def test_get_file_stats_async(self, analyzer, temp_directory):
        """Test getting file statistics."""
        test_file = os.path.join(temp_directory, "test.txt")
        with open(test_file, 'w') as f:
            f.write("test content")
        
        stats = await analyzer._get_file_stats_async(test_file)
        
        assert "file_size" in stats
        assert "created_date" in stats
        assert "modified_date" in stats
        assert stats["file_size"] > 0
    
    @pytest.mark.asyncio
    async def test_get_file_type_async(self, analyzer, temp_directory):
        """Test getting file type information."""
        test_file = os.path.join(temp_directory, "test.py")
        with open(test_file, 'w') as f:
            f.write("print('hello')")
        
        file_type_info = await analyzer._get_file_type_async(test_file)
        
        assert file_type_info["file_type"] == "py"
        assert file_type_info["category"] == "code"
        assert file_type_info["extension"] == ".py"
    
    @pytest.mark.asyncio
    async def test_extract_image_metadata(self, analyzer, temp_directory):
        """Test extracting image metadata."""
        # Create a minimal valid image file for testing
        test_file = os.path.join(temp_directory, "test.jpg")
        with open(test_file, 'wb') as f:
            # Write minimal JPEG header
            f.write(b'\xff\xd8\xff\xe0\x00\x10JFIF\x00\x01\x01\x01\x00H\x00H\x00\x00\xff\xdb')
        
        # Mock the Image.open to avoid dependency on actual image processing
        with patch('async_file_analyzer.Image') as mock_image:
            mock_img = Mock()
            mock_img.width = 100
            mock_img.height = 200
            mock_img.format = "JPEG"
            mock_img.mode = "RGB"
            mock_image.open.return_value.__enter__.return_value = mock_img
            
            metadata = await analyzer._get_metadata_async(test_file)
            
            assert isinstance(metadata, dict)
    
    def test_should_analyze_content(self, analyzer):
        """Test content analysis decision."""
        # Mock config for max content analysis size
        analyzer.config_manager.get_setting.side_effect = lambda key, default: {
            'max_content_analysis_size': 10 * 1024 * 1024  # 10MB
        }.get(key, default)
        
        # Text files should be analyzed (mock file size as small)
        with patch('os.path.getsize', return_value=1024):  # 1KB
            assert analyzer._should_analyze_content("/path/to/file.txt")
        
        # Large files should not be analyzed
        with patch('os.path.getsize', return_value=50 * 1024 * 1024):  # 50MB
            assert not analyzer._should_analyze_content("/path/to/large.txt")
        
        # Archive files should not be analyzed
        assert not analyzer._should_analyze_content("/path/to/file.zip")
        assert not analyzer._should_analyze_content("/path/to/file.mp4")
    
    def test_stop(self, analyzer):
        """Test stopping the analyzer."""
        analyzer.stop()
        assert analyzer._cancelled.is_set()
    
    @pytest.mark.asyncio
    async def test_analyze_file_async_with_error(self, analyzer, temp_directory):
        """Test file analysis with error handling."""
        # Try to analyze non-existent file
        result = await analyzer.analyze_file_async("/nonexistent/file.txt")
        
        assert "error" in result
        assert result["file_type"] == "unknown"
        assert result["category"] == "other"