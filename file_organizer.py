import os
import shutil
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional
import threading
import json
from config_manager import ConfigManager

class FileOrganizer:
    def __init__(self, config_manager: ConfigManager = None):
        self.stop_flag = threading.Event()
        self.config_manager = config_manager or ConfigManager()

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

    def determine_para_category(self, file_path: str, analysis: Dict[str, Any]) -> tuple[str, str]:
        """
        Determine the PARA category for a file based on its analysis
        Returns (main_category, sub_category)
        """
        # Check content analysis for PARA indicators
        if ('content_analysis' in analysis and 
            analysis['content_analysis'].get('success', False)):
            content = analysis['content_analysis']['analysis'].lower()
            
            # Projects
            project_current = ['ongoing project', 'current task', 'in progress', 'this week', 'this month', 
                             'active development', 'sprint', 'milestone', 'deadline', 'deliverable']
            project_future = ['planned', 'scheduled', 'upcoming', 'next phase', 'future project', 
                            'to be started', 'roadmap', 'backlog']
            
            if any(phrase in content for phrase in project_current + project_future):
                main_category = "projects"
                if any(phrase in content for phrase in project_future):
                    sub_category = "next"
                else:
                    sub_category = "active"
                return main_category, sub_category
            
            # Areas
            area_work = ['business', 'career', 'job duties', 'professional development', 'work-related',
                        'meeting notes', 'client', 'stakeholder', 'department']
            area_personal = ['personal goals', 'family', 'home', 'lifestyle', 'relationships', 'finances',
                           'budget', 'household', 'personal project']
            area_health = ['fitness', 'diet', 'exercise', 'medical', 'mental health', 'wellness',
                         'workout', 'nutrition', 'health goals']
            
            if any(phrase in content for phrase in area_work + area_personal + area_health):
                main_category = "areas"
                if any(phrase in content for phrase in area_work):
                    sub_category = "work"
                elif any(phrase in content for phrase in area_health):
                    sub_category = "health"
                else:
                    sub_category = "personal"
                return main_category, sub_category
            
            # Resources
            resource_ref = ['guide', 'manual', 'documentation', 'reference material', 'instructions', 
                          'specifications', 'api', 'handbook', 'guidelines']
            resource_learn = ['tutorial', 'course', 'study material', 'learning resource', 'educational content',
                            'training', 'workshop', 'lesson', 'examples']
            resource_tools = ['tool', 'template', 'script', 'utility', 'software', 'application',
                            'configuration', 'setup', 'automation']
            
            if any(phrase in content for phrase in resource_ref + resource_learn + resource_tools):
                main_category = "resources"
                if any(phrase in content for phrase in resource_learn):
                    sub_category = "learning"
                elif any(phrase in content for phrase in resource_tools):
                    sub_category = "tools"
                else:
                    sub_category = "references"
                return main_category, sub_category
            
            # Archives
            archive_done = ['completed', 'finished', 'delivered', 'done', 'accomplished', 'closed',
                          'final version', 'released', 'shipped']
            archive_old = ['archived', 'outdated', 'old version', 'past', 'historical', 'deprecated',
                         'legacy', 'obsolete', 'previous']
            
            if any(phrase in content for phrase in archive_done + archive_old):
                main_category = "archives"
                if any(phrase in content for phrase in archive_done):
                    sub_category = "done"
                else:
                    sub_category = "old"
                return main_category, sub_category
            
            # Check file name and path for additional context
            file_name = os.path.basename(file_path).lower()
            if any(word in file_name for word in ['old', 'archive', 'backup', 'deprecated']):
                return "archives", "old"
            if any(word in file_name for word in ['done', 'complete', 'final']):
                return "archives", "done"
            
        # If no category determined or content analysis failed, return "other"
        return "other", "other"

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
        if self.config_manager.get_setting("backup_enabled", False):
            try:
                backup_dir = self.create_backup(source_dir)
                if progress_callback:
                    progress_callback(0, f"Created backup at: {backup_dir}")
            except Exception as e:
                print(f"Failed to create backup: {str(e)}")

        total_files = len(analysis_results)
        processed = 0

        for file_path, analysis in analysis_results.items():
            if self.stop_flag.is_set():
                break

            try:
                main_category, sub_category = self.determine_para_category(file_path, analysis)
                category_path = self.get_para_category_name(main_category, sub_category)
                
                if category_path:
                    target_dir = os.path.join(source_dir, category_path)
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
                
                processed += 1
                if progress_callback:
                    progress = (processed / total_files) * 100
                    progress_callback(progress, f"Organizing: {os.path.basename(file_path)}")

            except Exception as e:
                print(f"Error organizing {file_path}: {str(e)}")
                continue

        if remove_empty and not self.stop_flag.is_set():
            if progress_callback:
                progress_callback(100, "Removing empty folders...")
            removed_count = self.remove_empty_folders(source_dir)
            if progress_callback:
                progress_callback(100, f"Completed. Removed {removed_count} empty folders.")
        elif progress_callback:
            progress_callback(100, "Organization complete")

    def stop(self):
        """
        Stop ongoing organization
        """
        self.stop_flag.set()
