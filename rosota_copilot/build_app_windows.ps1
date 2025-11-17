# Rosota Copilot Windows 빌드 스크립트 (PowerShell)
# UTF-8 인코딩 설정 (한글 출력을 위해)
$PSDefaultParameterValues['*:Encoding'] = 'utf8'
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
$OutputEncoding = [System.Text.Encoding]::UTF8
[Console]::InputEncoding = [System.Text.Encoding]::UTF8
$env:PYTHONIOENCODING = "utf-8"
chcp 65001 | Out-Null

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

# 필수 패키지 설치 확인 및 업그레이드
Write-Host "필수 패키지 확인 중..." -ForegroundColor Yellow
& $pythonCmd -m pip install --upgrade setuptools wheel 2>&1 | Out-Null

# backports.tarfile 설치 확인 (PyInstaller 의존성)
$backportsCheck = & $pythonCmd -c "import backports.tarfile" 2>&1
if ($LASTEXITCODE -ne 0) {
    Write-Host "backports.tarfile 설치 중..." -ForegroundColor Yellow
    & $pythonCmd -m pip install backports.tarfile
}

# requirements.txt에서 모든 패키지 설치 확인
Write-Host "requirements.txt 확인 중..." -ForegroundColor Yellow
$requirementsPath = Join-Path $PSScriptRoot "..\requirements.txt"
if (-not (Test-Path $requirementsPath)) {
    $requirementsPath = Join-Path $PSScriptRoot "requirements.txt"
}

if (Test-Path $requirementsPath) {
    Write-Host "requirements.txt에서 패키지 설치 확인 중..." -ForegroundColor Yellow
    & $pythonCmd -m pip install -r $requirementsPath --quiet
    Write-Host "requirements.txt 패키지 확인 완료" -ForegroundColor Green
} else {
    Write-Host "경고: requirements.txt를 찾을 수 없습니다. 수동으로 패키지 확인합니다." -ForegroundColor Yellow
    
    # 필수 패키지 수동 확인
    $requiredPackages = @(
        @{name="python-socketio[asgi]"; module="socketio"; version=">=5.11.4"},
        @{name="pyserial"; module="serial"; version=">=3.5"},
        @{name="feetech-servo-sdk"; module="scservo_sdk"; version=">=1.0.0"},
        @{name="loguru"; module="loguru"; version=""},
        @{name="numpy"; module="numpy"; version=""}
    )
    
    foreach ($pkg in $requiredPackages) {
        $checkResult = & $pythonCmd -c "import $($pkg.module)" 2>&1
        if ($LASTEXITCODE -ne 0) {
            Write-Host "$($pkg.name) 설치 중..." -ForegroundColor Yellow
            $installCmd = $pkg.name
            if ($pkg.version) {
                $installCmd += $pkg.version
            }
            & $pythonCmd -m pip install $installCmd
        } else {
            Write-Host "$($pkg.name) 확인 완료" -ForegroundColor Green
        }
    }
}

# PyInstaller 설치 확인
$pyInstallerInstalled = & $pythonCmd -c "import PyInstaller" 2>&1
if ($LASTEXITCODE -ne 0) {
    Write-Host "PyInstaller 설치 중..." -ForegroundColor Yellow
    & $pythonCmd -m pip install pyinstaller
}

# pathlib 패키지 확인 (PyInstaller 충돌 방지)
Write-Host "pathlib 패키지 확인 중..." -ForegroundColor Yellow
$pathlibCheck = & $pythonCmd -m pip show pathlib 2>&1
if ($LASTEXITCODE -eq 0) {
    Write-Host "경고: pathlib 패키지가 설치되어 있습니다. PyInstaller와 충돌할 수 있습니다." -ForegroundColor Yellow
    Write-Host "pathlib 패키지 제거를 권장합니다: pip uninstall -y pathlib" -ForegroundColor Yellow
} else {
    Write-Host "pathlib 패키지가 설치되어 있지 않습니다. (정상)" -ForegroundColor Green
}

