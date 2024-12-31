import os
import shutil
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional, Tuple
import threading
import json
import re
from config_manager import ConfigManager
from error_handler import ErrorHandler, FileCategorizationError, FileOperationError, RetryableError
from file_renamer import FileRenamer

class FileOrganizer:
    def __init__(self, config_manager: ConfigManager = None):
        self.stop_flag = threading.Event()
        self.config_manager = config_manager or ConfigManager()
        self.error_handler = ErrorHandler()
        self.batch_size = self.config_manager.get_setting("batch_size", 50)
        self.operation_stats = {
            "processed": 0,
            "succeeded": 0,
            "failed": 0,
            "skipped": 0
        }
        self._undo_stack = []
        self._redo_stack = []
        self.source_dir = None  # Initialize source directory as None
        self.file_renamer = FileRenamer()  # Initialize file renamer

    def get_stats(self) -> Dict[str, int]:
        """Get current operation statistics"""
        return self.operation_stats.copy()

    def process_batch(self, files: list, analysis_results: Dict[str, Any], 
                     progress_callback: Optional[callable] = None) -> None:
        """Process a batch of files with progress tracking"""
        total_files = len(files)
        
        for idx, file_path in enumerate(files):
            if self.stop_flag.is_set():
                break
                
            try:
                self.error_handler.retry_operation(
                    self._process_single_file,
                    file_path,
                    analysis_results.get(file_path, {})
                )
                self.operation_stats["succeeded"] += 1
            except Exception as e:
                self.operation_stats["failed"] += 1
                self.error_handler.handle_error(e, f"Processing {file_path}")
                
            self.operation_stats["processed"] += 1
            
            if progress_callback:
                progress = (idx + 1) / total_files * 100
                progress_callback(progress, f"Processed {idx + 1}/{total_files} files")

    def _process_single_file(self, file_path: str, analysis: Dict[str, Any]) -> None:
        """Process a single file with undo/redo support"""
        try:
            main_category, sub_category = self.determine_para_category(file_path, analysis)
            target_dir = self._get_target_directory(main_category, sub_category)
            
            # Save original state for undo
            original_state = {
                "path": file_path,
                "target": target_dir
            }
            
            # Move file with smart rename
            new_path = self._move_file(file_path, target_dir, analysis)
            
            # Record operation for undo
            self._undo_stack.append({
                "operation": "move",
                "original": original_state,
                "new": {"path": new_path}
            })
            
            # Clear redo stack after new operation
            self._redo_stack.clear()
            
        except Exception as e:
            raise RetryableError(f"Failed to process {file_path}: {str(e)}")

    def undo(self) -> bool:
        """Undo last operation"""
        if not self._undo_stack:
            return False
            
        operation = self._undo_stack.pop()
        try:
            if operation["operation"] == "move":
                # Move file back to original location
                shutil.move(operation["new"]["path"], operation["original"]["path"])
                self._redo_stack.append(operation)
                return True
        except Exception as e:
            self.error_handler.handle_error(e, "Undo operation")
            return False

    def redo(self) -> bool:
        """Redo last undone operation"""
        if not self._redo_stack:
            return False
            
        operation = self._redo_stack.pop()
        try:
            if operation["operation"] == "move":
                # Redo the move operation
                shutil.move(operation["original"]["path"], operation["new"]["path"])
                self._undo_stack.append(operation)
                return True
        except Exception as e:
            self.error_handler.handle_error(e, "Redo operation")
            return False

    def create_backup(self, source_dir: str) -> str:
        """
        Create a backup of the source directory
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_dir = f"{source_dir}_backup_{timestamp}"
        shutil.copytree(source_dir, backup_dir)
        return backup_dir

    def get_para_category_name(self, main_category: str, sub_category: str) -> Optional[str]:
        """
        Get the localized PARA category name based on current language setting
        """
        language = self.config_manager.get_setting("language", "english")
        category_names = self.config_manager.get_setting("category_names", {})
        
        # Handle unclassified files
        if main_category == "other":
            return category_names[language]["other"]["other"]
        
        if (language in category_names and 
            main_category in category_names[language] and
            sub_category in category_names[language][main_category]):
            return category_names[language][main_category][sub_category]
        
        # If category not found, return the "other" folder name
        return category_names[language]["other"]["other"]

    def determine_para_category(self, file_path: str, analysis: Dict[str, Any]) -> Tuple[str, str]:
        """Determine PARA category based on file analysis"""
        main_category = ''
        sub_category = ''
        
        # Default to 'other/uncategorized'
        default_category = ('other', 'other')
        
        try:
            # Check if we have content analysis results
            if 'content_analysis' in analysis and analysis['content_analysis'].get('success'):
                analysis_text = analysis['content_analysis']['analysis']
                print(f"Content analysis found: {analysis_text}")
                
                # Parse PARA category from analysis
                if 'Category:' in analysis_text:
                    lines = analysis_text.split('\n')
                    for line in lines:
                        if line.startswith('Category:'):
                            # Remove markdown formatting and clean the text
                            category_text = line.split(':', 1)[1].strip()
                            # Remove markdown formatting (**, etc.)
                            category_text = re.sub(r'\*\*|\*', '', category_text)
                            # Extract main category (handle Korean in parentheses)
                            main_match = re.match(r'([^(]+)(?:\s*\([^)]+\))?', category_text)
                            if main_match:
                                main_category = main_match.group(1).strip().lower()
                        elif line.startswith('Subcategory:'):
                            # Remove markdown formatting and clean the text
                            subcategory_text = line.split(':', 1)[1].strip()
                            # Remove markdown formatting (**, etc.)
                            subcategory_text = re.sub(r'\*\*|\*', '', subcategory_text)
                            # Extract subcategory (handle Korean in parentheses)
                            sub_match = re.match(r'([^(]+)(?:\s*\([^)]+\))?', subcategory_text)
                            if sub_match:
                                sub_category = sub_match.group(1).strip().lower()
                    
                    # Map the categories to our structure
                    main_category_map = {
                        'projects': 'projects',
                        'project': 'projects',
                        'areas': 'areas',
                        'area': 'areas',
                        'resources': 'resources',
                        'resource': 'resources',
                        'archives': 'archives',
                        'archive': 'archives',
                        '프로젝트': 'projects',
                        '영역': 'areas',
                        '자료': 'resources',
                        '보관': 'archives'
                    }
                    
                    # Clean and map the main category
                    main_category = main_category_map.get(main_category.lower().strip(), '')
                    
                    if main_category in ['projects', 'areas', 'resources', 'archives']:
                        if sub_category:
                            print(f"Found category from analysis: {main_category}/{sub_category}")
                            return main_category, sub_category
                            
            print(f"No valid category found in analysis, using default: {default_category}")
            return default_category
            
        except Exception as e:
            print(f"Error determining category: {str(e)}")
            return default_category

    def _get_target_directory(self, main_category: str, sub_category: str) -> str:
        """Get the target directory for a file based on its PARA category"""
        if not self.source_dir:
            raise ValueError("Source directory not set. Call organize_files first.")
        category_path = self.get_para_category_name(main_category, sub_category)
        return os.path.join(self.source_dir, category_path)

    def _move_file(self, file_path: str, target_dir: str, analysis: Dict[str, Any] = None) -> str:
        """Move a file to the target directory with optional smart renaming"""
        if not os.path.exists(file_path):
            raise FileOperationError(f"Source file not found: {file_path}")
            
        if not os.path.exists(target_dir):
            os.makedirs(target_dir, exist_ok=True)
        
        current_path = file_path
        renamed_path = None
        
        # Step 1: Rename the file if we have analysis data
        if analysis and analysis.get('content_analysis'):
            content_analysis = analysis['content_analysis']
            if content_analysis.get('success', False):
                suggested_name = content_analysis.get('suggested_name', '')
                
                if suggested_name:
                    print(f"[Smart Rename] {os.path.basename(file_path)}\n  → New name: {suggested_name}{os.path.splitext(file_path)[1]}\n  → Location: {os.path.relpath(target_dir, os.path.dirname(file_path))}")
                    
                    suggestion = {
                        'success': True,
                        'suggested_name': suggested_name
                    }
                    
                    # Try to rename the file in its current location
                    rename_result = self.file_renamer.rename_with_suggestion(current_path, suggestion)
                    if rename_result.get('success'):
                        renamed_path = rename_result.get('new_path')
                        if renamed_path and os.path.exists(renamed_path):
                            current_path = renamed_path
                            print(f"Successfully renamed file to: {os.path.basename(renamed_path)}")
                        else:
                            self.error_handler.log_warning(f"Renamed file not found: {renamed_path}, using original name")
                            renamed_path = None
                    else:
                        self.error_handler.log_warning(f"Rename failed: {rename_result.get('error', 'Unknown error')}")
                else:
                    print("No rename suggestion found in analysis")
        
        # Step 2: Move the file (either renamed or original) to target directory
        target_filename = os.path.basename(current_path)
        target_path = os.path.join(target_dir, target_filename)
        
        # Handle file name conflicts at target location
        if os.path.exists(target_path) and target_path != current_path:
            base, ext = os.path.splitext(target_path)
            counter = 1
            while os.path.exists(f"{base}_{counter}{ext}"):
                counter += 1
            target_path = f"{base}_{counter}{ext}"
        
        try:
            # Only move if the target is different from current location
            if os.path.normpath(os.path.dirname(current_path)) != os.path.normpath(target_dir):
                shutil.move(current_path, target_path)
                return target_path
            else:
                return current_path
        except Exception as e:
            # If move fails and we renamed the file, try to restore original name
            if renamed_path and file_path != current_path:
                try:
                    shutil.move(current_path, file_path)
                except:
                    pass  # If restoration fails, continue with the error
            raise FileOperationError(f"Failed to move file {current_path} to {target_path}: {str(e)}")

    def remove_empty_folders(self, directory: str):
        """
        Remove all empty folders in the given directory recursively
        Returns the number of folders removed
        """
        removed_count = 0
        for root, dirs, files in os.walk(directory, topdown=False):
            for dir_name in dirs:
                dir_path = os.path.join(root, dir_name)
                try:
                    # Check if directory is empty (no files and no subdirectories)
                    if not os.listdir(dir_path):
                        os.rmdir(dir_path)
                        removed_count += 1
                except Exception as e:
                    print(f"Error removing directory {dir_path}: {str(e)}")
        return removed_count

    def organize_files(self, source_dir: str, analysis_results: Dict[str, Any],
                      remove_empty: bool = False, progress_callback=None) -> None:
        """
        Organize files based on analysis results
        """
        try:
            self.source_dir = source_dir  # Set the source directory
            
            if self.config_manager.get_setting("backup_enabled", False):
                try:
                    backup_dir = self.create_backup(source_dir)
                    if progress_callback:
                        progress_callback(0, f"Created backup at: {backup_dir}")
                except Exception as e:
                    self.error_handler.handle_error(FileOperationError(str(e)), "backup creation")

            total_files = len(analysis_results)
            processed = 0

            for file_path, analysis in analysis_results.items():
                if self.stop_flag.is_set():
                    self.error_handler.log_info("Operation interrupted by user")
                    if progress_callback:
                        progress_callback(processed / total_files * 100, "Operation cancelled")
                    break

                try:
                    self.error_handler.retry_operation(
                        self._process_single_file,
                        file_path,
                        analysis
                    )
                    self.operation_stats["succeeded"] += 1
                except Exception as e:
                    self.operation_stats["failed"] += 1
                    self.error_handler.handle_error(e, f"organizing {file_path}")
                    
                self.operation_stats["processed"] += 1
                
                if progress_callback:
                    progress = (processed + 1) / total_files * 100
                    progress_callback(progress, f"Organizing: {os.path.basename(file_path)}")
                processed += 1

            if remove_empty and not self.stop_flag.is_set():
                if progress_callback:
                    progress_callback(100, "Removing empty folders...")
                removed_count = self.remove_empty_folders(source_dir)
                if progress_callback:
                    progress_callback(100, f"Completed. Removed {removed_count} empty folders.")
            elif progress_callback:
                progress_callback(100, "Organization complete")

        except KeyboardInterrupt:
            self.stop_flag.set()
            error_msg = self.error_handler.handle_error(KeyboardInterrupt(), "during organization")
            if progress_callback:
                progress_callback(processed / total_files * 100, error_msg)
        except Exception as e:
            error_msg = self.error_handler.handle_error(e, "during organization")
            if progress_callback:
                progress_callback(processed / total_files * 100, error_msg)

    def stop(self):
        """
        Stop ongoing organization
        """
        self.stop_flag.set()
