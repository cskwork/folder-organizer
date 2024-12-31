import json
from pathlib import Path
import customtkinter as ctk
from typing import Dict, Any

class ThemeManager:
    """Manages application themes and appearance settings"""
    
    def __init__(self, config_manager=None):
        self.config_manager = config_manager
        self._current_theme = "light"
        self._observers = []
        
        # Default themes
        self.themes = {
            "light": {
                "primary": "#4A90E2",
                "secondary": "#F5F7FA",
                "accent": "#34C759",
                "text": "#2C3E50",
                "border": "#E1E8ED",
                "background": "#FFFFFF",
                "card": "#F8F9FA",
                "hover": "#EDF2F7",
                "success": "#34C759",
                "warning": "#FF9500",
                "error": "#FF3B30"
            },
            "dark": {
                "primary": "#5E9CEA",
                "secondary": "#1A1D21",
                "accent": "#34C759",
                "text": "#E4E6EB",
                "border": "#2C3038",
                "background": "#17181C",
                "card": "#1E2024",
                "hover": "#25272C",
                "success": "#32D74B",
                "warning": "#FF9F0A",
                "error": "#FF453A"
            }
        }
        
        self.load_themes()
        
    def load_themes(self):
        """Load themes from config"""
        if self.config_manager:
            saved_themes = self.config_manager.get_setting("themes", {})
            self.themes.update(saved_themes)
            self._current_theme = self.config_manager.get_setting("current_theme", "light")
    
    def get_current_theme(self) -> Dict[str, str]:
        """Get current theme colors"""
        return self.themes[self._current_theme]
    
    def get_color(self, color_name: str) -> str:
        """Get specific color from current theme"""
        return self.themes[self._current_theme].get(color_name)
    
    def toggle_theme(self):
        """Toggle between light and dark themes"""
        self._current_theme = "dark" if self._current_theme == "light" else "light"
        self._apply_theme()
        
        if self.config_manager:
            self.config_manager.update_setting("current_theme", self._current_theme)
    
    def _apply_theme(self):
        """Apply current theme to application"""
        theme = self.get_current_theme()
        
        # Set CustomTkinter appearance mode
        ctk.set_appearance_mode("dark" if self._current_theme == "dark" else "light")
        
        # Notify observers of theme change
        for observer in self._observers:
            if hasattr(observer, 'on_theme_changed'):
                observer.on_theme_changed(theme)
    
    def add_observer(self, observer):
        """Add observer for theme changes"""
        if observer not in self._observers:
            self._observers.append(observer)
    
    def remove_observer(self, observer):
        """Remove observer"""
        if observer in self._observers:
            self._observers.remove(observer)

    def set_theme(self, theme_name: str):
        """Set specific theme by name"""
        if theme_name in self.themes:
            self._current_theme = theme_name
            self._apply_theme()
            
            if self.config_manager:
                self.config_manager.update_setting("current_theme", self._current_theme)
        else:
            raise ValueError(f"Theme '{theme_name}' not found. Available themes: {list(self.themes.keys())}")
