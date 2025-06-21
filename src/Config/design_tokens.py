"""Design tokens and styling system for the Intelligent File Organizer."""

from typing import Dict, Any, Optional, Union
from dataclasses import dataclass
from enum import Enum


class ThemeMode(Enum):
    """Available theme modes."""
    LIGHT = "light"
    DARK = "dark"
    AUTO = "auto"


class ComponentSize(Enum):
    """Standard component sizes."""
    SMALL = "small"
    MEDIUM = "medium"
    LARGE = "large"
    EXTRA_LARGE = "xl"


@dataclass
class ColorPalette:
    """Color palette for a theme."""
    # Primary colors
    primary: str
    primary_hover: str
    primary_disabled: str
    
    # Secondary colors
    secondary: str
    secondary_hover: str
    secondary_disabled: str
    
    # Accent colors
    accent: str
    accent_hover: str
    
    # Status colors
    success: str
    warning: str
    error: str
    info: str
    
    # Neutral colors
    background: str
    surface: str
    border: str
    divider: str
    
    # Text colors
    text_primary: str
    text_secondary: str
    text_disabled: str
    text_on_primary: str
    text_on_accent: str


@dataclass
class Spacing:
    """Spacing scale for consistent layouts."""
    xs: int = 4
    sm: int = 8
    md: int = 16
    lg: int = 24
    xl: int = 32
    xxl: int = 48
    xxxl: int = 64


@dataclass
class Typography:
    """Typography definitions."""
    # Font families
    primary_font: str = "Segoe UI"
    secondary_font: str = "Arial"
    monospace_font: str = "Consolas"
    
    # Font sizes
    xs: int = 10
    sm: int = 12
    md: int = 14
    lg: int = 16
    xl: int = 20
    xxl: int = 24
    xxxl: int = 32
    
    # Font weights
    light: str = "300"
    normal: str = "400"
    medium: str = "500"
    semibold: str = "600"
    bold: str = "700"


@dataclass
class BorderRadius:
    """Border radius values."""
    none: int = 0
    sm: int = 4
    md: int = 8
    lg: int = 12
    xl: int = 16
    full: int = 9999


@dataclass
class Shadows:
    """Shadow definitions."""
    none: str = "none"
    sm: str = "0 1px 2px rgba(0, 0, 0, 0.05)"
    md: str = "0 4px 6px rgba(0, 0, 0, 0.1)"
    lg: str = "0 10px 15px rgba(0, 0, 0, 0.1)"
    xl: str = "0 20px 25px rgba(0, 0, 0, 0.1)"


@dataclass
class ComponentSizes:
    """Standard component dimensions."""
    button_height_sm: int = 32
    button_height_md: int = 38
    button_height_lg: int = 44
    
    input_height_sm: int = 32
    input_height_md: int = 38
    input_height_lg: int = 44
    
    icon_size_sm: int = 16
    icon_size_md: int = 20
    icon_size_lg: int = 24


