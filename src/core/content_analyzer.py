"""
Async implementation of content analyzer with improved performance and error handling.
"""

import asyncio
import aiohttp
import aiofiles
import json
import os
import re
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional, List
import concurrent.futures
import threading

from ..interfaces.types import IContentAnalyzer, IConfigManager
from ..utils.korean_utils import KoreanTextHandler

class AsyncContentAnalyzer(IContentAnalyzer):
    """Async implementation of content analyzer with improved performance."""
    
    def __init__(self, config_manager: IConfigManager):
        self.config_manager = config_manager
        self.korean_handler = KoreanTextHandler()
        self._cancelled = threading.Event()
        self._executor = concurrent.futures.ThreadPoolExecutor(max_workers=2)
        self._session: Optional[aiohttp.ClientSession] = None
        
    async def _get_session(self) -> aiohttp.ClientSession:
        """Get or create HTTP session."""
        if self._session is None or self._session.closed:
            timeout = aiohttp.ClientTimeout(total=30)
            self._session = aiohttp.ClientSession(timeout=timeout)
        return self._session

    async def analyze_content_async(self, file_path: str, 
                                  content: Optional[str] = None) -> Dict[str, Any]:
        """Analyze file content asynchronously."""
        if self._cancelled.is_set():
            raise asyncio.CancelledError("Content analysis cancelled")
            
        result = {
            'success': False,
            'category': 'other',
            'confidence': 0.0,
            'suggested_name': None,
            'content_summary': None,
            'keywords': [],
            'language': 'unknown',
            'error': None
        }
        
        try:
            # Extract content if not provided
            if content is None:
                content = await self._extract_content_async(file_path)
            
            if not content or len(content.strip()) < 10:
                result['error'] = 'Insufficient content for analysis'
                return result
            
            # Analyze content with LLM
            llm_config = self.config_manager.get_setting('llm_config', {})
            if llm_config.get('enabled', True):
                llm_result = await self._analyze_with_llm_async(content, file_path)
                result.update(llm_result)
            else:
                # Fallback to basic analysis
                basic_result = await self._basic_content_analysis_async(content, file_path)
                result.update(basic_result)
                
        except Exception as e:
            result['error'] = str(e)
            
        return result

    async def suggest_name_async(self, file_path: str, 
                               content: Optional[str] = None) -> Optional[str]:
        """Suggest smart file name asynchronously."""
        try:
            analysis = await self.analyze_content_async(file_path, content)
            return analysis.get('suggested_name')
        except Exception:
            return None

    async def _extract_content_async(self, file_path: str) -> str:
        """Extract text content from file asynchronously."""
        extension = Path(file_path).suffix.lower()
        
        # Text files
        if extension in ['.txt', '.md', '.py', '.js', '.html', '.css', '.json', '.xml', '.yaml', '.yml']:
            return await self._read_text_file_async(file_path)
        
        # PDF files
        elif extension == '.pdf':
            return await self._extract_pdf_text_async(file_path)
        
        # Office documents
        elif extension in ['.doc', '.docx']:
            return await self._extract_office_text_async(file_path)
        
        # CSV files
        elif extension == '.csv':
            return await self._extract_csv_text_async(file_path)
        
        return ""

    async def _read_text_file_async(self, file_path: str) -> str:
        """Read text file asynchronously."""
        try:
            async with aiofiles.open(file_path, 'r', encoding='utf-8') as file:
                content = await file.read()
                # Limit content size for analysis
                max_size = self.config_manager.get_setting('max_content_size', 50000)
                return content[:max_size] if len(content) > max_size else content
        except UnicodeDecodeError:
            # Try with different encodings
            for encoding in ['cp949', 'latin1', 'utf-16']:
                try:
                    async with aiofiles.open(file_path, 'r', encoding=encoding) as file:
                        content = await file.read()
                        max_size = self.config_manager.get_setting('max_content_size', 50000)
                        return content[:max_size] if len(content) > max_size else content
                except:
                    continue
            return ""
        except Exception:
            return ""

    async def _extract_pdf_text_async(self, file_path: str) -> str:
        """Extract text from PDF asynchronously."""
        loop = asyncio.get_event_loop()
        
        def extract_pdf():
            try:
                import PyPDF2
                with open(file_path, 'rb') as file:
                    reader = PyPDF2.PdfReader(file)
                    text = ""
                    max_pages = min(len(reader.pages), 10)  # Limit pages for performance
                    for page_num in range(max_pages):
                        page = reader.pages[page_num]
                        text += page.extract_text() + "\n"
                    return text[:10000]  # Limit text size
            except Exception:
                return ""
        
        return await loop.run_in_executor(self._executor, extract_pdf)

    async def _extract_office_text_async(self, file_path: str) -> str:
        """Extract text from Office documents asynchronously."""
        loop = asyncio.get_event_loop()
        
        def extract_office():
            try:
                if file_path.endswith('.docx'):
                    import docx
                    doc = docx.Document(file_path)
                    text = ""
                    for paragraph in doc.paragraphs[:50]:  # Limit paragraphs
                        text += paragraph.text + "\n"
                    return text[:10000]  # Limit text size
            except Exception:
                return ""
        
        return await loop.run_in_executor(self._executor, extract_office)

    async def _extract_csv_text_async(self, file_path: str) -> str:
        """Extract text from CSV files asynchronously."""
        try:
            async with aiofiles.open(file_path, 'r', encoding='utf-8') as file:
                lines = []
                async for line in file:
                    lines.append(line.strip())
                    if len(lines) >= 20:  # Limit rows for analysis
                        break
                return '\n'.join(lines)
        except Exception:
            return ""

    async def _analyze_with_llm_async(self, content: str, file_path: str) -> Dict[str, Any]:
        """Analyze content using LLM asynchronously."""
        llm_config = self.config_manager.get_setting('llm_config', {})
        provider = llm_config.get('provider', 'openrouter')
        
        if provider == 'openrouter':
            return await self._analyze_with_openrouter_async(content, file_path, llm_config)
        elif provider == 'ollama':
            return await self._analyze_with_ollama_async(content, file_path, llm_config)
        else:
            return await self._basic_content_analysis_async(content, file_path)

    async def _analyze_with_openrouter_async(self, content: str, file_path: str, 
                                           llm_config: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze content using OpenRouter API asynchronously."""
        try:
            session = await self._get_session()
            
            # Prepare the prompt
            prompt = self._create_analysis_prompt(content, file_path)
            
            # API request
            headers = {
                "Authorization": f"Bearer {llm_config.get('api_key', '')}",
                "Content-Type": "application/json",
                "HTTP-Referer": "https://github.com/file-organizer",
                "X-Title": "File Organizer"
            }
            
            payload = {
                "model": llm_config.get('model', 'google/gemini-flash-1.5-8b'),
                "messages": [
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                "temperature": 0.3,
                "max_tokens": 500
            }
            
            async with session.post('https://openrouter.ai/api/v1/chat/completions', 
                                  json=payload, headers=headers) as response:
                if response.status == 200:
                    data = await response.json()
                    return self._parse_llm_response(data)
                else:
                    error_text = await response.text()
                    return {
                        'success': False,
                        'error': f'OpenRouter API error: {response.status} - {error_text}'
                    }
                    
        except Exception as e:
            return {
                'success': False,
                'error': f'OpenRouter analysis failed: {str(e)}'
            }

    async def _analyze_with_ollama_async(self, content: str, file_path: str, 
                                       llm_config: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze content using Ollama asynchronously."""
        try:
            session = await self._get_session()
            
            # Prepare the prompt
            prompt = self._create_analysis_prompt(content, file_path)
            
            # Ollama API request
            payload = {
                "model": llm_config.get('ollama_model', 'llama3.2'),
                "prompt": prompt,
                "stream": False,
                "options": {
                    "temperature": 0.3,
                    "num_predict": 500
                }
            }
            
            ollama_url = llm_config.get('ollama_url', 'http://localhost:11434')
            async with session.post(f'{ollama_url}/api/generate', 
                                  json=payload) as response:
                if response.status == 200:
                    data = await response.json()
                    return self._parse_ollama_response(data)
                else:
                    error_text = await response.text()
                    return {
                        'success': False,
                        'error': f'Ollama API error: {response.status} - {error_text}'
                    }
                    
        except Exception as e:
            return {
                'success': False,
                'error': f'Ollama analysis failed: {str(e)}'
            }

    def _create_analysis_prompt(self, content: str, file_path: str) -> str:
        """Create analysis prompt for LLM."""
        file_name = os.path.basename(file_path)
        
        return f"""Analyze this file content and provide a JSON response with the following structure:
{{
    "category": "one of: projects, areas, resources, archives, other",
    "confidence": "float between 0.0 and 1.0",
    "suggested_name": "descriptive filename without extension",
    "content_summary": "brief summary in 1-2 sentences",
    "keywords": ["list", "of", "relevant", "keywords"],
    "language": "detected language (korean, english, etc.)"
}}

File: {file_name}
Content: {content[:2000]}

Respond only with valid JSON."""

    def _parse_llm_response(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Parse LLM response from OpenRouter."""
        try:
            content = data['choices'][0]['message']['content']
            # Try to extract JSON from the response
            json_match = re.search(r'\{.*\}', content, re.DOTALL)
            if json_match:
                result = json.loads(json_match.group())
                result['success'] = True
                return result
            else:
                return {
                    'success': False,
                    'error': 'Could not parse JSON from LLM response'
                }
        except Exception as e:
            return {
                'success': False,
                'error': f'Failed to parse LLM response: {str(e)}'
            }

    def _parse_ollama_response(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Parse response from Ollama."""
        try:
            content = data['response']
            # Try to extract JSON from the response
            json_match = re.search(r'\{.*\}', content, re.DOTALL)
            if json_match:
                result = json.loads(json_match.group())
                result['success'] = True
                return result
            else:
                return {
                    'success': False,
                    'error': 'Could not parse JSON from Ollama response'
                }
        except Exception as e:
            return {
                'success': False,
                'error': f'Failed to parse Ollama response: {str(e)}'
            }

    async def _basic_content_analysis_async(self, content: str, file_path: str) -> Dict[str, Any]:
        """Perform basic content analysis without LLM."""
        loop = asyncio.get_event_loop()
        
        def analyze():
            # Basic keyword extraction
            words = re.findall(r'\b\w+\b', content.lower())
            word_freq = {}
            for word in words:
                if len(word) > 3:  # Skip short words
                    word_freq[word] = word_freq.get(word, 0) + 1
            
            # Get top keywords
            keywords = sorted(word_freq.items(), key=lambda x: x[1], reverse=True)[:10]
            keywords = [word for word, _ in keywords]
            
            # Basic categorization based on file extension and keywords
            extension = Path(file_path).suffix.lower()
            category = 'other'
            confidence = 0.5
            
            if extension in ['.py', '.js', '.html', '.css']:
                category = 'projects'
                confidence = 0.8
            elif extension in ['.pdf', '.doc', '.docx']:
                if any(keyword in content.lower() for keyword in ['project', 'task', 'todo']):
                    category = 'projects'
                    confidence = 0.7
                elif any(keyword in content.lower() for keyword in ['manual', 'guide', 'reference']):
                    category = 'resources'
                    confidence = 0.7
                else:
                    category = 'areas'
                    confidence = 0.6
            
            # Generate suggested name
            base_name = Path(file_path).stem
            if len(base_name) > 20:
                # Use first few keywords for name
                if keywords:
                    suggested_name = '_'.join(keywords[:3])
                else:
                    suggested_name = base_name[:20]
            else:
                suggested_name = base_name
            
            # Clean up suggested name
            suggested_name = re.sub(r'[^a-zA-Z0-9가-힣_-]', '_', suggested_name)
            suggested_name = re.sub(r'_+', '_', suggested_name).strip('_')
            
            return {
                'success': True,
                'category': category,
                'confidence': confidence,
                'suggested_name': suggested_name,
                'content_summary': content[:200] + '...' if len(content) > 200 else content,
                'keywords': keywords,
                'language': 'korean' if self.korean_handler.contains_korean(content) else 'english'
            }
        
        return await loop.run_in_executor(self._executor, analyze)

    def stop(self) -> None:
        """Stop all content analysis operations."""
        self._cancelled.set()

    async def close(self) -> None:
        """Close HTTP session and cleanup."""
        if self._session and not self._session.closed:
            await self._session.close()
        self._executor.shutdown(wait=False)

    def __del__(self):
        """Cleanup on deletion."""
        if hasattr(self, '_session') and self._session and not self._session.closed:
            asyncio.create_task(self._session.close())
        if hasattr(self, '_executor'):
            self._executor.shutdown(wait=False)