import os
from pathlib import Path
import logging
import customtkinter as ctk
from tkinterdnd2 import TkinterDnD

# Add src to Python path
src_path = Path(__file__).parent.parent
if str(src_path) not in os.sys.path:
    os.sys.path.append(str(src_path))

from src.views.main_window import MainWindow
from src.core.file_analyzer import FileAnalyzer
from src.core.file_organizer import FileOrganizer
from src.core.settings_manager import SettingsManager

def setup_logging():
    """Setup logging configuration"""
    log_dir = Path("logs")
    log_dir.mkdir(exist_ok=True)
    
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_dir / "app.log"),
            logging.StreamHandler()
        ]
    )

def main():
    """Main entry point for the application"""
    # Setup logging
    setup_logging()
    
    # Initialize TkinterDnD
    root = TkinterDnD.Tk()
    ctk.set_appearance_mode("dark")
    ctk.set_default_color_theme("blue")
    
    # Create settings manager
    settings_manager = SettingsManager()
    
    # Create core components
    file_analyzer = FileAnalyzer(config_manager=settings_manager)
    file_organizer = FileOrganizer(config_manager=settings_manager)
    
    # Create and run main window
    app = MainWindow()
    app.settings_manager = settings_manager
    app.file_analyzer = file_analyzer
    app.file_organizer = file_organizer
    
    # Register main window as settings observer
    settings_manager.add_observer(app)
    
    app.mainloop()

if __name__ == "__main__":
    main()
