# Rosota Copilot Windows 빌드 스크립트 (PowerShell)

Write-Host "==========================================" -ForegroundColor Cyan
Write-Host "Rosota Copilot 앱 빌드 (Windows)" -ForegroundColor Cyan
Write-Host "==========================================" -ForegroundColor Cyan

# Python 경로 확인
$pythonCmd = $null
if (Get-Command python -ErrorAction SilentlyContinue) {
    $pythonCmd = "python"
} elseif (Get-Command python3 -ErrorAction SilentlyContinue) {
    $pythonCmd = "python3"
} else {
    Write-Host "❌ Python을 찾을 수 없습니다!" -ForegroundColor Red
    Write-Host "Python을 설치하고 PATH에 추가하세요." -ForegroundColor Yellow
    exit 1
}

Write-Host "사용 중인 Python: $pythonCmd" -ForegroundColor Green
& $pythonCmd --version

# PyInstaller 설치 확인
$pyInstallerInstalled = & $pythonCmd -c "import PyInstaller" 2>&1
if ($LASTEXITCODE -ne 0) {
    Write-Host "PyInstaller 설치 중..." -ForegroundColor Yellow
    & $pythonCmd -m pip install pyinstaller
}

# 빌드 디렉토리 정리
Write-Host "빌드 디렉토리 정리 중..." -ForegroundColor Yellow
if (Test-Path "build") { Remove-Item -Recurse -Force "build" }
if (Test-Path "dist") { Remove-Item -Recurse -Force "dist" }

# 앱 빌드
Write-Host "앱 빌드 중..." -ForegroundColor Yellow
& $pythonCmd -m PyInstaller `
    --name "Rosota Copilot" `
    --onedir `
    --windowed `
    --add-data "rosota_copilot/templates;templates" `
    --add-data "rosota_copilot/static;static" `
    --add-data "rosota_copilot/resources;resources" `
    --hidden-import socketio.async_server `
    --hidden-import socketio.asgi `
    --hidden-import uvicorn `
    --hidden-import fastapi `
    --hidden-import starlette `
    --hidden-import engineio `
    --hidden-import pydantic `
    --hidden-import jinja2 `
    --hidden-import serial `
    --hidden-import serial.tools.list_ports `
    --hidden-import feetech_servo_sdk `
    --hidden-import numpy `
    --hidden-import loguru `
    --collect-all uvicorn `
    --collect-all fastapi `
    --collect-all socketio `
    rosota_copilot/__main__.py

if ($LASTEXITCODE -eq 0) {
    Write-Host ""
    Write-Host "==========================================" -ForegroundColor Green
    Write-Host "✅ 빌드 완료!" -ForegroundColor Green
    Write-Host "==========================================" -ForegroundColor Green
    Write-Host "앱 위치: dist\Rosota Copilot\" -ForegroundColor Cyan
    Write-Host "실행 파일: dist\Rosota Copilot\Rosota Copilot.exe" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "실행 방법:" -ForegroundColor Yellow
    Write-Host "  1. dist\Rosota Copilot 폴더 열기" -ForegroundColor White
    Write-Host "  2. 'Rosota Copilot.exe' 더블 클릭" -ForegroundColor White
    Write-Host "==========================================" -ForegroundColor Green
} else {
    Write-Host ""
    Write-Host "❌ 빌드 실패!" -ForegroundColor Red
    exit 1
}

