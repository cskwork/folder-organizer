import customtkinter as ctk
from pathlib import Path
from typing import Optional, Dict, Any
import threading

from src.ui.base_component import BaseComponent
from src.ui.toast import ToastManager
from src.themes.theme_manager import ThemeManager
from .file_analysis_view import FileAnalysisView
from .file_organization_view import FileOrganizationView
from .settings_dialog import SettingsDialog

class MainWindow(ctk.CTk, BaseComponent):
    """Modern main window for the File Organizer application"""
    
    def __init__(self):
        super().__init__()
        
        # Initialize managers
        self.settings_manager = None  # Will be injected
        self.theme_manager = ThemeManager(config_manager=None)  # We'll inject this later
        BaseComponent.__init__(self, theme_manager=self.theme_manager)
        self.toast_manager = ToastManager(self, self.theme_manager)
        
        self.file_analyzer = None  # Will be injected
        self.file_organizer = None  # Will be injected
        
        # Current view
        self.current_view = None
        
        # Configure window
        self.title("Intelligent File Organizer")
        self.geometry("1200x800")
        self._setup_grid()
        self._create_widgets()
        self.update_theme()
        
    def on_settings_changed(self, settings: Dict[str, Any]):
        """Handle settings changes"""
        # Update theme
        if self.theme_manager:
            theme = settings.get("appearance", {}).get("theme")
            if theme:
                self.theme_manager.set_theme(theme)
        
        # Update font size
        font_size = settings.get("appearance", {}).get("font_size")
        if font_size:
            # Update font size for all widgets
            self._update_font_size(self, font_size)
    
    def _update_font_size(self, widget: ctk.CTkBaseClass, size: int):
        """Recursively update font size for all widgets"""
        if hasattr(widget, "cget") and "font" in widget.cget():
            current_font = widget.cget("font")
            if isinstance(current_font, tuple):
                widget.configure(font=(current_font[0], size))
        
        for child in widget.winfo_children():
            self._update_font_size(child, size)
    
    def _setup_grid(self):
        """Configure grid layout"""
        self.grid_columnconfigure(1, weight=1)  # Main content area
        self.grid_rowconfigure(0, weight=1)
        
    def _create_widgets(self):
        """Create all window widgets"""
        self._create_sidebar()
        self._create_main_content()
        
    def _create_sidebar(self):
        """Create navigation sidebar"""
        sidebar = self.create_frame(
            self,
            width=250,
            corner_radius=0,
            border_width=0
        )
        sidebar.grid(row=0, column=0, sticky="nsew", padx=0, pady=0)
        sidebar.grid_propagate(False)
        
        # Logo/Title area
        title_frame = self.create_frame(sidebar, corner_radius=0, border_width=0)
        title_frame.pack(fill="x", padx=20, pady=(20, 10))
        
        title = self.create_label(
            title_frame,
            text="File Organizer",
            font=("Helvetica", 20, "bold")
        )
        title.pack(pady=10)
        
        # Navigation buttons
        nav_frame = self.create_frame(sidebar, corner_radius=0, border_width=0)
        nav_frame.pack(fill="x", padx=10)
        
        nav_buttons = [
            ("Analyze Files", self._on_analyze_click),
            ("Organize Files", self._on_organize_click),
            ("Settings", self._on_settings_click)
        ]
        
        for text, command in nav_buttons:
            btn = self.create_button(
                nav_frame,
                text=text,
                command=command,
                anchor="w",
                width=200
            )
            btn.pack(pady=5, padx=10)
        
        # Theme toggle at bottom
        theme_btn = self.create_button(
            sidebar,
            text="Toggle Theme",
            command=self.theme_manager.toggle_theme,
            width=200
        )
        theme_btn.pack(side="bottom", pady=20, padx=10)
    
    def _switch_view(self, view_class, **kwargs):
        """Switch main content view"""
        if self.current_view:
            self.current_view.destroy()
            
        self.current_view = view_class(
            self.main_content,
            theme_manager=self.theme_manager,
            **kwargs
        )
        self.current_view.pack(fill="both", expand=True)
        
    def _create_main_content(self):
        """Create main content area"""
        self.main_content = self.create_frame(
            self,
            corner_radius=0,
            border_width=0
        )
        self.main_content.grid(row=0, column=1, sticky="nsew", padx=0, pady=0)
        
        # Welcome message
        welcome = self.create_label(
            self.main_content,
            text="Welcome to File Organizer",
            font=("Helvetica", 24, "bold")
        )
        welcome.pack(pady=(100, 20))
        
        subtitle = self.create_label(
            self.main_content,
            text="Select an action from the sidebar to begin",
            font=("Helvetica", 14)
        )
        subtitle.pack()
    
    def update_theme(self):
        """Update window appearance based on theme"""
        theme = self._current_theme
        self.configure(fg_color=theme.get("background"))
        
        # Update all child widgets
        self._update_child_themes(self)
    
    def _update_child_themes(self, widget):
        """Recursively update theme for all child widgets"""
        for child in widget.winfo_children():
            if hasattr(child, "update_theme"):
                child.update_theme()
            self._update_child_themes(child)
    
    def _on_analyze_click(self):
        """Switch to file analysis view"""
        self._switch_view(FileAnalysisView)
    
    def _on_organize_click(self):
        """Switch to file organization view"""
        self._switch_view(FileOrganizationView, file_organizer=self.file_organizer)

    def _on_settings_click(self):
        """Open settings dialog"""
        if self.settings_manager:
            dialog = SettingsDialog(
                self,
                settings_manager=self.settings_manager,
                theme_manager=self.theme_manager
            )
