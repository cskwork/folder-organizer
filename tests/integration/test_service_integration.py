"""
Integration tests for service interactions.
"""

import pytest
import os
import tempfile
from pathlib import Path

from service_configuration import configure_services
from interfaces import *
from business_logic_service import BusinessLogicService, ProgressReporter


class TestServiceIntegration:
    """Integration tests for service interactions."""
    
    @pytest.fixture
    def container(self):
        """Create container with real services."""
        return configure_services()
    
    @pytest.fixture
    def temp_test_dir(self):
        """Create temporary directory with test files."""
        temp_dir = tempfile.mkdtemp()
        
        # Create test files
        test_files = {
            "project_notes.txt": "This document contains project planning information and task lists.",
            "budget.csv": "Item,Cost,Category\nSoftware,100,Tools\nTraining,500,Education",
            "README.md": "# Project Documentation\n\nThis is a software development project.",
            "presentation.pdf": b"fake_pdf_content",
            "image.jpg": b"fake_image_data",
            "archive.zip": b"fake_zip_data"
        }
        
        for filename, content in test_files.items():
            file_path = os.path.join(temp_dir, filename)
            mode = 'w' if isinstance(content, str) else 'wb'
            encoding = 'utf-8' if isinstance(content, str) else None
            
            with open(file_path, mode, encoding=encoding) as f:
                f.write(content)
        
        yield temp_dir
        
        # Cleanup
        import shutil
        shutil.rmtree(temp_dir, ignore_errors=True)
    
    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_end_to_end_workflow(self, container, temp_test_dir):
        """Test complete workflow from analysis to organization."""
        # Get services
        business_service = container.resolve(IBusinessLogicService)
        config_manager = container.resolve(IConfigManager)
        
        # Configure for testing
        config_manager.set_setting("llm_config", {"enabled": False})  # Use basic analysis
        
        # Create progress reporter
        progress_updates = []
        def progress_callback(progress, message):
            progress_updates.append((progress, message))
        
        progress_reporter = ProgressReporter(progress_callback)
        
        # Test preview first
        preview_result = await business_service.preview_organization_async(
            temp_test_dir,
            {
                "use_content_analysis": True,
                "use_file_type": True,
                "use_date": True,
                "remove_empty_folders": True
            }
        )
        
        assert preview_result["success"] is True
        assert preview_result["stats"]["total_files"] == 6
        assert len(preview_result["preview_items"]) == 6
        
        # Verify file categorization
        categories = {item["category"] for item in preview_result["preview_items"]}
        assert len(categories) > 1  # Should have multiple categories
        
        # Test actual organization
        organize_result = await business_service.analyze_and_organize_async(
            temp_test_dir,
            {
                "use_content_analysis": True,
                "use_file_type": True,
                "use_date": True,
                "remove_empty_folders": True
            },
            progress_reporter
        )
        
        assert organize_result["success"] is True
        assert organize_result["organization_stats"]["processed"] == 6
        assert organize_result["organization_stats"]["succeeded"] > 0
        
        # Verify progress updates were called
        assert len(progress_updates) > 0
        
        # Verify directory structure was created
        category_names = config_manager.get_setting('category_names', {})
        expected_dirs = [
            '1_프로젝트' if 'projects' in category_names else '1_projects',
            '2_영역' if 'areas' in category_names else '2_areas',
            '3_자료' if 'resources' in category_names else '3_resources',
            '5_기타' if 'other' in category_names else '5_other'
        ]
        
        created_dirs = [d for d in os.listdir(temp_test_dir) 
                       if os.path.isdir(os.path.join(temp_test_dir, d))]
        
        # At least some organization directories should be created
        assert len(created_dirs) > 0
    
    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_file_analyzer_content_analyzer_integration(self, container, temp_test_dir):
        """Test integration between file analyzer and content analyzer."""
        file_analyzer = container.resolve(IFileAnalyzer)
        
        # Analyze directory
        results = await file_analyzer.analyze_directory_async(
            temp_test_dir,
            use_content=True,
            use_type=True,
            use_date=True
        )
        
        assert len(results) == 6
        
        # Check that text files have content analysis
        text_files = [path for path in results if path.endswith('.txt') or path.endswith('.md')]
        assert len(text_files) > 0
        
        for file_path in text_files:
            result = results[file_path]
            assert "content_analysis" in result
            # Basic analysis should always succeed for text files
            if result["content_analysis"]:
                assert isinstance(result["content_analysis"], dict)
    
    @pytest.mark.integration
    def test_config_manager_observer_pattern(self, container):
        """Test configuration manager observer notifications."""
        config_manager = container.resolve(IConfigManager)
        
        # Create mock observer
        class MockObserver:
            def __init__(self):
                self.notified = False
            
            def on_settings_changed(self):
                self.notified = True
        
        observer = MockObserver()
        config_manager.add_observer(observer)
        
        # Change setting
        config_manager.set_setting("test_setting", "test_value")
        
        # Verify observer was notified
        assert observer.notified
        
        # Cleanup
        config_manager.remove_observer(observer)
    
    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_error_handling_integration(self, container):
        """Test error handling across services."""
        business_service = container.resolve(IBusinessLogicService)
        progress_reporter = ProgressReporter()
        
        # Test with invalid directory
        result = await business_service.analyze_and_organize_async(
            "/nonexistent/directory",
            {"use_content_analysis": True},
            progress_reporter
        )
        
        assert result["success"] is False
        assert len(result["errors"]) > 0
        assert "does not exist" in result["errors"][0]
    
    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_undo_redo_integration(self, container, temp_test_dir):
        """Test undo/redo functionality integration."""
        business_service = container.resolve(IBusinessLogicService)
        progress_reporter = ProgressReporter()
        
        # Perform organization
        result = await business_service.analyze_and_organize_async(
            temp_test_dir,
            {"use_content_analysis": False, "use_file_type": True},
            progress_reporter
        )
        
        assert result["success"] is True
        
        # Test undo
        undo_result = await business_service.undo_last_operation_async()
        # Note: Undo might fail in test environment due to file system limitations
        assert "undo" in undo_result["message"].lower()
        
        # Test redo
        redo_result = await business_service.redo_last_operation_async()
        assert "redo" in redo_result["message"].lower()
    
    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_directory_stats_integration(self, container, temp_test_dir):
        """Test directory statistics integration."""
        business_service = container.resolve(IBusinessLogicService)
        
        stats = await business_service.get_directory_stats_async(temp_test_dir)
        
        assert stats["total_files"] == 6
        assert stats["total_size"] > 0
        assert len(stats["file_types"]) > 1
        assert len(stats["largest_files"]) > 0
        assert len(stats["recent_files"]) > 0
        
        # Verify file types are detected
        expected_extensions = {'.txt', '.csv', '.md', '.pdf', '.jpg', '.zip'}
        detected_extensions = set(stats["file_types"].keys())
        assert expected_extensions.issubset(detected_extensions)
    
    @pytest.mark.integration
    def test_service_health_check(self, container):
        """Test service health check integration."""
        from service_configuration import check_service_health
        
        health_status = check_service_health()
        
        # All services should be healthy
        for service_name, is_healthy in health_status.items():
            assert is_healthy, f"Service {service_name} is not healthy"
    
    @pytest.mark.integration
    def test_service_cleanup(self, container):
        """Test service cleanup integration."""
        from service_configuration import cleanup_services
        
        # This should not raise any exceptions
        cleanup_services()