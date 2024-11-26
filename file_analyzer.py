import os
import magic
import json
import requests
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any
import threading

class FileAnalyzer:
    def __init__(self, model: str = "mistral"):
        self.model = model
        self.ollama_url = "http://localhost:11434/api/generate"
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
        Analyze a single file and return its properties
        """
        result = {
            'path': file_path,
            'name': os.path.basename(file_path),
            'size': os.path.getsize(file_path)
        }
        
        if use_date:
            stats = os.stat(file_path)
            result.update({
                'created': datetime.fromtimestamp(stats.st_ctime).isoformat(),
                'modified': datetime.fromtimestamp(stats.st_mtime).isoformat(),
                'accessed': datetime.fromtimestamp(stats.st_atime).isoformat()
            })
        
        if use_type:
            result['mime_type'] = magic.from_file(file_path, mime=True)
            result['extension'] = os.path.splitext(file_path)[1].lower()
            result['category'] = self._get_file_category(result['extension'])
        
        if use_content and self._should_analyze_content(file_path):
            result['content_analysis'] = self._analyze_content(file_path)
        
        return result

    def _get_file_category(self, extension: str) -> str:
        """
        Determine the category of a file based on its extension
        """
        for category, extensions in self.supported_extensions.items():
            if extension in extensions:
                return category
        return 'other'

    def _should_analyze_content(self, file_path: str) -> bool:
        """
        Determine if file content should be analyzed based on type and size
        """
        extension = os.path.splitext(file_path)[1].lower()
        size = os.path.getsize(file_path)
        
        # Only analyze text-based files under 1MB
        return (extension in self.supported_extensions['documents'] and
                size < 1024 * 1024 and
                magic.from_file(file_path, mime=True).startswith('text/'))

    def _analyze_content(self, file_path: str) -> Dict[str, Any]:
        """
        Analyze file content using Ollama for PARA categorization with max 1 depth
        """
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            prompt = f"""Analyze this content and classify it according to the PARA method. Choose the most appropriate category:

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

            Provide:
            1. Main PARA category (Projects/Areas/Resources/Archives)
            2. Specific subcategory from above
            3. Confidence level (high/medium/low)
            4. Key phrases from the content that justify this classification

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
                    'success': True
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
