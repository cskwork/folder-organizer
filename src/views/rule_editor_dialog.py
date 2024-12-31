import customtkinter as ctk
from pathlib import Path
from typing import Optional, Dict, Any, Callable
from tkinter import filedialog
from ..ui.base_component import BaseComponent

class RuleEditorDialog(ctk.CTkToplevel, BaseComponent):
    """Dialog for editing file organization rules"""
    
    def __init__(
        self,
        master,
        theme_manager=None,
        on_save: Optional[Callable[[Dict[str, Any]], None]] = None,
        rule_data: Optional[Dict[str, Any]] = None
    ):
        BaseComponent.__init__(self, theme_manager)
        super().__init__(master)
        
        self.on_save = on_save
        self.rule_data = rule_data or {}
        
        # Configure window
        self.title("Edit Rule")
        self.geometry("600x500")
        self._setup_grid()
        self._create_widgets()
        
        # Make dialog modal
        self.transient(master)
        self.grab_set()
        
        # Center dialog
        self.update_idletasks()
        width = self.winfo_width()
        height = self.winfo_height()
        x = (self.winfo_screenwidth() // 2) - (width // 2)
        y = (self.winfo_screenheight() // 2) - (height // 2)
        self.geometry(f"{width}x{height}+{x}+{y}")
    
    def _setup_grid(self):
        """Configure grid layout"""
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(4, weight=1)
    
    def _create_widgets(self):
        """Create dialog widgets"""
        # Rule name
        name_frame = self.create_frame(self, corner_radius=0)
        name_frame.grid(row=0, column=0, sticky="ew", padx=20, pady=(20, 10))
        
        name_label = self.create_label(
            name_frame,
            text="Rule Name:",
            font=("Helvetica", 12)
        )
        name_label.pack(side="left")
        
        self.name_entry = self.create_entry(
            name_frame,
            placeholder_text="Enter rule name",
            width=300
        )
        self.name_entry.pack(side="right")
        self.name_entry.insert(0, self.rule_data.get("name", ""))
        
        # Rule description
        desc_frame = self.create_frame(self, corner_radius=0)
        desc_frame.grid(row=1, column=0, sticky="ew", padx=20, pady=10)
        
        desc_label = self.create_label(
            desc_frame,
            text="Description:",
            font=("Helvetica", 12)
        )
        desc_label.pack(side="left")
        
        self.desc_entry = self.create_entry(
            desc_frame,
            placeholder_text="Enter rule description",
            width=300
        )
        self.desc_entry.pack(side="right")
        self.desc_entry.insert(0, self.rule_data.get("description", ""))
        
        # Pattern
        pattern_frame = self.create_frame(self, corner_radius=0)
        pattern_frame.grid(row=2, column=0, sticky="ew", padx=20, pady=10)
        
        pattern_label = self.create_label(
            pattern_frame,
            text="Pattern:",
            font=("Helvetica", 12)
        )
        pattern_label.pack(side="left")
        
        self.pattern_type = ctk.StringVar(value=self.rule_data.get("pattern_type", "ext"))
        
        pattern_type_frame = self.create_frame(pattern_frame, corner_radius=0)
        pattern_type_frame.pack(side="right")
        
        ext_radio = self.create_radio_button(
            pattern_type_frame,
            text="Extension",
            variable=self.pattern_type,
            value="ext"
        )
        ext_radio.pack(side="left", padx=5)
        
        mime_radio = self.create_radio_button(
            pattern_type_frame,
            text="MIME Type",
            variable=self.pattern_type,
            value="mime"
        )
        mime_radio.pack(side="left", padx=5)
        
        regex_radio = self.create_radio_button(
            pattern_type_frame,
            text="Regex",
            variable=self.pattern_type,
            value="regex"
        )
        regex_radio.pack(side="left", padx=5)
        
        # Pattern input
        self.pattern_entry = self.create_entry(
            self,
            placeholder_text="Enter pattern (e.g., .pdf,.doc for extensions)",
            width=560
        )
        self.pattern_entry.grid(row=3, column=0, sticky="ew", padx=20, pady=10)
        self.pattern_entry.insert(0, self.rule_data.get("pattern", ""))
        
        # Action
        action_frame = self.create_frame(self, corner_radius=0)
        action_frame.grid(row=4, column=0, sticky="ew", padx=20, pady=10)
        
        action_label = self.create_label(
            action_frame,
            text="Action:",
            font=("Helvetica", 12)
        )
        action_label.pack(side="left")
        
        self.action_var = ctk.StringVar(value=self.rule_data.get("action", "by_type"))
        
        actions = [
            ("By Type", "by_type"),
            ("By Date", "by_date"),
            ("By Language", "by_language")
        ]
        
        for text, value in actions:
            radio = self.create_radio_button(
                action_frame,
                text=text,
                variable=self.action_var,
                value=value
            )
            radio.pack(side="left", padx=5)
        
        # Target directory
        target_frame = self.create_frame(self, corner_radius=0)
        target_frame.grid(row=5, column=0, sticky="ew", padx=20, pady=10)
        
        target_label = self.create_label(
            target_frame,
            text="Target Directory:",
            font=("Helvetica", 12)
        )
        target_label.pack(side="left")
        
        self.target_entry = self.create_entry(
            target_frame,
            placeholder_text="Select target directory",
            width=300
        )
        self.target_entry.pack(side="left", padx=10)
        self.target_entry.insert(0, self.rule_data.get("target_dir", ""))
        
        browse_btn = self.create_button(
            target_frame,
            text="Browse",
            command=self._browse_directory
        )
        browse_btn.pack(side="right")
        
        # Enabled checkbox
        enabled_frame = self.create_frame(self, corner_radius=0)
        enabled_frame.grid(row=6, column=0, sticky="ew", padx=20, pady=10)
        
        self.enabled_var = ctk.BooleanVar(value=self.rule_data.get("enabled", True))
        enabled_check = self.create_checkbox(
            enabled_frame,
            text="Rule Enabled",
            variable=self.enabled_var
        )
        enabled_check.pack(side="left")
        
        # Buttons
        button_frame = self.create_frame(self, corner_radius=0)
        button_frame.grid(row=7, column=0, sticky="ew", padx=20, pady=(10, 20))
        
        cancel_btn = self.create_button(
            button_frame,
            text="Cancel",
            command=self.destroy,
            fg_color=self._current_theme.get("button_secondary")
        )
        cancel_btn.pack(side="right", padx=5)
        
        save_btn = self.create_button(
            button_frame,
            text="Save Rule",
            command=self._save_rule
        )
        save_btn.pack(side="right", padx=5)
    
    def _browse_directory(self):
        """Open directory selection dialog"""
        directory = filedialog.askdirectory(
            title="Select Target Directory",
            initialdir=self.target_entry.get() or "/"
        )
        if directory:
            self.target_entry.delete(0, "end")
            self.target_entry.insert(0, directory)
    
    def _save_rule(self):
        """Save rule data and close dialog"""
        if not self.name_entry.get():
            # Show error
            return
            
        rule_data = {
            "name": self.name_entry.get(),
            "description": self.desc_entry.get(),
            "pattern_type": self.pattern_type.get(),
            "pattern": self.pattern_entry.get(),
            "action": self.action_var.get(),
            "target_dir": self.target_entry.get(),
            "enabled": self.enabled_var.get()
        }
        
        if self.on_save:
            self.on_save(rule_data)
            
        self.destroy()
    
    def update_theme(self):
        """Update dialog appearance based on theme"""
        for widget in self.winfo_children():
            if hasattr(widget, "update_theme"):
                widget.update_theme()
