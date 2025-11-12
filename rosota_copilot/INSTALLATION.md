# 설치 및 실행 가이드

## 시스템 요구사항

- **Python**: 3.10 이상
- **운영체제**: Linux, macOS, Windows
- **하드웨어**: SO Arm 100/101 로봇, USB 케이블

## 설치

### 1. 저장소 클론

```bash
git clone <repository-url>
cd Rosota_lerobot
```

### 2. 가상 환경 생성 (선택사항)

```bash
python3 -m venv venv
source venv/bin/activate  # Linux/macOS
# 또는
venv\Scripts\activate  # Windows
```

### 3. 의존성 설치

```bash
pip install -r requirements.txt
```

### 4. 환경 변수 설정 (선택사항)

`.env` 파일을 생성하여 환경 변수를 설정할 수 있습니다:

```env
HOST=0.0.0.0
PORT=8000
ROBOT_PORT=/dev/ttyUSB0
ROBOT_BAUDRATE=115200
```

## 실행

### 기본 실행

```bash
python -m rosota_copilot.server
```

서버가 시작되면 브라우저에서 `http://localhost:8000`으로 접속합니다.

### 포트 변경

```bash
HOST=0.0.0.0 PORT=80 python -m rosota_copilot.server
```

### 프로덕션 실행

```bash
uvicorn rosota_copilot.server:asgi --host 0.0.0.0 --port 8000 --factory
```

## 하드웨어 연결

### 1. USB 케이블 연결
- SO Arm 100/101 로봇을 USB 케이블로 컴퓨터에 연결
- 로봇 전원이 켜져 있는지 확인

### 2. 자동 연결
- 서버가 시작되면 자동으로 로봇 포트를 감지하고 연결을 시도합니다
- 5초마다 자동 스캔을 수행하여 연결되지 않은 경우 재시도합니다

### 3. 수동 연결
- 대시보드의 "Connection" 섹션에서 포트를 선택하고 "Connect" 버튼 클릭

## 문제 해결

### 포트를 찾을 수 없는 경우

1. USB 케이블이 제대로 연결되었는지 확인
2. 로봇 전원이 켜져 있는지 확인
3. 다른 프로그램이 포트를 사용 중인지 확인
4. 권한 문제 확인 (Linux/macOS):
   ```bash
   sudo chmod 666 /dev/ttyUSB0
   ```

### 연결이 실패하는 경우

1. 보드레이트 확인 (기본값: 115200)
2. 로봇 전원 확인
3. USB 케이블 교체 시도
4. 서버 로그 확인

### 모터가 움직이지 않는 경우

1. 로봇이 연결되어 있는지 확인
2. E-Stop 상태 확인 (Space 키로 해제)
3. 조인트 제한 확인
4. 캘리브레이션 완료 여부 확인

## 개발 모드

### 디버그 모드 실행

```bash
# Socket.IO 디버그 로그 활성화
# server.py에서 logger=True, engineio_logger=True 설정
python -m rosota_copilot.server
```

### 로그 확인

- **서버 로그**: 콘솔에 출력
- **클라이언트 로그**: 브라우저 개발자 도구 콘솔
- **Socket.IO 로그**: 서버 콘솔 및 브라우저 콘솔

## 의존성

주요 의존성 패키지:
- `fastapi`: REST API 서버
- `python-socketio`: Socket.IO 서버
- `uvicorn`: ASGI 서버
- `pyserial`: 시리얼 통신
- `numpy`: 수치 계산
- `python-dotenv`: 환경 변수 관리

전체 의존성 목록은 `requirements.txt`를 참조하세요.

