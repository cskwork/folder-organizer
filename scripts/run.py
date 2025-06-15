#!/usr/bin/env python3
"""
Advanced runner script with options for the Intelligent File Organizer.
"""

import argparse
import sys
import os
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

def main():
    parser = argparse.ArgumentParser(description="Intelligent File Organizer")
    parser.add_argument("--config", help="Path to config file")
    parser.add_argument("--debug", action="store_true", help="Enable debug mode")
    parser.add_argument("--test-mode", action="store_true", help="Run in test mode")
    
    args = parser.parse_args()
    
    try:
        if args.test_mode:
            from src.services import configure_for_testing
            configure_for_testing()
        else:
            from src.services import configure_for_production
            configure_for_production()
            
        from src.ui import MainWindow
        
        app = MainWindow()
        app.mainloop()
        
    except ImportError as e:
        print(f"❌ Import Error: {e}")
        print("Please ensure all dependencies are installed:")
        print("pip install -r requirements.txt")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Error: {e}")
        if args.debug:
            import traceback
            traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()