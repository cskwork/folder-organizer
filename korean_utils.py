import re
from typing import Optional
import MeCab
from unidecode import unidecode

class KoreanTextHandler:
    """Handles Korean text processing and validation."""
    
    def __init__(self):
        """Initialize MeCab tokenizer."""
        self.mecab = MeCab.Tagger()
    
    def is_korean(self, text: str) -> bool:
        """Check if text contains Korean characters."""
        korean_pattern = re.compile('[가-힣ㄱ-ㅎㅏ-ㅣ]')
        return bool(korean_pattern.search(text))
    
    def contains_illegal_chars(self, text: str) -> bool:
        """Check for characters that might cause filesystem issues."""
        illegal_pattern = re.compile(r'[<>:"/\\|?*\x00-\x1f]')
        return bool(illegal_pattern.search(text))
    
    def romanize_korean(self, text: str) -> str:
        """Convert Korean text to romanized form using MeCab."""
        if not self.is_korean(text):
            return text
            
        # Parse with MeCab
        node = self.mecab.parseToNode(text)
        romanized_parts = []
        
        while node:
            if node.surface:  # Skip empty nodes
                if self.is_korean(node.surface):
                    # Get reading (if available) or use surface form
                    reading = node.feature.split(',')[7] if len(node.feature.split(',')) > 7 else node.surface
                    romanized = unidecode(reading)
                    romanized_parts.append(romanized)
                else:
                    romanized_parts.append(node.surface)
            node = node.next
            
        return '-'.join(romanized_parts)
    
    def sanitize_filename(self, text: str, max_length: int = 100) -> str:
        """Sanitize Korean filename for filesystem compatibility."""
        # Remove illegal characters
        text = re.sub(r'[<>:"/\\|?*\x00-\x1f]', '', text)
        
        # Handle Korean text
        if self.is_korean(text):
            try:
                # Try UTF-8 encoding
                text.encode('utf-8')
            except UnicodeEncodeError:
                text = self.romanize_korean(text)
        
        # Replace spaces with hyphens and remove multiple hyphens
        text = re.sub(r'\s+', '-', text)
        text = re.sub(r'-+', '-', text)
        
        # Trim to max length while preserving Korean character boundaries
        if len(text) > max_length:
            while len(text.encode('utf-8')) > max_length and text:
                text = text[:-1]
        
        return text.strip('-')
    
    def detect_korean_content(self, content: str) -> bool:
        """Detect if content is primarily Korean using MeCab analysis."""
        if not content:
            return False
            
        # Count Korean characters
        korean_chars = len(re.findall('[가-힣ㄱ-ㅎㅏ-ㅣ]', content))
        total_chars = len(re.findall(r'\w', content))
        
        # Use MeCab to analyze text structure
        if korean_chars > 0:
            node = self.mecab.parseToNode(content)
            korean_morphemes = 0
            total_morphemes = 0
            
            while node:
                if node.surface:  # Skip empty nodes
                    total_morphemes += 1
                    if any(self.is_korean(char) for char in node.surface):
                        korean_morphemes += 1
                node = node.next
            
            # Consider content Korean if more than 30% morphemes are Korean
            morpheme_ratio = korean_morphemes / total_morphemes if total_morphemes else 0
            return morpheme_ratio > 0.3
            
        return False
    
    def normalize_korean_text(self, text: str) -> str:
        """Normalize Korean text for consistency using MeCab."""
        if not text:
            return text
            
        # Parse with MeCab to get standard form
        node = self.mecab.parseToNode(text)
        normalized_parts = []
        
        while node:
            if node.surface:  # Skip empty nodes
                # Get dictionary form if available
                features = node.feature.split(',')
                if len(features) > 7 and features[7] != '*':
                    normalized_parts.append(features[7])
                else:
                    normalized_parts.append(node.surface)
            node = node.next
        
        # Join and normalize whitespace
        text = ' '.join(normalized_parts)
        text = re.sub(r'\s+', ' ', text).strip()
        
        return text
