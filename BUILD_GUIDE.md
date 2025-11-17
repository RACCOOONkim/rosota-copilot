# Rosota Copilot 앱 빌드 가이드

이 가이드는 Rosota Copilot을 macOS용 단일 실행 파일(.app 또는 .dmg)로 패키징하는 방법을 설명합니다.

## 사전 요구사항

1. **Python 3.10 이상** 설치
2. **PyInstaller** 설치:
   ```bash
   pip install pyinstaller
   ```
3. **(선택사항) create-dmg** (DMG 생성용):
   ```bash
   brew install create-dmg
   ```

## 빌드 방법

### 방법 1: 자동 빌드 스크립트 사용 (권장)

```bash
python build_app.py
```

이 스크립트는:
- PyInstaller 설치 확인 및 자동 설치
- 앱 빌드
- (선택사항) DMG 파일 생성

### 방법 2: 수동 빌드

#### 1. PyInstaller 설치

```bash
pip install pyinstaller
```

#### 2. Spec 파일 생성 및 수정

`build_app.py`를 실행하면 `RosotaCopilot.spec` 파일이 자동 생성됩니다.
또는 수동으로 생성할 수 있습니다.

#### 3. 빌드 실행

```bash
pyinstaller --clean --noconfirm RosotaCopilot.spec
```

#### 4. 결과 확인

빌드된 실행 파일은 `dist/RosotaCopilot`에 생성됩니다.

## 실행 방법

### 빌드된 실행 파일 실행

```bash
./dist/RosotaCopilot
```

또는 더블 클릭으로 실행 (macOS에서 .app 번들로 만든 경우)

### 브라우저 접속

서버가 시작되면 자동으로 브라우저가 열립니다.
수동으로 접속하려면: `http://localhost:8000`

## DMG 파일 생성

### 자동 생성 (create-dmg 사용)

```bash
# build_app.py 실행 시 DMG 생성 옵션 선택
python build_app.py
# 또는
create-dmg --volname "Rosota Copilot" \
  --window-pos 200 120 \
  --window-size 600 400 \
  --icon-size 100 \
  --app-drop-link 425 190 \
  RosotaCopilot.dmg \
  dist/
```

### 수동 생성 (Disk Utility 사용)

1. **Disk Utility** 열기
2. **File > New Image > Image from Folder**
3. `dist` 폴더 선택
4. **읽기/쓰기** 형식 선택
5. 저장

## 배포

### 단일 파일 배포

`dist/RosotaCopilot` 파일만 배포하면 됩니다.
사용자는 이 파일을 다운로드하여 실행할 수 있습니다.

### DMG 배포

`.dmg` 파일을 배포하면:
- 사용자가 더블 클릭으로 마운트
- 앱을 Applications 폴더로 드래그
- 일반 macOS 앱처럼 사용 가능

## 문제 해결

### "Permission denied" 오류

실행 권한 부여:
```bash
chmod +x dist/RosotaCopilot
```

### "Module not found" 오류

`RosotaCopilot.spec` 파일의 `hiddenimports`에 누락된 모듈 추가

### 리소스 파일을 찾을 수 없음

`RosotaCopilot.spec` 파일의 `datas` 섹션에 필요한 파일/폴더 추가:
```python
datas=[
    ('rosota_copilot/templates', 'templates'),
    ('rosota_copilot/static', 'static'),
    ('rosota_copilot/resources', 'resources'),
],
```

### USB 포트 접근 권한

macOS에서 USB 시리얼 포트 접근을 위해:
1. **시스템 설정 > 개인정보 보호 및 보안 > 전체 디스크 접근 권한**
2. 터미널 또는 앱에 권한 부여

또는 사용자에게 다음 명령 실행 안내:
```bash
sudo chmod 666 /dev/tty.usbmodem*
```

## 파일 크기 최적화

빌드된 파일 크기를 줄이려면:

1. **UPX 압축 사용** (이미 spec 파일에 포함됨)
2. **불필요한 모듈 제외**:
   ```python
   excludes=['matplotlib', 'pandas', 'scipy', ...]
   ```

## 코드 서명 (선택사항)

배포 전 코드 서명을 원하면:

```bash
codesign --deep --force --verify --verbose \
  --sign "Developer ID Application: Your Name" \
  dist/RosotaCopilot.app
```

## 공증 (Notarization) (선택사항)

Apple 공증을 받으려면:

```bash
xcrun notarytool submit RosotaCopilot.dmg \
  --apple-id your@email.com \
  --team-id YOUR_TEAM_ID \
  --password YOUR_APP_SPECIFIC_PASSWORD
```

## 참고사항

- 첫 실행 시 macOS가 "확인되지 않은 개발자" 경고를 표시할 수 있습니다.
- 시스템 설정에서 허용하거나 코드 서명을 추가하세요.
- USB 포트 접근 권한이 필요할 수 있습니다.

