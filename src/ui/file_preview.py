import customtkinter as ctk
from pathlib import Path
from typing import Optional, Dict, Any
import mimetypes
from PIL import Image, ImageTk
import magic
import os
from ..ui.base_component import BaseComponent

class FilePreview(ctk.CTkFrame, BaseComponent):
    """Modern file preview component"""
    
    def __init__(
        self,
        master,
        file_path: Optional[Path] = None,
        theme_manager=None,
        max_preview_size: int = 4096,  # Max bytes for text preview
        **kwargs
    ):
        BaseComponent.__init__(self, theme_manager)
        kwargs = self._apply_theme_params('frame', kwargs)
        super().__init__(master, **kwargs)
        
        self.max_preview_size = max_preview_size
        self.current_file: Optional[Path] = None
        self.preview_widgets = []
        
        self._setup_grid()
        self._create_widgets()
        
        if file_path:
            self.show_preview(file_path)
    
    def _setup_grid(self):
        """Configure grid layout"""
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)
    
    def _create_widgets(self):
        """Create preview widgets"""
        # Header with file info
        self.header = self.create_frame(self, corner_radius=0, border_width=0)
        self.header.grid(row=0, column=0, sticky="ew", padx=10, pady=10)
        
        self.file_name = self.create_label(
            self.header,
            text="No file selected",
            font=("Helvetica", 12, "bold")
        )
        self.file_name.pack(anchor="w")
        
        self.file_info = self.create_label(
            self.header,
            text="",
            font=("Helvetica", 10)
        )
        self.file_info.pack(anchor="w")
        
        # Preview area
        self.preview_area = self.create_frame(
            self,
            corner_radius=0,
            border_width=0
        )
        self.preview_area.grid(row=1, column=0, sticky="nsew", padx=10, pady=(0, 10))
        
        # Default message
        self.default_message = self.create_label(
            self.preview_area,
            text="Select a file to preview",
            font=("Helvetica", 12)
        )
        self.default_message.pack(expand=True)
    
    def show_preview(self, file_path: Path):
        """Show preview for the given file"""
        if not file_path.exists():
            return
        
        self.current_file = file_path
        
        # Update file info
        self.file_name.configure(text=file_path.name)
        size = self._format_size(file_path.stat().st_size)
        mime_type = magic.from_file(str(file_path), mime=True)
        self.file_info.configure(text=f"Type: {mime_type} | Size: {size}")
        
        # Clear previous preview
        self._clear_preview()
        
        try:
            # Handle different file types
            if self._is_image(file_path):
                self._show_image_preview(file_path)
            elif self._is_text(file_path):
                self._show_text_preview(file_path)
            else:
                self._show_generic_preview(file_path)
                
        except Exception as e:
            self._show_error(str(e))
    
    def _clear_preview(self):
        """Clear current preview"""
        self.default_message.pack_forget()
        for widget in self.preview_widgets:
            widget.destroy()
        self.preview_widgets = []
    
    def _show_image_preview(self, file_path: Path):
        """Show image preview"""
        try:
            # Open and resize image
            image = Image.open(file_path)
            
            # Calculate new size while maintaining aspect ratio
            max_size = (300, 300)
            image.thumbnail(max_size, Image.Resampling.LANCZOS)
            
            # Convert to PhotoImage
            photo = ImageTk.PhotoImage(image)
            
            # Create and pack label
            label = ctk.CTkLabel(self.preview_area, image=photo, text="")
            label.image = photo  # Keep reference
            label.pack(expand=True, pady=10)
            
            self.preview_widgets.append(label)
            
        except Exception as e:
            self._show_error(f"Error loading image: {e}")
    
    def _show_text_preview(self, file_path: Path):
        """Show text preview"""
        try:
            # Read file content
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read(self.max_preview_size)
            
            # Create text widget
            text = ctk.CTkTextbox(
                self.preview_area,
                wrap="word",
                fg_color=self._current_theme.get("background"),
                text_color=self._current_theme.get("text"),
                border_color=self._current_theme.get("border"),
                border_width=1
            )
            text.pack(fill="both", expand=True, pady=10)
            
            # Insert content
            text.insert("1.0", content)
            if file_path.stat().st_size > self.max_preview_size:
                text.insert("end", "\n\n[File truncated...]")
            
            text.configure(state="disabled")
            self.preview_widgets.append(text)
            
        except UnicodeDecodeError:
            self._show_error("Unable to preview binary file")
        except Exception as e:
            self._show_error(f"Error loading text: {e}")
    
    def _show_generic_preview(self, file_path: Path):
        """Show generic file info"""
        info = [
            f"File: {file_path.name}",
            f"Type: {magic.from_file(str(file_path), mime=True)}",
            f"Size: {self._format_size(file_path.stat().st_size)}",
            f"Created: {self._format_time(file_path.stat().st_ctime)}",
            f"Modified: {self._format_time(file_path.stat().st_mtime)}"
        ]
        
        label = self.create_label(
            self.preview_area,
            text="\n".join(info),
            font=("Helvetica", 11)
        )
        label.pack(expand=True)
        self.preview_widgets.append(label)
    
    def _show_error(self, message: str):
        """Show error message"""
        label = self.create_label(
            self.preview_area,
            text=f"Error: {message}",
            text_color="red"
        )
        label.pack(expand=True)
        self.preview_widgets.append(label)
    
    def _is_image(self, file_path: Path) -> bool:
        """Check if file is an image"""
        mime_type = magic.from_file(str(file_path), mime=True)
        return mime_type.startswith('image/')
    
    def _is_text(self, file_path: Path) -> bool:
        """Check if file is text"""
        mime_type = magic.from_file(str(file_path), mime=True)
        return (mime_type.startswith('text/') or
                mime_type in ['application/json', 'application/xml'])
    
    def _format_size(self, size_bytes: int) -> str:
        """Format file size in human-readable format"""
        for unit in ['B', 'KB', 'MB', 'GB']:
            if size_bytes < 1024:
                return f"{size_bytes:.1f} {unit}"
            size_bytes /= 1024
        return f"{size_bytes:.1f} TB"
    
    def _format_time(self, timestamp: float) -> str:
        """Format timestamp"""
        from datetime import datetime
        dt = datetime.fromtimestamp(timestamp)
        return dt.strftime("%Y-%m-%d %H:%M:%S")
    
    def update_theme(self):
        """Update preview appearance based on theme"""
        self.configure(
            fg_color=self._current_theme.get("card"),
            border_color=self._current_theme.get("border")
        )
        
        # Update text preview if present
        for widget in self.preview_widgets:
            if isinstance(widget, ctk.CTkTextbox):
                widget.configure(
                    fg_color=self._current_theme.get("background"),
                    text_color=self._current_theme.get("text"),
                    border_color=self._current_theme.get("border")
                )
