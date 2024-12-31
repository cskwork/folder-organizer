import customtkinter as ctk
from typing import Optional, Dict, Any
import logging

logger = logging.getLogger(__name__)

class BaseComponent:
    """Base class for UI components with theme support"""
    
    def __init__(self, theme_manager=None):
        self.theme_manager = theme_manager
        self._current_theme = {}
        
        if theme_manager:
            self._current_theme = theme_manager.get_current_theme()
            theme_manager.add_observer(self)
            logger.debug(f"Initialized BaseComponent with theme: {self._current_theme}")

    def on_theme_changed(self, theme: Dict[str, str]):
        """Handle theme changes"""
        logger.debug(f"Theme changed to: {theme}")
        self._current_theme = theme
        self.update_theme()
    
    def update_theme(self):
        """Update component appearance based on theme"""
        pass  # To be implemented by subclasses
    
    def _apply_theme_params(self, widget_type: str, kwargs: dict) -> dict:
        """Apply theme parameters to kwargs if not already present"""
        logger.debug(f"Applying theme params for {widget_type}")
        theme_params = {
            'fg_color': self._current_theme.get('background'),
            'bg_color': self._current_theme.get('background')
        }

        # Widget-specific supported parameters
        supported_params = {
            'label': ['text', 'fg_color', 'bg_color', 'text_color', 'font', 'anchor'],
            'button': ['text', 'fg_color', 'bg_color', 'text_color', 'hover_color', 'border_color', 'border_width', 'font', 'command', 'anchor', 'width', 'height', 'corner_radius'],
            'frame': ['fg_color', 'bg_color', 'border_color', 'border_width', 'corner_radius', 'width', 'height'],
            'entry': ['fg_color', 'bg_color', 'text_color', 'border_color', 'border_width', 'font', 'width', 'height', 'corner_radius'],
            'progressbar': ['fg_color', 'bg_color', 'progress_color', 'width', 'height', 'corner_radius'],
            'checkbox': ['text', 'fg_color', 'bg_color', 'text_color', 'font', 'anchor']
        }

        # Get widget-specific theme parameters
        widget_params = {
            'frame': {
                'border_color': self._current_theme.get('border'),
                'border_width': 1
            },
            'button': {
                'border_color': self._current_theme.get('border'),
                'border_width': 1,
                'text_color': self._current_theme.get('text')
            },
            'label': {
                'text_color': self._current_theme.get('text')
            },
            'entry': {
                'border_color': self._current_theme.get('border'),
                'border_width': 1,
                'text_color': self._current_theme.get('text')
            },
            'checkbox': {
                'text_color': self._current_theme.get('text')
            }
        }

        if widget_type in widget_params:
            theme_params.update(widget_params[widget_type])

        # Only apply supported theme params if not already in kwargs
        widget_supported_params = supported_params.get(widget_type, [])
        filtered_kwargs = {}
        
        # First copy existing kwargs that are supported
        for key, value in kwargs.items():
            if key in widget_supported_params:
                filtered_kwargs[key] = value
            else:
                logger.debug(f"Skipping unsupported parameter '{key}' for {widget_type}")
        
        # Then apply theme params that are supported and not already set
        for key, value in theme_params.items():
            if key in widget_supported_params and key not in filtered_kwargs:
                filtered_kwargs[key] = value

        logger.debug(f"Applied theme params for {widget_type}: {filtered_kwargs}")
        return filtered_kwargs

    def create_button(self, parent, text: str, command=None, style="primary", **kwargs) -> ctk.CTkButton:
        """Create a themed button"""
        logger.debug(f"Creating button with text: {text}, style: {style}")
        
        # Set colors based on style
        if style == "secondary":
            fg_color = self._current_theme.get("border")
            hover_color = self._current_theme.get("hover")
        else:
            fg_color = self._current_theme.get("accent")
            hover_color = self._current_theme.get("accent_hover")

        kwargs.update({
            'text': text,
            'command': command,
            'fg_color': fg_color,
            'hover_color': hover_color
        })
        
        kwargs = self._apply_theme_params('button', kwargs)
        logger.debug(f"Button kwargs: {kwargs}")
        return ctk.CTkButton(parent, **kwargs)

    def create_frame(self, parent, **kwargs) -> ctk.CTkFrame:
        """Create a themed frame"""
        logger.debug(f"Creating frame with kwargs before theme: {kwargs}")
        kwargs = self._apply_theme_params('frame', kwargs)
        logger.debug(f"Creating frame with kwargs after theme: {kwargs}")
        return ctk.CTkFrame(parent, **kwargs)

    def create_label(self, parent, text: str, **kwargs) -> ctk.CTkLabel:
        """Create a themed label"""
        logger.debug(f"Creating label with text: {text}")
        kwargs.update({'text': text})
        kwargs = self._apply_theme_params('label', kwargs)
        logger.debug(f"Label kwargs: {kwargs}")
        return ctk.CTkLabel(parent, **kwargs)

    def create_entry(self, parent, **kwargs) -> ctk.CTkEntry:
        """Create a themed entry"""
        logger.debug(f"Creating entry")
        kwargs = self._apply_theme_params('entry', kwargs)
        logger.debug(f"Entry kwargs: {kwargs}")
        return ctk.CTkEntry(parent, **kwargs)

    def create_progressbar(self, parent, **kwargs) -> ctk.CTkProgressBar:
        """Create a themed progress bar"""
        logger.debug(f"Creating progress bar")
        kwargs = self._apply_theme_params('progressbar', kwargs)
        logger.debug(f"Progress bar kwargs: {kwargs}")
        return ctk.CTkProgressBar(parent, **kwargs)

    def create_checkbox(self, parent, text: str, **kwargs) -> ctk.CTkCheckBox:
        """Create a themed checkbox"""
        logger.debug(f"Creating checkbox with text: {text}")
        kwargs.update({'text': text})
        kwargs = self._apply_theme_params('checkbox', kwargs)
        logger.debug(f"Checkbox kwargs: {kwargs}")
        return ctk.CTkCheckBox(parent, **kwargs)