# 빌드 디렉토리 정리
Write-Host "빌드 디렉토리 정리 중..." -ForegroundColor Yellow
if (Test-Path "build") { Remove-Item -Recurse -Force "build" }
if (Test-Path "dist") { Remove-Item -Recurse -Force "dist" }

# PyInstaller 인자 구성
$pyInstallerArgs = @(
    "--name", "Rosota Copilot",
    "--onedir",
    "--windowed",
    "--noconfirm",
    "--add-data", "templates;templates",
    "--add-data", "static;static"
)

# resources 디렉토리가 존재하는 경우에만 추가
if (Test-Path "resources") {
    $pyInstallerArgs += "--add-data", "resources;resources"
    Write-Host "resources 디렉토리 포함" -ForegroundColor Green
} else {
    Write-Host "resources 디렉토리가 없습니다. (건너뜀)" -ForegroundColor Yellow
}

# 불필요한 패키지 제외 (빌드 시간 단축)
# 주의: 실제 코드에서 사용하지 않는 패키지만 제외
# numpy는 사용되지만, pandas/scipy는 numpy에 의존하므로 numpy는 제외하지 않음
$excludeModules = @(
    # 머신러닝/딥러닝 (사용 안 함)
    "torch", "torchvision", "torchaudio", "tensorflow",
    # 데이터 분석 (사용 안 함, numpy는 제외하지 않음 - 실제 사용)
    "pandas", "scipy", 
    # 시각화 (사용 안 함)
    "matplotlib", "bokeh", "plotly",
    # 개발 도구 (사용 안 함)
    "IPython", "jupyter", "notebook", "sphinx", "pytest", "black",
    # 기타 (사용 안 함)
    "sklearn", "skimage", "dask", "distributed"
)

foreach ($exclude in $excludeModules) {
    $pyInstallerArgs += "--exclude-module", $exclude
}

# 필수 의존성 명시적 포함
$hiddenImports = @(
    # socketio 관련
    "socketio",
    "socketio.async_server",
    "socketio.asgi",
    "socketio.client",
    "socketio.server",
    "engineio",
    "engineio.async_drivers",
    "engineio.async_drivers.asgi",
    # uvicorn 관련
    "uvicorn",
    "uvicorn.lifespan",
    "uvicorn.lifespan.on",
    "uvicorn.lifespan.off",
    "uvicorn.protocols",
    "uvicorn.protocols.http",
    "uvicorn.protocols.http.auto",
    "uvicorn.protocols.websockets",
    "uvicorn.protocols.websockets.auto",
    # fastapi/starlette 관련
    "fastapi",
    "fastapi.middleware",
    "fastapi.middleware.cors",
    "starlette",
    "starlette.applications",
    "starlette.routing",
    "starlette.responses",
    "starlette.middleware",
    "starlette.middleware.cors",
    # 기타 필수
    "pydantic",
    "jinja2",
    "serial",
    "serial.tools",
    "serial.tools.list_ports",
    "scservo_sdk",
    "scservo_sdk.port_handler",
    "scservo_sdk.packet_handler",
    "scservo_sdk.group_sync_write",
    "scservo_sdk.group_sync_read",
    "numpy",
    "loguru",
    "dotenv",
    "requests"
)

foreach ($import in $hiddenImports) {
    $pyInstallerArgs += "--hidden-import", $import
}

# collect-all 옵션 (필수 패키지만)
$pyInstallerArgs += @(
    "--collect-all", "uvicorn",
    "--collect-all", "fastapi",
    "--collect-all", "socketio",
    "--collect-all", "engineio",
    "--collect-all", "loguru",
    "__main__.py"
)

# 앱 빌드
Write-Host "앱 빌드 중..." -ForegroundColor Yellow
& $pythonCmd -m PyInstaller $pyInstallerArgs

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
