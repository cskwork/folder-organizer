from pathlib import Path
from typing import List, Dict, Optional, Callable
import shutil
import logging
from .rules_engine import RulesEngine

class FileOrganizer:
    """Core file organization functionality"""
    
    def __init__(self, config_manager=None):
        self.config_manager = config_manager
        self.logger = logging.getLogger(__name__)
        self.rules_engine = RulesEngine(config_manager)
        self.progress_callback: Optional[Callable] = None
    
    def set_progress_callback(self, callback: Callable[[int, int, str], None]):
        """Set callback for progress updates"""
        self.progress_callback = callback
    
    def organize_files(
        self,
        files: List[Path],
        target_dir: Path,
        organization_type: str = "by_type",
        file_info: Optional[Dict[Path, Dict]] = None
    ) -> Dict[str, List]:
        """Organize files using rules engine"""
        results = {
            "success": [],
            "failed": [],
            "skipped": []
        }
        
        if not target_dir.exists():
            target_dir.mkdir(parents=True)
        
        total_files = len(files)
        for i, file_path in enumerate(files, 1):
            try:
                if not file_path.exists():
                    results["skipped"].append(str(file_path))
                    continue
                
                # Update progress
                if self.progress_callback:
                    self.progress_callback(
                        i,
                        total_files,
                        f"Processing {file_path.name}"
                    )
                
                # Process file through rules
                new_path = self.rules_engine.process_file(file_path, target_dir)
                
                if new_path:
                    results["success"].append(str(file_path))
                else:
                    # Fallback to basic organization if no rule matched
                    self._organize_file(
                        file_path,
                        target_dir,
                        organization_type
                    )
                    results["success"].append(str(file_path))
                
            except Exception as e:
                self.logger.error(f"Error organizing {file_path}: {e}")
                results["failed"].append(str(file_path))
        
        return results
    
    def _organize_file(self, file_path: Path, target_dir: Path, organization_type: str):
        """Fallback organization method"""
        if organization_type == "by_date":
            self.rules_engine._organize_by_date(file_path, target_dir)
        elif organization_type == "by_language":
            self.rules_engine._organize_by_language(file_path, target_dir)
        else:  # by_type
            self.rules_engine._organize_by_type(file_path, target_dir)
