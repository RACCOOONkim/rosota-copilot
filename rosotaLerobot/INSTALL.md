# 설치 가이드

## 필수 요구사항

- Python 3.10 이상
- SO-100 또는 SO-101 로봇
- USB 케이블

## 설치 단계

### 1. 저장소 클론 및 이동

```bash
cd /Users/kwangtaikim/Desktop/Rosota_lerobot/rosotaLerobot
```

### 2. 가상 환경 생성 (권장)

```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
# 또는
venv\Scripts\activate  # Windows
```

### 3. 패키지 설치

```bash
pip install -e .
```

### 4. 의존성 확인

```bash
rosota-lerobot info
```

## 사용법

### 1. 로봇 연결 확인

```bash
rosota-lerobot connect
```

### 2. 캘리브레이션 (처음 한 번만)

```bash
rosota-lerobot calibrate
```

캘리브레이션은 3단계로 진행됩니다:
- Step 1: 로봇을 초기 위치에 배치
- Step 2: 로봇을 캘리브레이션 위치에 배치
- Step 3: 완료 및 설정 저장

### 3. 키보드 제어

```bash
rosota-lerobot control
```

## 문제 해결

### 권한 오류 (Linux)

시리얼 포트 접근 권한이 필요한 경우:

```bash
sudo usermod -a -G dialout $USER
# 로그아웃 후 다시 로그인
```

또는:

```bash
sudo chmod 666 /dev/ttyUSB0  # 포트 번호에 맞게 변경
```

### Windows에서 포트를 찾을 수 없음

장치 관리자에서 COM 포트 번호를 확인하고, 필요시 관리자 권한으로 실행하세요.

