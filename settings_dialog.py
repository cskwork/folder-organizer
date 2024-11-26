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
        
        # Model settings
        self.model_frame = self._create_section_frame("Ollama Model Settings")
        
        self.model_var = ctk.StringVar(value=config_manager.get_setting("default_model"))
        self.model_entry = ctk.CTkEntry(self.model_frame, textvariable=self.model_var)
        self.model_entry.pack(fill="x", padx=5, pady=5)
        
        # File size limit
        self.size_frame = self._create_section_frame("File Size Limit")
        
        self.size_var = ctk.StringVar(value=str(config_manager.get_setting("max_file_size_mb")))
        self.size_entry = ctk.CTkEntry(self.size_frame, textvariable=self.size_var)
        self.size_entry.pack(fill="x", padx=5, pady=5)
        
        # Organization rules
        self.rules_frame = self._create_section_frame("Organization Rules")
        
        rules = config_manager.get_organization_rules()
        
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
        
        # Backup settings
        self.backup_settings_frame = self._create_section_frame("Backup Settings")
        
        self.backup_enabled_var = ctk.BooleanVar(
            value=config_manager.get_setting("backup_enabled", True))
        self.backup_enabled_check = ctk.CTkCheckBox(self.backup_settings_frame, text="Enable Backup",
                                          variable=self.backup_enabled_var)
        self.backup_enabled_check.pack(fill="x", padx=5, pady=5)
        
        # Buttons
        self.button_frame = ctk.CTkFrame(self)
        self.button_frame.pack(fill="x", padx=20, pady=10)
        
        self.save_button = ctk.CTkButton(self.button_frame, text="Save",
                                       command=self.save_settings)
        self.save_button.pack(side="left", padx=5)
        
        self.cancel_button = ctk.CTkButton(self.button_frame, text="Cancel",
                                         command=self.cancel)
        self.cancel_button.pack(side="left", padx=5)

    def _create_section_frame(self, title: str) -> ctk.CTkFrame:
        """Create a section frame with title"""
        frame = ctk.CTkFrame(self.main_frame)
        frame.pack(fill="x", padx=5, pady=5)
        
        label = ctk.CTkLabel(frame, text=title)
        label.pack(padx=5, pady=5)
        
        return frame

    def save_settings(self) -> None:
        """Save settings and close dialog"""
        try:
            # Update configuration
            self.config_manager.set_setting("default_model", self.model_var.get())
            self.config_manager.set_setting("max_file_size_mb",
                                          float(self.size_var.get()))
            self.config_manager.set_setting("backup_enabled",
                                          self.backup_enabled_var.get())
            self.config_manager.set_setting("language",
                                          self.language_var.get())
            
            # Update organization rules
            rules = {
                "use_content_analysis": self.content_var.get(),
                "use_file_type": self.type_var.get(),
                "use_date": self.date_var.get(),
                "date_format": self.date_format_var.get(),
                "min_confidence_score": float(self.confidence_var.get()),
                "remove_empty_folders": self.empty_folder_var.get()
            }
            self.config_manager.set_setting("organization_rules", rules)
            
            self.result = True
            self.destroy()
            
        except ValueError as e:
            ctk.CTkMessagebox(title="Error",
                            message="Please enter valid numeric values for size and confidence score")

    def cancel(self) -> None:
        """Cancel and close dialog"""
        self.result = False
        self.destroy()
