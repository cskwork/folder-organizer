import customtkinter as ctk
import tkinter as tk
from tkinter import filedialog
import os
from datetime import datetime
from pathlib import Path
from file_analyzer import FileAnalyzer
from file_organizer import FileOrganizer
from config_manager import ConfigManager
from settings_dialog import SettingsDialog
from CTkMessagebox import CTkMessagebox
import threading

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
        
        self.remove_empty_var = tk.BooleanVar(value=self.config_manager.get_setting("remove_empty_folders", True))
        self.remove_empty_checkbox = ctk.CTkCheckBox(self.options_frame, text="Remove Empty Folders",
                                                    variable=self.remove_empty_var)
        self.remove_empty_checkbox.grid(row=0, column=3, padx=5, pady=5)
        
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
        """Show settings dialog"""
        settings = SettingsDialog(self, self.config_manager)
        settings.wait_window()
        
        # Update checkboxes based on new settings
        rules = self.config_manager.get_organization_rules()
        self.content_analysis_var.set(rules.get("use_content_analysis", True))
        self.file_type_var.set(rules.get("use_file_type", True))
        self.remove_empty_var.set(self.config_manager.get_setting("remove_empty_folders", True))

    def analyze_files(self):
        """Analyze files in the selected directory"""
        if not self.source_entry.get():
            CTkMessagebox(title="Error", message="Please select a source directory", icon="warning")
            return

        # Disable buttons during analysis
        self.analyze_button.configure(state="disabled")
        self.organize_button.configure(state="disabled")
        self.settings_button.configure(state="disabled")

        try:
            # Reset progress
            self.progress_bar.set(0)
            self.status_label.configure(text="Starting analysis...")
            
            # Get analysis options
            use_content = self.content_analysis_var.get()
            use_type = self.file_type_var.get()
            use_date = self.date_var.get()
            
            def analyze_thread():
                try:
                    self.analysis_results = self.file_analyzer.analyze_directory(
                        self.source_entry.get(),
                        use_content=use_content,
                        use_type=use_type,
                        use_date=use_date,
                        progress_callback=self.update_progress
                    )
                    
                    # Enable buttons and update status on completion
                    self.after(0, lambda: [
                        self.analyze_button.configure(state="normal"),
                        self.organize_button.configure(state="normal"),
                        self.settings_button.configure(state="normal"),
                        self.status_label.configure(text="Analysis complete"),
                        CTkMessagebox(title="Success", message="File analysis completed successfully", icon="info")
                    ])
                except Exception as e:
                    # Handle errors
                    self.after(0, lambda: [
                        self.analyze_button.configure(state="normal"),
                        self.organize_button.configure(state="normal"),
                        self.settings_button.configure(state="normal"),
                        self.status_label.configure(text="Analysis failed"),
                        CTkMessagebox(title="Error", message=f"Analysis failed: {str(e)}", icon="error")
                    ])
            
            # Start analysis in a separate thread
            threading.Thread(target=analyze_thread, daemon=True).start()
            
        except Exception as e:
            # Re-enable buttons on error
            self.analyze_button.configure(state="normal")
            self.organize_button.configure(state="normal")
            self.settings_button.configure(state="normal")
            CTkMessagebox(title="Error", message=f"Failed to start analysis: {str(e)}", icon="error")

    def organize_files(self):
        if not self.analysis_results:
            CTkMessagebox(title="Error", message="Please analyze files first", icon="warning")
            return

        source_dir = self.source_entry.get()
        if not source_dir or not os.path.exists(source_dir):
            CTkMessagebox(title="Error", message="Please select a valid source directory",
                         icon="warning")
            return

        # Disable buttons during organization
        self.analyze_button.configure(state="disabled")
        self.organize_button.configure(state="disabled")
        self.settings_button.configure(state="disabled")

        try:
            # Reset progress
            self.progress_bar.set(0)
            self.status_label.configure(text="Starting organization...")

            def organize_thread():
                try:
                    self.file_organizer.organize_files(
                        source_dir,
                        self.analysis_results,
                        remove_empty=self.remove_empty_var.get(),
                        progress_callback=self.update_progress
                    )
                    
                    # Enable buttons and update status on completion
                    self.after(0, lambda: [
                        self.analyze_button.configure(state="normal"),
                        self.organize_button.configure(state="normal"),
                        self.settings_button.configure(state="normal"),
                        self.status_label.configure(text="Organization complete"),
                        CTkMessagebox(title="Success", message="File organization completed successfully", icon="info")
                    ])
                except Exception as e:
                    # Handle errors
                    self.after(0, lambda: [
                        self.analyze_button.configure(state="normal"),
                        self.organize_button.configure(state="normal"),
                        self.settings_button.configure(state="normal"),
                        self.status_label.configure(text="Organization failed"),
                        CTkMessagebox(title="Error", message=f"Organization failed: {str(e)}", icon="error")
                    ])
            
            # Start organization in a separate thread
            threading.Thread(target=organize_thread, daemon=True).start()
            
        except Exception as e:
            # Re-enable buttons on error
            self.analyze_button.configure(state="normal")
            self.organize_button.configure(state="normal")
            self.settings_button.configure(state="normal")
            CTkMessagebox(title="Error", message=f"Failed to start organization: {str(e)}", icon="error")

    def update_progress(self, progress: float, status: str):
        """Update progress bar and status label"""
        self.progress_bar.set(progress / 100)  # Progress bar expects value between 0 and 1
        self.status_label.configure(text=status)
        self.update()  # Force GUI update

    def stop_processing(self):
        self.file_analyzer.stop()
        self.file_organizer.stop()
        self.status_label.configure(text="Processing stopped")

if __name__ == "__main__":
    app = FileOrganizerGUI()
    app.mainloop()
