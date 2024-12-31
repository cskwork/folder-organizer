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
        else:
            # Update config path if different and reload config
            if cls._instance.config_path != config_path:
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
        config = {
            "llm_config": {
                "default_provider": "ollama",
                "providers": {
                    "ollama": {
                        "url": "http://localhost:11434/api/generate",
                        "default_model": "mistral"
                    },
                    "openrouter": {
                        "url": "https://openrouter.ai/api/v1/chat/completions",
                        "api_key": "",
                        "site_url": "",
                        "app_name": "",
                        "default_model": "openai/gpt-3.5-turbo"
                    }
                }
            },
            "max_file_size_mb": 1,
            "backup_enabled": False,
            "date_organization_enabled": False,
            "remove_empty_folders": True,
            "language": "english",
            "parent_folders": {
                "english": ["1_projects", "2_areas", "3_resources", "4_archives", "5_other"],
                "korean": ["1_프로젝트", "2_영역", "3_자료", "4_보관", "5_기타"]
            },
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
                "smart_rename_enabled": True
            }
        }
        
        self.save_config(config)
        return config

    def save_config(self, config: Dict[str, Any] = None) -> None:
        """Save configuration to file"""
        if config is not None:
            self.config = config
            
        with open(self.config_path, 'w', encoding='utf-8') as f:
            json.dump(self.config, f, indent=4)
            
        # Reload config to ensure all instances have the latest version
        self.config = self._load_config()
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

    def get_llm_provider_config(self) -> Dict[str, Any]:
        """Get the current LLM provider configuration"""
        llm_config = self.get_setting("llm_config", {})
        provider = llm_config.get("default_provider", "ollama")
        providers = llm_config.get("providers", {})
        provider_config = providers.get(provider, {})
        
        if not provider_config:
            # Return default Ollama config if no provider config found
            return {
                "url": "http://localhost:11434/api/generate",
                "model": "mistral"
            }
            
        return {
            "url": provider_config.get("url"),
            "model": provider_config.get("default_model"),
            "api_key": provider_config.get("api_key", ""),
            "site_url": provider_config.get("site_url", ""),
            "app_name": provider_config.get("app_name", "")
        }

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
