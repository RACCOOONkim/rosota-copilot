# 📱 Rosota Copilot 앱 만들기 (가장 간단한 방법)

사용자가 **앱 아이콘을 더블 클릭**하면 서버가 시작되고 브라우저가 자동으로 열립니다.

## 🚀 빠른 시작

### 1. py2app 설치

```bash
pip install py2app
```

### 2. 앱 빌드

```bash
./build_simple.sh
```

또는

```bash
python setup.py py2app
```

### 3. 완료!

`dist/Rosota Copilot.app` 파일이 생성됩니다.

## 📦 사용 방법

### 개발자 (빌드)

```bash
# 1. 빌드
./build_simple.sh

# 2. 테스트
open "dist/Rosota Copilot.app"
```

### 사용자 (실행)

1. **`Rosota Copilot.app` 더블 클릭**
2. 서버가 자동으로 시작됩니다
3. 브라우저가 자동으로 열립니다 (`http://localhost:8000`)
4. 끝!

## 🎯 특징

- ✅ **더블 클릭으로 실행**: 일반 macOS 앱처럼 작동
- ✅ **자동 브라우저 열기**: 서버 시작 시 자동으로 웹 페이지 열림
- ✅ **단일 파일**: 모든 의존성 포함
- ✅ **간단한 배포**: `.app` 파일만 배포하면 됨

## 📂 빌드 결과

```
dist/
└── Rosota Copilot.app  ← 이 파일만 배포하면 됨!
```

## 🔧 고급 옵션

### 아이콘 추가

1. `.icns` 파일 준비
2. `setup.py`의 `'iconfile': 'path/to/icon.icns'` 수정
3. 재빌드

### DMG 생성

```bash
# create-dmg 설치
brew install create-dmg

# DMG 생성
create-dmg --volname "Rosota Copilot" \
  --window-pos 200 120 \
  --window-size 600 400 \
  --icon-size 100 \
  --app-drop-link 425 190 \
  "RosotaCopilot.dmg" \
  "dist/"
```

## ⚠️ 주의사항

### 첫 실행 시

macOS가 "확인되지 않은 개발자" 경고를 표시할 수 있습니다:

1. **시스템 설정** 열기
2. **개인정보 보호 및 보안** 선택
3. **"Rosota Copilot이 차단되었습니다"** 옆의 **"허용"** 클릭

### USB 포트 접근 권한

로봇 연결을 위해 USB 포트 접근 권한이 필요할 수 있습니다:

1. **시스템 설정** > **개인정보 보호 및 보안** > **전체 디스크 접근 권한**
2. **터미널** 또는 **Rosota Copilot**에 권한 부여

## 🆚 다른 방법과 비교

| 방법 | 장점 | 단점 |
|------|------|------|
| **py2app** ✅ | 가장 간단, .app 자동 생성 | macOS 전용 |
| PyInstaller | 크로스 플랫폼 | 설정 복잡 |
| 수동 .app | 완전한 제어 | 매우 복잡 |

**결론**: macOS만 지원한다면 **py2app이 가장 간단합니다!**

## 📝 문제 해결

### "Module not found" 오류

`setup.py`의 `'packages'` 또는 `'includes'`에 누락된 모듈 추가

### 리소스 파일을 찾을 수 없음

`setup.py`의 `DATA_FILES`에 필요한 파일/폴더 추가

### 앱이 시작되지 않음

터미널에서 실행하여 에러 메시지 확인:
```bash
./dist/Rosota\ Copilot.app/Contents/MacOS/Rosota\ Copilot
```

