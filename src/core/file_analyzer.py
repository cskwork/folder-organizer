import os
from pathlib import Path
from typing import Dict, Any, Optional
import magic
import langdetect
from datetime import datetime
import logging

class FileAnalyzer:
    """Core file analysis functionality"""
    
    def __init__(self, config_manager=None):
        self.config_manager = config_manager
        self.logger = logging.getLogger(__name__)
        
        # Load configuration
        self.config = {
            "sample_size": 4096,  # bytes to read for content analysis
            "confidence_threshold": 0.7,
            "supported_languages": ["en", "ko", "ja", "zh"],
            "ignored_extensions": [".exe", ".dll", ".sys"]
        }
        
        if config_manager:
            self.config.update(config_manager.get("file_analyzer", {}))
    
    def analyze_file(self, file_path: Path) -> Dict[str, Any]:
        """
        Analyze a file and return its properties
        
        Args:
            file_path: Path to the file to analyze
            
        Returns:
            Dict containing file analysis results
        """
        try:
            self.logger.info(f"Analyzing file: {file_path}")
            
            if not file_path.exists():
                raise FileNotFoundError(f"File not found: {file_path}")
            
            result = {
                "path": str(file_path),
                "name": file_path.name,
                "extension": file_path.suffix.lower(),
                "size": file_path.stat().st_size,
                "created": datetime.fromtimestamp(file_path.stat().st_ctime),
                "modified": datetime.fromtimestamp(file_path.stat().st_mtime),
                "mime_type": self._get_mime_type(file_path)
            }
            
            # Skip binary files and ignored extensions
            if (result["extension"] in self.config["ignored_extensions"] or
                result["mime_type"].startswith(("application/x-executable", "application/x-dosexec"))):
                result["type"] = "Binary"
                result["confidence"] = 1.0
                return result
            
            # Analyze content
            content_info = self._analyze_content(file_path)
            result.update(content_info)
            
            self.logger.info(f"Analysis complete for {file_path}")
            return result
            
        except Exception as e:
            self.logger.error(f"Error analyzing file {file_path}: {e}")
            raise
    
    def _get_mime_type(self, file_path: Path) -> str:
        """Get MIME type of file"""
        try:
            return magic.from_file(str(file_path), mime=True)
        except Exception as e:
            self.logger.error(f"Error getting MIME type for {file_path}: {e}")
            return "application/octet-stream"
    
    def _analyze_content(self, file_path: Path) -> Dict[str, Any]:
        """Analyze file content"""
        result = {}
        
        try:
            # Read sample of file content
            with open(file_path, 'rb') as f:
                sample = f.read(self.config["sample_size"])
            
            # Try to decode as text
            try:
                text = sample.decode('utf-8')
                result["type"] = "Text"
                
                # Detect language
                try:
                    lang = langdetect.detect(text)
                    if lang in self.config["supported_languages"]:
                        result["language"] = lang
                        result["confidence"] = 0.8
                except:
                    pass
                    
            except UnicodeDecodeError:
                # Binary file
                result["type"] = "Binary"
                result["confidence"] = 1.0
            
            # Suggest name based on content
            suggested_name = self._suggest_name(file_path, result)
            if suggested_name:
                result["suggested_name"] = suggested_name
            
        except Exception as e:
            self.logger.error(f"Error analyzing content of {file_path}: {e}")
            result["type"] = "Unknown"
            result["confidence"] = 0.0
        
        return result
    
    def _suggest_name(self, file_path: Path, analysis: Dict[str, Any]) -> Optional[str]:
        """Suggest a name based on file analysis"""
        # This is a placeholder for more sophisticated name suggestion logic
        # You can implement your own logic here
        
        original_name = file_path.stem
        extension = file_path.suffix
        
        if "language" in analysis:
            return f"{original_name}_{analysis['language']}{extension}"
            
        return None
