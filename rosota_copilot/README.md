# Rosota Copilot

SO Arm 100/101 Start Pack을 위한 웹 기반 Quick Start 시스템

## 📋 개요

Rosota Copilot은 SO Arm 100/101 로봇을 쉽게 연결, 캘리브레이션, 조작할 수 있도록 도와주는 웹 기반 대시보드입니다. 초보자도 직관적인 인터페이스를 통해 로봇을 빠르게 시작할 수 있습니다.

## ✨ 주요 기능

### 1. 자동 연결 감지
- **PID 기반 자동 감지**: CH340 칩셋 (PID 21971, 29987) 자동 감지
- **USB 포트 자동 스캔**: 5초마다 자동으로 로봇 포트 감지 및 연결
- **연결 상태 실시간 표시**: 상단 상태바에 연결 정보 표시

### 2. 전압 자동 감지 및 설정
- **전압 자동 감지**: 6V 또는 12V 자동 감지
- **기본 설정 자동 로드**: 전압에 맞는 기본 설정 파일 자동 로드
  - `so-100-6V.json` (6V용)
  - `so-100-12V.json` (12V용)
- **PID 게인 자동 적용**: 전압별 최적 PID 게인 자동 적용

### 3. 단계별 캘리브레이션 마법사
- **Step 1**: Position 1 - 모든 조인트를 0도 위치로 이동
- **Step 2**: Position 2 - CALIBRATION_POSITION으로 이동
- **Step 3**: Position 3 - 최종 검증
- **진행 상태 표시**: 진행률 바 및 단계별 안내 메시지
- **자동 토크 제어**: 각 단계에서 토크 자동 활성화/비활성화

### 4. 키보드 텔레오퍼레이션
- **3가지 제어 모드**:
  - **Joint 모드**: 각 관절 개별 제어 (6 DOF)
  - **Cartesian 모드**: 엔드 이펙터 위치/자세 제어
  - **Gripper 모드**: 그리퍼 제어
- **실시간 제어**: 50ms 간격 (20Hz)으로 명령 전송
- **한글 입력 모드 지원**: `e.code`를 사용한 물리적 키 감지
- **안전 기능**: E-Stop, 속도 조절, 조인트 제한 확인

### 5. 온보딩 튜토리얼
- **페이지 형태 튜토리얼**: 사이드바 메뉴에서 접근
- **3단계 가이드**: 연결 → 캘리브레이션 → 키보드 제어
- **페이지 네비게이션**: 이전/다음 버튼 및 인디케이터
- **첫 실행 시 자동 표시**: 처음 방문 시 튜토리얼 섹션으로 자동 이동

### 6. 다국어 지원
- **한국어/영어 지원**: 실시간 언어 전환
- **전체 UI 번역**: 모든 메뉴, 버튼, 메시지 번역
- **브라우저 언어 자동 감지**: 기본 언어 자동 설정

### 7. 테마 지원
- **Light/Dark/System 테마**: 사용자 선호도에 맞는 테마 선택
- **시스템 테마 자동 감지**: OS 설정에 따라 자동 전환
- **테마 설정 저장**: localStorage에 설정 저장

### 8. 실시간 모니터링
- **로봇 상태 실시간 업데이트**: 20Hz 업데이트 주기
- **조인트 위치 표시**: 현재 조인트 각도 실시간 표시
- **로그 시스템**: 실시간 로그 패널 (INFO, SUCCESS, WARNING, ERROR)

## 🚀 Quick Start

### 설치

```bash
# 프로젝트 디렉토리로 이동
cd /path/to/Rosota_lerobot

# 의존성 설치
pip install -r requirements.txt
```

### 실행

```bash
# 서버 실행
python -m rosota_copilot.server
```

기본 설정:
- 호스트: `0.0.0.0`
- 포트: `8000`
- 접속: 브라우저에서 `http://localhost:8000`

포트 변경:
```bash
HOST=0.0.0.0 PORT=80 python -m rosota_copilot.server
```

### 사용 방법

1. **로봇 연결**
   - USB 케이블로 로봇을 컴퓨터에 연결
   - 자동으로 포트 감지 및 연결 (또는 수동으로 포트 선택)

2. **캘리브레이션**
   - "Calibration" 섹션으로 이동
   - "📋 Open Calibration Wizard" 버튼 클릭
   - 마법사의 단계를 따라 캘리브레이션 완료

3. **로봇 제어**
   - "Control" 섹션으로 이동
   - "▶ Start Control" 버튼 클릭
   - 브라우저에 포커스를 두고 키보드로 로봇 제어

## ⌨️ 키보드 단축키

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

### Gripper 모드
- `C`: 그리퍼 토글

