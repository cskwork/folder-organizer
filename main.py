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
        self.config_manager.add_observer(self)  # Register as observer
        
        # Initialize components
        self.file_analyzer = FileAnalyzer(
            model=self.config_manager.get_setting("default_model"),
            config_manager=self.config_manager)
        self.file_organizer = FileOrganizer(config_manager=self.config_manager)
        self.analysis_results = None
        
        # Configure window
        self.title("Intelligent File Organizer")
        self.geometry("800x700")  # Increased height for new controls

        # Create menu bar
        self.menu_bar = tk.Menu(self)
        self.config(menu=self.menu_bar)

        # Create File menu
        self.file_menu = tk.Menu(self.menu_bar, tearoff=0)
        self.menu_bar.add_cascade(label="File", menu=self.file_menu)
        self.file_menu.add_command(label="Settings", command=self.show_settings)
        self.file_menu.add_separator()
        self.file_menu.add_command(label="Exit", command=self.quit)
        
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
        
        # Add preview frame
        self.preview_frame = ctk.CTkFrame(self.main_frame)
        self.preview_frame.grid(row=2, column=0, padx=10, pady=5, sticky="ew")
        
        self.preview_text = ctk.CTkTextbox(self.preview_frame, height=150)
        self.preview_text.grid(row=0, column=0, padx=5, pady=5, sticky="ew")
        
        # Stats frame
        self.stats_frame = ctk.CTkFrame(self.main_frame)
        self.stats_frame.grid(row=3, column=0, padx=10, pady=5, sticky="ew")
        
        self.stats_label = ctk.CTkLabel(self.stats_frame, text="Statistics:")
        self.stats_label.grid(row=0, column=0, padx=5, pady=5)
        
        # Progress frame
        self.progress_frame = ctk.CTkFrame(self.main_frame)
        self.progress_frame.grid(row=4, column=0, padx=10, pady=5, sticky="ew")
        
        self.progress_bar = ctk.CTkProgressBar(self.progress_frame)
        self.progress_bar.grid(row=0, column=0, padx=5, pady=5, sticky="ew")
        self.progress_bar.set(0)
        
        self.status_label = ctk.CTkLabel(self.progress_frame, text="Ready")
        self.status_label.grid(row=1, column=0, padx=5, pady=5)
        
        # Action buttons
        self.button_frame = ctk.CTkFrame(self.main_frame)
        self.button_frame.grid(row=5, column=0, padx=10, pady=5, sticky="ew")
        
        self.analyze_button = ctk.CTkButton(self.button_frame, text="Analyze",
                                          command=self.analyze_files)
        self.analyze_button.grid(row=0, column=0, padx=5, pady=5)
        
        self.preview_button = ctk.CTkButton(self.button_frame, text="Preview",
                                          command=self.preview_organization)
        self.preview_button.grid(row=0, column=1, padx=5, pady=5)
        
        self.organize_button = ctk.CTkButton(self.button_frame, text="Organize",
                                           command=self.organize_files)
        self.organize_button.grid(row=0, column=2, padx=5, pady=5)
        
        self.undo_button = ctk.CTkButton(self.button_frame, text="Undo",
                                        command=self.undo_operation)
        self.undo_button.grid(row=0, column=3, padx=5, pady=5)
        
        self.redo_button = ctk.CTkButton(self.button_frame, text="Redo",
                                        command=self.redo_operation)
        self.redo_button.grid(row=0, column=4, padx=5, pady=5)
        
        self.settings_button = ctk.CTkButton(self.button_frame, text="Settings",
                                           command=self.show_settings)
        self.settings_button.grid(row=0, column=5, padx=5, pady=5)
        
        self.stop_button = ctk.CTkButton(self.button_frame, text="Stop",
                                        command=self.stop_processing)
        self.stop_button.grid(row=0, column=6, padx=5, pady=5)

    def browse_source(self):
        directory = filedialog.askdirectory()
        if directory:
            self.source_entry.delete(0, tk.END)
            self.source_entry.insert(0, directory)

    def show_settings(self):
        """Show settings dialog"""
        settings_dialog = SettingsDialog(self, self.config_manager)
        settings_dialog.focus()  # Give focus to the dialog

    def on_settings_changed(self):
        """Handle settings changes"""
        # Update file analyzer model
        self.file_analyzer.model = self.config_manager.get_setting("default_model")
        
        # Update checkboxes with new values
        rules = self.config_manager.get_organization_rules()
        self.content_analysis_var.set(rules.get("use_content_analysis", True))
        self.file_type_var.set(rules.get("use_file_type", True))
        self.date_var.set(rules.get("use_date", True))
        self.remove_empty_var.set(self.config_manager.get_setting("remove_empty_folders", True))

        # Update any UI elements that depend on settings
        self.update_preview()  # If you have a preview function

    def analyze_files(self):
        source_dir = self.source_entry.get()
        if not source_dir:
            CTkMessagebox(title="Error", message="Please select a source directory", icon="warning")
            return

        try:
            self.status_label.configure(text="Analyzing files...")
            self.progress_bar.set(0)
            self.update()

            self.analysis_results = self.file_analyzer.analyze_directory(source_dir)
            self.status_label.configure(text="Analysis complete")
            self.progress_bar.set(100)
            
            CTkMessagebox(title="Success", 
                         message=f"Analysis complete. Found {len(self.analysis_results)} files.",
                         icon="info")

        except Exception as e:
            CTkMessagebox(title="Error", 
                         message=f"Error during analysis: {str(e)}", 
                         icon="error")
            self.status_label.configure(text="Analysis failed")
            self.progress_bar.set(0)

    def organize_files(self):
        if not self.analysis_results:
            CTkMessagebox(title="Error", 
                         message="Please analyze files first", 
                         icon="warning")
            return

        source_dir = self.source_entry.get()
        try:
            self.file_organizer.organize_files(
                source_dir=source_dir,
                analysis_results=self.analysis_results,
                remove_empty=self.remove_empty_var.get(),
                progress_callback=self.update_progress
            )
        except KeyboardInterrupt:
            self.status_label.configure(text="Operation cancelled")
            self.progress_bar.set(0)
        except Exception as e:
            CTkMessagebox(title="Error", 
                         message=f"Error during organization: {str(e)}", 
                         icon="error")
            self.status_label.configure(text="Organization failed")
            self.progress_bar.set(0)

    def update_progress(self, progress: float, status: str):
        self.progress_bar.set(progress / 100)
        self.status_label.configure(text=status)
        self.update()

    def stop_processing(self):
        self.file_analyzer.stop()
        self.file_organizer.stop()
        self.status_label.configure(text="Processing stopped")

    def preview_organization(self):
        """Preview how files will be organized"""
        if not self.analysis_results:
            CTkMessagebox(title="Error", message="Please analyze files first", icon="warning")
            return
            
        print("\nGenerating preview...")
        print(f"Analysis results: {self.analysis_results}")
        
        self.preview_text.delete("1.0", tk.END)
        preview_text = "Preview of file organization:\n\n"
        
        # Get smart rename setting
        rules = self.config_manager.get_organization_rules()
        smart_rename_enabled = rules.get("smart_rename_enabled", True)
        print(f"Smart rename enabled: {smart_rename_enabled}")
        
        for file_path, analysis in self.analysis_results.items():
            try:
                print(f"\nProcessing file: {file_path}")
                print(f"Analysis: {analysis}")
                
                main_category, sub_category = self.file_organizer.determine_para_category(file_path, analysis)
                category_path = self.file_organizer.get_para_category_name(main_category, sub_category)
                print(f"Category: {main_category}/{sub_category} -> {category_path}")
                
                # Show original name and smart rename suggestion if enabled
                original_name = os.path.basename(file_path)
                if smart_rename_enabled and 'suggested_name' in analysis:
                    print(f"Found rename suggestion: {analysis['suggested_name']}")
                    new_name = f"{analysis['suggested_name']}{os.path.splitext(original_name)[1]}"
                    preview_text += f"[Smart Rename] {original_name}\n"
                    preview_text += f"  → New name: {new_name}\n"
                    preview_text += f"  → Location: {category_path}\n\n"
                else:
                    if smart_rename_enabled:
                        print("No rename suggestion found in analysis")
                    preview_text += f"{original_name} → {category_path}\n\n"
                    
            except Exception as e:
                print(f"Error processing file {file_path}: {str(e)}")
                preview_text += f"{os.path.basename(file_path)} → Error: {str(e)}\n\n"
                
        self.preview_text.insert("1.0", preview_text)

    def update_stats(self):
        """Update statistics display"""
        stats = self.file_organizer.get_stats()
        stats_text = (
            f"Processed: {stats['processed']}\n"
            f"Succeeded: {stats['succeeded']}\n"
            f"Failed: {stats['failed']}\n"
            f"Skipped: {stats['skipped']}"
        )
        self.stats_label.configure(text=stats_text)

    def undo_operation(self):
        """Undo last operation"""
        if self.file_organizer.undo():
            self.update_stats()
            CTkMessagebox(title="Success", message="Operation undone successfully", icon="info")
        else:
            CTkMessagebox(title="Error", message="Nothing to undo", icon="warning")

    def redo_operation(self):
        """Redo last undone operation"""
        if self.file_organizer.redo():
            self.update_stats()
            CTkMessagebox(title="Success", message="Operation redone successfully", icon="info")
        else:
            CTkMessagebox(title="Error", message="Nothing to redo", icon="warning")

if __name__ == "__main__":
    app = FileOrganizerGUI()
    app.mainloop()
