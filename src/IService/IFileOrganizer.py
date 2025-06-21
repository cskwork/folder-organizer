from abc import ABC, abstractmethod
from typing import Dict, Any, Tuple, Optional, Callable

class IFileOrganizer(ABC):
    """파일 조직화 서비스 인터페이스"""
    
    @abstractmethod
    def organize_files(self, source_dir: str, analysis_results: Dict[str, Any], 
                      remove_empty: bool = True, progress_callback: Optional[Callable] = None) -> None:
        """파일들을 조직화"""
        pass
    
    @abstractmethod
    def determine_para_category(self, file_path: str, analysis: Dict[str, Any]) -> Tuple[str, str]:
        """PARA 카테고리 결정"""
        pass
    
    @abstractmethod
    def get_para_category_name(self, main_category: str, sub_category: str) -> str:
        """PARA 카테고리 이름 생성"""
        pass
    
    @abstractmethod
    def stop(self) -> None:
        """조직화 작업 중단"""
        pass
    
    @abstractmethod
    def undo(self) -> bool:
        """마지막 작업 취소"""
        pass
    
    @abstractmethod
    def redo(self) -> bool:
        """마지막 취소 작업 재실행"""
        pass
    
    @abstractmethod
    def get_stats(self) -> Dict[str, int]:
        """통계 정보 반환"""
        pass 