"""
Unit tests for the business logic service.
"""

import pytest
import asyncio
from unittest.mock import AsyncMock, Mock, patch
from business_logic_service import BusinessLogicService, ProgressReporter


class TestProgressReporter:
    """Test cases for progress reporter."""
    
    def test_progress_reporter_creation(self):
        """Test progress reporter creation."""
        callback = Mock()
        reporter = ProgressReporter(callback)
        
        assert reporter._callback == callback
        assert not reporter.is_cancelled()
    
    def test_report_progress(self):
        """Test progress reporting."""
        callback = Mock()
        reporter = ProgressReporter(callback)
        
        reporter.report_progress(50, 100, "Testing")
        
        callback.assert_called_once_with(50.0, "Testing")
    
    def test_cancel(self):
        """Test progress cancellation."""
        reporter = ProgressReporter()
        
        assert not reporter.is_cancelled()
        reporter.cancel()
        assert reporter.is_cancelled()


class TestBusinessLogicService:
    """Test cases for business logic service."""
    
    @pytest.fixture
    def service(self, mock_file_analyzer, mock_file_organizer, mock_config_manager):
        """Create business logic service with mocks."""
        return BusinessLogicService(
            mock_file_analyzer,
            mock_file_organizer,
            mock_config_manager
        )
    
    @pytest.mark.asyncio
    async def test_preview_organization_async(self, service, mock_file_analyzer, mock_config_manager):
        """Test organization preview."""
        # Setup mocks
        mock_file_analyzer.analyze_directory_async.return_value = {
            "/test/file.txt": {
                "file_type": "txt",
                "category": "documents",
                "content_analysis": {
                    "success": True,
                    "suggested_name": "test_file",
                    "category": "projects"
                }
            }
        }
        
        mock_config_manager.get_organization_rules.return_value = {
            "smart_rename_enabled": True
        }
        
        mock_config_manager.get_setting.return_value = {
            "projects": "1_Projects"
        }
        
        # Mock directory existence
        with patch('os.path.exists', return_value=True), \
             patch('os.path.isdir', return_value=True):
            # Test preview
            result = await service.preview_organization_async(
                "/test/directory",
                {"use_content_analysis": True}
            )
        
        assert result["success"] is True
        assert len(result["preview_items"]) == 1
        assert result["stats"]["total_files"] == 1
        assert result["stats"]["smart_renames"] == 1
    
    @pytest.mark.asyncio
    async def test_analyze_and_organize_async_success(self, service, mock_file_analyzer, 
                                                    mock_file_organizer, mock_progress_reporter):
        """Test successful analyze and organize operation."""
        # Setup mocks
        mock_file_analyzer.analyze_directory_async.return_value = {
            "/test/file.txt": {"file_type": "txt", "category": "documents"}
        }
        
        mock_file_organizer.get_stats.return_value = {
            "processed": 1,
            "succeeded": 1,
            "failed": 0,
            "skipped": 0
        }
        
        # Mock directory existence
        with patch('os.path.exists', return_value=True), \
             patch('os.path.isdir', return_value=True):
            # Test operation
            result = await service.analyze_and_organize_async(
                "/test/directory",
                {"use_content_analysis": True},
                mock_progress_reporter
            )
        
        assert result["success"] is True
        assert "analysis_results" in result
        assert "organization_stats" in result
        assert result["organization_stats"]["succeeded"] == 1
        
        # Verify calls
        mock_file_analyzer.analyze_directory_async.assert_called_once()
        mock_file_organizer.organize_files_async.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_analyze_and_organize_async_invalid_directory(self, service, mock_progress_reporter):
        """Test analyze and organize with invalid directory."""
        result = await service.analyze_and_organize_async(
            "/nonexistent/directory",
            {"use_content_analysis": True},
            mock_progress_reporter
        )
        
        assert result["success"] is False
        assert len(result["errors"]) > 0
        assert "does not exist" in result["errors"][0]
    
    @pytest.mark.asyncio
    async def test_undo_last_operation_async(self, service, mock_file_organizer):
        """Test undo operation."""
        mock_file_organizer.undo.return_value = True
        
        result = await service.undo_last_operation_async()
        
        assert result["success"] is True
        assert "successfully" in result["message"]
        mock_file_organizer.undo.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_redo_last_operation_async(self, service, mock_file_organizer):
        """Test redo operation."""
        mock_file_organizer.redo.return_value = True
        
        result = await service.redo_last_operation_async()
        
        assert result["success"] is True
        assert "successfully" in result["message"]
        mock_file_organizer.redo.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_get_directory_stats_async(self, service, temp_directory, sample_files):
        """Test directory statistics."""
        stats = await service.get_directory_stats_async(temp_directory)
        
        assert stats["total_files"] > 0
        assert stats["total_size"] > 0
        assert isinstance(stats["file_types"], dict)
        assert isinstance(stats["largest_files"], list)
        assert isinstance(stats["recent_files"], list)
    
    def test_stop_all_operations(self, service, mock_file_analyzer, mock_file_organizer):
        """Test stopping all operations."""
        service.stop_all_operations()
        
        mock_file_analyzer.stop.assert_called_once()
        mock_file_organizer.stop.assert_called_once()
    
    def test_get_operation_history(self, service):
        """Test getting operation history."""
        history = service.get_operation_history()
        
        assert isinstance(history, list)
        # Initially empty
        assert len(history) == 0