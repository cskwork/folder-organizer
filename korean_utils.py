import re
from typing import Optional
import os
import unidecode

class KoreanTextHandler:
    """Handles Korean text processing and validation."""
    
    def __init__(self):
        """Initialize Korean text handler with basic romanization mappings."""
        # Basic mapping for common Korean syllables to roman letters
        self.korean_to_roman = {
            # Basic consonants
            'ㄱ': 'g', 'ㄴ': 'n', 'ㄷ': 'd', 'ㄹ': 'r', 'ㅁ': 'm',
            'ㅂ': 'b', 'ㅅ': 's', 'ㅇ': '', 'ㅈ': 'j', 'ㅊ': 'ch',
            'ㅋ': 'k', 'ㅌ': 't', 'ㅍ': 'p', 'ㅎ': 'h',
            # Basic vowels
            '아': 'a', '어': 'eo', '오': 'o', '우': 'u', '으': 'eu',
            '이': 'i', '애': 'ae', '에': 'e', '외': 'oe', '위': 'wi',
            '야': 'ya', '여': 'yeo', '요': 'yo', '유': 'yu', '예': 'ye',
            # Common syllables
            '김': 'kim', '이': 'lee', '박': 'park', '최': 'choi', '정': 'jung',
            '강': 'kang', '조': 'jo', '윤': 'yoon', '장': 'jang', '임': 'im',
            '한': 'han', '오': 'oh', '서': 'seo', '신': 'shin', '권': 'kwon',
            '황': 'hwang', '안': 'ahn', '송': 'song', '전': 'jeon', '홍': 'hong'
        }
    
    def is_korean(self, text: str) -> bool:
        """Check if text contains Korean characters."""
        korean_pattern = re.compile('[가-힣ㄱ-ㅎㅏ-ㅣ]')
        return bool(korean_pattern.search(text))
    
    def contains_illegal_chars(self, text: str) -> bool:
        """Check for characters that might cause filesystem issues."""
        illegal_pattern = re.compile(r'[<>:"/\\|?*\x00-\x1f]')
        return bool(illegal_pattern.search(text))
    
    def romanize_korean(self, text: str) -> str:
        """Convert Korean text to romanized form using simple character mapping."""
        if not self.is_korean(text):
            return text
            
        try:
            result = []
            current_word = ''
            
            for char in text:
                if self.is_korean(char):
                    # Try to find direct mapping
                    if char in self.korean_to_roman:
                        current_word += self.korean_to_roman[char]
                    else:
                        # Fallback to unidecode for unknown characters
                        current_word += unidecode.unidecode(char)
                else:
                    if current_word:
                        result.append(current_word)
                        current_word = ''
                    result.append(char)
            
            if current_word:
                result.append(current_word)
            
            # Join and clean up the result
            romanized = ''.join(result)
            romanized = re.sub(r'\s+', ' ', romanized).strip()
            return romanized
            
        except Exception as e:
            print(f"Korean romanization failed: {str(e)}")
            return unidecode.unidecode(text)
    
    def sanitize_filename(self, text: str, max_length: int = 100) -> str:
        """Sanitize Korean filename for filesystem compatibility."""
        # Remove illegal characters
        text = re.sub(r'[<>:"/\\|?*\x00-\x1f]', '', text)
        
        # Handle Korean text
        if self.is_korean(text):
            # Try to romanize if needed
            text = self.romanize_korean(text)
        
        # Replace spaces with hyphens and remove multiple hyphens
        text = re.sub(r'\s+', '-', text)
        text = re.sub(r'-+', '-', text)
        
        # Truncate if too long
        if len(text) > max_length:
            base, ext = os.path.splitext(text)
            text = base[:max_length-len(ext)] + ext
            
        return text.strip('-')
    
    def detect_korean_content(self, content: str) -> bool:
        """Detect if content is primarily Korean."""
        if not content:
            return False
            
        # Count Korean characters
        korean_chars = len(re.findall('[가-힣ㄱ-ㅎㅏ-ㅣ]', content))
        total_chars = len(re.findall(r'\w', content))
        
        # Consider content Korean if more than 30% characters are Korean
        char_ratio = korean_chars / total_chars if total_chars else 0
        return char_ratio > 0.3
    
    def normalize_korean_text(self, text: str) -> str:
        """Normalize Korean text for consistency."""
        if not text:
            return text
            
        # Basic text normalization rules
        text = text.strip()
        text = re.sub(r'\s+', ' ', text)  # Normalize whitespace
        text = text.lower()  # Convert to lowercase
        
        # Remove common noise patterns
        text = re.sub(r'[^\w\s가-힣ㄱ-ㅎㅏ-ㅣ-]', '', text)  # Keep only word chars, spaces, and Korean
        
        return text
