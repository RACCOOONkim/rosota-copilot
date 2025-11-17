@echo off
setlocal enabledelayedexpansion
REM Rosota Copilot Windows 빌드 스크립트
REM UTF-8 인코딩 설정
chcp 65001 >nul

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

REM 필수 패키지 설치 확인 및 업그레이드
echo 필수 패키지 확인 중...
%PYTHON_CMD% -m pip install --upgrade setuptools wheel >nul 2>&1

REM backports.tarfile 설치 확인 (PyInstaller 의존성)
%PYTHON_CMD% -c "import backports.tarfile" >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo backports.tarfile 설치 중...
    %PYTHON_CMD% -m pip install backports.tarfile
)

REM requirements.txt에서 모든 패키지 설치 확인
if exist ..\requirements.txt (
    echo requirements.txt에서 패키지 설치 확인 중...
    %PYTHON_CMD% -m pip install -r ..\requirements.txt --quiet >nul 2>&1
    echo requirements.txt 패키지 확인 완료
) else if exist requirements.txt (
    echo requirements.txt에서 패키지 설치 확인 중...
    %PYTHON_CMD% -m pip install -r requirements.txt --quiet >nul 2>&1
    echo requirements.txt 패키지 확인 완료
) else (
    echo 경고: requirements.txt를 찾을 수 없습니다. 수동으로 패키지 확인합니다.
    REM 필수 패키지 수동 확인
    %PYTHON_CMD% -c "import socketio" >nul 2>&1
    if %ERRORLEVEL% NEQ 0 (
        echo python-socketio 설치 중...
        %PYTHON_CMD% -m pip install "python-socketio[asgi]>=5.11.4"
    )
    %PYTHON_CMD% -c "import serial" >nul 2>&1
    if %ERRORLEVEL% NEQ 0 (
        echo pyserial 설치 중...
        %PYTHON_CMD% -m pip install "pyserial>=3.5"
    )
    %PYTHON_CMD% -c "import scservo_sdk" >nul 2>&1
    if %ERRORLEVEL% NEQ 0 (
        echo feetech-servo-sdk 설치 중...
        %PYTHON_CMD% -m pip install "feetech-servo-sdk>=1.0.0"
    )
    %PYTHON_CMD% -c "import loguru" >nul 2>&1
    if %ERRORLEVEL% NEQ 0 (
        echo loguru 설치 중...
        %PYTHON_CMD% -m pip install "loguru"
    )
    %PYTHON_CMD% -c "import numpy" >nul 2>&1
    if %ERRORLEVEL% NEQ 0 (
        echo numpy 설치 중...
        %PYTHON_CMD% -m pip install "numpy"
    )
)

REM PyInstaller 설치 확인
%PYTHON_CMD% -c "import PyInstaller" >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo PyInstaller 설치 중...
    %PYTHON_CMD% -m pip install pyinstaller
)

REM pathlib 패키지 확인 (PyInstaller 충돌 방지)
echo pathlib 패키지 확인 중...
%PYTHON_CMD% -m pip show pathlib >nul 2>&1
if %ERRORLEVEL% EQU 0 (
    echo 경고: pathlib 패키지가 설치되어 있습니다. PyInstaller와 충돌할 수 있습니다.
    echo pathlib 패키지 제거를 권장합니다: pip uninstall -y pathlib
) else (
    echo pathlib 패키지가 설치되어 있지 않습니다. (정상)
)

REM 빌드 디렉토리 정리
echo 빌드 디렉토리 정리 중...
if exist build rmdir /s /q build
if exist dist rmdir /s /q dist

