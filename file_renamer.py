import os
from typing import Dict, Any, Optional
from pathlib import Path
import shutil
from korean_utils import KoreanTextHandler

class FileRenamer:
    """Handles safe file renaming operations."""
    
    def __init__(self):
        self.korean_handler = KoreanTextHandler()
        
    def rename_with_suggestion(self, file_path: str, suggestion: Dict[str, Any]) -> Dict[str, Any]:
        """
        Rename a file based on the suggested name.
        
        Args:
            file_path: Path to the file to rename
            suggestion: Dictionary containing suggested name and metadata
            
        Returns:
            Dict containing success status and new path or error
        """
        try:
            if not suggestion.get('success'):
                return {
                    'success': False,
                    'error': 'Invalid suggestion data'
                }
            
            # Get original file info
            original_path = Path(file_path)
            if not original_path.exists():
                return {
                    'success': False,
                    'error': 'Original file not found'
                }
            
            # Get and process suggested name
            suggested_name = suggestion.get('suggested_name', '')
            if not suggested_name:
                return {
                    'success': False,
                    'error': 'No name suggestion provided'
                }
            
            # Handle Korean filename
            is_korean = self.korean_handler.is_korean(suggested_name)
            if is_korean:
                suggested_name = self.korean_handler.sanitize_filename(suggested_name)
            
            # Keep original extension
            original_extension = original_path.suffix
            
            # Create new filename
            new_filename = f"{suggested_name}{original_extension}"
            new_path = original_path.parent / new_filename
            
            # Handle name conflicts
            counter = 1
            while new_path.exists():
                base_name = suggested_name
                if is_korean:
                    base_name = f"{suggested_name}_{counter}"
                else:
                    base_name = f"{suggested_name}-{counter}"
                new_filename = f"{base_name}{original_extension}"
                new_path = original_path.parent / new_filename
                counter += 1
            
            # Perform the rename operation
            try:
                original_path.rename(new_path)
                return {
                    'success': True,
                    'new_path': str(new_path),
                    'original_path': str(original_path)
                }
            except OSError as e:
                # Fallback to copy-delete if rename fails
                shutil.copy2(str(original_path), str(new_path))
                original_path.unlink()
                return {
                    'success': True,
                    'new_path': str(new_path),
                    'original_path': str(original_path),
                    'note': 'Used copy-delete fallback'
                }
                
        except Exception as e:
            return {
                'success': False,
                'error': f'Error renaming file: {str(e)}'
            }
    
    def _get_unique_path(self, path: Path) -> Path:
        """
        Generate a unique path if the target path already exists.
        Adds a number suffix if necessary.
        """
        if not path.exists():
            return path
            
        counter = 1
        while True:
            stem = path.stem
            suffix = path.suffix
            new_path = path.parent / f"{stem}_{counter}{suffix}"
            
            if not new_path.exists():
                return new_path
                
            counter += 1
