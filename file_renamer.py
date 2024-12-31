import os
from typing import Dict, Any
from pathlib import Path
import shutil
import re
from korean_utils import KoreanTextHandler

class FileRenamer:
    """Handles safe file renaming operations."""
    
    def __init__(self):
        try:
            self.korean_handler = KoreanTextHandler()
        except Exception as e:
            print(f"Warning: Korean text handling disabled: {str(e)}")
            self.korean_handler = None
        
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
            
            print(f"Processing rename suggestion: {suggested_name}")
            
            # Clean the suggested name
            # Remove markdown formatting
            suggested_name = re.sub(r'\*\*|\*', '', suggested_name)
            # Remove any other special characters except alphanumeric, Korean characters, and underscores
            suggested_name = ''.join(c for c in suggested_name if c.isalnum() or c == '_' or ord(c) > 128)
            suggested_name = suggested_name.strip()
            
            # Handle Korean filename if Korean handler is available
            is_korean = False
            if self.korean_handler:
                is_korean = self.korean_handler.is_korean(suggested_name)
                if is_korean:
                    # First normalize the Korean text
                    suggested_name = self.korean_handler.normalize_korean_text(suggested_name)
                    # Then sanitize it for filesystem
                    suggested_name = self.korean_handler.sanitize_filename(suggested_name)
                    print(f"Processed Korean name: {suggested_name}")
            
            # Keep original extension
            original_extension = original_path.suffix.lower()
            
            # Create new filename with proper path handling
            base_name = suggested_name.strip()
            new_filename = f"{base_name}{original_extension}"
            new_path = original_path.parent / new_filename
            
            print(f"Attempting to rename: {original_path} -> {new_path}")
            
            # Handle name conflicts with consistent naming
            counter = 1
            base_path = new_path
            while new_path.exists() and new_path != original_path:
                base_name = suggested_name
                # Use consistent naming pattern for both Korean and non-Korean
                new_filename = f"{base_name}-{counter}{original_extension}"
                new_path = original_path.parent / new_filename
                counter += 1
                
                # Prevent infinite loop if we can't find a unique name
                if counter > 1000:
                    return {
                        'success': False,
                        'error': 'Could not generate unique filename after 1000 attempts'
                    }
            
            # If the paths are the same, no need to rename
            if new_path == original_path:
                return {
                    'success': True,
                    'new_path': str(original_path),
                    'original_path': str(original_path),
                    'note': 'File already has the suggested name'
                }
            
            # Verify the new path is valid and not too long
            try:
                # Convert to absolute path to check length
                abs_new_path = new_path.resolve()
                if len(str(abs_new_path)) >= 260:  # Windows MAX_PATH limit
                    return {
                        'success': False,
                        'error': 'Generated path exceeds maximum length'
                    }
            except Exception as e:
                return {
                    'success': False,
                    'error': f'Invalid path generated: {str(e)}'
                }
            
            # Perform the rename operation with proper verification
            try:
                print(f"Executing rename: {original_path} -> {new_path}")
                # First try a direct rename
                original_path.rename(new_path)
                print(f"Rename successful: {new_path}")
                return {
                    'success': True,
                    'new_path': str(new_path),
                    'original_path': str(original_path)
                }
            except OSError as e:
                print(f"Direct rename failed, trying copy-delete: {str(e)}")
                # If direct rename fails, try copy-delete with verification
                try:
                    shutil.copy2(str(original_path), str(new_path))
                    if new_path.exists() and new_path.stat().st_size == original_path.stat().st_size:
                        original_path.unlink()
                        print(f"Copy-delete successful: {new_path}")
                        return {
                            'success': True,
                            'new_path': str(new_path),
                            'original_path': str(original_path),
                            'note': 'Used copy-delete fallback'
                        }
                    else:
                        # If verification fails, clean up and return error
                        if new_path.exists():
                            new_path.unlink()
                        return {
                            'success': False,
                            'error': 'Copy verification failed'
                        }
                except Exception as copy_error:
                    # Clean up any partial copy
                    if new_path.exists():
                        try:
                            new_path.unlink()
                        except:
                            pass
                    return {
                        'success': False,
                        'error': f'Copy-delete fallback failed: {str(copy_error)}'
                    }
                
        except Exception as e:
            print(f"Rename error: {str(e)}")
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
