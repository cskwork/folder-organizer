import json
import os
from pathlib import Path
from typing import Dict, Any

class ConfigManager:
    _instance = None
    _observers = []

    def __new__(cls, config_path: str = "config.json"):
        if cls._instance is None:
            cls._instance = super(ConfigManager, cls).__new__(cls)
            cls._instance.config_path = config_path
            cls._instance.config = cls._instance._load_config()
        return cls._instance

    def __init__(self, config_path: str = "config.json"):
        # __new__ handles initialization
        pass

    def _load_config(self) -> Dict[str, Any]:
        """Load configuration from file or create default"""
        try:
            with open(self.config_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except FileNotFoundError:
            return self._create_default_config()

    def _create_default_config(self) -> Dict[str, Any]:
        """Create and save default configuration"""
        default_config = {
            "default_model": "mistral",
            "ollama_url": "http://localhost:11434/api/generate",
            "max_file_size_mb": 1,
            "backup_enabled": True,
            "supported_extensions": {
                "documents": [".txt", ".doc", ".docx", ".pdf", ".rtf", ".odt"],
                "images": [".jpg", ".jpeg", ".png", ".gif", ".bmp", ".tiff"],
                "videos": [".mp4", ".avi", ".mov", ".wmv", ".flv", ".mkv"],
                "audio": [".mp3", ".wav", ".ogg", ".m4a", ".flac"],
                "archives": [".zip", ".rar", ".7z", ".tar", ".gz"]
            },
            "organization_rules": {
                "use_content_analysis": True,
                "use_file_type": True,
                "use_date": True,
                "date_format": "%Y-%m",
                "min_confidence_score": 0.7,
                "smart_rename_enabled": True  # New option
            }
        }
        
        self.save_config(default_config)
        return default_config

    def save_config(self, config: Dict[str, Any] = None) -> None:
        """Save configuration to file"""
        if config is not None:
            self.config = config
            
        with open(self.config_path, 'w') as f:
            json.dump(self.config, f, indent=4)
        self.notify_observers()  # Notify observers when config is saved

    def get_setting(self, key: str, default: Any = None) -> Any:
        """Get a configuration setting by key"""
        return self.config.get(key, default)

    def set_setting(self, key: str, value: Any) -> None:
        """Set a configuration setting"""
        self.config[key] = value
        self.save_config()
        self.notify_observers()  # Notify observers when setting is changed

    def get_supported_extensions(self) -> Dict[str, list]:
        """Get supported file extensions by category"""
        return self.config.get("supported_extensions", {})

    def get_organization_rules(self) -> Dict[str, Any]:
        """Get file organization rules"""
        return self.config.get("organization_rules", {})

    def add_observer(self, observer):
        """Add an observer that will be notified of config changes"""
        if observer not in self._observers:
            self._observers.append(observer)

    def remove_observer(self, observer):
        """Remove an observer"""
        if observer in self._observers:
            self._observers.remove(observer)

    def notify_observers(self):
        """Notify all observers of config changes"""
        for observer in self._observers:
            observer.on_settings_changed()
