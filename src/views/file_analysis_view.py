import customtkinter as ctk
from pathlib import Path
from typing import Dict, List, Set
import threading
from tkinterdnd2 import DND_FILES, TkinterDnD
from ..ui.base_component import BaseComponent
from ..ui.file_card import FileCard
from ..ui.file_preview import FilePreview
from ..ui.drag_drop_handler import DropZone
from tkinter import filedialog

class FileAnalysisView(ctk.CTkFrame, BaseComponent):
    """Modern view for file analysis"""
    
    def __init__(self, master, theme_manager=None, file_analyzer=None, **kwargs):
        BaseComponent.__init__(self, theme_manager)
        kwargs = self._apply_theme_params('frame', kwargs)
        kwargs['fg_color'] = self._current_theme.get("background")  # Override for view background
        super().__init__(master, **kwargs)
        
        self.file_analyzer = file_analyzer
        self.selected_files: Set[Path] = set()
        self.analysis_results: Dict[Path, dict] = {}
        
        self._setup_grid()
        self._create_widgets()
    
    def _setup_grid(self):
        """Configure grid layout"""
        self.grid_columnconfigure(0, weight=2)  # Files list
        self.grid_columnconfigure(1, weight=1)  # Preview
        self.grid_rowconfigure(1, weight=1)
    
    def _create_widgets(self):
        """Create view widgets"""
        # Header section
        header = self.create_frame(self, corner_radius=0, border_width=0)
        header.grid(row=0, column=0, columnspan=2, sticky="ew", padx=20, pady=(20, 0))
        
        title = self.create_label(
            header,
            text="File Analysis",
            font=("Helvetica", 24, "bold")
        )
        title.pack(side="left")
        
        # Action buttons
        btn_frame = self.create_frame(header, corner_radius=0, border_width=0)
        btn_frame.pack(side="right")
        
        select_btn = self.create_button(
            btn_frame,
            text="Select Files",
            command=self._select_files
        )
        select_btn.pack(side="left", padx=5)
        
        analyze_btn = self.create_button(
            btn_frame,
            text="Analyze Selected",
            command=self._analyze_files
        )
        analyze_btn.pack(side="left", padx=5)
        
        # Left panel - Files list and drop zone
        left_panel = self.create_frame(self, corner_radius=0, border_width=0)
        left_panel.grid(row=1, column=0, sticky="nsew", padx=20, pady=20)
        left_panel.grid_columnconfigure(0, weight=1)
        left_panel.grid_rowconfigure(1, weight=1)
        
        # Drop zone
        self.drop_zone = DropZone(
            left_panel,
            on_drop=self._handle_dropped_files,
            theme_manager=self.theme_manager,
            height=100
        )
        self.drop_zone.grid(row=0, column=0, sticky="ew", pady=(0, 10))
        
        # Files list
        self.content_frame = ctk.CTkScrollableFrame(
            left_panel,
            fg_color="transparent"
        )
        self.content_frame.grid(row=1, column=0, sticky="nsew")
        self.content_frame.grid_columnconfigure(0, weight=1)
        
        # Right panel - Preview
        right_panel = self.create_frame(self, corner_radius=0, border_width=0)
        right_panel.grid(row=1, column=1, sticky="nsew", padx=20, pady=20)
        right_panel.grid_columnconfigure(0, weight=1)
        right_panel.grid_rowconfigure(0, weight=1)
        
        self.preview = FilePreview(
            right_panel,
            theme_manager=self.theme_manager
        )
        self.preview.grid(row=0, column=0, sticky="nsew")
    
    def _handle_dropped_files(self, files: List[Path]):
        """Handle dropped files"""
        self._add_files(files)
    
    def _select_files(self):
        """Open file selection dialog"""
        files = filedialog.askopenfilenames(
            title="Select Files to Analyze",
            filetypes=[("All Files", "*.*")]
        )
        
        if not files:
            return
            
        self._add_files([Path(f) for f in files])
    
    def _add_files(self, files: List[Path]):
        """Add files to the view"""
        # Clear previous content
        for widget in self.content_frame.winfo_children():
            widget.destroy()
        
        # Create cards for files
        for file_path in files:
            card = FileCard(
                self.content_frame,
                file_path,
                {"type": file_path.suffix[1:].upper() if file_path.suffix else "Unknown"},
                self.theme_manager,
                on_select=self._on_file_select
            )
            card.pack(fill="x", pady=5)
            
            # Bind click for preview
            card.bind("<Button-1>", lambda e, p=file_path: self._show_preview(p))
    
    def _on_file_select(self, file_path: Path, selected: bool):
        """Handle file selection"""
        if selected:
            self.selected_files.add(file_path)
        else:
            self.selected_files.discard(file_path)
    
    def _show_preview(self, file_path: Path):
        """Show file preview"""
        self.preview.show_preview(file_path)
    
    def _analyze_files(self):
        """Analyze selected files"""
        if not self.selected_files or not self.file_analyzer:
            return
            
        # Start analysis in background thread
        threading.Thread(
            target=self._run_analysis,
            daemon=True
        ).start()
    
    def _run_analysis(self):
        """Run file analysis in background"""
        for file_path in self.selected_files:
            try:
                # Analyze file
                result = self.file_analyzer.analyze_file(file_path)
                self.analysis_results[file_path] = result
                
                # Update UI in main thread
                self.after(0, self._update_file_card, file_path, result)
                
            except Exception as e:
                print(f"Error analyzing {file_path}: {e}")
    
    def _update_file_card(self, file_path: Path, result: dict):
        """Update file card with analysis results"""
        for widget in self.content_frame.winfo_children():
            if isinstance(widget, FileCard) and widget.file_path == file_path:
                widget.file_info.update(result)
                widget._create_widgets()  # Recreate widgets with new info
                break
    
    def update_theme(self):
        """Update view appearance based on theme"""
        self.configure(fg_color=self._current_theme.get("background"))
        
        # Update all child widgets
        for widget in self.winfo_children():
            if hasattr(widget, "update_theme"):
                widget.update_theme()
