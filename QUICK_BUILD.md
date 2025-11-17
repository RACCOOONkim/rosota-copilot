# 🚀 가장 간단한 빌드 방법

**목표**: 앱 아이콘을 더블 클릭하면 서버가 시작되고 브라우저가 자동으로 열림

## ⚠️ Python 3.12 사용 시

Python 3.12에서는 `py2app`이 호환성 문제가 있을 수 있습니다. **PyInstaller를 사용하는 것을 권장합니다.**

## 3단계로 완성!

### 1단계: PyInstaller 설치

```bash
pip install pyinstaller
```

### 2단계: 빌드

```bash
./build_app_simple.sh
```

### 3단계: 완료! 🎉

`dist/Rosota Copilot.app` 파일이 생성되었습니다!

## 사용 방법

### 개발자
```bash
# 빌드
./build_app_simple.sh

# 테스트
open "dist/Rosota Copilot.app"
```

### 사용자
1. **`Rosota Copilot.app` 더블 클릭** 👆
2. 서버 자동 시작 🚀
3. 브라우저 자동 열림 🌐
4. 끝! ✅

## 배포

`dist/Rosota Copilot.app` 파일만 배포하면 됩니다!

사용자는:
- 파일을 다운로드
- 더블 클릭
- 끝!

## 문제 해결

### "Python을 찾을 수 없습니다"
- conda 환경이 활성화되어 있는지 확인: `conda activate base`

### 빌드 실패
- 필요한 패키지가 설치되어 있는지 확인: `pip install -r requirements.txt`

### 앱이 실행되지 않음
- 터미널에서 직접 실행하여 에러 확인:
  ```bash
  ./dist/Rosota\ Copilot.app/Contents/MacOS/Rosota\ Copilot
  ```

---

**이게 가장 간단하고 안정적인 방법입니다!** 🎯
