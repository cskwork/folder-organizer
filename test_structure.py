#!/usr/bin/env python3
"""
Test script to verify the reorganized project structure.
"""

import sys
from pathlib import Path

# Add src directory to Python path
src_path = Path(__file__).parent / "src"
sys.path.insert(0, str(src_path))

def test_imports():
    """Test that all imports work correctly."""
    try:
        print("🧪 Testing project structure...")
        
        # Test core imports
        print("  📦 Testing core imports...")
        from src.core import FileAnalyzer, ContentAnalyzer, FileOrganizer
        print("  ✅ Core imports successful")
        
        # Test services imports  
        print("  📦 Testing services imports...")
        from src.services import ConfigManager
        print("  ✅ Services imports successful")
        
        # Test utils imports
        print("  📦 Testing utils imports...")
        from src.utils import KoreanTextHandler, ErrorHandler, DIContainer
        print("  ✅ Utils imports successful")
        
        # Test interfaces imports
        print("  📦 Testing interfaces imports...")
        from src.interfaces import IFileAnalyzer, IConfigManager
        print("  ✅ Interfaces imports successful")
        
        print("\n🎉 All imports working correctly!")
        print("✅ Project structure reorganization successful!")
        return True
        
    except ImportError as e:
        print(f"\n❌ Import Error: {e}")
        print("Some modules may have missing dependencies.")
        print("Run: pip install -r requirements.txt")
        return False
    except Exception as e:
        print(f"\n❌ Unexpected Error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_imports()
    sys.exit(0 if success else 1)