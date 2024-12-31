import customtkinter as ctk
from pathlib import Path
from typing import Dict, List, Set, Optional
import threading
from tkinterdnd2 import DND_FILES
from ..ui.base_component import BaseComponent
from ..ui.file_card import FileCard
from ..ui.file_preview import FilePreview
from ..ui.drag_drop_handler import DropZone
from .rule_editor_dialog import RuleEditorDialog
from tkinter import filedialog, messagebox

class FileOrganizationView(ctk.CTkFrame, BaseComponent):
    """Modern view for file organization with rules support"""
    
    def __init__(self, master, theme_manager=None, file_organizer=None, **kwargs):
        BaseComponent.__init__(self, theme_manager)
        super().__init__(
            master,
            fg_color=self._current_theme.get("background"),
            **kwargs
        )
        
        self.file_organizer = file_organizer
        self.selected_files: Set[Path] = set()
        self.organization_results: Dict[Path, dict] = {}
        
        self._setup_grid()
        self._create_widgets()
        self._load_rules()
    
    def _setup_grid(self):
        """Configure grid layout"""
        self.grid_columnconfigure(0, weight=2)  # Files list
        self.grid_columnconfigure(1, weight=1)  # Preview/Rules
        self.grid_rowconfigure(1, weight=1)
    
    def _create_widgets(self):
        """Create view widgets"""
        # Header section
        header = self.create_frame(self, corner_radius=0, border_width=0)
        header.grid(row=0, column=0, columnspan=2, sticky="ew", padx=20, pady=(20, 0))
        
        title = self.create_label(
            header,
            text="File Organization",
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
        
        organize_btn = self.create_button(
            btn_frame,
            text="Organize Selected",
            command=self._organize_files
        )
        organize_btn.pack(side="left", padx=5)
        
        rules_btn = self.create_button(
            btn_frame,
            text="Manage Rules",
            command=self._show_rule_editor
        )
        rules_btn.pack(side="left", padx=5)
        
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
        
        # Right panel - Preview and Rules
        right_panel = self.create_frame(self, corner_radius=0, border_width=0)
        right_panel.grid(row=1, column=1, sticky="nsew", padx=20, pady=20)
        right_panel.grid_columnconfigure(0, weight=1)
        right_panel.grid_rowconfigure(1, weight=1)
        
        # Preview
        self.preview = FilePreview(
            right_panel,
            theme_manager=self.theme_manager
        )
        self.preview.grid(row=0, column=0, sticky="nsew", pady=(0, 10))
        
        # Rules list
        rules_frame = self.create_frame(
            right_panel,
            corner_radius=10,
            border_width=1,
            border_color=self._current_theme.get("border")
        )
        rules_frame.grid(row=1, column=0, sticky="nsew")
        rules_frame.grid_columnconfigure(0, weight=1)
        rules_frame.grid_rowconfigure(1, weight=1)
        
        rules_header = self.create_label(
            rules_frame,
            text="Organization Rules",
            font=("Helvetica", 14, "bold")
        )
        rules_header.grid(row=0, column=0, sticky="w", padx=10, pady=10)
        
        self.rules_list = ctk.CTkScrollableFrame(
            rules_frame,
            fg_color="transparent"
        )
        self.rules_list.grid(row=1, column=0, sticky="nsew", padx=10, pady=(0, 10))
        self.rules_list.grid_columnconfigure(0, weight=1)
    
    def _load_rules(self):
        """Load and display organization rules"""
        if not self.file_organizer or not hasattr(self.file_organizer, "rules_engine"):
            return
            
        # Clear current rules
        for widget in self.rules_list.winfo_children():
            widget.destroy()
            
        # Add rules
        for rule_info in self.file_organizer.rules_engine.get_rule_info():
            rule_frame = self.create_frame(
                self.rules_list,
                corner_radius=5,
                border_width=1,
                border_color=self._current_theme.get("border")
            )
            rule_frame.pack(fill="x", pady=2)
            
            # Rule name and description
            name = self.create_label(
                rule_frame,
                text=rule_info["name"],
                font=("Helvetica", 12, "bold")
            )
            name.pack(anchor="w", padx=10, pady=(5, 0))
            
            desc = self.create_label(
                rule_frame,
                text=rule_info["description"],
                font=("Helvetica", 10)
            )
            desc.pack(anchor="w", padx=10, pady=(0, 5))
            
            # Enable/disable checkbox
            enabled_var = ctk.BooleanVar(value=rule_info["enabled"])
            enabled_check = self.create_checkbox(
                rule_frame,
                text="Enabled",
                variable=enabled_var,
                command=lambda n=rule_info["name"], v=enabled_var:
                    self._toggle_rule(n, v.get())
            )
            enabled_check.pack(anchor="w", padx=10, pady=(0, 5))
    
    def _toggle_rule(self, rule_name: str, enabled: bool):
        """Toggle rule enabled state"""
        if self.file_organizer and hasattr(self.file_organizer, "rules_engine"):
            self.file_organizer.rules_engine.enable_rule(rule_name, enabled)
            self.file_organizer.rules_engine.save_rules()
    
    def _show_rule_editor(self, rule_data: Optional[Dict] = None):
        """Show rule editor dialog"""
        dialog = RuleEditorDialog(
            self,
            theme_manager=self.theme_manager,
            on_save=self._save_rule,
            rule_data=rule_data
        )
    
    def _save_rule(self, rule_data: Dict):
        """Save new or updated rule"""
        if not self.file_organizer or not hasattr(self.file_organizer, "rules_engine"):
            return
            
        try:
            # Create rule condition
            pattern_type = rule_data["pattern_type"]
            pattern = rule_data["pattern"]
            
            if pattern_type == "ext":
                pattern = "ext:" + pattern
            elif pattern_type == "mime":
                pattern = "mime:" + pattern
                
            condition = self.file_organizer.rules_engine._create_condition(pattern)
            
            # Create rule action
            action = self.file_organizer.rules_engine._get_action_function(
                rule_data["action"]
            )
            
            # Add rule
            self.file_organizer.rules_engine.add_rule(
                name=rule_data["name"],
                description=rule_data["description"],
                condition=condition,
                action=action,
                target_dir=Path(rule_data["target_dir"]),
                enabled=rule_data["enabled"]
            )
            
            # Save and reload rules
            self.file_organizer.rules_engine.save_rules()
            self._load_rules()
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to save rule: {e}")
    
    def _handle_dropped_files(self, files: List[Path]):
        """Handle dropped files"""
        self._add_files(files)
    
    def _select_files(self):
        """Open file selection dialog"""
        files = filedialog.askopenfilenames(
            title="Select Files to Organize",
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
    
    def _organize_files(self):
        """Organize selected files"""
        if not self.selected_files or not self.file_organizer:
            return
            
        # Get target directory
        target_dir = filedialog.askdirectory(
            title="Select Target Directory for Organized Files"
        )
        
        if not target_dir:
            return
            
        # Start organization in background thread
        threading.Thread(
            target=self._run_organization,
            args=(Path(target_dir),),
            daemon=True
        ).start()
    
    def _run_organization(self, target_dir: Path):
        """Run file organization in background"""
        try:
            for file_path in self.selected_files:
                try:
                    # Process file through rules
                    new_path = self.file_organizer.rules_engine.process_file(
                        file_path,
                        target_dir
                    )
                    
                    # Update UI in main thread
                    if new_path:
                        self.after(0, self._update_file_card, file_path, {
                            "status": "Organized",
                            "new_path": str(new_path)
                        })
                        
                except Exception as e:
                    print(f"Error organizing {file_path}: {e}")
                    self.after(0, self._update_file_card, file_path, {
                        "status": "Error",
                        "error": str(e)
                    })
                    
        except Exception as e:
            messagebox.showerror("Error", f"Organization failed: {e}")
    
    def _update_file_card(self, file_path: Path, result: dict):
        """Update file card with organization results"""
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
