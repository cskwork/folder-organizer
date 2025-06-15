import customtkinter as ctk
from typing import Dict, Any
from config_manager import ConfigManager

class SettingsDialog(ctk.CTkToplevel):
    def __init__(self, parent, config_manager: ConfigManager):
        super().__init__(parent)
        
        self.config_manager = config_manager
        self.result = None
        
        # Configure window
        self.title("Settings")
        self.geometry("600x800")
        self.protocol("WM_DELETE_WINDOW", self.on_closing)
        
        # Create main frame
        self.main_frame = ctk.CTkScrollableFrame(self)
        self.main_frame.pack(fill="both", expand=True, padx=20, pady=20)
        
        # Language settings
        self.language_frame = self._create_section_frame("Language Settings")
        
        self.language_label = ctk.CTkLabel(self.language_frame, text="Directory Names Language:")
        self.language_label.pack(side="left", padx=5)
        
        self.language_var = ctk.StringVar(value=config_manager.get_setting("language", "english"))
        self.language_menu = ctk.CTkOptionMenu(
            self.language_frame,
            values=["english", "korean"],
            variable=self.language_var
        )
        self.language_menu.pack(side="left", padx=5)
        
        # File size limit
        self.size_frame = self._create_section_frame("File Size Limit")
        
        self.size_var = ctk.StringVar(value=str(config_manager.get_setting("max_file_size_mb")))
        self.size_entry = ctk.CTkEntry(self.size_frame, textvariable=self.size_var)
        self.size_entry.pack(fill="x", padx=5, pady=5)
        
        # Organization rules
        self.rules_frame = self._create_section_frame("Organization Rules")
        
        rules = config_manager.get_organization_rules()

        # Smart Rename
        self.smart_rename_var = ctk.BooleanVar(value=rules.get("smart_rename_enabled", True))
        self.smart_rename_check = ctk.CTkCheckBox(self.rules_frame, text="Use Smart Rename",
                                                variable=self.smart_rename_var)
        self.smart_rename_check.pack(fill="x", padx=5, pady=5)

        self.content_var = ctk.BooleanVar(value=rules.get("use_content_analysis", True))
        self.content_check = ctk.CTkCheckBox(self.rules_frame, text="Use Content Analysis",
                                           variable=self.content_var)
        self.content_check.pack(fill="x", padx=5, pady=5)
        
        self.type_var = ctk.BooleanVar(value=rules.get("use_file_type", True))
        self.type_check = ctk.CTkCheckBox(self.rules_frame, text="Use File Type",
                                        variable=self.type_var)
        self.type_check.pack(fill="x", padx=5, pady=5)
        
        self.date_var = ctk.BooleanVar(value=rules.get("use_date", True))
        self.date_check = ctk.CTkCheckBox(self.rules_frame, text="Use Date",
                                        variable=self.date_var)
        self.date_check.pack(fill="x", padx=5, pady=5)
        
        # Date format
        self.date_format_frame = ctk.CTkFrame(self.rules_frame)
        self.date_format_frame.pack(fill="x", padx=5, pady=5)
        
        self.date_format_label = ctk.CTkLabel(self.date_format_frame, text="Date Format:")
        self.date_format_label.pack(side="left", padx=5)
        
        self.date_format_var = ctk.StringVar(value=rules.get("date_format", "%Y-%m"))
        self.date_format_entry = ctk.CTkEntry(self.date_format_frame,
                                            textvariable=self.date_format_var)
        self.date_format_entry.pack(side="left", fill="x", expand=True, padx=5)
        
        # Confidence score
        self.confidence_frame = ctk.CTkFrame(self.rules_frame)
        self.confidence_frame.pack(fill="x", padx=5, pady=5)
        
        self.confidence_label = ctk.CTkLabel(self.confidence_frame,
                                           text="Min Confidence Score:")
        self.confidence_label.pack(side="left", padx=5)
        
        self.confidence_var = ctk.StringVar(
            value=str(rules.get("min_confidence_score", 0.7)))
        self.confidence_entry = ctk.CTkEntry(self.confidence_frame,
                                           textvariable=self.confidence_var)
        self.confidence_entry.pack(side="left", fill="x", expand=True, padx=5)
        
        # Backup setting
        self.backup_frame = ctk.CTkFrame(self.rules_frame)
        self.backup_frame.pack(fill="x", padx=5, pady=5)
        
        self.backup_var = ctk.BooleanVar(value=config_manager.get_setting("backup_enabled", False))
        self.backup_checkbox = ctk.CTkCheckBox(self.backup_frame, text="Create Backup",
                                             variable=self.backup_var)
        self.backup_checkbox.pack(side="left", padx=5)
        
        # Empty folder removal setting
        self.empty_folder_frame = ctk.CTkFrame(self.rules_frame)
        self.empty_folder_frame.pack(fill="x", padx=5, pady=5)
        
        self.empty_folder_var = ctk.BooleanVar(value=config_manager.get_setting("remove_empty_folders", True))
        self.empty_folder_checkbox = ctk.CTkCheckBox(self.empty_folder_frame, text="Remove Empty Folders",
                                                   variable=self.empty_folder_var)
        self.empty_folder_checkbox.pack(side="left", padx=5)
        
        # LLM Provider settings
        self.llm_frame = self._create_section_frame("LLM Provider Settings")
        
        # Provider selection
        self.provider_label = ctk.CTkLabel(self.llm_frame, text="Default Provider:")
        self.provider_label.pack(anchor="w", padx=5, pady=2)
        
        llm_config = config_manager.get_setting("llm_config", {})
        self.provider_var = ctk.StringVar(value=llm_config.get("default_provider", "ollama"))
        self.provider_menu = ctk.CTkOptionMenu(
            self.llm_frame,
            values=["ollama", "openrouter"],
            variable=self.provider_var,
            command=self.on_provider_change
        )
        self.provider_menu.pack(anchor="w", padx=5, pady=2)
        
        # Model selection (common for both providers)
        self.model_label = ctk.CTkLabel(self.llm_frame, text="Model:")
        self.model_label.pack(anchor="w", padx=5, pady=2)
        
        # Default models for each provider
        self.provider_models = {
            "openrouter": ["google/gemini-pro", "anthropic/claude-3-opus", "anthropic/claude-3-sonnet", "mistralai/mistral-large"],
            "ollama": ["llama2", "codellama", "mistral", "mixtral"]
        }
        
        self.model_var = ctk.StringVar()
        self.model_menu = ctk.CTkOptionMenu(
            self.llm_frame,
            values=self.provider_models["ollama"],  # Default to ollama models
            variable=self.model_var
        )
        self.model_menu.pack(anchor="w", padx=5, pady=2)
        
        # Provider specific settings
        self.provider_settings_frame = ctk.CTkFrame(self.llm_frame)
        self.provider_settings_frame.pack(fill="x", padx=5, pady=5)
        
        # OpenRouter settings
        self.openrouter_frame = ctk.CTkFrame(self.provider_settings_frame)
        openrouter_config = llm_config.get("providers", {}).get("openrouter", {})
        
        self.api_key_label = ctk.CTkLabel(self.openrouter_frame, text="API Key:")
        self.api_key_label.pack(anchor="w", padx=5, pady=2)
        
        self.api_key_var = ctk.StringVar(value=openrouter_config.get("api_key", ""))
        self.api_key_entry = ctk.CTkEntry(self.openrouter_frame, textvariable=self.api_key_var, width=300)
        self.api_key_entry.pack(anchor="w", padx=5, pady=2)
        
        # Ollama settings
        self.ollama_frame = ctk.CTkFrame(self.provider_settings_frame)
        ollama_config = llm_config.get("providers", {}).get("ollama", {})
        
        self.ollama_url_label = ctk.CTkLabel(self.ollama_frame, text="URL:")
        self.ollama_url_label.pack(anchor="w", padx=5, pady=2)
        
        self.ollama_url_var = ctk.StringVar(value=ollama_config.get("url", "http://localhost:11434/api/generate"))
        self.ollama_url_entry = ctk.CTkEntry(self.ollama_frame, textvariable=self.ollama_url_var, width=300)
        self.ollama_url_entry.pack(anchor="w", padx=5, pady=2)
        
        # Test connection button
        self.test_button = ctk.CTkButton(self.llm_frame, text="Test Connection", command=self.test_llm_connection)
        self.test_button.pack(anchor="w", padx=5, pady=10)
        
        # Status label
        self.status_label = ctk.CTkLabel(self.llm_frame, text="")
        self.status_label.pack(anchor="w", padx=5, pady=5)
        
        # Show initial provider frame
        self.on_provider_change(self.provider_var.get())
        
        # Backup settings
        self.backup_settings_frame = self._create_section_frame("Backup Settings")
        
        self.backup_enabled_var = ctk.BooleanVar(
            value=config_manager.get_setting("backup_enabled", True))
        self.backup_enabled_check = ctk.CTkCheckBox(self.backup_settings_frame, text="Enable Backup",
                                          variable=self.backup_enabled_var)
        self.backup_enabled_check.pack(fill="x", padx=5, pady=5)
        
        # Add Save and Cancel buttons
        self.button_frame = ctk.CTkFrame(self.main_frame)
        self.button_frame.pack(fill="x", padx=5, pady=10)

        self.save_button = ctk.CTkButton(self.button_frame, text="Save", command=self.save_settings)
        self.save_button.pack(side="right", padx=5)

        self.cancel_button = ctk.CTkButton(self.button_frame, text="Cancel", command=self.on_closing)
        self.cancel_button.pack(side="right", padx=5)

    def _create_section_frame(self, title: str) -> ctk.CTkFrame:
        """Create a section frame with title"""
        frame = ctk.CTkFrame(self.main_frame)
        frame.pack(fill="x", padx=5, pady=5)
        
        label = ctk.CTkLabel(frame, text=title)
        label.pack(padx=5, pady=5)
        
        return frame

    def on_provider_change(self, provider: str):
        """Handle provider change in the UI."""
        # Hide all provider frames
        self.openrouter_frame.pack_forget()
        self.ollama_frame.pack_forget()
        
        # Update model menu with provider-specific models
        self.model_menu.configure(values=self.provider_models[provider])
        self.model_var.set(self.provider_models[provider][0])  # Set first model as default
        
        # Show selected provider frame
        if provider == "openrouter":
            self.openrouter_frame.pack(fill="x", padx=5, pady=5)
        elif provider == "ollama":
            self.ollama_frame.pack(fill="x", padx=5, pady=5)
            
    def test_llm_connection(self):
        """Test the LLM provider connection."""
        provider = self.provider_var.get()
        
        # Update config with current values
        llm_config = {
            "default_provider": provider,
            "providers": {
                "openrouter": {
                    "url": "https://openrouter.ai/api/v1/chat/completions",
                    "api_key": self.api_key_var.get(),
                    "default_model": self.model_var.get()
                },
                "ollama": {
                    "url": self.ollama_url_var.get(),
                    "default_model": self.model_var.get()
                }
            }
        }
        
        # Create temporary ContentAnalyzer with current settings
        from content_analyzer import ContentAnalyzer
        analyzer = ContentAnalyzer(None)
        analyzer.provider = provider
        analyzer.providers_config = llm_config["providers"]
        
        # Test the connection
        self.status_label.configure(text="Testing connection...")
        self.update()
        
        result = analyzer.test_llm_provider(provider)
        
        if result["success"]:
            self.status_label.configure(text=f"✓ {result['message']}", text_color="green")
        else:
            self.status_label.configure(text=f"✗ {result['message']}", text_color="red")

    def save_settings(self):
        """Save all settings to config manager"""
        # Update organization rules
        rules = {
            "smart_rename_enabled": self.smart_rename_var.get(),
            "use_content_analysis": self.content_var.get(),
            "use_file_type": self.type_var.get(),
            "use_date": self.date_var.get(),
            "date_format": self.date_format_var.get(),
            "min_confidence_score": float(self.confidence_var.get())
        }

        # Update main settings
        self.config_manager.set_setting("language", self.language_var.get())
        self.config_manager.set_setting("max_file_size_mb", float(self.size_var.get()))
        self.config_manager.set_setting("organization_rules", rules)
        
        # Update LLM config
        llm_config = {
            "default_provider": self.provider_var.get(),
            "providers": {
                "openrouter": {
                    "url": "https://openrouter.ai/api/v1/chat/completions",
                    "api_key": self.api_key_var.get(),
                    "default_model": self.model_var.get()
                },
                "ollama": {
                    "url": self.ollama_url_var.get(),
                    "default_model": self.model_var.get()
                }
            }
        }
        self.config_manager.set_setting("llm_config", llm_config)
        
        self.destroy()

    def on_closing(self):
        """Handle window closing"""
        self.destroy()