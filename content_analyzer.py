import os
from typing import Dict, Any, Optional
import requests
import json
from pathlib import Path
import mimetypes
import magic
import langdetect
from korean_utils import KoreanTextHandler

class ContentAnalyzer:
    """Analyzes file content and suggests appropriate names using LLM."""
    
    def __init__(self, model: str = "mistral", ollama_url: str = "http://localhost:11434/api/generate"):
        self.model = model
        self.ollama_url = ollama_url
        self.korean_handler = KoreanTextHandler()
        
    def analyze_for_rename(self, file_path: str, content_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Analyze file content and suggest a new name.
        
        Args:
            file_path: Path to the file
            content_data: Dictionary containing file content analysis
            
        Returns:
            Dict containing suggested name and confidence score
        """
        try:
            content_type = content_data.get('type', '')
            content_text = content_data.get('text', '')
            
            if not content_text:
                return {
                    'success': False,
                    'error': 'No content available for analysis'
                }
            
            # Enhanced language detection with Korean support
            is_korean = self.korean_handler.detect_korean_content(content_text[:1000])
            try:
                language = 'ko' if is_korean else langdetect.detect(content_text[:1000])
            except:
                language = 'unknown'
            
            # Normalize Korean text before analysis
            if is_korean:
                content_text = self.korean_handler.normalize_korean_text(content_text)
            
            # Create prompt with language-specific handling
            prompt = self._create_rename_prompt(content_type, content_text[:1000], language)
            
            # Get suggestion from LLM
            response = self._query_llm(prompt)
            
            if not response:
                return {
                    'success': False,
                    'error': 'Failed to get name suggestion'
                }
            
            # Process suggested name
            suggested_name = response.strip()
            if is_korean:
                suggested_name = self.korean_handler.sanitize_filename(suggested_name)
            
            return {
                'success': True,
                'suggested_name': suggested_name,
                'confidence': 0.8 if is_korean else 0.7,
                'language': language
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': f'Error analyzing content: {str(e)}'
            }
    
    def _create_rename_prompt(self, content_type: str, content_text: str, language: str) -> str:
        """Create a prompt for the LLM with language-specific considerations."""
        if language == 'ko':
            prompt = (
                "다음 파일의 내용을 분석하여 적절한 파일 이름을 제안해주세요.\n"
                "파일 이름은 다음 조건을 만족해야 합니다:\n"
                "1. 파일의 주요 내용이나 목적을 잘 나타내야 함\n"
                "2. 한글과 영문 모두 사용 가능\n"
                "3. 길이는 2-5단어 정도로 적절하게\n"
                "4. 특수문자는 하이픈(-)만 사용\n"
                "5. 확장자는 제외\n\n"
                f"파일 종류: {content_type}\n"
                f"파일 내용:\n{content_text}\n\n"
                "파일 이름 제안 (확장자 제외): "
            )
        else:
            prompt = (
                "Suggest a filename for the following content.\n"
                "The filename should:\n"
                "1. Reflect the main content or purpose\n"
                "2. Be 2-5 words long\n"
                "3. Use only hyphens for separators\n"
                "4. Exclude the extension\n\n"
                f"Content type: {content_type}\n"
                f"Content:\n{content_text}\n\n"
                "Suggested filename (without extension): "
            )
        
        return prompt
        
    def _query_llm(self, prompt: str) -> Optional[str]:
        """Query the LLM using Ollama API."""
        try:
            response = requests.post(
                self.ollama_url,
                json={
                    'model': self.model,
                    'prompt': prompt,
                    'stream': False,
                    'options': {
                        'temperature': 0.7,
                        'top_k': 50,
                        'top_p': 0.9,
                        'num_predict': 100,
                    }
                }
            )
            
            if response.status_code == 200:
                result = response.json()
                # Clean up the response
                suggested_name = result['response'].strip()
                # Remove any quotes or extra whitespace
                suggested_name = suggested_name.strip('"\'').strip()
                return suggested_name
                
            return None
            
        except Exception as e:
            print(f"Error querying LLM: {str(e)}")
            return None
    
    def _parse_llm_response(self, response: str) -> Dict[str, Any]:
        """Parse the LLM response to extract suggested name and confidence."""
        try:
            # Try to parse as JSON first
            data = json.loads(response)
            return {
                'name': data.get('name', ''),
                'confidence': float(data.get('confidence', 0.0)),
                'reasoning': data.get('reasoning', '')
            }
        except:
            # Fallback: try to extract just the filename if JSON parsing fails
            lines = response.split('\n')
            for line in lines:
                if line.strip() and not line.startswith(('#', '//', '-')):
                    return {
                        'name': line.strip()[:50],
                        'confidence': 0.5,
                        'reasoning': 'Extracted from plain text response'
                    }
