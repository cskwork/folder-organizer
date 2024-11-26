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

    def organize_directory(self, source_dir: str, analysis_results: Dict[str, Any],
                         use_content: bool = True, use_type: bool = True,
                         use_date: bool = True) -> None:
        """
        Organize files based on analysis results
        """
        self.stop_flag.clear()
        
        for file_path, analysis in analysis_results.items():
            if self.stop_flag.is_set():
                break
                
            try:
                self._organize_file(file_path, analysis, source_dir,
                                  use_content, use_type, use_date)
            except Exception as e:
                print(f"Error organizing {file_path}: {str(e)}")
                continue

    def _organize_file(self, file_path: str, analysis: Dict[str, Any],
                      source_dir: str, use_content: bool, use_type: bool,
                      use_date: bool) -> None:
        """
        Organize a single file based on its analysis using PARA method
        """
        # Base target directory is the source directory
        target_dir = source_dir
        
        # Determine PARA categories
        main_category, sub_category = self.determine_para_category(file_path, analysis)
        
        # Get localized category names
        category_name = self.get_para_category_name(main_category, sub_category)
        if category_name:
            target_dir = os.path.join(target_dir, category_name)
        
        # Add date-based subdirectory if enabled
        if use_date and 'created' in analysis:
            date_str = datetime.fromisoformat(analysis['created']).strftime("%Y-%m")
            target_dir = os.path.join(target_dir, date_str)
        
        # Create target directory if it doesn't exist
        os.makedirs(target_dir, exist_ok=True)
        
        # Move the file
        target_path = os.path.join(target_dir, os.path.basename(file_path))
        
        # Handle filename conflicts
        counter = 1
        while os.path.exists(target_path):
            name, ext = os.path.splitext(os.path.basename(file_path))
            target_path = os.path.join(target_dir, f"{name}_{counter}{ext}")
            counter += 1
        
        shutil.move(file_path, target_path)

    def stop(self):
        """
        Stop ongoing organization
        """
        self.stop_flag.set()
