import json
import os
from pathlib import Path
from typing import Dict, Any, List, Optional, Union
from pydantic import BaseModel, Field, validator
import logging

class LLMProviderConfig(BaseModel):
    """Configuration for LLM providers."""
    url: str = Field(..., description="API endpoint URL")
    api_key: Optional[str] = Field(default="", description="API key for authentication")
    site_url: Optional[str] = Field(default="", description="Site URL for HTTP-Referer header")
    app_name: Optional[str] = Field(default="", description="Application name for X-Title header")
    default_model: str = Field(..., description="Default model to use")
    configured: bool = Field(default=True, description="Whether this provider is configured")

class LLMConfig(BaseModel):
    """LLM configuration settings."""
    default_provider: str = Field(default="ollama", description="Default LLM provider")
    providers: Dict[str, LLMProviderConfig] = Field(default_factory=dict, description="Available providers")
    model_configs: Dict[str, Dict[str, Any]] = Field(default_factory=dict, description="Model-specific configurations")

class OrganizationRules(BaseModel):
    """File organization rules configuration."""
    use_content_analysis: bool = Field(default=True, description="Enable content analysis")
    use_file_type: bool = Field(default=True, description="Enable file type organization")
    use_date: bool = Field(default=True, description="Enable date organization")
    date_format: str = Field(default="%Y-%m", description="Date format for organization")
    min_confidence_score: float = Field(default=0.7, ge=0.0, le=1.0, description="Minimum confidence score")
    smart_rename_enabled: bool = Field(default=True, description="Enable smart file renaming")

class AppConfig(BaseModel):
    """Main application configuration model."""
    llm_config: LLMConfig = Field(default_factory=LLMConfig, description="LLM configuration")
    max_file_size_mb: int = Field(default=1, ge=1, le=100, description="Maximum file size in MB")
    backup_enabled: bool = Field(default=False, description="Enable backup creation")
    date_organization_enabled: bool = Field(default=False, description="Enable date-based organization")
    remove_empty_folders: bool = Field(default=True, description="Remove empty folders after organization")
    language: str = Field(default="english", description="UI language")
    parent_folders: Dict[str, List[str]] = Field(default_factory=dict, description="Language-specific folder names")
    supported_extensions: Dict[str, List[str]] = Field(default_factory=dict, description="Supported file extensions by category")
    organization_rules: OrganizationRules = Field(default_factory=OrganizationRules, description="Organization rules")
    category_names: Optional[Dict[str, Dict[str, Dict[str, str]]]] = Field(default=None, description="Localized category names")
    batch_size: int = Field(default=50, ge=1, le=1000, description="Batch processing size")
    
    @validator('language')
    def validate_language(cls, v: str) -> str:
        allowed_languages = ['english', 'korean']
        if v not in allowed_languages:
            raise ValueError(f'Language must be one of {allowed_languages}')
        return v

class ConfigManager:
    _instance: Optional['ConfigManager'] = None
    _observers: List[Any] = []
    
    config_path: str
    config: Dict[str, Any]
    _validated_config: Optional[AppConfig]
    logger: logging.Logger

    def __new__(cls, config_path: str = "config.json") -> 'ConfigManager':
        if cls._instance is None:
            cls._instance = super(ConfigManager, cls).__new__(cls)
            cls._instance.config_path = config_path
            cls._instance._validated_config = None
            cls._instance._setup_logging()
            cls._instance.config = cls._instance._load_config()
        else:
            # Update config path if different and reload config
            if cls._instance.config_path != config_path:
                cls._instance.config_path = config_path
                cls._instance.config = cls._instance._load_config()
        return cls._instance

    def __init__(self, config_path: str = "config.json") -> None:
        # __new__ handles initialization
        pass

    def _setup_logging(self) -> None:
        """Setup logging for configuration management."""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        self.logger = logging.getLogger(__name__)

    def _load_config(self) -> Dict[str, Any]:
        """Load configuration from file or create default"""
        try:
            with open(self.config_path, 'r', encoding='utf-8') as f:
                config = json.load(f)
                self.logger.info(f"Configuration loaded from {self.config_path}")
                return config
        except FileNotFoundError:
            self.logger.warning(f"Configuration file not found: {self.config_path}. Creating default configuration.")
            return self._create_default_config()
        except json.JSONDecodeError as e:
            self.logger.error(f"Invalid JSON in configuration file: {e}")
            raise ValueError(f"Configuration file contains invalid JSON: {e}")

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

    def validate_config(self) -> AppConfig:
        """Validate configuration using Pydantic model."""
        try:
            if self._validated_config is None:
                self._validated_config = AppConfig(**self.config)
                self.logger.info("Configuration validation successful")
            return self._validated_config
        except Exception as e:
            self.logger.error(f"Configuration validation failed: {e}")
            raise ValueError(f"Invalid configuration: {e}")

    def save_config(self, config: Optional[Dict[str, Any]] = None) -> None:
        """Save configuration to file"""
        if config is not None:
            self.config = config
            
        try:
            # Validate before saving
            self._validated_config = None  # Reset validation cache
            self.validate_config()
            
            with open(self.config_path, 'w', encoding='utf-8') as f:
                json.dump(self.config, f, indent=4)
                
            self.logger.info(f"Configuration saved to {self.config_path}")
            
            # Reload config to ensure all instances have the latest version
            self.config = self._load_config()
            self.notify_observers()  # Notify observers when config is saved
        except Exception as e:
            self.logger.error(f"Failed to save configuration: {e}")
            raise

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

    def add_observer(self, observer: Any) -> None:
        """Add an observer that will be notified of config changes"""
        if observer not in self._observers:
            self._observers.append(observer)

    def remove_observer(self, observer: Any) -> None:
        """Remove an observer"""
        if observer in self._observers:
            self._observers.remove(observer)

    def notify_observers(self) -> None:
        """Notify all observers of config changes"""
        for observer in self._observers:
            if hasattr(observer, 'on_settings_changed'):
                try:
                    observer.on_settings_changed()
                except Exception as e:
                    self.logger.error(f"Error notifying observer {observer}: {e}")
