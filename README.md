# Rosota Copilot

Phospho와 유사한 로봇 제어 대시보드 - SO Arm 100을 위한 웹 기반 제어 시스템

## 주요 기능

- 🔌 **로봇 연결**: Serial (USB) 또는 TCP/IP 연결 지원
- 🎯 **캘리브레이션**: 홈 포지션, 조인트 제로, TCP 오프셋 설정
- ⌨️ **키보드 제어**: 실시간 키보드 텔레오퍼레이션
  - Joint 모드: 각 관절 개별 제어
  - Cartesian 모드: 엔드 이펙터 위치/자세 제어
  - Gripper 모드: 그리퍼 제어
- 📊 **실시간 모니터링**: 로봇 상태 실시간 표시 (20Hz)
- 🎨 **모던 UI**: 다크 테마 대시보드 (rosota.run 스타일 참고)

## Quick Start

### 1. 의존성 설치

```bash
pip install -r requirements.txt
```

### 2. 서버 실행

```bash
python -m rosota_copilot.server
```

기본 설정:
- 호스트: `0.0.0.0`
- 포트: `8000`
- 접속: 브라우저에서 `http://localhost:8000`

포트 변경 (예: 80번 포트):
```bash
HOST=0.0.0.0 PORT=80 python -m rosota_copilot.server
```

### 3. 대시보드 사용

1. **연결**: Connection 카드에서 연결 타입(Serial/TCP) 선택 후 Connect 버튼 클릭
2. **캘리브레이션**: Home Position → Zero Joints → Run Calibration 순서로 진행
3. **제어**: 브라우저에 포커스를 두고 키보드로 로봇 제어

## 키보드 단축키

### Joint 모드
- `I/K`: Joint 1 ±
- `J/L`: Joint 2 ±
- `U/O`: Joint 3 ±
- `7/9`: Joint 4 ±
- `8/0`: Joint 5 ±
- `Y/H`: Joint 6 ±

### Cartesian 모드
- `W/S`: X ±
- `A/D`: Y ±
- `Q/E`: Z ±
- `R/F`: Roll ±
- `T/G`: Pitch ±
- `Z/X`: Yaw ±

### 공통
- `M`: 모드 전환 (Joint → Cartesian → Gripper → Joint)
- `+/-`: 속도 조절
- `Space`: 긴급 정지 (E-Stop)
- `C`: 그리퍼 토글 (Gripper 모드)

## 프로젝트 구조

```
rosota_copilot/
├── __init__.py
├── server.py              # FastAPI + Socket.IO 서버
├── config.py              # 설정 파일
├── api/
│   ├── __init__.py
│   └── routes.py          # REST API 엔드포인트
├── robot/
│   ├── __init__.py
│   ├── so_arm.py          # SO Arm 100 어댑터
│   ├── calibration.py     # 캘리브레이션 관리
│   └── keyboard_control.py # 키보드 컨트롤러
├── static/
│   └── js/
│       └── dashboard.js   # 프론트엔드 로직
└── templates/
    └── index.html         # 대시보드 HTML
```

## API 엔드포인트

### REST API

- `GET /api/health` - 서버 상태 확인
- `POST /api/connect` - 로봇 연결
- `POST /api/disconnect` - 로봇 연결 해제
- `GET /api/state` - 현재 로봇 상태
- `POST /api/calibration/home` - 홈 포지션으로 이동
- `POST /api/calibration/zero` - 조인트 제로 설정
- `POST /api/calibration/run` - 전체 캘리브레이션 실행
- `GET /api/calibration/load` - 캘리브레이션 데이터 로드

### WebSocket (Socket.IO)

- `control:key` - 키보드 입력 이벤트 전송
- `state:update` - 로봇 상태 업데이트 (서버 → 클라이언트)
- `control:response` - 제어 명령 응답
- `robot:error` - 로봇 에러 알림

## SO Arm 100 SDK 연동

현재는 시뮬레이션 모드로 동작합니다. 실제 로봇 제어를 위해서는:

1. `rosota_copilot/robot/so_arm.py`의 `SOArm100Adapter` 클래스에서 실제 SDK 연동
2. `connect()` 메서드: Serial 또는 TCP 연결 구현
3. `get_state()` 메서드: 로봇에서 상태 읽기
4. `move_joint_delta()`, `move_cartesian_delta()`: 로봇 명령 전송

예시 코드는 각 메서드의 TODO 주석에 포함되어 있습니다.

## 설정

`rosota_copilot/config.py`에서 다음 설정을 변경할 수 있습니다:

- 서버 호스트/포트
- 로봇 기본 연결 설정 (포트, 보드레이트, 호스트)
- 제어 파라미터 (스텝 크기, 속도 범위)
- 조인트 제한값
- 상태 업데이트 주기

## 데이터 저장

캘리브레이션 데이터는 `data/calibration/default.json`에 저장됩니다.

## 개발 상태

- ✅ 기본 서버 구조
- ✅ 웹 대시보드 UI
- ✅ 키보드 컨트롤러
- ✅ 캘리브레이션 관리
- ✅ WebSocket 실시간 통신
- ⏳ 실제 SO Arm 100 SDK 연동 (TODO)
- ⏳ 데이터 레코딩 (LeRobot 포맷)
- ⏳ 조이스틱/VR 컨트롤러 지원

## 라이선스

MIT

## 참고

- [Phospho](https://phospho.mintlify.app/) - 로봇 제어 대시보드 참고
- [Rosota](https://www.rosota.run/) - UI 디자인 참고
- [LeRobot](https://github.com/huggingface/lerobot) - 로봇 학습 프레임워크