### 공통
- `M`: 모드 전환 (Joint → Cartesian → Gripper → Joint)
- `+/-`: 속도 조절
- `Space`: 긴급 정지 (E-Stop)

## 📁 프로젝트 구조

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
│   ├── so_arm.py          # SO-100 어댑터 (자동 감지, 전압 감지)
│   ├── calibration.py     # 캘리브레이션 마법사
│   ├── keyboard_control.py # 키보드 컨트롤러
│   ├── usb_scanner.py     # PID 기반 자동 감지
│   └── motors/
│       ├── __init__.py
│       ├── feetech.py     # FeetechMotorsBus
│       └── motor_utils.py
├── static/
│   └── js/
│       └── dashboard.js   # 프론트엔드 로직
├── templates/
│   └── index.html         # 대시보드 UI
└── resources/
    └── configs/
        ├── so-100-6V.json  # 6V 기본 설정
        └── so-100-12V.json # 12V 기본 설정
```

## 🔧 기술 스택

### 백엔드
- **FastAPI**: REST API 서버
- **Socket.IO**: 실시간 양방향 통신
- **FeetechMotorsBus**: 모터 제어 라이브러리 (phosphobot 참고)
- **pyserial**: 시리얼 통신

### 프론트엔드
- **HTML/CSS/JavaScript**: 순수 웹 기술
- **Socket.IO Client**: 실시간 통신
- **LocalStorage**: 사용자 설정 저장

### 하드웨어
- **모터**: Feetech STS3215 (6개, ID 1-6)
- **통신**: Serial (USB-C)
- **Baudrate**: 1,000,000 (1Mbps)
- **Resolution**: 4096 (12-bit)

## 📡 API 엔드포인트

### 연결
- `POST /api/connect`: 로봇 연결
- `POST /api/disconnect`: 로봇 연결 해제
- `GET /api/ports`: 사용 가능한 시리얼 포트 목록

### 상태
- `GET /api/state`: 현재 로봇 상태
- `GET /api/voltage`: 로봇 전압 정보

### 캘리브레이션
- `POST /api/calibration/home`: 홈 포지션으로 이동
- `POST /api/calibration/zero`: 조인트 제로 설정
- `POST /api/calibration/run`: 전체 캘리브레이션 실행
- `POST /api/calibration/wizard/step`: 캘리브레이션 마법사 단계 실행
- `GET /api/calibration/wizard/status`: 캘리브레이션 마법사 상태 조회
- `POST /api/calibration/wizard/reset`: 캘리브레이션 마법사 리셋

### 제어
- `POST /api/control/start`: 키보드 제어 시작
- `POST /api/control/stop`: 키보드 제어 중지
- `GET /api/control/status`: 키보드 제어 상태 조회

### 조인트 제어
- `POST /api/joint/move`: 조인트 상대 이동
- `POST /api/joint/set`: 조인트 절대 위치 설정

## 🔌 Socket.IO 이벤트

### 클라이언트 → 서버
- `control:key`: 키보드 입력 전송

### 서버 → 클라이언트
- `server:hello`: 서버 연결 확인
- `state:update`: 로봇 상태 업데이트 (20Hz)
- `control:response`: 제어 명령 응답
- `robot:auto_connected`: 자동 연결 알림
- `robot:error`: 에러 메시지
- `calibration:log`: 캘리브레이션 로그

## 🎨 UI 기능

### 사이드바 메뉴
- **튜토리얼**: 온보딩 가이드
- **연결**: 로봇 연결 설정
- **캘리브레이션**: 캘리브레이션 마법사
- **제어**: 키보드 제어
- **상태**: 로봇 상태 모니터링

### 상단 상태바
- 로봇 연결 상태
- 포트 정보
- 보드레이트 정보
- 테마/언어 전환 버튼

### 로그 패널
- 실시간 로그 표시
- 로그 레벨별 색상 구분
- 자동 스크롤 옵션
- 로그 지우기 기능

## 🛠️ 개발

### 환경 변수
- `HOST`: 서버 호스트 (기본값: `0.0.0.0`)
- `PORT`: 서버 포트 (기본값: `8000`)
- `ROBOT_PORT`: 기본 로봇 포트
- `ROBOT_BAUDRATE`: 기본 보드레이트 (기본값: `115200`)

### 디버깅
- 서버 로그: 콘솔에 상세 로그 출력
- 클라이언트 로그: 브라우저 콘솔에 로그 출력
- Socket.IO 디버그 모드: `socketio.AsyncServer(..., logger=True, engineio_logger=True)`

## 📝 라이선스

이 프로젝트는 phosphobot의 SO-100 구현을 참고하여 개발되었습니다.

## 🙏 참고

- **phosphobot**: SO-100 하드웨어 인터페이스 참고
- **FeetechMotorsBus**: 모터 제어 라이브러리

