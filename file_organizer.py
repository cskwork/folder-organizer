import os
import shutil
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional, Tuple
import threading
import json
from config_manager import ConfigManager
from error_handler import ErrorHandler, FileCategorizationError, FileOperationError, RetryableError

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
            
            # Move file
            new_path = self._move_file(file_path, target_dir)
            
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
        print(f"\nDetermining PARA category for {file_path}")
        print(f"Analysis data: {analysis}")
        
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
                            main_category = line.split(':')[1].strip().lower()
                        elif line.startswith('Subcategory:'):
                            sub_category = line.split(':')[1].strip().lower()
                            
                    # Map the categories to our structure
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

    def _move_file(self, file_path: str, target_dir: str) -> str:
        """Move a file to the target directory"""
        os.makedirs(target_dir, exist_ok=True)
        target_path = os.path.join(target_dir, os.path.basename(file_path))
        # Handle file name conflicts
        if os.path.exists(target_path):
            base, ext = os.path.splitext(target_path)
            counter = 1
            while os.path.exists(f"{base}_{counter}{ext}"):
                counter += 1
            target_path = f"{base}_{counter}{ext}"
        shutil.move(file_path, target_path)
        return target_path

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
