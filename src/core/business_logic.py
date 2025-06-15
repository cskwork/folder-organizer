"""
Business logic service that separates core functionality from UI components.
"""

import asyncio
from typing import Dict, Any, Optional, List, Callable
from datetime import datetime
import os

from ..interfaces.types import (
    IBusinessLogicService, IFileAnalyzer, IContentAnalyzer, 
    IFileOrganizer, IConfigManager, IProgressReporter
)

class ProgressReporter(IProgressReporter):
    """Implementation of progress reporter."""
    
    def __init__(self, callback: Optional[Callable[[float, str], None]] = None):
        self._callback = callback
        self._cancelled = False
        self._current = 0
        self._total = 0
        self._message = ""
    
    def report_progress(self, current: int, total: int, message: str) -> None:
        """Report progress update."""
        self._current = current
        self._total = total
        self._message = message
        
        if self._callback and not self._cancelled:
            progress_percent = (current / total * 100) if total > 0 else 0
            self._callback(progress_percent, message)
    
    def is_cancelled(self) -> bool:
        """Check if operation is cancelled."""
        return self._cancelled
    
    def cancel(self) -> None:
        """Cancel operation."""
        self._cancelled = True

class BusinessLogicService(IBusinessLogicService):
    """Core business logic service for file organization."""
    
    def __init__(self, 
                 file_analyzer: IFileAnalyzer,
                 file_organizer: IFileOrganizer,
                 config_manager: IConfigManager):
        self.file_analyzer = file_analyzer
        self.file_organizer = file_organizer
        self.config_manager = config_manager
        self._operation_history: List[Dict[str, Any]] = []

    async def analyze_and_organize_async(self, 
                                       source_directory: str,
                                       options: Dict[str, Any],
                                       progress_reporter: IProgressReporter) -> Dict[str, Any]:
        """Main business logic workflow for analyzing and organizing files."""
        
        result = {
            'success': False,
            'analysis_results': {},
            'organization_stats': {},
            'errors': [],
            'start_time': datetime.now(),
            'end_time': None
        }
        
        try:
            # Validate source directory
            if not os.path.exists(source_directory):
                raise ValueError(f"Source directory does not exist: {source_directory}")
            
            if not os.path.isdir(source_directory):
                raise ValueError(f"Path is not a directory: {source_directory}")
            
            # Step 1: Analyze files
            progress_reporter.report_progress(0, 100, "Starting file analysis...")
            
            analysis_results = await self.file_analyzer.analyze_directory_async(
                source_directory,
                use_content=options.get('use_content_analysis', True),
                use_type=options.get('use_file_type', True),
                use_date=options.get('use_date', True),
                progress_callback=lambda p, s: progress_reporter.report_progress(int(p * 0.7), 100, s)
            )
            
            if progress_reporter.is_cancelled():
                result['errors'].append("Operation cancelled during analysis")
                return result
            
            result['analysis_results'] = analysis_results
            
            # Step 2: Organize files
            progress_reporter.report_progress(70, 100, "Starting file organization...")
            
            await self.file_organizer.organize_files_async(
                source_directory,
                analysis_results,
                remove_empty=options.get('remove_empty_folders', True),
                progress_callback=lambda p, s: progress_reporter.report_progress(70 + int(p * 0.3), 100, s)
            )
            
            if progress_reporter.is_cancelled():
                result['errors'].append("Operation cancelled during organization")
                return result
            
            # Get final stats
            result['organization_stats'] = self.file_organizer.get_stats()
            result['success'] = True
            
            progress_reporter.report_progress(100, 100, "Organization completed successfully")
            
        except Exception as e:
            result['errors'].append(str(e))
            progress_reporter.report_progress(0, 100, f"Error: {str(e)}")
        
        finally:
            result['end_time'] = datetime.now()
            # Add to operation history
            self._operation_history.append(result.copy())
        
        return result

    async def preview_organization_async(self, 
                                       source_directory: str,
                                       options: Dict[str, Any]) -> Dict[str, Any]:
        """Preview organization without executing file moves."""
        
        result = {
            'success': False,
            'preview_items': [],
            'stats': {},
            'errors': []
        }
        
        try:
            # Validate source directory
            if not os.path.exists(source_directory):
                raise ValueError(f"Source directory does not exist: {source_directory}")
            
            # Analyze files
            analysis_results = await self.file_analyzer.analyze_directory_async(
                source_directory,
                use_content=options.get('use_content_analysis', True),
                use_type=options.get('use_file_type', True),
                use_date=options.get('use_date', True)
            )
            
            # Generate preview
            preview_items = []
            stats = {
                'total_files': len(analysis_results),
                'by_category': {},
                'smart_renames': 0
            }
            
            rules = self.config_manager.get_organization_rules()
            smart_rename_enabled = rules.get('smart_rename_enabled', True)
            
            for file_path, analysis in analysis_results.items():
                try:
                    # Determine category
                    main_category, sub_category = self.file_organizer.determine_para_category(
                        file_path, analysis
                    )
                    
                    # Get category display name
                    category_path = await self._get_category_display_name(main_category, sub_category)
                    
                    # Determine filename
                    original_name = os.path.basename(file_path)
                    new_name = original_name
                    is_renamed = False
                    
                    if smart_rename_enabled:
                        content_analysis = analysis.get('content_analysis', {})
                        if (content_analysis.get('success') and 
                            'suggested_name' in content_analysis and
                            content_analysis['suggested_name']):
                            
                            suggested_name = content_analysis['suggested_name']
                            extension = os.path.splitext(original_name)[1]
                            new_name = f"{suggested_name}{extension}"
                            is_renamed = True
                            stats['smart_renames'] += 1
                    
                    preview_item = {
                        'original_path': file_path,
                        'original_name': original_name,
                        'new_name': new_name,
                        'category': f"{main_category}/{sub_category}",
                        'category_display': category_path,
                        'is_renamed': is_renamed,
                        'file_type': analysis.get('file_type', 'unknown'),
                        'file_size': analysis.get('file_size', 0),
                        'confidence': analysis.get('content_analysis', {}).get('confidence', 0.0)
                    }
                    
                    preview_items.append(preview_item)
                    
                    # Update category stats
                    category_key = f"{main_category}/{sub_category}"
                    stats['by_category'][category_key] = stats['by_category'].get(category_key, 0) + 1
                    
                except Exception as e:
                    result['errors'].append(f"Error processing {file_path}: {str(e)}")
            
            result.update({
                'success': True,
                'preview_items': preview_items,
                'stats': stats
            })
            
        except Exception as e:
            result['errors'].append(str(e))
        
        return result

    async def _get_category_display_name(self, main_category: str, sub_category: str) -> str:
        """Get display name for category."""
        category_names = self.config_manager.get_setting('category_names', {})
        
        folder_mapping = {
            'projects': category_names.get('projects', '1_프로젝트'),
            'areas': category_names.get('areas', '2_영역'),
            'resources': category_names.get('resources', '3_자료'),
            'archives': category_names.get('archives', '4_보관'),
            'other': category_names.get('other', '5_기타')
        }
        
        main_folder = folder_mapping.get(main_category, folder_mapping['other'])
        return f"{main_folder}/{sub_category}"

    def get_operation_history(self) -> List[Dict[str, Any]]:
        """Get history of operations for undo/redo."""
        return self._operation_history.copy()

    async def undo_last_operation_async(self) -> Dict[str, Any]:
        """Undo the last organization operation."""
        result = {
            'success': False,
            'message': '',
            'error': None
        }
        
        try:
            if self.file_organizer.undo():
                result.update({
                    'success': True,
                    'message': 'Last operation undone successfully'
                })
            else:
                result.update({
                    'success': False,
                    'message': 'Nothing to undo'
                })
        except Exception as e:
            result.update({
                'success': False,
                'error': str(e),
                'message': f'Undo failed: {str(e)}'
            })
        
        return result

    async def redo_last_operation_async(self) -> Dict[str, Any]:
        """Redo the last undone operation."""
        result = {
            'success': False,
            'message': '',
            'error': None
        }
        
        try:
            if self.file_organizer.redo():
                result.update({
                    'success': True,
                    'message': 'Last operation redone successfully'
                })
            else:
                result.update({
                    'success': False,
                    'message': 'Nothing to redo'
                })
        except Exception as e:
            result.update({
                'success': False,
                'error': str(e),
                'message': f'Redo failed: {str(e)}'
            })
        
        return result

    async def get_directory_stats_async(self, directory: str) -> Dict[str, Any]:
        """Get statistics about a directory."""
        stats = {
            'total_files': 0,
            'total_size': 0,
            'file_types': {},
            'empty_directories': 0,
            'largest_files': [],
            'recent_files': []
        }
        
        try:
            for root, dirs, files in os.walk(directory):
                # Count empty directories
                if not dirs and not files:
                    stats['empty_directories'] += 1
                
                for file in files:
                    file_path = os.path.join(root, file)
                    
                    try:
                        file_stat = os.stat(file_path)
                        file_size = file_stat.st_size
                        
                        stats['total_files'] += 1
                        stats['total_size'] += file_size
                        
                        # Track file types
                        extension = os.path.splitext(file)[1].lower()
                        stats['file_types'][extension] = stats['file_types'].get(extension, 0) + 1
                        
                        # Track largest files (top 10)
                        if len(stats['largest_files']) < 10:
                            stats['largest_files'].append({
                                'path': file_path,
                                'size': file_size,
                                'name': file
                            })
                        else:
                            # Replace smallest if current is larger
                            min_item = min(stats['largest_files'], key=lambda x: x['size'])
                            if file_size > min_item['size']:
                                stats['largest_files'].remove(min_item)
                                stats['largest_files'].append({
                                    'path': file_path,
                                    'size': file_size,
                                    'name': file
                                })
                        
                        # Track recent files (top 10)
                        modified_time = file_stat.st_mtime
                        if len(stats['recent_files']) < 10:
                            stats['recent_files'].append({
                                'path': file_path,
                                'modified': modified_time,
                                'name': file
                            })
                        else:
                            # Replace oldest if current is newer
                            min_item = min(stats['recent_files'], key=lambda x: x['modified'])
                            if modified_time > min_item['modified']:
                                stats['recent_files'].remove(min_item)
                                stats['recent_files'].append({
                                    'path': file_path,
                                    'modified': modified_time,
                                    'name': file
                                })
                    
                    except OSError:
                        continue
            
            # Sort results
            stats['largest_files'].sort(key=lambda x: x['size'], reverse=True)
            stats['recent_files'].sort(key=lambda x: x['modified'], reverse=True)
            
        except Exception as e:
            stats['error'] = str(e)
        
        return stats

    def stop_all_operations(self) -> None:
        """Stop all running operations."""
        self.file_analyzer.stop()
        self.file_organizer.stop()