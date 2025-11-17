# Windows 빌드 문제 해결 기록

이 문서는 Rosota Copilot Windows 앱 빌드 과정에서 발생한 문제들과 해결 방법을 기록합니다.

## 발생한 문제들 및 해결 방법

### 1. pathlib 패키지 충돌 문제

**문제:**
```
ERROR: The 'pathlib' package is an obsolete backport of a standard library package 
and is incompatible with PyInstaller.
```

**원인:**
- Anaconda base 환경에 설치된 구버전 `pathlib` 백포트 패키지가 PyInstaller와 충돌
- `pathlib`은 Python 3.4+ 표준 라이브러리이므로 별도 패키지가 필요 없음

**해결:**
- Anaconda base 환경에서 `pathlib` 패키지 제거:
  ```bash
  C:\Users\Medisc\anaconda3\python.exe -m pip uninstall -y pathlib
  ```
- 빌드 스크립트에서 `--exclude-module pathlib` 옵션 제거 (표준 라이브러리이므로 제외하면 안 됨)

---

### 2. 한글 인코딩 문제

**문제:**
- 빌드 스크립트 실행 시 한글이 깨져서 표시됨 (`??鍮뚮뱶`)

**원인:**
- Windows PowerShell/Batch 스크립트의 기본 인코딩이 UTF-8이 아님

**해결:**
- **PowerShell 스크립트 (`build_app_windows.ps1`):**
  ```powershell
  $PSDefaultParameterValues['*:Encoding'] = 'utf8'
  [Console]::OutputEncoding = [System.Text.Encoding]::UTF8
  $OutputEncoding = [System.Text.Encoding]::UTF8
  [Console]::InputEncoding = [System.Text.Encoding]::UTF8
  $env:PYTHONIOENCODING = "utf-8"
  chcp 65001 | Out-Null
  ```

- **Batch 스크립트 (`build_app_windows.bat`):**
  ```batch
  chcp 65001 >nul
  setlocal enabledelayedexpansion
  ```

---

### 3. backports.tarfile 모듈 누락

**문제:**
```
ImportError: cannot import name 'tarfile' from 'backports'
```

**원인:**
- PyInstaller가 `backports.tarfile` 패키지를 자동으로 감지하지 못함

**해결:**
- 빌드 스크립트에 `backports.tarfile` 설치 확인 및 설치 로직 추가
- `requirements.txt`에 명시적으로 포함 (필요한 경우)

---

### 4. ModuleNotFoundError 문제들

#### 4.1 socketio 모듈 누락

**문제:**
```
ModuleNotFoundError: No module named 'socketio'
```

**해결:**
- 빌드 스크립트에 `python-socketio[asgi]` 설치 확인 추가
- PyInstaller 인자에 `--hidden-import socketio`, `--hidden-import engineio` 추가
- `--collect-all socketio`, `--collect-all engineio` 추가

#### 4.2 serial 모듈 누락

**문제:**
```
ModuleNotFoundError: No module named 'serial'
```

**해결:**
- 빌드 스크립트에 `pyserial` 설치 확인 추가
- PyInstaller 인자에 `--hidden-import serial`, `--hidden-import serial.tools`, `--hidden-import serial.tools.list_ports` 추가

#### 4.3 loguru 모듈 누락

**문제:**
```
ModuleNotFoundError: No module named 'loguru'
```

**해결:**
- `requirements.txt`에 `loguru>=0.7.0` 추가
- 빌드 스크립트에 `loguru` 설치 확인 추가
- PyInstaller 인자에 `--hidden-import loguru` 추가
- `--collect-all loguru` 추가

---

### 5. loguru 포매터 설정 오류

**문제:**
```
서버 시작 실패: Unable to configure formatter 'default'
```

**원인:**
- PyInstaller `--windowed` 모드로 빌드 시 `sys.stderr`와 `sys.stdout`이 `None`으로 설정됨
- `loguru`가 기본 포매터를 설정하려고 할 때 출력 스트림이 없어서 오류 발생

**해결:**
- `rosota_copilot/__main__.py`에서 애플리케이션 시작 전에 `loguru` 초기화 코드 추가:
  1. PyInstaller 빌드 환경 감지 (`sys.frozen`)
  2. `sys.stderr`/`sys.stdout`이 `None`인 경우 파일로 리디렉션
  3. `loguru` 기본 핸들러 제거 후 간단한 포매터로 재설정
  4. 출력 스트림을 사용할 수 없는 경우 파일로 로깅 설정

**구현 코드:**
```python
# PyInstaller로 빌드된 경우 sys.stderr가 None일 수 있으므로 처리
if getattr(sys, 'frozen', False):
    if sys.stderr is None:
        log_dir = Path(sys.executable).parent / 'logs'
        log_dir.mkdir(exist_ok=True)
        sys.stderr = open(str(log_dir / 'app.log'), 'w', encoding='utf-8')

# loguru 초기화
from loguru import logger
logger.remove()  # 기본 핸들러 제거
if sys.stderr is not None:
    logger.add(sys.stderr, format="...", level="INFO", colorize=False)
else:
    logger.add(str(log_file), format="...", level="INFO")
```

---

## 빌드 스크립트 개선 사항

### 의존성 자동 확인 및 설치

빌드 스크립트가 `requirements.txt`를 자동으로 확인하고 필요한 패키지를 설치하도록 개선:

```powershell
# requirements.txt에서 모든 패키지 설치 확인
$requirementsPath = Join-Path $PSScriptRoot "..\requirements.txt"
if (Test-Path $requirementsPath) {
    & $pythonCmd -m pip install -r $requirementsPath --quiet
}
```

### 필수 의존성 명시적 포함

PyInstaller 인자에 모든 필수 모듈을 명시적으로 포함:

- `socketio`, `engineio` 및 모든 서브모듈
- `uvicorn`, `fastapi`, `starlette` 및 모든 서브모듈
- `serial`, `serial.tools`, `serial.tools.list_ports`
- `scservo_sdk` 및 모든 서브모듈
- `loguru`, `numpy`, `pydantic`, `jinja2`, `dotenv`, `requests`

### 불필요한 패키지 제외

빌드 시간 단축을 위해 사용하지 않는 대형 패키지 제외:

- `torch`, `torchvision`, `torchaudio`
- `tensorflow`, `pandas`, `scipy`, `matplotlib`
- `IPython`, `jupyter`, `notebook`

---

## 최종 빌드 명령어

### PowerShell:
```powershell
cd rosota_copilot
powershell -ExecutionPolicy Bypass -File build_app_windows.ps1
```

### Batch:
```cmd
cd rosota_copilot
build_app_windows.bat
```

---

## 빌드 결과물

- **실행 파일:** `rosota_copilot/dist/Rosota Copilot/Rosota Copilot.exe`
- **로그 파일:** 실행 파일과 같은 디렉토리의 `logs/app.log` (windowed 모드인 경우)

---

## 참고 사항

1. **빌드 시간:** 약 2-3분 (의존성 제외로 최적화됨)
2. **실행 파일 크기:** 약 200-300MB (모든 의존성 포함)
3. **로그 위치:** windowed 모드에서는 `logs/app.log` 파일에 로그가 저장됨
4. **한글 인코딩:** UTF-8로 설정되어 정상 표시됨

---

## 향후 개선 사항

1. 빌드 스크립트를 더 모듈화하여 유지보수성 향상
2. 빌드 시간을 더 단축하기 위한 추가 최적화
3. 자동 테스트 추가로 빌드 검증 강화

