"""
Unit tests for the async content analyzer.
"""

import pytest
import asyncio
import aiohttp
from unittest.mock import Mock, AsyncMock, patch
from async_content_analyzer import AsyncContentAnalyzer


class TestAsyncContentAnalyzer:
    """Test cases for async content analyzer."""
    
    @pytest.fixture
    def analyzer(self, mock_config_manager):
        """Create content analyzer with mock config."""
        return AsyncContentAnalyzer(mock_config_manager)
    
    @pytest.mark.asyncio
    async def test_analyze_content_async_with_content(self, analyzer):
        """Test content analysis with provided content."""
        content = "This is a project document about software development."
        
        # Mock LLM config
        analyzer.config_manager.get_setting.return_value = {
            "enabled": False  # Use basic analysis
        }
        
        result = await analyzer.analyze_content_async("/test/file.txt", content)
        
        assert result["success"] is True
        assert "category" in result
        assert "suggested_name" in result
        assert "keywords" in result
        assert isinstance(result["keywords"], list)
    
    @pytest.mark.asyncio
    async def test_analyze_content_async_insufficient_content(self, analyzer):
        """Test analysis with insufficient content."""
        content = "short"
        
        result = await analyzer.analyze_content_async("/test/file.txt", content)
        
        assert result["success"] is False
        assert "Insufficient content" in result["error"]
    
    @pytest.mark.asyncio
    async def test_read_text_file_async(self, analyzer, temp_directory):
        """Test reading text file content."""
        import os
        test_file = os.path.join(temp_directory, "test.txt")
        test_content = "This is test content for analysis."
        
        # Mock the max_content_size setting properly
        analyzer.config_manager.get_setting.side_effect = lambda key, default: {
            'max_content_size': 50000
        }.get(key, default)
        
        with open(test_file, 'w', encoding='utf-8') as f:
            f.write(test_content)
        
        content = await analyzer._read_text_file_async(test_file)
        
        assert content == test_content
    
    @pytest.mark.asyncio
    async def test_read_text_file_async_encoding_fallback(self, analyzer, temp_directory):
        """Test reading text file with encoding fallback."""
        import os
        test_file = os.path.join(temp_directory, "test_encoding.txt")
        
        # Mock the max_content_size setting properly
        analyzer.config_manager.get_setting.side_effect = lambda key, default: {
            'max_content_size': 50000
        }.get(key, default)
        
        # Write file with different encoding
        with open(test_file, 'w', encoding='utf-8') as f:
            f.write("Test content with special chars: àáâã")
        
        content = await analyzer._read_text_file_async(test_file)
        
        assert "Test content" in content
    
    @pytest.mark.asyncio
    async def test_extract_pdf_text_async(self, analyzer, temp_directory):
        """Test PDF text extraction."""
        import os
        test_file = os.path.join(temp_directory, "test.pdf")
        
        # Create fake PDF file
        with open(test_file, 'wb') as f:
            f.write(b"fake_pdf_content")
        
        # Mock PDF reader
        with patch('PyPDF2.PdfReader') as mock_pdf_reader:
            mock_page = Mock()
            mock_page.extract_text.return_value = "PDF text content"
            mock_pdf_reader.return_value.pages = [mock_page]
            
            content = await analyzer._extract_pdf_text_async(test_file)
            
            assert "PDF text content" in content
    
    @pytest.mark.asyncio
    async def test_extract_office_text_async(self, analyzer, temp_directory):
        """Test Office document text extraction."""
        import os
        test_file = os.path.join(temp_directory, "test.docx")
        
        # Create fake docx file
        with open(test_file, 'wb') as f:
            f.write(b"fake_docx_content")
        
        # Mock docx library
        with patch('docx.Document') as mock_docx_document:
            mock_paragraph = Mock()
            mock_paragraph.text = "Document paragraph text"
            mock_docx_document.return_value.paragraphs = [mock_paragraph]
            
            content = await analyzer._extract_office_text_async(test_file)
            
            assert "Document paragraph text" in content
    
    @pytest.mark.asyncio
    async def test_analyze_with_openrouter_async(self, analyzer):
        """Test analysis using OpenRouter API."""
        content = "This is a test document."
        file_path = "/test/file.txt"
        
        llm_config = {
            "api_key": "test_key",
            "model": "test_model"
        }
        
        # Mock HTTP session
        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.json.return_value = {
            "choices": [{
                "message": {
                    "content": '{"category": "projects", "confidence": 0.8, "suggested_name": "test_doc"}'
                }
            }]
        }
        
        with patch.object(analyzer, '_get_session') as mock_get_session:
            mock_session = AsyncMock()
            mock_session.post.return_value.__aenter__.return_value = mock_response
            mock_get_session.return_value = mock_session
            
            result = await analyzer._analyze_with_openrouter_async(content, file_path, llm_config)
            
            assert result["success"] is True
            assert result["category"] == "projects"
            assert result["confidence"] == 0.8
    
    @pytest.mark.asyncio
    async def test_analyze_with_ollama_async(self, analyzer):
        """Test analysis using Ollama API."""
        content = "This is a test document."
        file_path = "/test/file.txt"
        
        llm_config = {
            "ollama_model": "test_model",
            "ollama_url": "http://localhost:11434"
        }
        
        # Mock HTTP session
        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.json.return_value = {
            "response": '{"category": "areas", "confidence": 0.7, "suggested_name": "area_doc"}'
        }
        
        with patch.object(analyzer, '_get_session') as mock_get_session:
            mock_session = AsyncMock()
            mock_session.post.return_value.__aenter__.return_value = mock_response
            mock_get_session.return_value = mock_session
            
            result = await analyzer._analyze_with_ollama_async(content, file_path, llm_config)
            
            assert result["success"] is True
            assert result["category"] == "areas"
            assert result["confidence"] == 0.7
    
    @pytest.mark.asyncio
    async def test_basic_content_analysis_async(self, analyzer):
        """Test basic content analysis without LLM."""
        content = "This is a project management document with tasks and todos."
        file_path = "/test/project.txt"
        
        result = await analyzer._basic_content_analysis_async(content, file_path)
        
        assert result["success"] is True
        assert "category" in result
        assert "suggested_name" in result
        assert "keywords" in result
        assert len(result["keywords"]) > 0
    
    @pytest.mark.asyncio
    async def test_suggest_name_async(self, analyzer):
        """Test name suggestion."""
        content = "Software development project notes."
        
        # Mock analyze_content_async
        analyzer.analyze_content_async = AsyncMock(return_value={
            "success": True,
            "suggested_name": "software_dev_notes"
        })
        
        suggested_name = await analyzer.suggest_name_async("/test/file.txt", content)
        
        assert suggested_name == "software_dev_notes"
    
    @pytest.mark.asyncio
    async def test_suggest_name_async_failure(self, analyzer):
        """Test name suggestion with analysis failure."""
        # Mock analyze_content_async to raise exception
        analyzer.analyze_content_async = AsyncMock(side_effect=Exception("Analysis failed"))
        
        suggested_name = await analyzer.suggest_name_async("/test/file.txt", "content")
        
        assert suggested_name is None
    
    def test_create_analysis_prompt(self, analyzer):
        """Test LLM prompt creation."""
        content = "Test content for analysis."
        file_path = "/test/file.txt"
        
        prompt = analyzer._create_analysis_prompt(content, file_path)
        
        assert "file.txt" in prompt
        assert "Test content" in prompt
        assert "JSON" in prompt
        assert "category" in prompt
    
    def test_parse_llm_response(self, analyzer):
        """Test parsing LLM response."""
        data = {
            "choices": [{
                "message": {
                    "content": '{"category": "projects", "confidence": 0.8}'
                }
            }]
        }
        
        result = analyzer._parse_llm_response(data)
        
        assert result["success"] is True
        assert result["category"] == "projects"
        assert result["confidence"] == 0.8
    
    def test_parse_ollama_response(self, analyzer):
        """Test parsing Ollama response."""
        data = {
            "response": '{"category": "resources", "confidence": 0.9}'
        }
        
        result = analyzer._parse_ollama_response(data)
        
        assert result["success"] is True
        assert result["category"] == "resources"
        assert result["confidence"] == 0.9
    
    def test_stop(self, analyzer):
        """Test stopping the analyzer."""
        analyzer.stop()
        assert analyzer._cancelled.is_set()
    
    @pytest.mark.asyncio
    async def test_close(self, analyzer):
        """Test closing the analyzer."""
        # Mock session
        analyzer._session = AsyncMock()
        analyzer._session.closed = False
        
        await analyzer.close()
        
        analyzer._session.close.assert_called_once()