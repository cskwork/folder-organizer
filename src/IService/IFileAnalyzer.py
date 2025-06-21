from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional
from pathlib import Path

class IFileAnalyzer(ABC):
    """파일 분석 서비스 인터페이스"""
    
    @abstractmethod
    def analyze_directory(self, directory: str) -> Dict[str, Any]:
        """디렉토리 내 파일들을 분석"""
        pass
    
    @abstractmethod
    def analyze_file(self, file_path: Path) -> Dict[str, Any]:
        """단일 파일 분석"""
        pass
    
    @abstractmethod
    def stop(self) -> None:
        """분석 작업 중단"""
        pass 