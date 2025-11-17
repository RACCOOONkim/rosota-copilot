#!/bin/bash
# Rosota Copilot macOS 빌드 스크립트

echo "=========================================="
echo "Rosota Copilot 앱 빌드 (macOS)"
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
    --windowed \
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
    echo ""
    echo "=========================================="
    echo "✅ 빌드 완료!"
    echo "=========================================="
    echo "앱 위치: dist/Rosota Copilot.app"
    echo ""
    echo "실행 방법:"
    echo "  1. Finder에서 'dist' 폴더 열기"
    echo "  2. 'Rosota Copilot.app' 더블 클릭"
    echo "  3. 또는 Applications 폴더로 드래그"
    echo "=========================================="
else
    echo ""
    echo "❌ 빌드 실패!"
    exit 1
fi

