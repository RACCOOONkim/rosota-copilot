# 크로스 플랫폼 빌드 가이드

Rosota Copilot을 Windows, Linux, macOS에서 빌드하는 방법입니다.

## 사전 요구사항

### 공통
- **Python 3.10 이상** 설치
- **PyInstaller** (빌드 스크립트가 자동 설치)

### Windows
- Python이 PATH에 등록되어 있어야 함
- PowerShell 또는 Command Prompt 사용 가능

### Linux
- Python 3 개발 패키지
- 기본 빌드 도구

### macOS
- Xcode Command Line Tools (선택사항, 권장)

## 빌드 방법

### Windows

#### 방법 1: PowerShell 스크립트 (권장)
```powershell
.\build_app_windows.ps1
```

#### 방법 2: 배치 파일
```cmd
build_app_windows.bat
```

#### 결과
- 위치: `dist\Rosota Copilot\`
- 실행 파일: `dist\Rosota Copilot\Rosota Copilot.exe`
- 실행: `Rosota Copilot.exe` 더블 클릭

### Linux

```bash
chmod +x build_app_linux.sh
./build_app_linux.sh
```

#### 결과
- 위치: `dist/Rosota Copilot/`
- 실행 파일: `dist/Rosota Copilot/Rosota Copilot`
- 실행: 
  ```bash
  ./dist/Rosota\ Copilot/Rosota\ Copilot
  ```
  또는 파일 관리자에서 더블 클릭

### macOS

```bash
chmod +x build_app_macos.sh
./build_app_macos.sh
```

#### 결과
- 위치: `dist/Rosota Copilot.app`
- 실행: 더블 클릭 또는 Applications 폴더로 드래그

## 수동 빌드

빌드 스크립트를 사용하지 않고 직접 빌드하려면:

### Windows
```cmd
python -m PyInstaller --name "Rosota Copilot" --onedir --windowed --add-data "templates;templates" --add-data "static;static" --add-data "resources;resources" --hidden-import socketio.async_server --hidden-import socketio.asgi --hidden-import uvicorn --hidden-import fastapi --hidden-import starlette --hidden-import engineio --hidden-import pydantic --hidden-import jinja2 --hidden-import serial --hidden-import serial.tools.list_ports --hidden-import feetech_servo_sdk --hidden-import numpy --hidden-import loguru --collect-all uvicorn --collect-all fastapi --collect-all socketio __main__.py
```

### Linux
```bash
python -m PyInstaller --name "Rosota Copilot" --onedir --noconsole --add-data "templates:templates" --add-data "static:static" --add-data "resources:resources" --hidden-import socketio.async_server --hidden-import socketio.asgi --hidden-import uvicorn --hidden-import fastapi --hidden-import starlette --hidden-import engineio --hidden-import pydantic --hidden-import jinja2 --hidden-import serial --hidden-import serial.tools.list_ports --hidden-import feetech_servo_sdk --hidden-import numpy --hidden-import loguru --collect-all uvicorn --collect-all fastapi --collect-all socketio __main__.py
```

### macOS
```bash
python -m PyInstaller --name "Rosota Copilot" --onedir --windowed --add-data "templates:templates" --add-data "static:static" --add-data "resources:resources" --hidden-import socketio.async_server --hidden-import socketio.asgi --hidden-import uvicorn --hidden-import fastapi --hidden-import starlette --hidden-import engineio --hidden-import pydantic --hidden-import jinja2 --hidden-import serial --hidden-import serial.tools.list_ports --hidden-import feetech_servo_sdk --hidden-import numpy --hidden-import loguru --collect-all uvicorn --collect-all fastapi --collect-all socketio __main__.py
```

## 플랫폼별 차이점

### 경로 구분자
- **Windows**: `;` (세미콜론)
- **Linux/macOS**: `:` (콜론)

### 실행 파일 확장자
- **Windows**: `.exe`
- **Linux**: 확장자 없음
- **macOS**: `.app` 번들

### 콘솔 옵션
- **Windows**: `--windowed` (GUI 앱)
- **Linux**: `--noconsole` (콘솔 없음)
- **macOS**: `--windowed` (GUI 앱)

## 배포

### Windows
- `dist\Rosota Copilot\` 폴더 전체를 ZIP으로 압축
- 또는 설치 프로그램 생성 (Inno Setup, NSIS 등)

### Linux
- `dist/Rosota Copilot/` 폴더를 tar.gz로 압축
- 또는 AppImage로 패키징 (선택사항)

### macOS
- `dist/Rosota Copilot.app` 파일만 배포
- 또는 DMG로 패키징 (선택사항)

## 문제 해결

### "Module not found" 오류
빌드 스크립트의 `--hidden-import` 목록에 누락된 모듈 추가

### 리소스 파일을 찾을 수 없음
`--add-data` 옵션 확인:
- Windows: `source;destination`
- Linux/macOS: `source:destination`

### 실행 파일이 시작되지 않음
- Windows: 관리자 권한으로 실행 시도
- Linux: 실행 권한 확인 (`chmod +x`)
- macOS: 시스템 설정에서 허용

### USB 포트 접근 권한
- Linux: `sudo chmod 666 /dev/ttyUSB0`
- macOS: 시스템 설정 > 개인정보 보호 및 보안
- Windows: 일반적으로 권한 문제 없음

## 빌드 크기 최적화

빌드 크기를 줄이려면:
1. 불필요한 모듈 제외: `--exclude-module`
2. UPX 압축 사용 (이미 활성화됨)
3. 단일 파일 모드 사용: `--onefile` (대신 `--onedir` 사용 중)

## 참고사항

- 빌드는 각 플랫폼에서 해당 플랫폼용으로만 가능합니다
- 크로스 컴파일은 지원되지 않습니다
- 각 플랫폼에서 빌드한 결과물은 해당 플랫폼에서만 실행됩니다

