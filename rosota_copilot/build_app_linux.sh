#!/bin/bash
# Rosota Copilot Linux 빌드 스크립트

echo "=========================================="
echo "Rosota Copilot 앱 빌드 (Linux)"
echo "=========================================="

# 현재 활성화된 Python 사용
PYTHON_CMD=$(which python)
if [ -z "$PYTHON_CMD" ]; then
    PYTHON_CMD=$(which python3)
fi

if [ -z "$PYTHON_CMD" ]; then
    echo "❌ Python을 찾을 수 없습니다!"
    exit 1
fi

echo "사용 중인 Python: $PYTHON_CMD"
echo "Python 버전: $($PYTHON_CMD --version)"

# PyInstaller 설치 확인
if ! $PYTHON_CMD -c "import PyInstaller" 2>/dev/null; then
    echo "PyInstaller 설치 중..."
    $PYTHON_CMD -m pip install pyinstaller
fi

# 빌드 디렉토리 정리
echo "빌드 디렉토리 정리 중..."
rm -rf build dist

# 앱 빌드
echo "앱 빌드 중..."
$PYTHON_CMD -m PyInstaller \
    --name "Rosota Copilot" \
    --onedir \
    --noconsole \
    --add-data "templates:templates" \
    --add-data "static:static" \
    --add-data "resources:resources" \
    --hidden-import socketio.async_server \
    --hidden-import socketio.asgi \
    --hidden-import uvicorn \
    --hidden-import fastapi \
    --hidden-import starlette \
    --hidden-import engineio \
    --hidden-import pydantic \
    --hidden-import jinja2 \
    --hidden-import serial \
    --hidden-import serial.tools.list_ports \
    --hidden-import feetech_servo_sdk \
    --hidden-import numpy \
    --hidden-import loguru \
    --collect-all uvicorn \
    --collect-all fastapi \
    --collect-all socketio \
    __main__.py

if [ $? -eq 0 ]; then
    # 실행 권한 부여
    chmod +x "dist/Rosota Copilot/Rosota Copilot"
    
    echo ""
    echo "=========================================="
    echo "✅ 빌드 완료!"
    echo "=========================================="
    echo "앱 위치: dist/Rosota Copilot/"
    echo "실행 파일: dist/Rosota Copilot/Rosota Copilot"
    echo ""
    echo "실행 방법:"
    echo "  1. 터미널에서: ./dist/Rosota\ Copilot/Rosota\ Copilot"
    echo "  2. 또는 파일 관리자에서 더블 클릭"
    echo "=========================================="
else
    echo ""
    echo "❌ 빌드 실패!"
    exit 1
fi