REM resources 디렉토리 확인
if exist resources (
    echo resources 디렉토리 포함
    REM 앱 빌드 (resources 포함)
    echo 앱 빌드 중...
    %PYTHON_CMD% -m PyInstaller ^
        --name "Rosota Copilot" ^
        --onedir ^
        --windowed ^
        --noconfirm ^
        --add-data "templates;templates" ^
        --add-data "static;static" ^
        --add-data "resources;resources" ^
        REM 머신러닝/딥러닝 제외 (사용 안 함)
        --exclude-module torch ^
        --exclude-module torchvision ^
        --exclude-module torchaudio ^
        --exclude-module tensorflow ^
        REM 데이터 분석 제외 (사용 안 함, numpy는 제외하지 않음 - 실제 사용)
        --exclude-module pandas ^
        --exclude-module scipy ^
        REM 시각화 제외 (사용 안 함)
        --exclude-module matplotlib ^
        --exclude-module bokeh ^
        --exclude-module plotly ^
        REM 개발 도구 제외 (사용 안 함)
        --exclude-module IPython ^
        --exclude-module jupyter ^
        --exclude-module notebook ^
        --exclude-module sphinx ^
        --exclude-module pytest ^
        --exclude-module black ^
        REM 기타 제외 (사용 안 함)
        --exclude-module sklearn ^
        --exclude-module skimage ^
        --exclude-module dask ^
        --exclude-module distributed ^
        --hidden-import socketio ^
        --hidden-import socketio.async_server ^
        --hidden-import socketio.asgi ^
        --hidden-import socketio.client ^
        --hidden-import socketio.server ^
        --hidden-import engineio ^
        --hidden-import engineio.async_drivers ^
        --hidden-import engineio.async_drivers.asgi ^
        --hidden-import uvicorn ^
        --hidden-import uvicorn.lifespan ^
        --hidden-import uvicorn.lifespan.on ^
        --hidden-import uvicorn.lifespan.off ^
        --hidden-import uvicorn.protocols ^
        --hidden-import uvicorn.protocols.http ^
        --hidden-import uvicorn.protocols.http.auto ^
        --hidden-import uvicorn.protocols.websockets ^
        --hidden-import uvicorn.protocols.websockets.auto ^
        --hidden-import fastapi ^
        --hidden-import fastapi.middleware ^
        --hidden-import fastapi.middleware.cors ^
        --hidden-import starlette ^
        --hidden-import starlette.applications ^
        --hidden-import starlette.routing ^
        --hidden-import starlette.responses ^
        --hidden-import starlette.middleware ^
        --hidden-import starlette.middleware.cors ^
        --hidden-import pydantic ^
        --hidden-import jinja2 ^
        --hidden-import serial ^
        --hidden-import serial.tools ^
        --hidden-import serial.tools.list_ports ^
        --hidden-import scservo_sdk ^
        --hidden-import scservo_sdk.port_handler ^
        --hidden-import scservo_sdk.packet_handler ^
        --hidden-import scservo_sdk.group_sync_write ^
        --hidden-import scservo_sdk.group_sync_read ^
        --hidden-import numpy ^
        --hidden-import loguru ^
        --hidden-import dotenv ^
        --hidden-import requests ^
        --collect-all uvicorn ^
        --collect-all fastapi ^
        --collect-all socketio ^
        --collect-all engineio ^
        --collect-all loguru ^
        __main__.py
) else (
    echo resources 디렉토리가 없습니다. (건너뜀)
    REM 앱 빌드 (resources 제외)
    echo 앱 빌드 중...
    %PYTHON_CMD% -m PyInstaller ^
        --name "Rosota Copilot" ^
        --onedir ^
        --windowed ^
        --noconfirm ^
        --add-data "templates;templates" ^
        --add-data "static;static" ^
        REM 머신러닝/딥러닝 제외 (사용 안 함)
        --exclude-module torch ^
        --exclude-module torchvision ^
        --exclude-module torchaudio ^
        --exclude-module tensorflow ^
        REM 데이터 분석 제외 (사용 안 함, numpy는 제외하지 않음 - 실제 사용)
        --exclude-module pandas ^
        --exclude-module scipy ^
        REM 시각화 제외 (사용 안 함)
        --exclude-module matplotlib ^
        --exclude-module bokeh ^
        --exclude-module plotly ^
        REM 개발 도구 제외 (사용 안 함)
        --exclude-module IPython ^
        --exclude-module jupyter ^
        --exclude-module notebook ^
        --exclude-module sphinx ^
        --exclude-module pytest ^
        --exclude-module black ^
        REM 기타 제외 (사용 안 함)
        --exclude-module sklearn ^
        --exclude-module skimage ^
        --exclude-module dask ^
        --exclude-module distributed ^
        --hidden-import socketio ^
        --hidden-import socketio.async_server ^
        --hidden-import socketio.asgi ^
        --hidden-import socketio.client ^
        --hidden-import socketio.server ^
        --hidden-import engineio ^
        --hidden-import engineio.async_drivers ^
        --hidden-import engineio.async_drivers.asgi ^
        --hidden-import uvicorn ^
        --hidden-import uvicorn.lifespan ^
        --hidden-import uvicorn.lifespan.on ^
        --hidden-import uvicorn.lifespan.off ^
        --hidden-import uvicorn.protocols ^
        --hidden-import uvicorn.protocols.http ^
        --hidden-import uvicorn.protocols.http.auto ^
        --hidden-import uvicorn.protocols.websockets ^
        --hidden-import uvicorn.protocols.websockets.auto ^
        --hidden-import fastapi ^
        --hidden-import fastapi.middleware ^
        --hidden-import fastapi.middleware.cors ^
        --hidden-import starlette ^
        --hidden-import starlette.applications ^
        --hidden-import starlette.routing ^
        --hidden-import starlette.responses ^
        --hidden-import starlette.middleware ^
        --hidden-import starlette.middleware.cors ^
        --hidden-import pydantic ^
        --hidden-import jinja2 ^
        --hidden-import serial ^
        --hidden-import serial.tools ^
        --hidden-import serial.tools.list_ports ^
        --hidden-import scservo_sdk ^
        --hidden-import scservo_sdk.port_handler ^
        --hidden-import scservo_sdk.packet_handler ^
        --hidden-import scservo_sdk.group_sync_write ^
        --hidden-import scservo_sdk.group_sync_read ^
        --hidden-import numpy ^
        --hidden-import loguru ^
        --hidden-import dotenv ^
        --hidden-import requests ^
        --collect-all uvicorn ^
        --collect-all fastapi ^
        --collect-all socketio ^
        --collect-all engineio ^
        --collect-all loguru ^
        __main__.py
)

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
