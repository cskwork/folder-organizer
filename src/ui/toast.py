import customtkinter as ctk
from typing import Optional, Tuple
import time
import threading

class Toast(ctk.CTkFrame):
    """Modern toast notification widget"""
    
    def __init__(
        self,
        master,
        message: str,
        duration: int = 3000,
        theme_manager=None,
        position: Tuple[int, int] = None,
        **kwargs
    ):
        self.theme = theme_manager.get_current_theme() if theme_manager else None
        
        super().__init__(
            master,
            fg_color=self.theme.get("card") if self.theme else "#1E2024",
            border_width=1,
            border_color=self.theme.get("border") if self.theme else "#2C3038",
            **kwargs
        )
        
        # Configure grid
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)
        
        # Create message label
        self.label = ctk.CTkLabel(
            self,
            text=message,
            text_color=self.theme.get("text") if self.theme else "#E4E6EB",
            padx=20,
            pady=10
        )
        self.label.grid(row=0, column=0, sticky="nsew")
        
        # Position the toast
        if not position:
            # Default to bottom right
            position = (
                master.winfo_width() - self.winfo_reqwidth() - 20,
                master.winfo_height() - self.winfo_reqheight() - 20
            )
        
        self.place(x=position[0], y=position[1])
        
        # Start fade out timer
        self.duration = duration
        threading.Thread(target=self._destroy_after_duration, daemon=True).start()
    
    def _destroy_after_duration(self):
        """Destroy the toast after duration"""
        time.sleep(self.duration / 1000)  # Convert to seconds
        self.destroy()

class ToastManager:
    """Manages toast notifications"""
    
    def __init__(self, master, theme_manager=None):
        self.master = master
        self.theme_manager = theme_manager
        self.active_toasts = []
    
    def show_toast(
        self,
        message: str,
        duration: int = 3000,
        position: Optional[Tuple[int, int]] = None
    ):
        """Show a toast notification"""
        toast = Toast(
            self.master,
            message,
            duration,
            self.theme_manager,
            position
        )
        self.active_toasts.append(toast)
        
        # Clean up destroyed toasts
        self.active_toasts = [t for t in self.active_toasts if str(t) != ""]
