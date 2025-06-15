"""
Async implementation of file organizer with improved performance and atomic operations.
"""

import os
import asyncio
import aiofiles
import aiofiles.os
import shutil
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional, Callable, Tuple, List
import json
import threading
import concurrent.futures

from ..interfaces.types import IFileOrganizer, IConfigManager, IFileRenamer, IErrorHandler, IProgressReporter
from ..utils.error_handler import FileOperationError, RetryableError

class AsyncFileOrganizer(IFileOrganizer):
    """Async implementation of file organizer with improved performance."""
    
    def __init__(self, config_manager: IConfigManager, 
                 file_renamer: IFileRenamer, 
                 error_handler: IErrorHandler):
        self.config_manager = config_manager
        self.file_renamer = file_renamer
        self.error_handler = error_handler
        self._cancelled = threading.Event()
        self._executor = concurrent.futures.ThreadPoolExecutor(max_workers=4)
        
        self.operation_stats = {
            "processed": 0,
            "succeeded": 0,
            "failed": 0,
            "skipped": 0
        }
        
        # Operation history for undo/redo
        self._operation_history: List[Dict[str, Any]] = []
        self._history_index = -1
        self._max_history = 100

    async def organize_files_async(self, 
                                 source_dir: str,
                                 analysis_results: Dict[str, Any],
                                 remove_empty: bool = True,
                                 progress_callback: Optional[Callable] = None) -> None:
        """Organize files asynchronously with batch processing."""
        if self._cancelled.is_set():
            raise asyncio.CancelledError("Organization cancelled")
            
        # Reset stats
        self.operation_stats = {
            "processed": 0,
            "succeeded": 0,
            "failed": 0,
            "skipped": 0
        }
        
        # Create operation record for history
        operation = {
            'type': 'organize',
            'timestamp': datetime.now(),
            'source_dir': source_dir,
            'files': [],
            'completed': False
        }
        
        try:
            # Process files in batches
            files = list(analysis_results.keys())
            batch_size = self.config_manager.get_setting("batch_size", 10)
            total_files = len(files)
            
            for i in range(0, len(files), batch_size):
                if self._cancelled.is_set():
                    break
                    
                batch = files[i:i + batch_size]
                await self._process_batch_async(batch, analysis_results, source_dir, operation)
                
                # Report progress
                if progress_callback:
                    progress_percent = (self.operation_stats['processed'] / total_files) * 100
                    status = f"Processed {self.operation_stats['processed']}/{total_files} files"
                    progress_callback(progress_percent, status)
            
            # Remove empty directories if requested
            if remove_empty and not self._cancelled.is_set():
                await self._remove_empty_directories_async(source_dir)
                
            # Mark operation as completed
            operation['completed'] = True
            self._add_to_history(operation)
            
        except Exception as e:
            operation['error'] = str(e)
            self._add_to_history(operation)
            raise

    async def _process_batch_async(self, files: List[str], 
                                 analysis_results: Dict[str, Any],
                                 source_dir: str,
                                 operation: Dict[str, Any]) -> None:
        """Process a batch of files concurrently."""
        tasks = []
        
        for file_path in files:
            if self._cancelled.is_set():
                break
                
            analysis = analysis_results.get(file_path, {})
            task = self._process_single_file_async(file_path, analysis, source_dir, operation)
            tasks.append(task)
        
        # Wait for all tasks in the batch to complete
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Update stats
        for result in results:
            if isinstance(result, Exception):
                self.operation_stats['failed'] += 1
            else:
                self.operation_stats['succeeded'] += 1
            self.operation_stats['processed'] += 1

    async def _process_single_file_async(self, file_path: str, 
                                       analysis: Dict[str, Any],
                                       source_dir: str,
                                       operation: Dict[str, Any]) -> Dict[str, Any]:
        """Process a single file asynchronously."""
        if self._cancelled.is_set():
            raise asyncio.CancelledError("Processing cancelled")
            
        file_record = {
            'original_path': file_path,
            'new_path': None,
            'action': 'none',
            'success': False,
            'error': None
        }
        
        try:
            # Determine PARA category
            main_category, sub_category = self.determine_para_category(file_path, analysis)
            
            # Get destination directory
            dest_dir = await self._get_destination_directory_async(source_dir, main_category, sub_category)
            
            # Determine new filename
            new_filename = await self._determine_new_filename_async(file_path, analysis, dest_dir)
            dest_path = os.path.join(dest_dir, new_filename)
            
            # Skip if file is already in the correct location
            if os.path.abspath(file_path) == os.path.abspath(dest_path):
                file_record['action'] = 'skipped'
                file_record['success'] = True
                self.operation_stats['skipped'] += 1
                return file_record
            
            # Ensure destination directory exists
            await self._ensure_directory_exists_async(dest_dir)
            
            # Handle filename conflicts
            if await aiofiles.os.path.exists(dest_path):
                dest_path = await self._resolve_filename_conflict_async(dest_path)
            
            # Move/copy file
            await self._move_file_async(file_path, dest_path)
            
            file_record.update({
                'new_path': dest_path,
                'action': 'moved',
                'success': True,
                'category': f"{main_category}/{sub_category}"
            })
            
            operation['files'].append(file_record)
            
        except Exception as e:
            file_record.update({
                'success': False,
                'error': str(e),
                'action': 'failed'
            })
            operation['files'].append(file_record)
            raise
            
        return file_record

    def determine_para_category(self, file_path: str, analysis: Dict[str, Any]) -> Tuple[str, str]:
        """Determine PARA category for file."""
        # Get organization rules
        rules = self.config_manager.get_organization_rules()
        
        # Default category
        main_category = "other"
        sub_category = "miscellaneous"
        
        # Use content analysis if available
        content_analysis = analysis.get('content_analysis', {})
        if content_analysis.get('success') and 'category' in content_analysis:
            llm_category = content_analysis['category'].lower()
            confidence = content_analysis.get('confidence', 0.0)
            
            if confidence > 0.7:
                if llm_category in ['projects', 'project']:
                    main_category = "projects"
                    sub_category = self._determine_project_subcategory(analysis)
                elif llm_category in ['areas', 'area']:
                    main_category = "areas"
                    sub_category = self._determine_area_subcategory(analysis)
                elif llm_category in ['resources', 'resource']:
                    main_category = "resources"
                    sub_category = self._determine_resource_subcategory(analysis)
                elif llm_category in ['archives', 'archive']:
                    main_category = "archives"
                    sub_category = self._determine_archive_subcategory(analysis)
        
        # Fallback to file type and date-based categorization
        if main_category == "other":
            main_category, sub_category = self._categorize_by_type_and_date(file_path, analysis)
        
        return main_category, sub_category

    def _determine_project_subcategory(self, analysis: Dict[str, Any]) -> str:
        """Determine project subcategory."""
        file_type = analysis.get('category', 'other')
        
        if file_type == 'code':
            return 'development'
        elif file_type == 'documents':
            return 'documentation'
        elif file_type in ['images', 'videos']:
            return 'media'
        else:
            return 'general'

    def _determine_area_subcategory(self, analysis: Dict[str, Any]) -> str:
        """Determine area subcategory."""
        keywords = analysis.get('content_analysis', {}).get('keywords', [])
        
        # Check for specific area keywords
        if any(kw in ['finance', 'budget', 'money'] for kw in keywords):
            return 'finance'
        elif any(kw in ['health', 'medical', 'fitness'] for kw in keywords):
            return 'health'
        elif any(kw in ['work', 'job', 'career'] for kw in keywords):
            return 'work'
        else:
            return 'personal'

    def _determine_resource_subcategory(self, analysis: Dict[str, Any]) -> str:
        """Determine resource subcategory."""
        file_type = analysis.get('category', 'other')
        
        if file_type == 'documents':
            return 'references'
        elif file_type in ['images', 'videos']:
            return 'media'
        elif file_type == 'data':
            return 'datasets'
        else:
            return 'general'

    def _determine_archive_subcategory(self, analysis: Dict[str, Any]) -> str:
        """Determine archive subcategory."""
        modified_date = analysis.get('modified_date')
        if modified_date:
            # Archive by year
            return str(modified_date.year)
        else:
            return 'unknown'

    def _categorize_by_type_and_date(self, file_path: str, analysis: Dict[str, Any]) -> Tuple[str, str]:
        """Categorize based on file type and date as fallback."""
        file_type = analysis.get('category', 'other')
        extension = Path(file_path).suffix.lower()
        
        # Code files usually go to projects
        if file_type == 'code' or extension in ['.py', '.js', '.html', '.css']:
            return 'projects', 'development'
            
        # Documents could be any category, default to areas
        elif file_type == 'documents':
            return 'areas', 'documents'
            
        # Media files to resources
        elif file_type in ['images', 'videos', 'audio']:
            return 'resources', 'media'
            
        # Archive files to archives
        elif file_type == 'archives':
            return 'archives', 'compressed'
            
        # Everything else to other
        else:
            return 'other', 'miscellaneous'

    async def _get_destination_directory_async(self, source_dir: str, 
                                             main_category: str, 
                                             sub_category: str) -> str:
        """Get destination directory path."""
        # Get category names from config
        category_names = self.config_manager.get_setting('category_names', {})
        
        # Map categories to folder names
        folder_mapping = {
            'projects': category_names.get('projects', '1_프로젝트'),
            'areas': category_names.get('areas', '2_영역'),
            'resources': category_names.get('resources', '3_자료'),
            'archives': category_names.get('archives', '4_보관'),
            'other': category_names.get('other', '5_기타')
        }
        
        main_folder = folder_mapping.get(main_category, folder_mapping['other'])
        return os.path.join(source_dir, main_folder, sub_category)

    async def _determine_new_filename_async(self, file_path: str, 
                                          analysis: Dict[str, Any],
                                          dest_dir: str) -> str:
        """Determine new filename with smart renaming."""
        original_name = os.path.basename(file_path)
        
        # Check if smart rename is enabled
        rules = self.config_manager.get_organization_rules()
        if not rules.get('smart_rename_enabled', True):
            return original_name
        
        # Use suggested name from content analysis
        content_analysis = analysis.get('content_analysis', {})
        if content_analysis.get('success') and 'suggested_name' in content_analysis:
            suggested_name = content_analysis['suggested_name']
            if suggested_name and len(suggested_name.strip()) > 0:
                # Keep original extension
                extension = Path(file_path).suffix
                new_name = f"{suggested_name.strip()}{extension}"
                
                # Generate safe filename
                safe_name = self.file_renamer.generate_safe_name(new_name, dest_dir)
                return safe_name
        
        return original_name

    async def _ensure_directory_exists_async(self, directory: str) -> None:
        """Ensure directory exists asynchronously."""
        if not await aiofiles.os.path.exists(directory):
            await aiofiles.os.makedirs(directory, exist_ok=True)

    async def _resolve_filename_conflict_async(self, file_path: str) -> str:
        """Resolve filename conflicts by adding suffix."""
        base_path = Path(file_path)
        base_name = base_path.stem
        extension = base_path.suffix
        directory = base_path.parent
        
        counter = 1
        while await aiofiles.os.path.exists(file_path):
            new_name = f"{base_name}_{counter}{extension}"
            file_path = os.path.join(directory, new_name)
            counter += 1
            
            if counter > 1000:  # Prevent infinite loop
                raise FileOperationError(f"Could not resolve filename conflict for {file_path}")
        
        return file_path

    async def _move_file_async(self, source: str, destination: str) -> None:
        """Move file asynchronously."""
        loop = asyncio.get_event_loop()
        
        def move_file():
            try:
                shutil.move(source, destination)
            except Exception as e:
                raise FileOperationError(f"Failed to move {source} to {destination}: {str(e)}")
        
        await loop.run_in_executor(self._executor, move_file)

    async def _remove_empty_directories_async(self, root_dir: str) -> None:
        """Remove empty directories asynchronously."""
        loop = asyncio.get_event_loop()
        
        def remove_empty():
            # Walk bottom-up to remove nested empty directories
            for root, dirs, files in os.walk(root_dir, topdown=False):
                if root == root_dir:  # Don't remove the root directory
                    continue
                    
                try:
                    if not dirs and not files:  # Directory is empty
                        os.rmdir(root)
                except OSError:
                    pass  # Directory not empty or permission denied
        
        await loop.run_in_executor(self._executor, remove_empty)

    def get_stats(self) -> Dict[str, int]:
        """Get current operation statistics."""
        return self.operation_stats.copy()

    def _add_to_history(self, operation: Dict[str, Any]) -> None:
        """Add operation to history for undo/redo."""
        # Remove any operations after current index (when new operation after undo)
        self._operation_history = self._operation_history[:self._history_index + 1]
        
        # Add new operation
        self._operation_history.append(operation)
        self._history_index = len(self._operation_history) - 1
        
        # Limit history size
        if len(self._operation_history) > self._max_history:
            self._operation_history.pop(0)
            self._history_index -= 1

    def undo(self) -> bool:
        """Undo last operation."""
        if self._history_index < 0 or not self._operation_history:
            return False
            
        operation = self._operation_history[self._history_index]
        
        try:
            # Reverse the file operations
            for file_record in reversed(operation.get('files', [])):
                if file_record['success'] and file_record['action'] == 'moved':
                    original_path = file_record['original_path']
                    new_path = file_record['new_path']
                    
                    if os.path.exists(new_path):
                        # Move file back to original location
                        os.makedirs(os.path.dirname(original_path), exist_ok=True)
                        shutil.move(new_path, original_path)
            
            self._history_index -= 1
            return True
            
        except Exception as e:
            # Log error but don't raise - partial undo is better than none
            print(f"Undo operation partially failed: {e}")
            return False

    def redo(self) -> bool:
        """Redo last undone operation."""
        if self._history_index >= len(self._operation_history) - 1:
            return False
            
        self._history_index += 1
        operation = self._operation_history[self._history_index]
        
        try:
            # Redo the file operations
            for file_record in operation.get('files', []):
                if file_record['success'] and file_record['action'] == 'moved':
                    original_path = file_record['original_path']
                    new_path = file_record['new_path']
                    
                    if os.path.exists(original_path):
                        # Move file to new location again
                        os.makedirs(os.path.dirname(new_path), exist_ok=True)
                        shutil.move(original_path, new_path)
            
            return True
            
        except Exception as e:
            # Log error but don't raise
            print(f"Redo operation partially failed: {e}")
            return False

    def stop(self) -> None:
        """Stop all organization operations."""
        self._cancelled.set()

    def __del__(self):
        """Cleanup executor on deletion."""
        if hasattr(self, '_executor'):
            self._executor.shutdown(wait=False)