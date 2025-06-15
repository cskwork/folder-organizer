"""
Async implementation of file analyzer with improved performance and cancellation support.
"""

import os
import asyncio
import aiofiles
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional, Callable
import magic
import json
from PIL import Image
from PIL.ExifTags import TAGS
import email
import PyPDF2
import docx
import mimetypes
import yaml
from xml.etree import ElementTree
import re
import concurrent.futures
import threading

from ..interfaces.types import IFileAnalyzer, IContentAnalyzer, IConfigManager, IProgressReporter
from .content_analyzer import AsyncContentAnalyzer as ContentAnalyzer

class AsyncFileAnalyzer(IFileAnalyzer):
    """Async implementation of file analyzer with improved performance."""
    
    def __init__(self, config_manager: IConfigManager, content_analyzer: IContentAnalyzer):
        self.config_manager = config_manager
        self.content_analyzer = content_analyzer
        self._cancelled = threading.Event()
        self._executor = concurrent.futures.ThreadPoolExecutor(max_workers=4)
        
        self.supported_extensions = {
            'documents': ['.txt', '.doc', '.docx', '.pdf', '.rtf', '.odt', '.md', '.csv', '.json', '.xml'],
            'images': ['.jpg', '.jpeg', '.png', '.gif', '.bmp', '.tiff', '.webp', '.svg'],
            'videos': ['.mp4', '.avi', '.mov', '.wmv', '.flv', '.mkv', '.webm'],
            'audio': ['.mp3', '.wav', '.ogg', '.m4a', '.flac', '.aac'],
            'archives': ['.zip', '.rar', '.7z', '.tar', '.gz', '.bz2'],
            'code': ['.py', '.js', '.html', '.css', '.java', '.cpp', '.h', '.cs', '.php'],
            'data': ['.xlsx', '.xls', '.db', '.sqlite', '.sql']
        }

    async def analyze_directory_async(self, directory: str, 
                                    use_content: bool = True,
                                    use_type: bool = True, 
                                    use_date: bool = True,
                                    progress_callback: Optional[Callable] = None) -> Dict[str, Any]:
        """Analyze all files in directory asynchronously with batching."""
        self._cancelled.clear()
        results = {}
        
        # Collect all files first
        all_files = []
        for root, _, files in os.walk(directory):
            for file in files:
                if self._cancelled.is_set():
                    return results
                file_path = os.path.join(root, file)
                all_files.append(file_path)
        
        total_files = len(all_files)
        if total_files == 0:
            return results
            
        # Process files in batches
        batch_size = self.config_manager.get_setting("batch_size", 10)
        processed = 0
        
        for i in range(0, len(all_files), batch_size):
            if self._cancelled.is_set():
                break
                
            batch = all_files[i:i + batch_size]
            
            # Process batch concurrently
            tasks = []
            for file_path in batch:
                task = self.analyze_file_async(file_path, use_content, use_type, use_date)
                tasks.append(task)
            
            # Wait for batch to complete
            batch_results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # Collect results
            for file_path, result in zip(batch, batch_results):
                if isinstance(result, Exception):
                    results[file_path] = {
                        'error': str(result),
                        'file_type': 'unknown',
                        'category': 'other'
                    }
                else:
                    results[file_path] = result
                    
                processed += 1
                
                # Report progress
                if progress_callback:
                    progress_percent = (processed / total_files) * 100
                    progress_callback(progress_percent, f"Analyzed {processed}/{total_files} files")
        
        return results

    async def analyze_file_async(self, file_path: str, 
                               use_content: bool = True,
                               use_type: bool = True, 
                               use_date: bool = True) -> Dict[str, Any]:
        """Analyze single file asynchronously."""
        if self._cancelled.is_set():
            raise asyncio.CancelledError("Analysis cancelled")
            
        result = {
            'file_path': file_path,
            'file_name': os.path.basename(file_path),
            'file_size': 0,
            'file_type': 'unknown',
            'category': 'other',
            'created_date': None,
            'modified_date': None,
            'content_analysis': {},
            'metadata': {}
        }
        
        try:
            # Get file stats
            stats = await self._get_file_stats_async(file_path)
            result.update(stats)
            
            # Determine file type
            if use_type:
                file_type_info = await self._get_file_type_async(file_path)
                result.update(file_type_info)
            
            # Get metadata
            metadata = await self._get_metadata_async(file_path)
            result['metadata'] = metadata
            
            # Content analysis
            if use_content and self._should_analyze_content(file_path):
                content_analysis = await self.content_analyzer.analyze_content_async(file_path)
                result['content_analysis'] = content_analysis
                
        except Exception as e:
            result['error'] = str(e)
            
        return result

    async def _get_file_stats_async(self, file_path: str) -> Dict[str, Any]:
        """Get file statistics asynchronously."""
        loop = asyncio.get_event_loop()
        
        def get_stats():
            stat = os.stat(file_path)
            return {
                'file_size': stat.st_size,
                'created_date': datetime.fromtimestamp(stat.st_ctime),
                'modified_date': datetime.fromtimestamp(stat.st_mtime)
            }
        
        return await loop.run_in_executor(self._executor, get_stats)

    async def _get_file_type_async(self, file_path: str) -> Dict[str, Any]:
        """Get file type information asynchronously."""
        loop = asyncio.get_event_loop()
        
        def get_file_type():
            extension = Path(file_path).suffix.lower()
            mime_type, _ = mimetypes.guess_type(file_path)
            
            # Determine category based on extension
            category = 'other'
            file_type = 'unknown'
            
            for cat, extensions in self.supported_extensions.items():
                if extension in extensions:
                    category = cat
                    file_type = extension[1:]  # Remove the dot
                    break
            
            return {
                'file_type': file_type,
                'category': category,
                'mime_type': mime_type,
                'extension': extension
            }
        
        return await loop.run_in_executor(self._executor, get_file_type)

    async def _get_metadata_async(self, file_path: str) -> Dict[str, Any]:
        """Extract metadata asynchronously based on file type."""
        loop = asyncio.get_event_loop()
        extension = Path(file_path).suffix.lower()
        
        def extract_metadata():
            try:
                if extension in ['.jpg', '.jpeg', '.png', '.tiff']:
                    return self._extract_image_metadata(file_path)
                elif extension == '.pdf':
                    return self._extract_pdf_metadata(file_path)
                elif extension in ['.doc', '.docx']:
                    return self._extract_office_metadata(file_path)
                elif extension in ['.mp3', '.wav', '.ogg']:
                    return self._extract_audio_metadata(file_path)
                elif extension in ['.json', '.xml', '.yaml', '.yml']:
                    return self._extract_structured_metadata(file_path)
                else:
                    return {}
            except Exception as e:
                return {'metadata_error': str(e)}
        
        return await loop.run_in_executor(self._executor, extract_metadata)

    def _extract_image_metadata(self, file_path: str) -> Dict[str, Any]:
        """Extract image metadata."""
        metadata = {}
        try:
            with Image.open(file_path) as img:
                metadata['dimensions'] = f"{img.width}x{img.height}"
                metadata['format'] = img.format
                metadata['mode'] = img.mode
                
                # Extract EXIF data
                if hasattr(img, '_getexif'):
                    exif_data = img._getexif()
                    if exif_data:
                        for tag_id, value in exif_data.items():
                            tag = TAGS.get(tag_id, tag_id)
                            metadata[f'exif_{tag}'] = str(value)
        except Exception as e:
            metadata['error'] = str(e)
        
        return metadata

    def _extract_pdf_metadata(self, file_path: str) -> Dict[str, Any]:
        """Extract PDF metadata."""
        metadata = {}
        try:
            with open(file_path, 'rb') as file:
                reader = PyPDF2.PdfReader(file)
                metadata['pages'] = len(reader.pages)
                
                if reader.metadata:
                    for key, value in reader.metadata.items():
                        metadata[key.replace('/', '')] = str(value)
        except Exception as e:
            metadata['error'] = str(e)
        
        return metadata

    def _extract_office_metadata(self, file_path: str) -> Dict[str, Any]:
        """Extract Office document metadata."""
        metadata = {}
        try:
            if file_path.endswith('.docx'):
                doc = docx.Document(file_path)
                props = doc.core_properties
                metadata['author'] = props.author or 'Unknown'
                metadata['created'] = str(props.created) if props.created else 'Unknown'
                metadata['title'] = props.title or 'Unknown'
                metadata['subject'] = props.subject or 'Unknown'
        except Exception as e:
            metadata['error'] = str(e)
        
        return metadata

    def _extract_audio_metadata(self, file_path: str) -> Dict[str, Any]:
        """Extract audio metadata."""
        metadata = {}
        try:
            # Basic file size and format info
            metadata['format'] = Path(file_path).suffix.lower()
            metadata['size'] = os.path.getsize(file_path)
        except Exception as e:
            metadata['error'] = str(e)
        
        return metadata

    def _extract_structured_metadata(self, file_path: str) -> Dict[str, Any]:
        """Extract metadata from structured files."""
        metadata = {}
        try:
            with open(file_path, 'r', encoding='utf-8') as file:
                content = file.read()
                
                if file_path.endswith('.json'):
                    data = json.loads(content)
                    metadata['json_keys'] = list(data.keys()) if isinstance(data, dict) else []
                    metadata['json_size'] = len(str(data))
                elif file_path.endswith('.xml'):
                    root = ElementTree.fromstring(content)
                    metadata['xml_root'] = root.tag
                    metadata['xml_children'] = len(list(root))
                elif file_path.endswith(('.yaml', '.yml')):
                    data = yaml.safe_load(content)
                    metadata['yaml_keys'] = list(data.keys()) if isinstance(data, dict) else []
        except Exception as e:
            metadata['error'] = str(e)
        
        return metadata

    def _should_analyze_content(self, file_path: str) -> bool:
        """Determine if content analysis should be performed."""
        extension = Path(file_path).suffix.lower()
        
        # Skip content analysis for certain file types
        skip_extensions = ['.zip', '.rar', '.7z', '.tar', '.gz', '.bz2', 
                          '.mp4', '.avi', '.mov', '.wmv', '.flv', '.mkv',
                          '.mp3', '.wav', '.ogg', '.m4a', '.flac']
        
        if extension in skip_extensions:
            return False
            
        # Check file size (skip very large files)
        try:
            file_size = os.path.getsize(file_path)
            max_size = self.config_manager.get_setting("max_content_analysis_size", 10 * 1024 * 1024)  # 10MB
            return file_size <= max_size
        except:
            return False

    def stop(self) -> None:
        """Stop all analysis operations."""
        self._cancelled.set()
        
    def __del__(self):
        """Cleanup executor on deletion."""
        if hasattr(self, '_executor'):
            self._executor.shutdown(wait=False)