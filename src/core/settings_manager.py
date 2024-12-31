import json
from pathlib import Path
from typing import Dict, Any, List, Optional
import logging

class SettingsManager:
    """Manager for application settings"""
    
    def __init__(self, config_file: str = "config.json"):
        self.logger = logging.getLogger(__name__)
        self.config_file = Path(config_file)
        self.observers = []
        self.settings = self._load_default_settings()
        
        # Load settings from file
        if self.config_file.exists():
            self._load_settings()
        else:
            self._save_settings()
            self.logger.info("Created new settings file")
    
    def _load_default_settings(self) -> Dict[str, Any]:
        """Load default settings"""
        return {
            "appearance": {
                "theme": "dark",
                "font_size": 12,
                "accent_color": "#1f538d"
            },
            "file_analyzer": {
                "sample_size": 4096,
                "confidence_threshold": 0.7,
                "supported_languages": ["en", "es", "fr", "de", "it"]
            },
            "file_organizer": {
                "confirm_moves": True,
                "create_backups": False,
                "default_organization": "by_type"
            },
            "rules": {
                "custom_rules": []
            },
            "general": {
                "default_directory": str(Path.home()),
                "keep_logs": True,
                "auto_update": True
            }
        }
    
    def _load_settings(self):
        """Load settings from file"""
        try:
            with open(self.config_file, 'r') as f:
                loaded_settings = json.load(f)
                # Update settings while preserving default values
                self._update_dict(self.settings, loaded_settings)
            self.logger.info("Settings loaded successfully")
        except Exception as e:
            self.logger.error(f"Error loading settings: {e}")
    
    def _save_settings(self):
        """Save settings to file"""
        try:
            with open(self.config_file, 'w') as f:
                json.dump(self.settings, f, indent=4)
            self.logger.info("Settings saved successfully")
        except Exception as e:
            self.logger.error(f"Error saving settings: {e}")
    
    def _update_dict(self, target: Dict, source: Dict):
        """Recursively update dictionary while preserving structure"""
        for key, value in source.items():
            if key in target:
                if isinstance(value, dict) and isinstance(target[key], dict):
                    self._update_dict(target[key], value)
                else:
                    target[key] = value
    
    def get(self, key: str, default: Any = None) -> Any:
        """Get setting value using dot notation (e.g., 'appearance.theme')"""
        try:
            value = self.settings
            for part in key.split('.'):
                value = value[part]
            return value
        except (KeyError, TypeError):
            return default
    
    def set(self, key: str, value: Any):
        """Set setting value using dot notation"""
        try:
            parts = key.split('.')
            target = self.settings
            
            # Navigate to the correct nested dictionary
            for part in parts[:-1]:
                if part not in target:
                    target[part] = {}
                target = target[part]
            
            # Set the value
            target[parts[-1]] = value
            
            # Save settings and notify observers
            self._save_settings()
            self._notify_observers()
            
        except Exception as e:
            self.logger.error(f"Error setting value for {key}: {e}")
    
    def get_all(self) -> Dict[str, Any]:
        """Get all settings"""
        return self.settings
    
    def add_observer(self, observer):
        """Add settings observer"""
        if observer not in self.observers:
            self.observers.append(observer)
    
    def remove_observer(self, observer):
        """Remove settings observer"""
        if observer in self.observers:
            self.observers.remove(observer)
    
    def _notify_observers(self):
        """Notify all observers of settings changes"""
        for observer in self.observers:
            if hasattr(observer, 'on_settings_changed'):
                observer.on_settings_changed(self.settings)
