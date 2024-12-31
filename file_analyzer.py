import os
import magic
import json
import requests
from datetime import datetime
from pathlib import Path
from typing import Dict, Any
import threading
import win32com.client
from PIL import Image
from PIL.ExifTags import TAGS
import email
import PyPDF2
import docx
import mimetypes
import yaml
from xml.etree import ElementTree

class FileAnalyzer:
    def __init__(self, model: str = "mistral", ollama_url: str = "http://localhost:11434/api/generate", config_manager=None):
        self.model = model
        self.ollama_url = ollama_url
        self.stop_flag = threading.Event()
        self.config_manager = config_manager
        self.supported_extensions = {
            'documents': ['.txt', '.doc', '.docx', '.pdf', '.rtf', '.odt'],
            'images': ['.jpg', '.jpeg', '.png', '.gif', '.bmp', '.tiff'],
            'videos': ['.mp4', '.avi', '.mov', '.wmv', '.flv', '.mkv'],
            'audio': ['.mp3', '.wav', '.ogg', '.m4a', '.flac'],
            'archives': ['.zip', '.rar', '.7z', '.tar', '.gz']
        }

    def analyze_directory(self, directory: str, use_content: bool = True,
                         use_type: bool = True, use_date: bool = True,
                         progress_callback=None) -> Dict[str, Any]:
        """
        Analyze all files in the directory and return analysis results
        """
        self.stop_flag.clear()
        results = {}
        
        # Count total files for progress tracking
        total_files = sum([len(files) for _, _, files in os.walk(directory)])
        processed_files = 0
        
        for root, _, files in os.walk(directory):
            if self.stop_flag.is_set():
                break
                
            for file in files:
                if self.stop_flag.is_set():
                    break
                    
                file_path = os.path.join(root, file)
                try:
                    results[file_path] = self.analyze_file(file_path, use_content, use_type, use_date)
                    processed_files += 1
                    
                    if progress_callback:
                        progress = (processed_files / total_files) * 100
                        status = f"Analyzing: {os.path.basename(file_path)} ({processed_files}/{total_files})"
                        progress_callback(progress, status)
                        
                except Exception as e:
                    print(f"Error analyzing {file_path}: {str(e)}")
                    processed_files += 1
                    continue
        
        if progress_callback:
            progress_callback(100, "Analysis complete")
        
        return results

    def analyze_file(self, file_path: str, use_content: bool = True,
                    use_type: bool = True, use_date: bool = True) -> Dict[str, Any]:
        try:
            print(f"\nAnalyzing file: {file_path}")
            # Get existing metadata and analysis
            metadata = self._extract_metadata(file_path)
            analysis = {'metadata': metadata}
            print(f"Metadata: {metadata}")
            
            # Add content analysis if requested and possible
            if use_content and self._can_analyze_content(file_path):
                print("Content analysis possible, proceeding...")
                content_analysis = self._analyze_content(file_path, metadata)
                print(f"Content analysis result: {content_analysis}")
                analysis['content_analysis'] = content_analysis
                
                # Generate smart rename suggestion if enabled
                if self.config_manager:
                    org_rules = self.config_manager.get_organization_rules()
                    print(f"Organization rules: {org_rules}")
                    if org_rules.get('smart_rename_enabled', True):
                        print("Smart rename enabled, generating suggestion...")
                        rename_suggestion = self._suggest_rename(file_path, content_analysis)
                        print(f"Rename suggestion: {rename_suggestion}")
                        if rename_suggestion['success']:
                            analysis['suggested_name'] = rename_suggestion['suggested_name']
            else:
                print(f"Content analysis skipped. use_content={use_content}, can_analyze={self._can_analyze_content(file_path)}")
            
            return analysis
            
        except Exception as e:
            print(f"Error in analyze_file: {str(e)}")
            return {
                'error': str(e),
                'metadata': {},
                'content_analysis': {'success': False, 'error': str(e)}
            }

    def _extract_metadata(self, file_path: str) -> Dict[str, Any]:
        """Extract metadata from the file."""
        try:
            # Convert path to Path object with proper encoding
            path = Path(file_path)
            stats = path.stat()
            
            # Handle Korean filename
            try:
                name = path.name
                # Try to decode bytes if needed
                if isinstance(name, bytes):
                    name = name.decode('utf-8')
            except UnicodeEncodeError:
                # Fallback to raw bytes if decode fails
                name = path.name
            
            metadata = {
                'name': name,
                'extension': path.suffix.lower(),
                'size': stats.st_size,
                'created': datetime.fromtimestamp(stats.st_ctime).isoformat(),
                'modified': datetime.fromtimestamp(stats.st_mtime).isoformat(),
                'accessed': datetime.fromtimestamp(stats.st_atime).isoformat(),
            }
            
            try:
                # Use raw bytes for mime type detection
                mime = magic.Magic(mime=True)
                mime_type = mime.from_buffer(open(file_path, 'rb').read(2048))
                metadata['mime_type'] = mime_type
            except Exception as e:
                metadata['mime_type'] = f"File type detection failed: {str(e)}"
            
            # Count lines for text files
            if self._is_text_file(path):
                try:
                    # Try different encodings for text files
                    encodings = ['utf-8', 'cp949', 'euc-kr']
                    for encoding in encodings:
                        try:
                            with open(file_path, 'r', encoding=encoding) as f:
                                metadata['size_lines'] = sum(1 for _ in f)
                            break
                        except UnicodeDecodeError:
                            continue
                except Exception:
                    metadata['size_lines'] = 0
            
            return metadata
            
        except Exception as e:
            return {
                'error': f"Error extracting metadata: {str(e)}"
            }

    def _suggest_rename(self, file_path: str, content_analysis: Dict[str, Any]) -> Dict[str, Any]:
        """Suggest a new name for the file based on its content."""
        try:
            if not content_analysis.get('success'):
                return {
                    'success': False,
                    'error': 'Content analysis failed'
                }
                
            # Extract key information from content analysis
            analysis_text = content_analysis.get('analysis', '')
            
            # Parse summary and keywords
            summary = ""
            keywords = []
            for line in analysis_text.split('\n'):
                if line.startswith('Summary:'):
                    summary = line.split(':', 1)[1].strip()
                elif line.startswith('Keywords:'):
                    keywords = line.split(':', 1)[1].strip().split(',')
            
            # Get language setting from config
            language = "korean"
            if self.config_manager:
                language = self.config_manager.get_setting("language", "korean")
            
            # Use Ollama to suggest a descriptive filename
            prompt = f"""Based on this content summary and keywords, suggest a clear and descriptive filename 
            (without extension) that reflects the content. The name should be in {language}.

            Content Summary: {summary}
            Keywords: {', '.join(keywords)}

            Requirements for the filename:
            1. Concise but descriptive (max 50 characters)
            2. If Korean:
               - Use Korean characters naturally
               - Can include English if needed for technical terms
               - Use hyphens (-) to separate words if needed
            3. If English:
               - Use only alphanumeric characters, hyphens, and underscores
               - All lowercase
               - No spaces (use hyphens instead)
            
            Return ONLY the suggested filename, nothing else."""
            
            response = requests.post(
                self.ollama_url,
                json={
                    "model": self.model,
                    "prompt": prompt,
                    "stream": False
                }
            )
            
            if response.status_code == 200:
                suggested_name = response.json()['response'].strip()
                
                # Clean the suggested name based on language
                if language == "korean":
                    # Allow Korean characters, numbers, letters, and basic punctuation
                    suggested_name = ''.join(c for c in suggested_name 
                                          if c.isalnum() or c in '-_' or ord(c) > 128)
                else:
                    # English mode - only alphanumeric and basic punctuation
                    suggested_name = ''.join(c if c.isalnum() or c in '-_' else '-' 
                                          for c in suggested_name.lower())
                
                suggested_name = suggested_name[:50]  # Truncate if too long
                
                return {
                    'success': True,
                    'suggested_name': suggested_name,
                    'confidence': 0.8
                }
            else:
                return {
                    'success': False,
                    'error': 'Failed to get rename suggestion'
                }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }

    def _get_office_metadata(self, file_path: str) -> Dict[str, Any]:
        """Extract metadata from Microsoft Office files"""
        try:
            app = win32com.client.Dispatch("Word.Application")
            app.Visible = False
            doc = app.Documents.Open(file_path)
            
            metadata = {
                "author": doc.Author,
                "title": doc.Title,
                "subject": doc.Subject,
                "keywords": doc.Keywords,
                "last_author": doc.LastAuthor,
                "revision": doc.Revisions.Count,
                "comments": doc.Comments.Count
            }
            
            doc.Close()
            app.Quit()
            return metadata
        except:
            return {}

    def _get_pdf_metadata(self, file_path: str) -> Dict[str, Any]:
        """Extract metadata from PDF files"""
        try:
            with open(file_path, 'rb') as file:
                reader = PyPDF2.PdfReader(file)
                metadata = reader.metadata
                if metadata:
                    return {
                        "author": metadata.get('/Author', ''),
                        "creator": metadata.get('/Creator', ''),
                        "producer": metadata.get('/Producer', ''),
                        "subject": metadata.get('/Subject', ''),
                        "title": metadata.get('/Title', ''),
                        "pages": len(reader.pages)
                    }
        except:
            return {}
        return {}

    def _get_image_metadata(self, file_path: str) -> Dict[str, Any]:
        """Extract EXIF metadata from image files"""
        try:
            image = Image.open(file_path)
            exif = image.getexif()
            
            metadata = {}
            if exif:
                for tag_id in exif:
                    tag = TAGS.get(tag_id, tag_id)
                    data = exif.get(tag_id)
                    metadata[tag] = str(data)
            
            # Add basic image info
            metadata.update({
                "format": image.format,
                "size": image.size,
                "mode": image.mode
            })
            return metadata
        except:
            return {}

    def _get_email_metadata(self, file_path: str) -> Dict[str, Any]:
        """Extract metadata from email files"""
        try:
            with open(file_path, 'r', encoding='utf-8') as file:
                msg = email.message_from_file(file)
                return {
                    "subject": msg.get("subject", ""),
                    "from": msg.get("from", ""),
                    "to": msg.get("to", ""),
                    "date": msg.get("date", ""),
                    "message_id": msg.get("message-id", "")
                }
        except:
            return {}

    def _get_code_metadata(self, file_path: str) -> Dict[str, Any]:
        """Extract metadata from code files"""
        try:
            with open(file_path, 'r', encoding='utf-8') as file:
                content = file.read()
                
            metadata = {
                "size_lines": len(content.splitlines()),
                "has_main": "def main" in content or "if __name__ == '__main__'" in content,
                "imports": [],
                "classes": [],
                "functions": []
            }
            
            # Extract imports
            import_lines = [line for line in content.splitlines() 
                          if line.strip().startswith(('import ', 'from '))]
            metadata["imports"] = import_lines
            
            # Basic class and function detection
            metadata["classes"] = [line.split('class ')[1].split(':')[0].strip() 
                                 for line in content.splitlines() 
                                 if line.strip().startswith('class ')]
            
            metadata["functions"] = [line.split('def ')[1].split('(')[0].strip() 
                                   for line in content.splitlines() 
                                   if line.strip().startswith('def ')]
            
            return metadata
        except:
            return {}

    def _can_analyze_content(self, file_path: str) -> bool:
        """
        Determine if file content should be analyzed based on type and size
        """
        try:
            extension = os.path.splitext(file_path)[1].lower()
            size = os.path.getsize(file_path)
            
            # Support more text-based files and increase size limit for Korean text
            is_text = False
            mime_type = magic.from_file(file_path, mime=True)
            
            # Check if it's a text file or source code
            if (mime_type.startswith('text/') or 
                mime_type in ['application/x-java-source', 'application/javascript'] or
                extension in ['.java', '.py', '.js', '.txt']):
                is_text = True
            
            # Increased size limit to 5MB for text files
            return is_text and size < 5 * 1024 * 1024
            
        except Exception as e:
            print(f"Error checking content analyzability: {str(e)}")
            return False

    def _analyze_content(self, file_path: str, metadata: Dict[str, Any]) -> Dict[str, Any]:
        """
        Analyze file content using Ollama for PARA categorization with metadata context
        """
        try:
            # Try different encodings for Korean text
            content = None
            encodings = ['utf-8', 'cp949', 'euc-kr']
            
            for encoding in encodings:
                try:
                    with open(file_path, 'r', encoding=encoding) as f:
                        content = f.read()
                    break
                except UnicodeDecodeError:
                    continue
                    
            if content is None:
                return {
                    'success': False,
                    'error': 'Failed to decode file content'
                }
            
            # Create metadata summary
            metadata_summary = []
            if metadata.get('author'):
                metadata_summary.append(f"Author: {metadata['author']}")
            if metadata.get('title'):
                metadata_summary.append(f"Title: {metadata['title']}")
            if metadata.get('subject'):
                metadata_summary.append(f"Subject: {metadata['subject']}")
            if metadata.get('keywords'):
                metadata_summary.append(f"Keywords: {metadata['keywords']}")
            if metadata.get('created'):
                metadata_summary.append(f"Created: {metadata['created']}")
            
            # First, analyze content and suggest category
            analysis_prompt = f"""Analyze this content and provide a PARA category classification. The content appears to be in Korean.

            File Metadata:
            {chr(10).join(metadata_summary)}

            Content Preview:
            {content[:2000]}...

            Based on the content and metadata, classify this file into one of these categories:

            1. Projects (프로젝트)
               - active: Current active projects (진행중인 프로젝트)
               - next: Future planned projects (예정된 프로젝트)
               - done: Completed projects (완료된 프로젝트)

            2. Areas (영역)
               - work: Work-related (업무)
               - personal: Personal life (개인)
               - health: Health and wellness (건강)
               - finance: Financial matters (재정)

            3. Resources (자료)
               - knowledge: Knowledge base (지식)
               - references: Reference materials (참고자료)
               - media: Media files (미디어)

            4. Archives (보관)
               - projects: Old projects (프로젝트)
               - resources: Old resources (자료)
               - quarterly: Quarterly archives (분기별)

            Respond in this exact format:
            Category: [main category]
            Subcategory: [subcategory]
            Confidence: [high/medium/low]
            Summary: [1-2 sentence summary]
            Keywords: [3-5 key topics]"""
            
            response = requests.post(
                self.ollama_url,
                json={
                    "model": self.model,
                    "prompt": analysis_prompt,
                    "stream": False
                }
            )
            
            if response.status_code == 200:
                return {
                    'success': True,
                    'analysis': response.json()['response']
                }
            else:
                return {
                    'success': False,
                    'error': f"HTTP {response.status_code}"
                }
                
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }

    def _is_text_file(self, path: Path) -> bool:
        """Check if the file is a text file."""
        mime_type = magic.Magic(mime=True).from_file(str(path))
        return mime_type.startswith('text/') or mime_type in ['application/x-java-source', 'application/javascript']

    def stop(self):
        """
        Stop ongoing analysis
        """
        self.stop_flag.set()
