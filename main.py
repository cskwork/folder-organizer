#!/usr/bin/env python
"""
파일 조직화 애플리케이션 메인 엔트리 포인트
"""
import sys
import os
from pathlib import Path

# src 디렉토리를 Python 경로에 추가
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

def main():
    """메인 함수"""
    try:
        # Controller에서 GUI 애플리케이션 실행
        from Controller.main_controller import FileOrganizerGUI
        app = FileOrganizerGUI()
        app.mainloop()
    except ImportError as e:
        print(f"Import error: {e}")
        print("Please make sure all dependencies are installed: pip install -r requirements.txt")
        sys.exit(1)
    except Exception as e:
        print(f"Unexpected error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()