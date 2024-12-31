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
        
        # Set theme and colors
        ctk.set_appearance_mode("light")
        ctk.set_default_color_theme("blue")
        
        # Custom colors
        self.colors = {
            "primary": "#4A90E2",
            "secondary": "#F5F7FA",
            "accent": "#34C759",
            "text": "#2C3E50",
            "border": "#E1E8ED"
        }
        
        # Initialize components
        self.file_analyzer = FileAnalyzer(config_manager=self.config_manager)
        self.file_organizer = FileOrganizer(config_manager=self.config_manager)
        self.analysis_results = None
        
        # Configure window
        self.title("Intelligent File Organizer")
        self.geometry("1200x800")  # Larger default size
        self.configure(fg_color=self.colors["secondary"])

        # Create menu bar with modern styling
        self.menu_bar = tk.Menu(self, bg=self.colors["secondary"], fg=self.colors["text"])
        self.config(menu=self.menu_bar)

        # Create File menu
        self.file_menu = tk.Menu(self.menu_bar, tearoff=0, bg=self.colors["secondary"], fg=self.colors["text"])
        self.menu_bar.add_cascade(label="File", menu=self.file_menu)
        self.file_menu.add_command(label="Settings", command=self.show_settings)
        self.file_menu.add_separator()
        self.file_menu.add_command(label="Exit", command=self.quit)
        
        # Configure grid with more padding
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)
        
        # Create main frame with modern styling
        self.main_frame = ctk.CTkFrame(self, fg_color=self.colors["secondary"], corner_radius=15)
        self.main_frame.grid(row=0, column=0, padx=30, pady=30, sticky="nsew")
        self.main_frame.grid_columnconfigure(0, weight=1)
        
        # Source directory selection with modern styling
        self.source_frame = ctk.CTkFrame(self.main_frame, corner_radius=10, fg_color="white", border_width=1, border_color=self.colors["border"])
        self.source_frame.grid(row=0, column=0, padx=15, pady=10, sticky="ew")
        
        self.source_label = ctk.CTkLabel(self.source_frame, text="Source Directory:", text_color=self.colors["text"], font=("Segoe UI", 12))
        self.source_label.grid(row=0, column=0, padx=10, pady=10)
        
        self.source_entry = ctk.CTkEntry(self.source_frame, width=500, height=35, corner_radius=8, border_color=self.colors["border"])
        self.source_entry.grid(row=0, column=1, padx=10, pady=10)
        
        self.source_button = ctk.CTkButton(self.source_frame, text="Browse", 
                                         command=self.browse_source,
                                         fg_color=self.colors["primary"],
                                         hover_color=self.colors["accent"],
                                         height=35,
                                         corner_radius=8)
        self.source_button.grid(row=0, column=2, padx=10, pady=10)
        
        # Organization options with modern styling
        self.options_frame = ctk.CTkFrame(self.main_frame, corner_radius=10, fg_color="white", border_width=1, border_color=self.colors["border"])
        self.options_frame.grid(row=1, column=0, padx=15, pady=10, sticky="ew")
        
        rules = self.config_manager.get_organization_rules()
        
        checkbox_style = {
            "corner_radius": 6,
            "border_width": 2,
            "text_color": self.colors["text"],
            "font": ("Segoe UI", 12),
            "hover_color": self.colors["accent"]
        }
        
        self.content_analysis_var = tk.BooleanVar(value=rules.get("use_content_analysis", True))
        self.content_checkbox = ctk.CTkCheckBox(self.options_frame, text="Content Analysis",
                                              variable=self.content_analysis_var,
                                              **checkbox_style)
        self.content_checkbox.grid(row=0, column=0, padx=15, pady=15)
        
        self.file_type_var = tk.BooleanVar(value=rules.get("use_file_type", True))
        self.file_type_checkbox = ctk.CTkCheckBox(self.options_frame, text="File Type Organization",
                                                 variable=self.file_type_var,
                                                 **checkbox_style)
        self.file_type_checkbox.grid(row=0, column=1, padx=15, pady=15)
        
        self.date_var = tk.BooleanVar(value=rules.get("use_date", True))
        self.date_checkbox = ctk.CTkCheckBox(self.options_frame, text="Date Organization",
                                           variable=self.date_var,
                                           **checkbox_style)
        self.date_checkbox.grid(row=0, column=2, padx=15, pady=15)
        
        self.remove_empty_var = tk.BooleanVar(value=self.config_manager.get_setting("remove_empty_folders", True))
        self.remove_empty_checkbox = ctk.CTkCheckBox(self.options_frame, text="Remove Empty Folders",
                                                    variable=self.remove_empty_var,
                                                    **checkbox_style)
        self.remove_empty_checkbox.grid(row=0, column=3, padx=15, pady=15)
        
        # Preview frame with modern styling
        self.preview_frame = ctk.CTkFrame(self.main_frame, corner_radius=10, fg_color="white", border_width=1, border_color=self.colors["border"])
        self.preview_frame.grid(row=2, column=0, padx=15, pady=10, sticky="nsew")
        self.preview_frame.grid_columnconfigure(0, weight=1)
        
        self.preview_text = ctk.CTkTextbox(self.preview_frame, height=200, width=1100,
                                         corner_radius=8,
                                         border_width=1,
                                         border_color=self.colors["border"],
                                         fg_color="white")
        self.preview_text.grid(row=0, column=0, padx=10, pady=10, sticky="nsew")
        
        # Stats frame with modern styling
        self.stats_frame = ctk.CTkFrame(self.main_frame, corner_radius=10, fg_color="white", border_width=1, border_color=self.colors["border"])
        self.stats_frame.grid(row=3, column=0, padx=15, pady=10, sticky="ew")
        
        self.stats_label = ctk.CTkLabel(self.stats_frame, text="Statistics:", 
                                      text_color=self.colors["text"],
                                      font=("Segoe UI", 12, "bold"))
        self.stats_label.grid(row=0, column=0, padx=10, pady=10)
        
        # Progress frame with modern styling
        self.progress_frame = ctk.CTkFrame(self.main_frame, corner_radius=10, fg_color="white", border_width=1, border_color=self.colors["border"])
        self.progress_frame.grid(row=4, column=0, padx=15, pady=10, sticky="ew")
        
        self.progress_bar = ctk.CTkProgressBar(self.progress_frame, 
                                             height=15,
                                             corner_radius=8,
                                             progress_color=self.colors["accent"])
        self.progress_bar.grid(row=0, column=0, padx=10, pady=10, sticky="ew")
        self.progress_bar.set(0)
        
        self.status_label = ctk.CTkLabel(self.progress_frame, text="Ready",
                                       text_color=self.colors["text"],
                                       font=("Segoe UI", 12))
        self.status_label.grid(row=1, column=0, padx=10, pady=5)
        
        # Action buttons with modern styling
        self.button_frame = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        self.button_frame.grid(row=5, column=0, padx=15, pady=15, sticky="ew")
        
        button_style = {
            "height": 38,
            "corner_radius": 8,
            "font": ("Segoe UI", 12),
            "hover_color": self.colors["accent"]
        }
        
        self.analyze_button = ctk.CTkButton(self.button_frame, text="Analyze",
                                          command=self.analyze_files,
                                          fg_color=self.colors["primary"],
                                          **button_style)
        self.analyze_button.grid(row=0, column=0, padx=8, pady=5)
        
        self.preview_button = ctk.CTkButton(self.button_frame, text="Preview",
                                          command=self.preview_organization,
                                          fg_color=self.colors["primary"],
                                          **button_style)
        self.preview_button.grid(row=0, column=1, padx=8, pady=5)
        
        self.organize_button = ctk.CTkButton(self.button_frame, text="Organize",
                                           command=self.organize_files,
                                           fg_color=self.colors["primary"],
                                           **button_style)
        self.organize_button.grid(row=0, column=2, padx=8, pady=5)
        
        self.undo_button = ctk.CTkButton(self.button_frame, text="Undo",
                                        command=self.undo_operation,
                                        fg_color=self.colors["primary"],
                                        **button_style)
        self.undo_button.grid(row=0, column=3, padx=8, pady=5)
        
        self.redo_button = ctk.CTkButton(self.button_frame, text="Redo",
                                        command=self.redo_operation,
                                        fg_color=self.colors["primary"],
                                        **button_style)
        self.redo_button.grid(row=0, column=4, padx=8, pady=5)
        
        self.settings_button = ctk.CTkButton(self.button_frame, text="Settings",
                                           command=self.show_settings,
                                           fg_color=self.colors["primary"],
                                           **button_style)
        self.settings_button.grid(row=0, column=5, padx=8, pady=5)
        
        self.stop_button = ctk.CTkButton(self.button_frame, text="Stop",
                                        command=self.stop_processing,
                                        fg_color="#E74C3C",  # Red for stop button
                                        **button_style)
        self.stop_button.grid(row=0, column=6, padx=8, pady=5)

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
        # Update organization rules
        rules = self.config_manager.get_organization_rules()
        self.content_analysis_var.set(rules.get("use_content_analysis", True))
        self.file_type_var.set(rules.get("use_file_type", True))
        self.date_var.set(rules.get("use_date", True))
        self.remove_empty_var.set(self.config_manager.get_setting("remove_empty_folders", True))

        # Update preview if source directory is set
        if hasattr(self, 'source_entry') and self.source_entry.get():
            self.preview_organization()
        
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
                content_analysis = analysis.get('content_analysis', {})
                if smart_rename_enabled and content_analysis.get('success') and 'suggested_name' in content_analysis:
                    suggested_name = content_analysis['suggested_name']
                    print(f"Found rename suggestion: {suggested_name}")
                    new_name = f"{suggested_name}{os.path.splitext(original_name)[1]}"
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
