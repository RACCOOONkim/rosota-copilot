@echo off
REM Rosota Copilot Windows 빌드 스크립트

echo ==========================================
echo Rosota Copilot 앱 빌드 (Windows)
echo ==========================================

REM Python 경로 확인
where python >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    where python3 >nul 2>&1
    if %ERRORLEVEL% NEQ 0 (
        echo ❌ Python을 찾을 수 없습니다!
        echo Python을 설치하고 PATH에 추가하세요.
        exit /b 1
    )
    set PYTHON_CMD=python3
) else (
    set PYTHON_CMD=python
)

echo 사용 중인 Python: %PYTHON_CMD%
%PYTHON_CMD% --version

REM PyInstaller 설치 확인
%PYTHON_CMD% -c "import PyInstaller" >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo PyInstaller 설치 중...
    %PYTHON_CMD% -m pip install pyinstaller
)

REM 빌드 디렉토리 정리
echo 빌드 디렉토리 정리 중...
if exist build rmdir /s /q build
if exist dist rmdir /s /q dist

REM 앱 빌드
echo 앱 빌드 중...
%PYTHON_CMD% -m PyInstaller ^
    --name "Rosota Copilot" ^
    --onedir ^
    --windowed ^
    --add-data "templates;templates" ^
    --add-data "static;static" ^
    --add-data "resources;resources" ^
    --hidden-import socketio.async_server ^
    --hidden-import socketio.asgi ^
    --hidden-import uvicorn ^
    --hidden-import fastapi ^
    --hidden-import starlette ^
    --hidden-import engineio ^
    --hidden-import pydantic ^
    --hidden-import jinja2 ^
    --hidden-import serial ^
    --hidden-import serial.tools.list_ports ^
    --hidden-import feetech_servo_sdk ^
    --hidden-import numpy ^
    --hidden-import loguru ^
    --collect-all uvicorn ^
    --collect-all fastapi ^
    --collect-all socketio ^
    __main__.py

if %ERRORLEVEL% EQU 0 (
    echo.
    echo ==========================================
    echo ✅ 빌드 완료!
    echo ==========================================
    echo 앱 위치: dist\Rosota Copilot\
    echo 실행 파일: dist\Rosota Copilot\Rosota Copilot.exe
    echo.
    echo 실행 방법:
    echo   1. dist\Rosota Copilot 폴더 열기
    echo   2. "Rosota Copilot.exe" 더블 클릭
    echo ==========================================
) else (
    echo.
    echo ❌ 빌드 실패!
    exit /b 1
)

