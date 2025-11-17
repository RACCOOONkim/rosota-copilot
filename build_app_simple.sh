#!/bin/bash
# Rosota Copilot 간단한 빌드 스크립트 (PyInstaller 사용)
# macOS용 - Linux는 build_app_linux.sh 사용

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
rm -rf build dist *.spec

# 앱 빌드
echo "앱 빌드 중..."
$PYTHON_CMD -m PyInstaller \
    --name "Rosota Copilot" \
    --onedir \
    --windowed \
    --add-data "rosota_copilot/templates:templates" \
    --add-data "rosota_copilot/static:static" \
    --add-data "rosota_copilot/resources:resources" \
    --hidden-import uvicorn \
    --hidden-import fastapi \
    --hidden-import starlette \
    --hidden-import socketio \
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
    rosota_copilot/__main__.py

# .app 번들 생성
if [ -d "dist/Rosota Copilot" ]; then
    echo ""
    echo ".app 번들 생성 중..."
    APP_NAME="Rosota Copilot.app"
    APP_PATH="dist/$APP_NAME"
    
    # 기존 .app 제거
    rm -rf "$APP_PATH"
    
    # .app 구조 생성
    mkdir -p "$APP_PATH/Contents/MacOS"
    mkdir -p "$APP_PATH/Contents/Resources"
    
    # 실행 파일 복사
    cp -r "dist/Rosota Copilot"/* "$APP_PATH/Contents/MacOS/"
    
    # Info.plist 생성
    cat > "$APP_PATH/Contents/Info.plist" <<EOF
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>CFBundleExecutable</key>
    <string>Rosota Copilot</string>
    <key>CFBundleIdentifier</key>
    <string>com.rosota.copilot</string>
    <key>CFBundleName</key>
    <string>Rosota Copilot</string>
    <key>CFBundleDisplayName</key>
    <string>Rosota Copilot</string>
    <key>CFBundleVersion</key>
    <string>1.0.0</string>
    <key>CFBundleShortVersionString</key>
    <string>1.0</string>
    <key>CFBundlePackageType</key>
    <string>APPL</string>
    <key>LSMinimumSystemVersion</key>
    <string>10.13</string>
    <key>NSHighResolutionCapable</key>
    <true/>
</dict>
</plist>
EOF
    
    # 실행 파일 이름 변경
    if [ -f "$APP_PATH/Contents/MacOS/__main__" ]; then
        mv "$APP_PATH/Contents/MacOS/__main__" "$APP_PATH/Contents/MacOS/Rosota Copilot"
    elif [ -f "$APP_PATH/Contents/MacOS/rosota_copilot" ]; then
        mv "$APP_PATH/Contents/MacOS/rosota_copilot" "$APP_PATH/Contents/MacOS/Rosota Copilot"
    fi
    
    chmod +x "$APP_PATH/Contents/MacOS/Rosota Copilot"
    
    echo ""
    echo "=========================================="
    echo "✅ 빌드 완료!"
    echo "=========================================="
    echo "앱 위치: $APP_PATH"
    echo ""
    echo "실행 방법:"
    echo "  1. Finder에서 'dist' 폴더 열기"
    echo "  2. '$APP_NAME' 더블 클릭"
    echo "  3. 또는 Applications 폴더로 드래그"
    echo "=========================================="
else
    echo "❌ 빌드 실패: dist/Rosota Copilot 디렉토리를 찾을 수 없습니다."
    exit 1
fi