class DesignTokens:
    """Central design tokens system."""
    
    # Light theme colors
    LIGHT_COLORS = ColorPalette(
        primary="#4A90E2",
        primary_hover="#3A7BD5",
        primary_disabled="#B3D1F2",
        
        secondary="#F5F7FA",
        secondary_hover="#E8ECF0",
        secondary_disabled="#F8F9FA",
        
        accent="#34C759",
        accent_hover="#2FAD4E",
        
        success="#10B981",
        warning="#F59E0B",
        error="#EF4444",
        info="#3B82F6",
        
        background="#FFFFFF",
        surface="#FAFBFC",
        border="#E1E8ED",
        divider="#F1F3F5",
        
        text_primary="#2C3E50",
        text_secondary="#64748B",
        text_disabled="#94A3B8",
        text_on_primary="#FFFFFF",
        text_on_accent="#FFFFFF"
    )
    
    # Dark theme colors
    DARK_COLORS = ColorPalette(
        primary="#5BA3F5",
        primary_hover="#4A90E2",
        primary_disabled="#3A5A7A",
        
        secondary="#2D3748",
        secondary_hover="#374151",
        secondary_disabled="#1F2937",
        
        accent="#48CC68",
        accent_hover="#34C759",
        
        success="#10B981",
        warning="#F59E0B",
        error="#EF4444",
        info="#3B82F6",
        
        background="#1A202C",
        surface="#2D3748",
        border="#4A5568",
        divider="#374151",
        
        text_primary="#F7FAFC",
        text_secondary="#E2E8F0",
        text_disabled="#A0AEC0",
        text_on_primary="#1A202C",
        text_on_accent="#1A202C"
    )
    
    def __init__(self, theme_mode: ThemeMode = ThemeMode.LIGHT):
        self.theme_mode = theme_mode
        self.spacing = Spacing()
        self.typography = Typography()
        self.border_radius = BorderRadius()
        self.shadows = Shadows()
        self.component_sizes = ComponentSizes()
        
    @property
    def colors(self) -> ColorPalette:
        """Get colors for current theme."""
        if self.theme_mode == ThemeMode.DARK:
            return self.DARK_COLORS
        return self.LIGHT_COLORS
    
    def get_component_style(self, component: str, variant: str = "default", size: ComponentSize = ComponentSize.MEDIUM) -> Dict[str, Any]:
        """Get complete style dictionary for a component."""
        styles = {
            "button": self._get_button_style(variant, size),
            "input": self._get_input_style(variant, size),
            "frame": self._get_frame_style(variant),
            "label": self._get_label_style(variant, size),
            "checkbox": self._get_checkbox_style(variant),
            "progressbar": self._get_progressbar_style(variant),
            "textbox": self._get_textbox_style(variant)
        }
        
        return styles.get(component, {})
    
    def _get_button_style(self, variant: str, size: ComponentSize) -> Dict[str, Any]:
        """Get button styling."""
        height_map = {
            ComponentSize.SMALL: self.component_sizes.button_height_sm,
            ComponentSize.MEDIUM: self.component_sizes.button_height_md,
            ComponentSize.LARGE: self.component_sizes.button_height_lg
        }
        
        base_style = {
            "height": height_map[size],
            "corner_radius": self.border_radius.md,
            "font": (self.typography.primary_font, self.typography.md),
            "border_width": 0
        }
        
        if variant == "primary":
            base_style.update({
                "fg_color": self.colors.primary,
                "hover_color": self.colors.primary_hover,
                "text_color": self.colors.text_on_primary
            })
        elif variant == "secondary":
            base_style.update({
                "fg_color": self.colors.secondary,
                "hover_color": self.colors.secondary_hover,
                "text_color": self.colors.text_primary,
                "border_width": 1,
                "border_color": self.colors.border
            })
        elif variant == "success":
            base_style.update({
                "fg_color": self.colors.success,
                "hover_color": self.colors.accent_hover,
                "text_color": self.colors.text_on_accent
            })
        elif variant == "error":
            base_style.update({
                "fg_color": self.colors.error,
                "hover_color": "#DC2626",
                "text_color": self.colors.text_on_primary
            })
        else:  # default
            base_style.update({
                "fg_color": self.colors.primary,
                "hover_color": self.colors.accent,
                "text_color": self.colors.text_on_primary
            })
        
        return base_style
    
    def _get_input_style(self, variant: str, size: ComponentSize) -> Dict[str, Any]:
        """Get input field styling."""
        height_map = {
            ComponentSize.SMALL: self.component_sizes.input_height_sm,
            ComponentSize.MEDIUM: self.component_sizes.input_height_md,
            ComponentSize.LARGE: self.component_sizes.input_height_lg
        }
        
        return {
            "height": height_map[size],
            "corner_radius": self.border_radius.md,
            "border_width": 1,
            "border_color": self.colors.border,
            "fg_color": self.colors.background,
            "text_color": self.colors.text_primary,
            "font": (self.typography.primary_font, self.typography.md)
        }
    
    def _get_frame_style(self, variant: str) -> Dict[str, Any]:
        """Get frame styling."""
        base_style = {
            "corner_radius": self.border_radius.lg,
            "border_width": 1,
            "border_color": self.colors.border
        }
        
        if variant == "card":
            base_style.update({
                "fg_color": self.colors.background,
                "corner_radius": self.border_radius.md
            })
        elif variant == "surface":
            base_style.update({
                "fg_color": self.colors.surface,
                "border_width": 0
            })
        else:  # default
            base_style.update({
                "fg_color": self.colors.background
            })
        
        return base_style
    
    def _get_label_style(self, variant: str, size: ComponentSize) -> Dict[str, Any]:
        """Get label styling."""
        font_size_map = {
            ComponentSize.SMALL: self.typography.sm,
            ComponentSize.MEDIUM: self.typography.md,
            ComponentSize.LARGE: self.typography.lg
        }
        
        base_style = {
            "font": (self.typography.primary_font, font_size_map[size]),
            "text_color": self.colors.text_primary
        }
        
        if variant == "heading":
            base_style.update({
                "font": (self.typography.primary_font, font_size_map[size], "bold"),
                "text_color": self.colors.text_primary
            })
        elif variant == "secondary":
            base_style.update({
                "text_color": self.colors.text_secondary
            })
        elif variant == "disabled":
            base_style.update({
                "text_color": self.colors.text_disabled
            })
        
        return base_style
    
    def _get_checkbox_style(self, variant: str) -> Dict[str, Any]:
        """Get checkbox styling."""
        return {
            "corner_radius": self.border_radius.sm,
            "border_width": 2,
            "border_color": self.colors.border,
            "checkmark_color": self.colors.primary,
            "hover_color": self.colors.accent,
            "text_color": self.colors.text_primary,
            "font": (self.typography.primary_font, self.typography.md)
        }
    
    def _get_progressbar_style(self, variant: str) -> Dict[str, Any]:
        """Get progress bar styling."""
        return {
            "height": 8,
            "corner_radius": self.border_radius.sm,
            "progress_color": self.colors.accent,
            "fg_color": self.colors.border
        }
    
    def _get_textbox_style(self, variant: str) -> Dict[str, Any]:
        """Get textbox styling."""
        return {
            "corner_radius": self.border_radius.md,
            "border_width": 1,
            "border_color": self.colors.border,
            "fg_color": self.colors.background,
            "text_color": self.colors.text_primary,
            "font": (self.typography.primary_font, self.typography.sm)
        }
    
    def set_theme(self, theme_mode: ThemeMode) -> None:
        """Change the current theme."""
        self.theme_mode = theme_mode
    
    def get_layout_padding(self, level: str = "normal") -> int:
        """Get consistent padding values."""
        padding_map = {
            "tight": self.spacing.sm,
            "normal": self.spacing.md,
            "relaxed": self.spacing.lg,
            "loose": self.spacing.xl
        }
        return padding_map.get(level, self.spacing.md)
    
    def get_grid_gap(self, level: str = "normal") -> int:
        """Get consistent grid gap values."""
        gap_map = {
            "tight": self.spacing.xs,
            "normal": self.spacing.sm,
            "relaxed": self.spacing.md,
            "loose": self.spacing.lg
        }
        return gap_map.get(level, self.spacing.sm)


# Global design tokens instance
design_tokens = DesignTokens()


def get_component_style(component: str, variant: str = "default", size: ComponentSize = ComponentSize.MEDIUM) -> Dict[str, Any]:
    """Convenient function to get component styles."""
    return design_tokens.get_component_style(component, variant, size)


def get_colors() -> ColorPalette:
    """Convenient function to get current theme colors."""
    return design_tokens.colors


def get_spacing() -> Spacing:
    """Convenient function to get spacing values."""
    return design_tokens.spacing


def get_typography() -> Typography:
    """Convenient function to get typography values."""
    return design_tokens.typography