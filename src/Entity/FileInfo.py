from dataclasses import dataclass
from datetime import datetime
from typing import Optional, Dict, Any
from pathlib import Path

@dataclass
class FileInfo:
    """파일 정보를 담는 엔티티"""
    path: Path
    name: str
    extension: str
    size: int
    created_date: datetime
    modified_date: datetime
    mime_type: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None
    
    @property
    def size_mb(self) -> float:
        """파일 크기를 MB 단위로 반환"""
        return self.size / (1024 * 1024)
    
    @property
    def is_text_file(self) -> bool:
        """텍스트 파일 여부 확인"""
        text_extensions = {'.txt', '.md', '.py', '.js', '.html', '.css', '.json', '.xml', '.csv'}
        return self.extension.lower() in text_extensions 