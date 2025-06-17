#!/usr/bin/env python3
"""
Entry point for the Intelligent File Organizer application.
"""

import sys
import os

# Add the current directory to the Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from folder_organizer import FileOrganizerGUI

def main():
    """Launch the File Organizer GUI application."""
    app = FileOrganizerGUI()
    app.mainloop()

if __name__ == "__main__":
    main()