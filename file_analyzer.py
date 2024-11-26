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
    def __init__(self, model: str = "mistral", ollama_url: str = "http://localhost:11434/api/generate"):
        self.model = model
        self.ollama_url = ollama_url
        self.stop_flag = threading.Event()
        self.supported_extensions = {
            'documents': ['.txt', '.doc', '.docx', '.pdf', '.rtf', '.odt'],
            'images': ['.jpg', '.jpeg', '.png', '.gif', '.bmp', '.tiff'],
            'videos': ['.mp4', '.avi', '.mov', '.wmv', '.flv', '.mkv'],
            'audio': ['.mp3', '.wav', '.ogg', '.m4a', '.flac'],
            'archives': ['.zip', '.rar', '.7z', '.tar', '.gz']
        }

    def analyze_directory(self, directory: str, use_content: bool = True,
                         use_type: bool = True, use_date: bool = True) -> Dict[str, Any]:
        """
        Analyze all files in the directory and return analysis results
        """
        self.stop_flag.clear()
        results = {}
        
        for root, _, files in os.walk(directory):
            if self.stop_flag.is_set():
                break
                
            for file in files:
                if self.stop_flag.is_set():
                    break
                    
                file_path = os.path.join(root, file)
                try:
                    results[file_path] = self.analyze_file(file_path, use_content, use_type, use_date)
                except Exception as e:
                    print(f"Error analyzing {file_path}: {str(e)}")
                    continue
        
        return results

    def analyze_file(self, file_path: str, use_content: bool = True,
                    use_type: bool = True, use_date: bool = True) -> Dict[str, Any]:
        """
        Analyze a single file
        """
        try:
            # Get file metadata
            metadata = self._get_file_metadata(file_path)
            analysis = {'metadata': metadata}
            
            # Add content analysis if requested and possible
            if use_content and self._can_analyze_content(file_path):
                content_analysis = self._analyze_content(file_path, metadata)
                analysis['content_analysis'] = content_analysis
            
            return analysis
            
        except Exception as e:
            return {
                'error': str(e),
                'metadata': {},
                'content_analysis': {'success': False, 'error': str(e)}
            }

    def _get_file_metadata(self, file_path: str) -> Dict[str, Any]:
        """Get comprehensive file metadata"""
        stat = os.stat(file_path)
        basic_metadata = {
            "name": os.path.basename(file_path),
            "extension": os.path.splitext(file_path)[1].lower(),
            "size": stat.st_size,
            "created": datetime.fromtimestamp(stat.st_ctime).isoformat(),
            "modified": datetime.fromtimestamp(stat.st_mtime).isoformat(),
            "accessed": datetime.fromtimestamp(stat.st_atime).isoformat(),
            "mime_type": magic.from_file(file_path, mime=True)
        }
        
        # Get type-specific metadata
        ext = basic_metadata["extension"]
        specific_metadata = {}
        
        if ext in ['.doc', '.docx', '.xls', '.xlsx', '.ppt', '.pptx']:
            specific_metadata = self._get_office_metadata(file_path)
        elif ext == '.pdf':
            specific_metadata = self._get_pdf_metadata(file_path)
        elif ext in ['.jpg', '.jpeg', '.png', '.gif', '.bmp', '.tiff']:
            specific_metadata = self._get_image_metadata(file_path)
        elif ext in ['.eml', '.msg']:
            specific_metadata = self._get_email_metadata(file_path)
        elif ext in ['.py', '.js', '.java', '.cpp', '.cs']:
            specific_metadata = self._get_code_metadata(file_path)
        
        return {**basic_metadata, **specific_metadata}

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
        extension = os.path.splitext(file_path)[1].lower()
        size = os.path.getsize(file_path)
        
        # Only analyze text-based files under 1MB
        return (extension in self.supported_extensions['documents'] and
                size < 1024 * 1024 and
                magic.from_file(file_path, mime=True).startswith('text/'))

    def _analyze_content(self, file_path: str, metadata: Dict[str, Any]) -> Dict[str, Any]:
        """
        Analyze file content using Ollama for PARA categorization with metadata context
        """
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
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
            
            prompt = f"""Analyze this content and its metadata to classify it according to the PARA method. Choose the most appropriate category:

            File Metadata:
            {chr(10).join(metadata_summary)}

            Categories:
            1. Projects: Time-bound efforts with clear goals
               - current_projects: Active work requiring immediate attention
                 Keywords: ongoing project, current task, in progress, this week, this month, active development
               - upcoming_projects: Future planned work
                 Keywords: planned, scheduled, upcoming, next phase, future project, to be started

            2. Areas: Ongoing responsibilities requiring maintenance
               - work: Professional responsibilities
                 Keywords: business, career, job duties, professional development, work-related
               - personal: Personal life management
                 Keywords: personal goals, family, home, lifestyle, relationships, finances
               - health: Health and wellness
                 Keywords: fitness, diet, exercise, medical, mental health, wellness

            3. Resources: Reference materials and tools
               - references: Knowledge base and documentation
                 Keywords: guide, manual, documentation, reference material, instructions, specifications
               - learning: Educational materials
                 Keywords: tutorial, course, study material, learning resource, educational content
               - tools: Utilities and templates
                 Keywords: tool, template, script, utility, software, application

            4. Archives: Completed or inactive items
               - done: Completed projects and tasks
                 Keywords: completed, finished, delivered, done, accomplished, closed
               - old: Outdated or archived materials
                 Keywords: archived, outdated, old version, past, historical, deprecated

            Consider both the content and metadata (especially dates, authors, and keywords) when classifying.
            
            Provide:
            1. Main PARA category (Projects/Areas/Resources/Archives)
            2. Specific subcategory from above
            3. Confidence level (high/medium/low)
            4. Key phrases and metadata that justify this classification

            Content: {content[:1000]}..."""
            
            response = requests.post(
                self.ollama_url,
                json={
                    "model": self.model,
                    "prompt": prompt,
                    "stream": False
                }
            )
            
            if response.status_code == 200:
                return {
                    'analysis': response.json()['response'],
                    'success': True,
                    'metadata_used': bool(metadata_summary)
                }
            else:
                return {
                    'analysis': "Content analysis failed",
                    'success': False,
                    'error': f"HTTP {response.status_code}"
                }
                
        except Exception as e:
            return {
                'analysis': "Content analysis failed",
                'success': False,
                'error': str(e)
            }

    def stop(self):
        """
        Stop ongoing analysis
        """
        self.stop_flag.set()
