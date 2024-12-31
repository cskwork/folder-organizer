import customtkinter as ctk
from pathlib import Path
from typing import Callable, List, Optional
import tkinter as tk
from tkinterdnd2 import DND_FILES, TkinterDnD
from ..ui.base_component import BaseComponent

class DropZone(ctk.CTkFrame, BaseComponent):
    """Modern drag and drop zone"""
    
    def __init__(
        self,
        master,
        on_drop: Callable[[List[Path]], None],
        theme_manager=None,
        text: str = "Drag files here",
        **kwargs
    ):
        BaseComponent.__init__(self, theme_manager)
        kwargs = self._apply_theme_params('frame', kwargs)
        super().__init__(master, **kwargs)
        
        self.on_drop = on_drop
        self._setup_drop_zone(text)
        
        # Bind drag and drop events
        if isinstance(self.winfo_toplevel(), TkinterDnD.Tk):
            self.drop_target_register(DND_FILES)
            self.dnd_bind('<<Drop>>', self._on_drop)
            self.dnd_bind('<<DragEnter>>', self._on_drag_enter)
            self.dnd_bind('<<DragLeave>>', self._on_drag_leave)
    
    def _setup_drop_zone(self, text: str):
        """Setup drop zone appearance"""
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)
        
        # Create inner frame for visual feedback
        self.inner_frame = self.create_frame(
            self,
            corner_radius=8,
            border_width=2
        )
        self.inner_frame.grid(row=0, column=0, padx=10, pady=10, sticky="nsew")
        
        # Label
        self.label = self.create_label(
            self.inner_frame,
            text=text,
            font=("Helvetica", 12)
        )
        self.label.pack(expand=True, pady=20)
        
        # Icon
        self.icon_label = self.create_label(
            self.inner_frame,
            text="📥",
            font=("Segoe UI Emoji", 24)
        )
        self.icon_label.pack(expand=True)
    
    def _on_drop(self, event):
        """Handle file drop"""
        # Get dropped files
        files = event.data
        if isinstance(files, str):
            # Convert string of files to list
            if files.startswith("{") and files.endswith("}"):
                files = files[1:-1]  # Remove braces
            files = [Path(f) for f in files.split("} {")]
        else:
            files = [Path(files)]
        
        # Reset appearance
        self._reset_appearance()
        
        # Call callback
        self.on_drop(files)
    
    def _on_drag_enter(self, event):
        """Handle drag enter"""
        self.configure(
            fg_color=self._current_theme.get("hover"),
            border_color=self._current_theme.get("accent")
        )
        self.inner_frame.configure(
            border_color=self._current_theme.get("accent")
        )
        self.label.configure(
            text="Drop files here",
            text_color=self._current_theme.get("accent")
        )
    
    def _on_drag_leave(self, event):
        """Handle drag leave"""
        self._reset_appearance()
    
    def _reset_appearance(self):
        """Reset drop zone appearance"""
        self.configure(
            fg_color=self._current_theme.get("card"),
            border_color=self._current_theme.get("border")
        )
        self.inner_frame.configure(
            border_color=self._current_theme.get("border")
        )
        self.label.configure(
            text="Drag files here",
            text_color=self._current_theme.get("text")
        )
    
    def update_theme(self):
        """Update drop zone appearance based on theme"""
        self.configure(
            fg_color=self._current_theme.get("card"),
            border_color=self._current_theme.get("border")
        )
        self.inner_frame.configure(
            border_color=self._current_theme.get("border")
        )
        self._reset_appearance()
