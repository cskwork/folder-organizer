from dataclasses import dataclass
from typing import Dict, Any, Optional, List
from datetime import datetime

@dataclass
class AnalysisResult:
    """파일 분석 결과를 담는 엔티티"""
    file_path: str
    file_type: str
    size: int
    created_date: datetime
    modified_date: datetime
    content_analysis: Optional[Dict[str, Any]] = None
    para_category: Optional[str] = None
    sub_category: Optional[str] = None
    confidence_score: float = 0.0
    keywords: Optional[List[str]] = None
    suggested_name: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """딕셔너리로 변환"""
        return {
            'file_path': self.file_path,
            'file_type': self.file_type,
            'size': self.size,
            'created_date': self.created_date.isoformat() if self.created_date else None,
            'modified_date': self.modified_date.isoformat() if self.modified_date else None,
            'content_analysis': self.content_analysis,
            'para_category': self.para_category,
            'sub_category': self.sub_category,
            'confidence_score': self.confidence_score,
            'keywords': self.keywords,
            'suggested_name': self.suggested_name
        } 