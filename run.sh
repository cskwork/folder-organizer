#!/bin/bash

# 가상 환경이 없는 경우 생성
if [ ! -d "venv" ]; then
    echo "가상 환경을 생성합니다..."
    python -m venv venv
fi

# Windows에서 가상 환경 활성화
source venv/Scripts/activate

# 필요한 패키지 설치
echo "필요한 패키지를 설치합니다..."
pip install -r requirements.txt

# 메인 프로그램 실행
echo "프로그램을 실행합니다..."
python main.py

# 가상 환경 비활성화
deactivate
