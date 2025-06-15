"""
Async-enabled GUI that uses dependency injection and separates UI from business logic.
"""

import customtkinter as ctk
import tkinter as tk
import asyncio
import threading
from typing import Optional, Dict, Any
from datetime import datetime

from interfaces import IBusinessLogicService, IUIService, IConfigManager
from business_logic_service import ProgressReporter
from service_configuration import get_service, initialize_application
from design_tokens import get_component_style, get_colors, get_spacing
from settings_dialog import SettingsDialog

class AsyncFileOrganizerGUI(ctk.CTk):
    """Modern async-enabled GUI with dependency injection."""
    
    def __init__(self):
        super().__init__()
        
        # Initialize services
        self.container = initialize_application()
        self.business_service = get_service(IBusinessLogicService)
        self.ui_service = get_service(IUIService)
        self.config_manager = get_service(IConfigManager)
        
        # Set UI service parent for dialogs
        self.ui_service.parent_window = self
        
        # Register as config observer
        self.config_manager.add_observer(self)
        
        # Async operation management
        self.current_operation: Optional[asyncio.Task] = None
        self.event_loop: Optional[asyncio.AbstractEventLoop] = None
        self.loop_thread: Optional[threading.Thread] = None
        
        # UI state
        self.analysis_results: Optional[Dict[str, Any]] = None
        self.progress_reporter: Optional[ProgressReporter] = None
        
        # Initialize UI
        self._setup_ui()
        self._start_event_loop()
    
    def _setup_ui(self):
        """Set up the user interface."""
        # Set theme and colors
        ctk.set_appearance_mode("light")
        ctk.set_default_color_theme("blue")
        
        # Get design tokens
        self.colors = get_colors()
        self.spacing = get_spacing()
        
        # Configure window
        self.title("Intelligent File Organizer - Async Edition")
        self.geometry("1200x800")
        self.configure(fg_color=self.colors.surface)
        
        # Create menu bar
        self._create_menu_bar()
        
        # Configure grid
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)
        
        # Create main frame
        main_frame_style = get_component_style("frame", "surface")
        self.main_frame = ctk.CTkFrame(self, **main_frame_style)
        self.main_frame.grid(row=0, column=0, padx=self.spacing.xl, pady=self.spacing.xl, sticky="nsew")
        self.main_frame.grid_columnconfigure(0, weight=1)
        
        # Create UI sections
        self._create_source_section()
        self._create_options_section()
        self._create_preview_section()
        self._create_stats_section()
        self._create_progress_section()
        self._create_action_buttons()
    
    def _create_menu_bar(self):
        """Create menu bar."""
        self.menu_bar = tk.Menu(self, bg=self.colors.surface, fg=self.colors.text_primary)
        self.config(menu=self.menu_bar)
        
        # File menu
        self.file_menu = tk.Menu(self.menu_bar, tearoff=0, bg=self.colors.surface, fg=self.colors.text_primary)
        self.menu_bar.add_cascade(label="File", menu=self.file_menu)
        self.file_menu.add_command(label="Settings", command=self.show_settings)
        self.file_menu.add_separator()
        self.file_menu.add_command(label="Exit", command=self.quit)
    
    def _create_source_section(self):
        """Create source directory selection section."""
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
        self.browse_button = ctk.CTkButton(
            self.source_frame, 
            text="Browse", 
            command=self.browse_source,
            **button_style
        )
        self.browse_button.grid(row=0, column=2, padx=self.spacing.sm, pady=self.spacing.sm)
    
    def _create_options_section(self):
        """Create organization options section."""
        options_frame_style = get_component_style("frame", "card")
        self.options_frame = ctk.CTkFrame(self.main_frame, **options_frame_style)
        self.options_frame.grid(row=1, column=0, padx=self.spacing.md, pady=self.spacing.sm, sticky="ew")
        
        rules = self.config_manager.get_organization_rules()
        checkbox_style = get_component_style("checkbox", "default")
        
        self.content_analysis_var = tk.BooleanVar(value=rules.get("use_content_analysis", True))
        self.content_checkbox = ctk.CTkCheckBox(
            self.options_frame, 
            text="Content Analysis",
            variable=self.content_analysis_var,
            **checkbox_style
        )
        self.content_checkbox.grid(row=0, column=0, padx=self.spacing.md, pady=self.spacing.md)
        
        self.file_type_var = tk.BooleanVar(value=rules.get("use_file_type", True))
        self.file_type_checkbox = ctk.CTkCheckBox(
            self.options_frame, 
            text="File Type Organization",
            variable=self.file_type_var,
            **checkbox_style
        )
        self.file_type_checkbox.grid(row=0, column=1, padx=self.spacing.md, pady=self.spacing.md)
        
        self.date_var = tk.BooleanVar(value=rules.get("use_date", True))
        self.date_checkbox = ctk.CTkCheckBox(
            self.options_frame, 
            text="Date Organization",
            variable=self.date_var,
            **checkbox_style
        )
        self.date_checkbox.grid(row=0, column=2, padx=self.spacing.md, pady=self.spacing.md)
        
        self.remove_empty_var = tk.BooleanVar(value=self.config_manager.get_setting("remove_empty_folders", True))
        self.remove_empty_checkbox = ctk.CTkCheckBox(
            self.options_frame, 
            text="Remove Empty Folders",
            variable=self.remove_empty_var,
            **checkbox_style
        )
        self.remove_empty_checkbox.grid(row=0, column=3, padx=self.spacing.md, pady=self.spacing.md)
    
    def _create_preview_section(self):
        """Create preview section."""
        preview_frame_style = get_component_style("frame", "card")
        self.preview_frame = ctk.CTkFrame(self.main_frame, **preview_frame_style)
        self.preview_frame.grid(row=2, column=0, padx=self.spacing.md, pady=self.spacing.sm, sticky="nsew")
        self.preview_frame.grid_columnconfigure(0, weight=1)
        self.main_frame.grid_rowconfigure(2, weight=1)
        
        textbox_style = get_component_style("textbox", "default")
        textbox_style.update({"height": 300, "width": 1100})
        self.preview_text = ctk.CTkTextbox(self.preview_frame, **textbox_style)
        self.preview_text.grid(row=0, column=0, padx=self.spacing.sm, pady=self.spacing.sm, sticky="nsew")
    
    def _create_stats_section(self):
        """Create statistics section."""
        stats_frame_style = get_component_style("frame", "card")
        self.stats_frame = ctk.CTkFrame(self.main_frame, **stats_frame_style)
        self.stats_frame.grid(row=3, column=0, padx=self.spacing.md, pady=self.spacing.sm, sticky="ew")
        
        stats_label_style = get_component_style("label", "heading")
        self.stats_label = ctk.CTkLabel(self.stats_frame, text="Ready", **stats_label_style)
        self.stats_label.grid(row=0, column=0, padx=self.spacing.sm, pady=self.spacing.sm)
    
    def _create_progress_section(self):
        """Create progress section."""
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
    
    def _create_action_buttons(self):
        """Create action buttons section."""
        self.button_frame = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        self.button_frame.grid(row=5, column=0, padx=self.spacing.md, pady=self.spacing.md, sticky="ew")
        
        button_style = get_component_style("button", "primary")
        
        self.analyze_button = ctk.CTkButton(
            self.button_frame, 
            text="Analyze",
            command=self.analyze_files,
            **button_style
        )
        self.analyze_button.grid(row=0, column=0, padx=self.spacing.xs, pady=self.spacing.xs)
        
        self.preview_button = ctk.CTkButton(
            self.button_frame, 
            text="Preview",
            command=self.preview_organization,
            **button_style
        )
        self.preview_button.grid(row=0, column=1, padx=self.spacing.xs, pady=self.spacing.xs)
        
        organize_button_style = get_component_style("button", "success")
        self.organize_button = ctk.CTkButton(
            self.button_frame, 
            text="Organize",
            command=self.organize_files,
            **organize_button_style
        )
        self.organize_button.grid(row=0, column=2, padx=self.spacing.xs, pady=self.spacing.xs)
        
        secondary_button_style = get_component_style("button", "secondary")
        
        self.undo_button = ctk.CTkButton(
            self.button_frame, 
            text="Undo",
            command=self.undo_operation,
            **secondary_button_style
        )
        self.undo_button.grid(row=0, column=3, padx=self.spacing.xs, pady=self.spacing.xs)
        
        self.redo_button = ctk.CTkButton(
            self.button_frame, 
            text="Redo",
            command=self.redo_operation,
            **secondary_button_style
        )
        self.redo_button.grid(row=0, column=4, padx=self.spacing.xs, pady=self.spacing.xs)
        
        self.settings_button = ctk.CTkButton(
            self.button_frame, 
            text="Settings",
            command=self.show_settings,
            **secondary_button_style
        )
        self.settings_button.grid(row=0, column=5, padx=self.spacing.xs, pady=self.spacing.xs)
        
        stop_button_style = get_component_style("button", "error")
        self.stop_button = ctk.CTkButton(
            self.button_frame, 
            text="Stop",
            command=self.stop_processing,
            **stop_button_style
        )
        self.stop_button.grid(row=0, column=6, padx=self.spacing.xs, pady=self.spacing.xs)
    
    def _start_event_loop(self):
        """Start async event loop in background thread."""
        def run_loop():
            self.event_loop = asyncio.new_event_loop()
            asyncio.set_event_loop(self.event_loop)
            self.event_loop.run_forever()
        
        self.loop_thread = threading.Thread(target=run_loop, daemon=True)
        self.loop_thread.start()
    
    def _run_async(self, coro):
        """Run coroutine in the background event loop."""
        if self.event_loop and not self.event_loop.is_closed():
            future = asyncio.run_coroutine_threadsafe(coro, self.event_loop)
            return future
        else:
            self.ui_service.show_error("Error", "Event loop not available")
            return None
    
    def browse_source(self):
        """Browse and select source directory."""
        directory = self.ui_service.select_directory("Select Source Directory")
        if directory:
            self.source_entry.delete(0, tk.END)
            self.source_entry.insert(0, directory)
    
    def show_settings(self):
        """Show settings dialog."""
        settings_dialog = SettingsDialog(self, self.config_manager)
        settings_dialog.focus()
    
    def on_settings_changed(self):
        """Handle settings changes."""
        # Update UI with new settings
        rules = self.config_manager.get_organization_rules()
        self.content_analysis_var.set(rules.get("use_content_analysis", True))
        self.file_type_var.set(rules.get("use_file_type", True))
        self.date_var.set(rules.get("use_date", True))
        self.remove_empty_var.set(self.config_manager.get_setting("remove_empty_folders", True))
    
    def analyze_files(self):
        """Start file analysis."""
        source_dir = self.source_entry.get().strip()
        if not source_dir:
            self.ui_service.show_error("Error", "Please select a source directory")
            return
        
        # Cancel any running operation
        self.stop_processing()
        
        # Create progress reporter
        self.progress_reporter = ProgressReporter(self.update_progress)
        
        # Get options
        options = {
            'use_content_analysis': self.content_analysis_var.get(),
            'use_file_type': self.file_type_var.get(),
            'use_date': self.date_var.get(),
            'remove_empty_folders': self.remove_empty_var.get()
        }
        
        # Start async analysis
        coro = self._analyze_files_async(source_dir, options)
        self.current_operation = self._run_async(coro)
    
    async def _analyze_files_async(self, source_dir: str, options: Dict[str, Any]):
        """Async file analysis implementation."""
        try:
            self.status_label.configure(text="Starting analysis...")
            self.progress_bar.set(0)
            self._set_buttons_enabled(False)
            
            # Use only preview for analysis
            result = await self.business_service.preview_organization_async(source_dir, options)
            
            if result['success']:
                self.analysis_results = result
                self.status_label.configure(text=f"Analysis complete. Found {result['stats']['total_files']} files.")
                self.progress_bar.set(1.0)
                self.ui_service.show_success("Success", f"Analysis complete. Found {result['stats']['total_files']} files.")
                
                # Auto-show preview
                self.show_preview(result)
            else:
                error_msg = '; '.join(result.get('errors', ['Unknown error']))
                self.status_label.configure(text="Analysis failed")
                self.progress_bar.set(0)
                self.ui_service.show_error("Analysis Failed", error_msg)
                
        except Exception as e:
            self.status_label.configure(text="Analysis failed")
            self.progress_bar.set(0)
            self.ui_service.show_error("Error", f"Analysis failed: {str(e)}")
        finally:
            self._set_buttons_enabled(True)
            self.current_operation = None
    
    def preview_organization(self):
        """Show organization preview."""
        if not self.analysis_results:
            self.ui_service.show_error("Error", "Please analyze files first")
            return
        
        self.show_preview(self.analysis_results)
    
    def show_preview(self, result: Dict[str, Any]):
        """Display preview in text area."""
        self.preview_text.delete("1.0", tk.END)
        
        preview_text = "Organization Preview:\n\n"
        
        # Show statistics
        stats = result.get('stats', {})
        preview_text += f"Total Files: {stats.get('total_files', 0)}\n"
        preview_text += f"Smart Renames: {stats.get('smart_renames', 0)}\n\n"
        
        # Show by category
        by_category = stats.get('by_category', {})
        if by_category:
            preview_text += "Files by Category:\n"
            for category, count in by_category.items():
                preview_text += f"  {category}: {count} files\n"
            preview_text += "\n"
        
        # Show file details
        preview_text += "File Organization Details:\n"
        preview_text += "-" * 50 + "\n"
        
        for item in result.get('preview_items', [])[:50]:  # Limit to first 50 for performance
            original_name = item['original_name']
            new_name = item['new_name']
            category = item['category_display']
            
            if item['is_renamed']:
                preview_text += f"[RENAME] {original_name}\n"
                preview_text += f"  → {new_name}\n"
                preview_text += f"  → {category}\n\n"
            else:
                preview_text += f"{original_name}\n"
                preview_text += f"  → {category}\n\n"
        
        if len(result.get('preview_items', [])) > 50:
            remaining = len(result['preview_items']) - 50
            preview_text += f"... and {remaining} more files\n"
        
        self.preview_text.insert("1.0", preview_text)
    
    def organize_files(self):
        """Start file organization."""
        if not self.analysis_results:
            self.ui_service.show_error("Error", "Please analyze files first")
            return
        
        source_dir = self.source_entry.get().strip()
        
        # Confirm with user
        stats = self.analysis_results.get('stats', {})
        total_files = stats.get('total_files', 0)
        smart_renames = stats.get('smart_renames', 0)
        
        message = f"Organize {total_files} files?"
        if smart_renames > 0:
            message += f"\n{smart_renames} files will be renamed."
        
        if not self.ui_service.ask_confirmation("Confirm Organization", message):
            return
        
        # Cancel any running operation
        self.stop_processing()
        
        # Create progress reporter
        self.progress_reporter = ProgressReporter(self.update_progress)
        
        # Get options
        options = {
            'use_content_analysis': self.content_analysis_var.get(),
            'use_file_type': self.file_type_var.get(),
            'use_date': self.date_var.get(),
            'remove_empty_folders': self.remove_empty_var.get()
        }
        
        # Start async organization
        coro = self._organize_files_async(source_dir, options)
        self.current_operation = self._run_async(coro)
    
    async def _organize_files_async(self, source_dir: str, options: Dict[str, Any]):
        """Async file organization implementation."""
        try:
            self.status_label.configure(text="Starting organization...")
            self.progress_bar.set(0)
            self._set_buttons_enabled(False)
            
            result = await self.business_service.analyze_and_organize_async(
                source_dir, options, self.progress_reporter
            )
            
            if result['success']:
                stats = result.get('organization_stats', {})
                self.status_label.configure(text="Organization completed")
                self.progress_bar.set(1.0)
                
                message = f"Organization completed successfully!\n"
                message += f"Processed: {stats.get('processed', 0)} files\n"
                message += f"Succeeded: {stats.get('succeeded', 0)} files\n"
                message += f"Failed: {stats.get('failed', 0)} files"
                
                self.ui_service.show_success("Organization Complete", message)
                
                # Update stats display
                self.stats_label.configure(text=f"Processed: {stats.get('processed', 0)}, "
                                                f"Succeeded: {stats.get('succeeded', 0)}, "
                                                f"Failed: {stats.get('failed', 0)}")
            else:
                error_msg = '; '.join(result.get('errors', ['Unknown error']))
                self.status_label.configure(text="Organization failed")
                self.progress_bar.set(0)
                self.ui_service.show_error("Organization Failed", error_msg)
                
        except Exception as e:
            self.status_label.configure(text="Organization failed")
            self.progress_bar.set(0)
            self.ui_service.show_error("Error", f"Organization failed: {str(e)}")
        finally:
            self._set_buttons_enabled(True)
            self.current_operation = None
    
    def undo_operation(self):
        """Undo last operation."""
        coro = self._undo_operation_async()
        self._run_async(coro)
    
    async def _undo_operation_async(self):
        """Async undo implementation."""
        try:
            result = await self.business_service.undo_last_operation_async()
            if result['success']:
                self.ui_service.show_success("Success", result['message'])
            else:
                self.ui_service.show_warning("Warning", result['message'])
        except Exception as e:
            self.ui_service.show_error("Error", f"Undo failed: {str(e)}")
    
    def redo_operation(self):
        """Redo last operation."""
        coro = self._redo_operation_async()
        self._run_async(coro)
    
    async def _redo_operation_async(self):
        """Async redo implementation."""
        try:
            result = await self.business_service.redo_last_operation_async()
            if result['success']:
                self.ui_service.show_success("Success", result['message'])
            else:
                self.ui_service.show_warning("Warning", result['message'])
        except Exception as e:
            self.ui_service.show_error("Error", f"Redo failed: {str(e)}")
    
    def stop_processing(self):
        """Stop current operation."""
        if self.current_operation and not self.current_operation.done():
            self.current_operation.cancel()
            
        if self.progress_reporter:
            self.progress_reporter.cancel()
            
        self.business_service.stop_all_operations()
        self.status_label.configure(text="Operation stopped")
        self._set_buttons_enabled(True)
    
    def update_progress(self, progress: float, status: str):
        """Update progress bar and status."""
        self.progress_bar.set(progress / 100.0)
        self.status_label.configure(text=status)
        self.update()
    
    def _set_buttons_enabled(self, enabled: bool):
        """Enable/disable buttons during operations."""
        state = "normal" if enabled else "disabled"
        self.analyze_button.configure(state=state)
        self.preview_button.configure(state=state)
        self.organize_button.configure(state=state)
        self.undo_button.configure(state=state)
        self.redo_button.configure(state=state)
    
    def on_closing(self):
        """Handle window closing."""
        self.stop_processing()
        
        # Cleanup services
        from service_configuration import cleanup_services
        cleanup_services()
        
        # Stop event loop
        if self.event_loop and not self.event_loop.is_closed():
            self.event_loop.call_soon_threadsafe(self.event_loop.stop)
        
        self.destroy()

if __name__ == "__main__":
    app = AsyncFileOrganizerGUI()
    app.protocol("WM_DELETE_WINDOW", app.on_closing)
    app.mainloop()