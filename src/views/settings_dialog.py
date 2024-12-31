import customtkinter as ctk
from pathlib import Path
from typing import Dict, Any, List, Optional
from tkinter import filedialog
from ..ui.base_component import BaseComponent

class SettingsDialog(ctk.CTkToplevel, BaseComponent):
    """Modern settings dialog"""
    
    def __init__(self, parent, settings_manager=None, theme_manager=None):
        super().__init__(parent)
        BaseComponent.__init__(self, theme_manager)
        
        self.settings_manager = settings_manager
        self.parent = parent
        self._setup_dialog()
        self._create_widgets()
        
        # Make dialog modal
        self.transient(parent)
        self.grab_set()
    
    def _setup_dialog(self):
        """Configure dialog window"""
        self.title("Settings")
        self.geometry("800x600")
        
        # Center dialog on parent
        if self.parent:
            x = self.parent.winfo_x() + (self.parent.winfo_width() - 800) // 2
            y = self.parent.winfo_y() + (self.parent.winfo_height() - 600) // 2
            self.geometry(f"+{x}+{y}")
        
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)
    
    def _create_widgets(self):
        """Create dialog widgets"""
        # Title
        title = self.create_label(
            self,
            text="Settings",
            font=("Helvetica", 20, "bold")
        )
        title.grid(row=0, column=0, padx=20, pady=20, sticky="w")
        
        # Create notebook for settings categories
        notebook = ctk.CTkTabview(
            self,
            fg_color=self._current_theme.get("card"),
            segmented_button_fg_color=self._current_theme.get("primary"),
            segmented_button_selected_color=self._current_theme.get("accent")
        )
        notebook.grid(row=1, column=0, padx=20, pady=(0, 20), sticky="nsew")
        
        # Add tabs
        self._add_appearance_tab(notebook)
        self._add_analyzer_tab(notebook)
        self._add_organizer_tab(notebook)
        self._add_general_tab(notebook)
        
        # Action buttons
        btn_frame = self.create_frame(self, corner_radius=0, border_width=0)
        btn_frame.grid(row=2, column=0, padx=20, pady=(0, 20))
        
        save_btn = self.create_button(
            btn_frame,
            text="Save",
            command=self._save_settings
        )
        save_btn.pack(side="left", padx=5)
        
        cancel_btn = self.create_button(
            btn_frame,
            text="Cancel",
            command=self.destroy,
            style="secondary"
        )
        cancel_btn.pack(side="left", padx=5)
    
    def _add_appearance_tab(self, notebook: ctk.CTkTabview):
        """Add appearance settings tab"""
        tab = notebook.add("Appearance")
        tab.grid_columnconfigure(1, weight=1)
        
        # Theme selection
        row = 0
        self.create_label(tab, text="Theme:").grid(row=row, column=0, padx=10, pady=10, sticky="w")
        theme_var = ctk.StringVar(value=self.settings_manager.get("appearance.theme"))
        theme_menu = ctk.CTkOptionMenu(
            tab,
            values=["light", "dark"],
            variable=theme_var,
            command=lambda _: self.settings_manager.set("appearance.theme", theme_var.get())
        )
        theme_menu.grid(row=row, column=1, padx=10, pady=10, sticky="w")
        
        # Font size
        row += 1
        self.create_label(tab, text="Font Size:").grid(row=row, column=0, padx=10, pady=10, sticky="w")
        font_var = ctk.StringVar(value=str(self.settings_manager.get("appearance.font_size")))
        font_menu = ctk.CTkOptionMenu(
            tab,
            values=["10", "12", "14", "16", "18"],
            variable=font_var,
            command=lambda _: self.settings_manager.set("appearance.font_size", int(font_var.get()))
        )
        font_menu.grid(row=row, column=1, padx=10, pady=10, sticky="w")
        
        # Accent color
        row += 1
        self.create_label(tab, text="Accent Color:").grid(row=row, column=0, padx=10, pady=10, sticky="w")
        color_var = ctk.StringVar(value=self.settings_manager.get("appearance.accent_color"))
        color_entry = self.create_entry(tab, textvariable=color_var)
        color_entry.grid(row=row, column=1, padx=10, pady=10, sticky="w")
        color_apply = self.create_button(
            tab,
            text="Apply",
            command=lambda: self.settings_manager.set("appearance.accent_color", color_var.get())
        )
        color_apply.grid(row=row, column=2, padx=10, pady=10, sticky="w")
        
        self._appearance_vars = {
            "theme": theme_var,
            "font_size": font_var,
            "accent_color": color_var
        }
    
    def _add_analyzer_tab(self, notebook: ctk.CTkTabview):
        """Add file analyzer settings tab"""
        tab = notebook.add("File Analyzer")
        tab.grid_columnconfigure(1, weight=1)
        
        # Sample size
        row = 0
        self.create_label(tab, text="Sample Size (bytes):").grid(row=row, column=0, padx=10, pady=10, sticky="w")
        sample_var = ctk.StringVar(value=str(self.settings_manager.get("file_analyzer.sample_size")))
        sample_entry = self.create_entry(tab, textvariable=sample_var)
        sample_entry.grid(row=row, column=1, padx=10, pady=10, sticky="w")
        
        # Confidence threshold
        row += 1
        self.create_label(tab, text="Confidence Threshold:").grid(row=row, column=0, padx=10, pady=10, sticky="w")
        conf_var = ctk.StringVar(value=str(self.settings_manager.get("file_analyzer.confidence_threshold")))
        conf_entry = self.create_entry(tab, textvariable=conf_var)
        conf_entry.grid(row=row, column=1, padx=10, pady=10, sticky="w")
        
        # Supported languages
        row += 1
        self.create_label(tab, text="Supported Languages:").grid(row=row, column=0, padx=10, pady=10, sticky="w")
        langs_var = ctk.StringVar(value=",".join(self.settings_manager.get("file_analyzer.supported_languages")))
        langs_entry = self.create_entry(tab, textvariable=langs_var)
        langs_entry.grid(row=row, column=1, padx=10, pady=10, sticky="w")
        langs_apply = self.create_button(
            tab,
            text="Apply",
            command=lambda: self.settings_manager.set("file_analyzer.supported_languages", langs_var.get().split(","))
        )
        langs_apply.grid(row=row, column=2, padx=10, pady=10, sticky="w")
        
        self._analyzer_vars = {
            "sample_size": sample_var,
            "confidence_threshold": conf_var,
            "supported_languages": langs_var
        }
    
    def _add_organizer_tab(self, notebook: ctk.CTkTabview):
        """Add file organizer settings tab"""
        tab = notebook.add("File Organizer")
        tab.grid_columnconfigure(1, weight=1)
        
        # Date format
        row = 0
        self.create_label(tab, text="Date Format:").grid(row=row, column=0, padx=10, pady=10, sticky="w")
        date_var = ctk.StringVar(value=self.settings_manager.get("file_organizer.by_date.format"))
        date_entry = self.create_entry(tab, textvariable=date_var)
        date_entry.grid(row=row, column=1, padx=10, pady=10, sticky="w")
        date_apply = self.create_button(
            tab,
            text="Apply",
            command=lambda: self.settings_manager.set("file_organizer.by_date.format", date_var.get())
        )
        date_apply.grid(row=row, column=2, padx=10, pady=10, sticky="w")
        
        # Use creation date
        row += 1
        create_var = ctk.BooleanVar(value=self.settings_manager.get("file_organizer.by_date.use_creation_date"))
        create_cb = ctk.CTkCheckBox(
            tab,
            text="Use Creation Date",
            variable=create_var,
            fg_color=self._current_theme.get("primary"),
            command=lambda: self.settings_manager.set("file_organizer.by_date.use_creation_date", create_var.get())
        )
        create_cb.grid(row=row, column=0, columnspan=2, padx=10, pady=10, sticky="w")
        
        # Language organization
        row += 1
        lang_var = ctk.BooleanVar(value=self.settings_manager.get("file_organizer.by_language.enabled"))
        lang_cb = ctk.CTkCheckBox(
            tab,
            text="Enable Language Organization",
            variable=lang_var,
            fg_color=self._current_theme.get("primary"),
            command=lambda: self.settings_manager.set("file_organizer.by_language.enabled", lang_var.get())
        )
        lang_cb.grid(row=row, column=0, columnspan=2, padx=10, pady=10, sticky="w")
        
        self._organizer_vars = {
            "date_format": date_var,
            "use_creation_date": create_var,
            "language_enabled": lang_var
        }
    
    def _add_general_tab(self, notebook: ctk.CTkTabview):
        """Add general settings tab"""
        tab = notebook.add("General")
        tab.grid_columnconfigure(1, weight=1)
        
        # Default target directory
        row = 0
        self.create_label(tab, text="Default Target Directory:").grid(row=row, column=0, padx=10, pady=10, sticky="w")
        dir_frame = self.create_frame(tab, corner_radius=0, border_width=0)
        dir_frame.grid(row=row, column=1, padx=10, pady=10, sticky="ew")
        
        dir_var = ctk.StringVar(value=self.settings_manager.get("general.default_target_dir"))
        dir_entry = self.create_entry(dir_frame, textvariable=dir_var)
        dir_entry.pack(side="left", fill="x", expand=True, padx=(0, 10))
        
        browse_btn = self.create_button(
            dir_frame,
            text="Browse",
            command=lambda: self._browse_directory(dir_var)
        )
        browse_btn.pack(side="right")
        
        # Backup files
        row += 1
        backup_var = ctk.BooleanVar(value=self.settings_manager.get("general.backup_files"))
        backup_cb = ctk.CTkCheckBox(
            tab,
            text="Create Backups",
            variable=backup_var,
            fg_color=self._current_theme.get("primary"),
            command=lambda: self.settings_manager.set("general.backup_files", backup_var.get())
        )
        backup_cb.grid(row=row, column=0, columnspan=2, padx=10, pady=10, sticky="w")
        
        # Confirm actions
        row += 1
        confirm_var = ctk.BooleanVar(value=self.settings_manager.get("general.confirm_actions"))
        confirm_cb = ctk.CTkCheckBox(
            tab,
            text="Confirm Actions",
            variable=confirm_var,
            fg_color=self._current_theme.get("primary"),
            command=lambda: self.settings_manager.set("general.confirm_actions", confirm_var.get())
        )
        confirm_cb.grid(row=row, column=0, columnspan=2, padx=10, pady=10, sticky="w")
        
        self._general_vars = {
            "default_target_dir": dir_var,
            "backup_files": backup_var,
            "confirm_actions": confirm_var
        }
    
    def _browse_directory(self, var: ctk.StringVar):
        """Open directory selection dialog"""
        directory = filedialog.askdirectory(
            title="Select Directory",
            initialdir=var.get() or None
        )
        
        if directory:
            var.set(directory)
            self.settings_manager.set("general.default_target_dir", directory)
    
    def _save_settings(self):
        """Save settings and close dialog"""
        try:
            # Update appearance settings
            self.settings_manager.set("appearance.theme", self._appearance_vars["theme"].get())
            self.settings_manager.set("appearance.font_size", int(self._appearance_vars["font_size"].get()))
            self.settings_manager.set("appearance.accent_color", self._appearance_vars["accent_color"].get())
            
            # Update analyzer settings
            self.settings_manager.set("file_analyzer.sample_size", int(self._analyzer_vars["sample_size"].get()))
            self.settings_manager.set("file_analyzer.confidence_threshold", float(self._analyzer_vars["confidence_threshold"].get()))
            self.settings_manager.set("file_analyzer.supported_languages", self._analyzer_vars["supported_languages"].get().split(","))
            
            # Update organizer settings
            self.settings_manager.set("file_organizer.by_date.format", self._organizer_vars["date_format"].get())
            self.settings_manager.set("file_organizer.by_date.use_creation_date", self._organizer_vars["use_creation_date"].get())
            self.settings_manager.set("file_organizer.by_language.enabled", self._organizer_vars["language_enabled"].get())
            
            # Update general settings
            self.settings_manager.set("general.default_target_dir", self._general_vars["default_target_dir"].get())
            self.settings_manager.set("general.backup_files", self._general_vars["backup_files"].get())
            self.settings_manager.set("general.confirm_actions", self._general_vars["confirm_actions"].get())
            
            self.settings_manager._save_settings()
            self.destroy()
            
        except ValueError as e:
            # Show error message
            error_label = self.create_label(
                self,
                text=f"Error: {str(e)}",
                text_color="red"
            )
            error_label.grid(row=3, column=0, pady=(0, 10))
    
    def update_theme(self):
        """Update dialog appearance based on theme"""
        self.configure(fg_color=self._current_theme.get("background"))
        
        # Update all child widgets
        for child in self.winfo_children():
            if hasattr(child, "update_theme"):
                child.update_theme()
