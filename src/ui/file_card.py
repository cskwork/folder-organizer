import customtkinter as ctk
from pathlib import Path
from ..ui.base_component import BaseComponent
import os
from datetime import datetime
from typing import Optional, Dict, Any

class FileCard(ctk.CTkFrame, BaseComponent):
    """A modern card component for displaying file information"""
    
    def __init__(
        self,
        master,
        file_path: Path,
        file_info: Dict[str, Any],
        theme_manager=None,
        on_select=None,
        **kwargs
    ):
        BaseComponent.__init__(self, theme_manager)
        kwargs = self._apply_theme_params('frame', kwargs)
        super().__init__(master, **kwargs)
        
        self.file_path = file_path
        self.file_info = file_info
        self.on_select = on_select
        self.selected = False
        
        self._create_widgets()
        self.bind("<Button-1>", self._toggle_select)
        
    def _create_widgets(self):
        """Create card widgets"""
        self.grid_columnconfigure(1, weight=1)
        
        # File icon (placeholder for now)
        icon_label = self.create_label(
            self,
            text="📄",
            font=("Segoe UI Emoji", 24)
        )
        icon_label.grid(row=0, column=0, rowspan=2, padx=(15, 10), pady=15)
        
        # File name
        name_label = self.create_label(
            self,
            text=self.file_path.name,
            font=("Helvetica", 12, "bold"),
            anchor="w"
        )
        name_label.grid(row=0, column=1, sticky="w", padx=(0, 15), pady=(15, 0))
        
        # File details
        details = self._format_file_details()
        details_label = self.create_label(
            self,
            text=details,
            font=("Helvetica", 10),
            anchor="w"
        )
        details_label.grid(row=1, column=1, sticky="w", padx=(0, 15), pady=(0, 15))
        
        # Suggested name (if available)
        if suggested_name := self.file_info.get("suggested_name"):
            suggested_frame = self.create_frame(self)
            suggested_frame.grid(row=2, column=0, columnspan=2, sticky="ew", padx=15, pady=(0, 15))
            
            suggested_label = self.create_label(
                suggested_frame,
                text=f"Suggested: {suggested_name}",
                font=("Helvetica", 10, "italic"),
                text_color=self._current_theme.get("accent")
            )
            suggested_label.pack(anchor="w")
    
    def _format_file_details(self) -> str:
        """Format file details for display"""
        size = self._format_size(self.file_path.stat().st_size)
        modified = datetime.fromtimestamp(self.file_path.stat().st_mtime)
        modified_str = modified.strftime("%Y-%m-%d %H:%M")
        
        details = []
        if type_info := self.file_info.get("type"):
            details.append(f"Type: {type_info}")
        details.extend([
            f"Size: {size}",
            f"Modified: {modified_str}"
        ])
        
        if confidence := self.file_info.get("confidence"):
            details.append(f"Confidence: {confidence:.0%}")
            
        return " | ".join(details)
    
    def _format_size(self, size_bytes: int) -> str:
        """Format file size in human-readable format"""
        for unit in ['B', 'KB', 'MB', 'GB']:
            if size_bytes < 1024:
                return f"{size_bytes:.1f} {unit}"
            size_bytes /= 1024
        return f"{size_bytes:.1f} TB"
    
    def _toggle_select(self, event=None):
        """Toggle card selection"""
        self.selected = not self.selected
        self._update_selection_state()
        
        if self.on_select:
            self.on_select(self.file_path, self.selected)
    
    def _update_selection_state(self):
        """Update card appearance based on selection state"""
        if self.selected:
            self.configure(
                fg_color=self._current_theme.get("primary"),
                border_color=self._current_theme.get("accent")
            )
            for child in self.winfo_children():
                if isinstance(child, ctk.CTkLabel):
                    child.configure(text_color=self._current_theme.get("background"))
        else:
            self.configure(
                fg_color=self._current_theme.get("card"),
                border_color=self._current_theme.get("border")
            )
            for child in self.winfo_children():
                if isinstance(child, ctk.CTkLabel):
                    child.configure(text_color=self._current_theme.get("text"))
    
    def update_theme(self):
        """Update card appearance based on theme"""
        self.configure(
            fg_color=self._current_theme.get("card"),
            border_color=self._current_theme.get("border")
        )
        self._update_selection_state()
