import os
import magic
import json
import requests
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional
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
import re
from content_analyzer import ContentAnalyzer

class FileAnalyzer:
    def __init__(self, config_manager=None):
        self.stop_flag = threading.Event()
        self.config_manager = config_manager
        self.content_analyzer = ContentAnalyzer(config_manager)
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
                
                # If content analysis was successful, try to get a rename suggestion
                if content_analysis.get('success'):
                    if 'suggested_name' in content_analysis:
                        print(f"Using existing suggested name: {content_analysis['suggested_name']}")
                    else:
                        # Generate smart rename suggestion if enabled
                        if self.config_manager and self.config_manager.get_organization_rules().get('smart_rename_enabled', True):
                            print("Smart rename enabled, generating suggestion...")
                            rename_suggestion = self._suggest_rename(file_path, content_analysis)
                            print(f"Rename suggestion: {rename_suggestion}")
                            if rename_suggestion['success']:
                                content_analysis['suggested_name'] = rename_suggestion['suggested_name']
                                print(f"Added suggested name to content analysis: {rename_suggestion['suggested_name']}")
                
                analysis['content_analysis'] = content_analysis
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
            
            # If content_analysis already has a suggested name, use it
            if 'suggested_name' in content_analysis:
                return {
                    'success': True,
                    'suggested_name': content_analysis['suggested_name']
                }
            
            # Parse summary and keywords
            summary = ""
            keywords = []
            for line in analysis_text.split('\n'):
                if line.startswith('Summary:'):
                    summary = line.split(':', 1)[1].strip()
                elif line.startswith('Keywords:'):
                    keywords = [k.strip() for k in line.split(':', 1)[1].strip().split(',')]
                    
            # Get language setting from config
            language = "korean"
            if self.config_manager:
                language = self.config_manager.get_setting("language", "korean")
            
            # Create a more specific prompt for better name suggestions
            prompt = f"""Based on this content summary and keywords, suggest a clear and descriptive filename 
            (without extension) that reflects the content. The name should be in {language}.
            
            Content Summary: {summary}
            Keywords: {', '.join(keywords)}
            Original Filename: {os.path.splitext(os.path.basename(file_path))[0]}

            Requirements for the filename:
            1. Concise but descriptive (max 50 characters)
            2. Must reflect the main purpose or content
            3. If technical terms exist in keywords, include the most important one
            4. Use underscores to separate words
            5. No spaces or special characters except underscores
            
            Return ONLY the suggested filename, nothing else."""
            
            response = requests.post(
                self.config_manager.get_llm_provider_config().get('url'),
                json={
                    "model": self.config_manager.get_llm_provider_config().get('model'),
                    "prompt": prompt,
                    "stream": False
                }
            )
            
            if response.status_code == 200:
                suggested_name = response.json()['response'].strip()
                
                # Clean the suggested name
                suggested_name = ''.join(c if c.isalnum() or c == '_' else '_' 
                                      for c in suggested_name.lower())
                suggested_name = re.sub(r'_+', '_', suggested_name)  # Replace multiple underscores with single
                suggested_name = suggested_name.strip('_')  # Remove leading/trailing underscores
                
                # Truncate if too long
                if len(suggested_name) > 50:
                    suggested_name = suggested_name[:47] + "..."
                
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
            
            # Check if it's a text file, source code, or specific mime types
            if (mime_type.startswith('text/') or 
                mime_type in ['application/x-java-source', 'application/javascript', 'text/x-java-source'] or
                extension in ['.java', '.py', '.js', '.txt', '.json', '.xml', '.yaml', '.yml']):
                is_text = True
            
            # Increased size limit to 5MB for text files
            max_size = 5 * 1024 * 1024  # 5MB
            return is_text and size < max_size
            
        except Exception as e:
            print(f"Error checking content analyzability: {str(e)}")
            return False

    def _analyze_content(self, file_path: str, metadata: Dict[str, Any]) -> Dict[str, Any]:
        """
        Analyze file content using configured LLM provider for PARA categorization
        """
        try:
            # Get file content based on type
            content = self._get_file_content(file_path)
            if not content:
                return {'success': False, 'error': 'Could not read file content'}
            
            # Create analysis prompt
            prompt = f"""Analyze this file and provide:
1. PARA category (Projects, Areas, Resources, Archives) with Korean translation
2. Subcategory that best fits the content
3. Confidence level (high, medium, low)
4. Brief summary of the content
5. Keywords (comma-separated)
6. Suggest a descriptive filename (without extension) that reflects the content

File: {metadata.get('name', '')}
Type: {metadata.get('mime_type', '')}
Content: {content[:2000]}  # Limit content to first 2000 chars

Format the response exactly like this:
Category: **category_name (한글)**
Subcategory: **subcategory_name (한글)**
Confidence: **level**
Summary: [brief summary]
Keywords: [comma-separated keywords]
Suggested name: [descriptive_filename_without_extension]
"""
            
            # Use ContentAnalyzer for LLM queries instead of direct API calls
            analysis_text = self.content_analyzer._query_llm(prompt)
            print("\nDebug - LLM Response:", analysis_text)  # Debug log
            if not analysis_text:
                print("Debug - No response from LLM")  # Debug log
                return {'success': False, 'error': 'Failed to get response from LLM'}
            
            # Extract suggested name from analysis
            suggested_name = None
            print("\nDebug - Parsing response lines:")  # Debug log
            for line in analysis_text.split('\n'):
                print(f"Debug - Checking line: {line}")  # Debug log
                if line.lower().startswith('suggested name:') or line.lower().startswith('suggested filename:'):
                    # Remove markdown formatting and clean the suggested name
                    suggested_name = line.split(':', 1)[1].strip()
                    suggested_name = re.sub(r'\*\*|\*', '', suggested_name)  # Remove markdown formatting
                    suggested_name = suggested_name.strip()
                    print(f"Debug - Found suggested name: {suggested_name}")  # Debug log
                    break
            
            print(f"\nDebug - Final suggested name: {suggested_name}")  # Debug log
            return {
                'success': True,
                'analysis': analysis_text,
                'suggested_name': suggested_name
            }
            
        except Exception as e:
            print(f"Error in content analysis: {str(e)}")
            return {'success': False, 'error': str(e)}

    def _get_file_content(self, file_path: str) -> Optional[str]:
        """
        Get file content with proper encoding handling.
        Tries multiple encodings for Korean text support.
        """
        # Try different encodings for text files
        encodings = ['utf-8', 'cp949', 'euc-kr', 'iso-8859-1']
        
        # First check if it's a text file
        path = Path(file_path)
        extension = path.suffix.lower()
        
        # Special handling for Java files
        if extension == '.java':
            try:
                with open(file_path, 'rb') as f:
                    content = f.read()
                    # Try multiple encodings
                    for encoding in encodings:
                        try:
                            decoded = content.decode(encoding)
                            print(f"Successfully decoded Java file with {encoding}")
                            return decoded
                        except UnicodeDecodeError:
                            continue
                    # Fallback to replace invalid characters
                    return content.decode('utf-8', errors='replace')
            except Exception as e:
                print(f"Error reading Java file: {str(e)}")
                return None
        
        # For other text files
        if not self._is_text_file(path):
            print(f"Not a text file: {file_path}")
            return "[Binary file content not shown]"
            
        # Try reading with different encodings
        for encoding in encodings:
            try:
                with open(file_path, 'r', encoding=encoding) as f:
                    content = f.read(1024 * 1024)  # Read up to 1MB
                    if len(content.strip()) > 0:
                        print(f"Successfully read file with {encoding} encoding")
                        return content
            except UnicodeDecodeError:
                continue
            except Exception as e:
                print(f"Error reading file with {encoding}: {str(e)}")
                continue
        
        # If all encodings fail, try binary read and decode
        try:
            with open(file_path, 'rb') as f:
                content = f.read(1024 * 1024)  # Read up to 1MB
                # Try to decode as utf-8 with error handling
                return content.decode('utf-8', errors='replace')
        except Exception as e:
            print(f"Error reading file in binary mode: {str(e)}")
            return None

    def _is_text_file(self, path: Path) -> bool:
        """Check if the file is a text file."""
        mime_type = magic.Magic(mime=True).from_file(str(path))
        return mime_type.startswith('text/') or mime_type in ['application/x-java-source', 'application/javascript']

    def stop(self):
        """
        Stop ongoing analysis
        """
        self.stop_flag.set()
