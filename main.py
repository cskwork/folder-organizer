import customtkinter as ctk
import tkinter as tk
from tkinter import filedialog, messagebox
import os
import json
from datetime import datetime
import shutil
from pathlib import Path
import requests
from file_analyzer import FileAnalyzer
from file_organizer import FileOrganizer
from config_manager import ConfigManager
from settings_dialog import SettingsDialog
from CTkMessagebox import CTkMessagebox

class FileOrganizerGUI(ctk.CTk):
    def __init__(self):
        super().__init__()

        # Initialize configuration
        self.config_manager = ConfigManager()
        
        # Initialize components
        self.file_analyzer = FileAnalyzer(
            model=self.config_manager.get_setting("default_model"))
        self.file_organizer = FileOrganizer(config_manager=self.config_manager)
        self.analysis_results = None  # Store analysis results
        
        # Configure window
        self.title("Intelligent File Organizer")
        self.geometry("800x600")
        
        # Configure grid
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)
        
        # Create main frame
        self.main_frame = ctk.CTkFrame(self)
        self.main_frame.grid(row=0, column=0, padx=20, pady=20, sticky="nsew")
        self.main_frame.grid_columnconfigure(0, weight=1)
        
        # Source directory selection
        self.source_frame = ctk.CTkFrame(self.main_frame)
        self.source_frame.grid(row=0, column=0, padx=10, pady=5, sticky="ew")
        
        self.source_label = ctk.CTkLabel(self.source_frame, text="Source Directory:")
        self.source_label.grid(row=0, column=0, padx=5, pady=5)
        
        self.source_entry = ctk.CTkEntry(self.source_frame, width=400)
        self.source_entry.grid(row=0, column=1, padx=5, pady=5)
        
        self.source_button = ctk.CTkButton(self.source_frame, text="Browse",
                                         command=self.browse_source)
        self.source_button.grid(row=0, column=2, padx=5, pady=5)
        
        # Organization options
        self.options_frame = ctk.CTkFrame(self.main_frame)
        self.options_frame.grid(row=1, column=0, padx=10, pady=5, sticky="ew")
        
        rules = self.config_manager.get_organization_rules()
        
        self.content_analysis_var = tk.BooleanVar(value=rules.get("use_content_analysis", True))
        self.content_checkbox = ctk.CTkCheckBox(self.options_frame, text="Content Analysis",
                                              variable=self.content_analysis_var)
        self.content_checkbox.grid(row=0, column=0, padx=5, pady=5)
        
        self.file_type_var = tk.BooleanVar(value=rules.get("use_file_type", True))
        self.file_type_checkbox = ctk.CTkCheckBox(self.options_frame, text="File Type Organization",
                                                 variable=self.file_type_var)
        self.file_type_checkbox.grid(row=0, column=1, padx=5, pady=5)
        
        self.date_var = tk.BooleanVar(value=rules.get("use_date", True))
        self.date_checkbox = ctk.CTkCheckBox(self.options_frame, text="Date Organization",
                                           variable=self.date_var)
        self.date_checkbox.grid(row=0, column=2, padx=5, pady=5)
        
        # Progress frame
        self.progress_frame = ctk.CTkFrame(self.main_frame)
        self.progress_frame.grid(row=2, column=0, padx=10, pady=5, sticky="ew")
        
        self.progress_bar = ctk.CTkProgressBar(self.progress_frame)
        self.progress_bar.grid(row=0, column=0, padx=5, pady=5, sticky="ew")
        self.progress_bar.set(0)
        
        self.status_label = ctk.CTkLabel(self.progress_frame, text="Ready")
        self.status_label.grid(row=1, column=0, padx=5, pady=5)
        
        # Action buttons
        self.button_frame = ctk.CTkFrame(self.main_frame)
        self.button_frame.grid(row=3, column=0, padx=10, pady=5, sticky="ew")
        
        self.analyze_button = ctk.CTkButton(self.button_frame, text="Analyze",
                                          command=self.analyze_files)
        self.analyze_button.grid(row=0, column=0, padx=5, pady=5)
        
        self.organize_button = ctk.CTkButton(self.button_frame, text="Organize",
                                           command=self.organize_files)
        self.organize_button.grid(row=0, column=1, padx=5, pady=5)
        
        self.settings_button = ctk.CTkButton(self.button_frame, text="Settings",
                                           command=self.show_settings)
        self.settings_button.grid(row=0, column=2, padx=5, pady=5)
        
        self.stop_button = ctk.CTkButton(self.button_frame, text="Stop",
                                        command=self.stop_processing)
        self.stop_button.grid(row=0, column=3, padx=5, pady=5)

    def browse_source(self):
        directory = filedialog.askdirectory()
        if directory:
            self.source_entry.delete(0, tk.END)
            self.source_entry.insert(0, directory)

    def show_settings(self):
        dialog = SettingsDialog(self, self.config_manager)
        self.wait_window(dialog)
        
        if dialog.result:
            # Reload components with new settings
            self.file_analyzer = FileAnalyzer(
                model=self.config_manager.get_setting("default_model"))
            
            # Update checkboxes
            rules = self.config_manager.get_organization_rules()
            self.content_analysis_var.set(rules.get("use_content_analysis", True))
            self.file_type_var.set(rules.get("use_file_type", True))
            self.date_var.set(rules.get("use_date", True))

    def analyze_files(self):
        source_dir = self.source_entry.get()
        if not source_dir or not os.path.exists(source_dir):
            CTkMessagebox(title="Error", message="Please select a valid source directory",
                         icon="cancel")
            return
            
        try:
            self.status_label.configure(text="Analyzing files...")
            self.progress_bar.set(0)
            
            # Start analysis in a separate thread
            self.analysis_results = self.file_analyzer.analyze_directory(
                source_dir,
                use_content=self.content_analysis_var.get(),
                use_type=self.file_type_var.get(),
                use_date=self.date_var.get()
            )
            
            self.status_label.configure(text="Analysis complete")
            self.progress_bar.set(1)
            
            # Show summary
            CTkMessagebox(title="Analysis Complete",
                         message=f"Found {len(self.analysis_results)} files to organize",
                         icon="info")
            
        except Exception as e:
            self.analysis_results = None
            CTkMessagebox(title="Error", message=f"Analysis failed: {str(e)}",
                         icon="cancel")

    def organize_files(self):
        source_dir = self.source_entry.get()
        if not source_dir or not os.path.exists(source_dir):
            CTkMessagebox(title="Error", message="Please select a valid source directory",
                         icon="cancel")
            return
            
        if self.analysis_results is None:
            CTkMessagebox(title="Error", message="Please analyze files first",
                         icon="cancel")
            return
            
        try:
            if self.config_manager.get_setting("backup_enabled", True):
                self.status_label.configure(text="Creating backup...")
                self.progress_bar.set(0)
                
                # Create backup
                backup_path = self.file_organizer.create_backup(source_dir)
            
            self.status_label.configure(text="Organizing files...")
            
            # Start organization in a separate thread
            self.file_organizer.organize_directory(
                source_dir,
                self.analysis_results,
                use_content=self.content_analysis_var.get(),
                use_type=self.file_type_var.get(),
                use_date=self.date_var.get()
            )
            
            self.status_label.configure(text="Organization complete")
            self.progress_bar.set(1)
            
            msg = "Files organized successfully"
            if self.config_manager.get_setting("backup_enabled", True):
                msg += f"\nBackup created at: {backup_path}"
                
            CTkMessagebox(title="Success", message=msg, icon="info")
            
        except Exception as e:
            CTkMessagebox(title="Error", message=f"Organization failed: {str(e)}",
                         icon="cancel")

    def stop_processing(self):
        self.file_analyzer.stop()
        self.file_organizer.stop()
        self.status_label.configure(text="Processing stopped")

if __name__ == "__main__":
    app = FileOrganizerGUI()
    app.mainloop()
