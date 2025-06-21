import customtkinter as ctk
import tkinter as tk
from tkinter import filedialog
import os
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, Any
from Service.file_analyzer import FileAnalyzer
from Service.file_organizer import FileOrganizer
from Utils.config_manager import ConfigManager
from UI.settings_dialog import SettingsDialog
from CTkMessagebox import CTkMessagebox
from Config.design_tokens import get_component_style, get_colors, get_spacing, ComponentSize, ThemeMode
from Config.logging_config import StructuredLogger
import threading

class FileOrganizerGUI(ctk.CTk):
    """Main GUI application with modern design tokens system."""
    
    def __init__(self):
        super().__init__()

        # Initialize logging
        self.logger = StructuredLogger('FileOrganizer.GUI')
        self.logger.info("Initializing File Organizer GUI")

        # Initialize configuration
        self.config_manager = ConfigManager()
        self.config_manager.add_observer(self)  # Register as observer
        
        # Set theme and colors using design tokens
        ctk.set_appearance_mode("light")
        ctk.set_default_color_theme("blue")
        
        # Get design tokens
        self.colors = get_colors()
        self.spacing = get_spacing()
        
        # Initialize components
        self.file_analyzer = FileAnalyzer(config_manager=self.config_manager)
        self.file_organizer = FileOrganizer(config_manager=self.config_manager)
        self.analysis_results = None
        
        # Configure window
        self.title("Intelligent File Organizer")
        self.geometry("1200x800")  # Larger default size
        self.configure(fg_color=self.colors.surface)

        # Create menu bar with modern styling
        self.menu_bar = tk.Menu(self, bg=self.colors.surface, fg=self.colors.text_primary)
        self.config(menu=self.menu_bar)

        # Create File menu
        self.file_menu = tk.Menu(self.menu_bar, tearoff=0, bg=self.colors.surface, fg=self.colors.text_primary)
        self.menu_bar.add_cascade(label="File", menu=self.file_menu)
        self.file_menu.add_command(label="Settings", command=self.show_settings)
        self.file_menu.add_separator()
        self.file_menu.add_command(label="Exit", command=self.quit)
        
        # Configure grid with more padding
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)
        
        # Create main frame with modern styling
        main_frame_style = get_component_style("frame", "surface")
        self.main_frame = ctk.CTkFrame(self, **main_frame_style)
        self.main_frame.grid(row=0, column=0, padx=self.spacing.xl, pady=self.spacing.xl, sticky="nsew")
        self.main_frame.grid_columnconfigure(0, weight=1)
        
        # Source directory selection with modern styling
        source_frame_style = get_component_style("frame", "card")
        self.source_frame = ctk.CTkFrame(self.main_frame, **source_frame_style)
        self.source_frame.grid(row=0, column=0, padx=self.spacing.md, pady=self.spacing.sm, sticky="ew")
        
        label_style = get_component_style("label", "default")
        self.source_label = ctk.CTkLabel(self.source_frame, text="Source Directory:", **label_style)
        self.source_label.grid(row=0, column=0, padx=self.spacing.sm, pady=self.spacing.sm)
        
        entry_style = get_component_style("input", "default")
        entry_style["width"] = 500
        self.source_entry = ctk.CTkEntry(self.source_frame, **entry_style)
        self.source_entry.grid(row=0, column=1, padx=self.spacing.sm, pady=self.spacing.sm)
        
        button_style = get_component_style("button", "primary")
        self.source_button = ctk.CTkButton(self.source_frame, text="Browse", 
                                         command=self.browse_source,
                                         **button_style)
        self.source_button.grid(row=0, column=2, padx=self.spacing.sm, pady=self.spacing.sm)
        
        # Organization options with modern styling
        options_frame_style = get_component_style("frame", "card")
        self.options_frame = ctk.CTkFrame(self.main_frame, **options_frame_style)
        self.options_frame.grid(row=1, column=0, padx=self.spacing.md, pady=self.spacing.sm, sticky="ew")
        
        rules = self.config_manager.get_organization_rules()
        
        checkbox_style = get_component_style("checkbox", "default")
        
        self.content_analysis_var = tk.BooleanVar(value=rules.get("use_content_analysis", True))
        self.content_checkbox = ctk.CTkCheckBox(self.options_frame, text="Content Analysis",
                                              variable=self.content_analysis_var,
                                              **checkbox_style)
        self.content_checkbox.grid(row=0, column=0, padx=self.spacing.md, pady=self.spacing.md)
        
        self.file_type_var = tk.BooleanVar(value=rules.get("use_file_type", True))
        self.file_type_checkbox = ctk.CTkCheckBox(self.options_frame, text="File Type Organization",
                                                 variable=self.file_type_var,
                                                 **checkbox_style)
        self.file_type_checkbox.grid(row=0, column=1, padx=self.spacing.md, pady=self.spacing.md)
        
        self.date_var = tk.BooleanVar(value=rules.get("use_date", True))
        self.date_checkbox = ctk.CTkCheckBox(self.options_frame, text="Date Organization",
                                           variable=self.date_var,
                                           **checkbox_style)
        self.date_checkbox.grid(row=0, column=2, padx=self.spacing.md, pady=self.spacing.md)
        
        self.remove_empty_var = tk.BooleanVar(value=self.config_manager.get_setting("remove_empty_folders", True))
        self.remove_empty_checkbox = ctk.CTkCheckBox(self.options_frame, text="Remove Empty Folders",
                                                    variable=self.remove_empty_var,
                                                    **checkbox_style)
        self.remove_empty_checkbox.grid(row=0, column=3, padx=self.spacing.md, pady=self.spacing.md)
        
        # Preview frame with modern styling
        preview_frame_style = get_component_style("frame", "card")
        self.preview_frame = ctk.CTkFrame(self.main_frame, **preview_frame_style)
        self.preview_frame.grid(row=2, column=0, padx=self.spacing.md, pady=self.spacing.sm, sticky="nsew")
        self.preview_frame.grid_columnconfigure(0, weight=1)
        
        textbox_style = get_component_style("textbox", "default")
        textbox_style.update({"height": 200, "width": 1100})
        self.preview_text = ctk.CTkTextbox(self.preview_frame, **textbox_style)
        self.preview_text.grid(row=0, column=0, padx=self.spacing.sm, pady=self.spacing.sm, sticky="nsew")
        
        # Stats frame with modern styling
        stats_frame_style = get_component_style("frame", "card")
        self.stats_frame = ctk.CTkFrame(self.main_frame, **stats_frame_style)
        self.stats_frame.grid(row=3, column=0, padx=self.spacing.md, pady=self.spacing.sm, sticky="ew")
        
        stats_label_style = get_component_style("label", "heading")
        self.stats_label = ctk.CTkLabel(self.stats_frame, text="Statistics:", **stats_label_style)
        self.stats_label.grid(row=0, column=0, padx=self.spacing.sm, pady=self.spacing.sm)
        
        # Progress frame with modern styling
        progress_frame_style = get_component_style("frame", "card")
        self.progress_frame = ctk.CTkFrame(self.main_frame, **progress_frame_style)
        self.progress_frame.grid(row=4, column=0, padx=self.spacing.md, pady=self.spacing.sm, sticky="ew")
        
        progressbar_style = get_component_style("progressbar", "default")
        self.progress_bar = ctk.CTkProgressBar(self.progress_frame, **progressbar_style)
        self.progress_bar.grid(row=0, column=0, padx=self.spacing.sm, pady=self.spacing.sm, sticky="ew")
        self.progress_bar.set(0)
        
        status_label_style = get_component_style("label", "secondary")
        self.status_label = ctk.CTkLabel(self.progress_frame, text="Ready", **status_label_style)
        self.status_label.grid(row=1, column=0, padx=self.spacing.sm, pady=self.spacing.xs)
        
        # Action buttons with modern styling
        self.button_frame = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        self.button_frame.grid(row=5, column=0, padx=self.spacing.md, pady=self.spacing.md, sticky="ew")
        
        button_style = get_component_style("button", "primary")
        
        self.analyze_button = ctk.CTkButton(self.button_frame, text="Analyze",
                                          command=self.analyze_files,
                                          **button_style)
        self.analyze_button.grid(row=0, column=0, padx=self.spacing.xs, pady=self.spacing.xs)
        
        self.preview_button = ctk.CTkButton(self.button_frame, text="Preview",
                                          command=self.preview_organization,
                                          **button_style)
        self.preview_button.grid(row=0, column=1, padx=self.spacing.xs, pady=self.spacing.xs)
        
        organize_button_style = get_component_style("button", "success")
        self.organize_button = ctk.CTkButton(self.button_frame, text="Organize",
                                           command=self.organize_files,
                                           **organize_button_style)
        self.organize_button.grid(row=0, column=2, padx=self.spacing.xs, pady=self.spacing.xs)
        
        secondary_button_style = get_component_style("button", "secondary")
        self.undo_button = ctk.CTkButton(self.button_frame, text="Undo",
                                        command=self.undo_operation,
                                        **secondary_button_style)
        self.undo_button.grid(row=0, column=3, padx=self.spacing.xs, pady=self.spacing.xs)
        
        self.redo_button = ctk.CTkButton(self.button_frame, text="Redo",
                                        command=self.redo_operation,
                                        **secondary_button_style)
        self.redo_button.grid(row=0, column=4, padx=self.spacing.xs, pady=self.spacing.xs)
        
        self.settings_button = ctk.CTkButton(self.button_frame, text="Settings",
                                           command=self.show_settings,
                                           **secondary_button_style)
        self.settings_button.grid(row=0, column=5, padx=self.spacing.xs, pady=self.spacing.xs)
        
        stop_button_style = get_component_style("button", "error")
        self.stop_button = ctk.CTkButton(self.button_frame, text="Stop",
                                        command=self.stop_processing,
                                        **stop_button_style)
        self.stop_button.grid(row=0, column=6, padx=self.spacing.xs, pady=self.spacing.xs)

    def browse_source(self) -> None:
        """Browse and select source directory."""
        directory = filedialog.askdirectory()
        if directory:
            self.logger.info(f"Source directory selected: {directory}")
            self.source_entry.delete(0, tk.END)
            self.source_entry.insert(0, directory)

    def show_settings(self) -> None:
        """Show settings dialog"""
        self.logger.info("Opening settings dialog")
        settings_dialog = SettingsDialog(self, self.config_manager)
        settings_dialog.focus()  # Give focus to the dialog

    def on_settings_changed(self) -> None:
        """Handle settings changes"""
        self.logger.info("Settings changed, updating UI")
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

    def update_progress(self, progress: float, status: str) -> None:
        """Update progress bar and status label."""
        self.progress_bar.set(progress / 100)
        self.status_label.configure(text=status)
        self.update()

    def stop_processing(self) -> None:
        """Stop all ongoing operations."""
        self.logger.info("User requested to stop processing")
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

def main():
    """Main entry point for the application."""
    app = FileOrganizerGUI()
    app.mainloop()

if __name__ == "__main__":
    main()
