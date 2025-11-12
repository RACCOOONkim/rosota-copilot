# 아키텍처 문서

## 시스템 개요

Rosota Copilot은 SO Arm 100/101 로봇을 제어하기 위한 웹 기반 대시보드 시스템입니다. FastAPI와 Socket.IO를 사용하여 실시간 양방향 통신을 구현하고, 순수 웹 기술로 프론트엔드를 구성합니다.

## 아키텍처 다이어그램

```
┌─────────────────────────────────────────────────────────┐
│                    웹 브라우저 (클라이언트)                │
│  ┌──────────────────────────────────────────────────┐   │
│  │  HTML/CSS/JavaScript (dashboard.js)             │   │
│  │  - Socket.IO Client                              │   │
│  │  - UI 이벤트 처리                                 │   │
│  │  - 키보드 입력 처리                                │   │
│  └──────────────────────────────────────────────────┘   │
└──────────────────────┬──────────────────────────────────┘
                       │ HTTP / WebSocket
                       │
┌──────────────────────▼──────────────────────────────────┐
│              FastAPI + Socket.IO 서버                    │
│  ┌──────────────────────────────────────────────────┐   │
│  │  FastAPI (REST API)                               │   │
│  │  - /api/* 엔드포인트                               │   │
│  │  - 정적 파일 서빙                                  │   │
│  └──────────────────────────────────────────────────┘   │
│  ┌──────────────────────────────────────────────────┐   │
│  │  Socket.IO (실시간 통신)                           │   │
│  │  - state:update (20Hz)                           │   │
│  │  - control:key (키보드 입력)                      │   │
│  │  - calibration:log (캘리브레이션 로그)              │   │
│  └──────────────────────────────────────────────────┘   │
└──────────────────────┬──────────────────────────────────┘
                       │
┌──────────────────────▼──────────────────────────────────┐
│              로봇 제어 레이어                             │
│  ┌──────────────────────────────────────────────────┐   │
│  │  SOArm100Adapter                                  │   │
│  │  - 연결 관리                                       │   │
│  │  - 전압 감지                                       │   │
│  │  - 조인트 제어                                      │   │
│  │  - 상태 관리                                       │   │
│  └──────────────────────────────────────────────────┘   │
│  ┌──────────────────────────────────────────────────┐   │
│  │  KeyboardController                               │   │
│  │  - 키 매핑                                         │   │
│  │  - 모드 전환                                       │   │
│  │  - 제어 명령 생성                                   │   │
│  └──────────────────────────────────────────────────┘   │
│  ┌──────────────────────────────────────────────────┐   │
│  │  CalibrationManager                              │   │
│  │  - 캘리브레이션 마법사                             │   │
│  │  - 홈 포지션                                       │   │
│  │  - 조인트 제로                                     │   │
│  └──────────────────────────────────────────────────┘   │
└──────────────────────┬──────────────────────────────────┘
                       │
┌──────────────────────▼──────────────────────────────────┐
│              하드웨어 레이어                              │
│  ┌──────────────────────────────────────────────────┐   │
│  │  FeetechMotorsBus                                 │   │
│  │  - 시리얼 통신                                     │   │
│  │  - 모터 제어                                       │   │
│  └──────────────────────────────────────────────────┘   │
│                       │                                   │
│                       ▼                                   │
│              SO Arm 100/101 (하드웨어)                    │
│              - Feetech STS3215 모터 (6개)                 │
└──────────────────────────────────────────────────────────┘
```

## 컴포넌트 상세

### 1. 서버 레이어 (`server.py`)

#### FastAPI 애플리케이션
- **역할**: REST API 서버 및 정적 파일 서빙
- **주요 기능**:
  - API 라우팅 (`/api/*`)
  - 정적 파일 서빙 (`/static/*`)
  - HTML 템플릿 서빙 (`/`)
  - CORS 미들웨어

#### Socket.IO 서버
- **역할**: 실시간 양방향 통신
- **주요 이벤트**:
  - `connect`: 클라이언트 연결
  - `disconnect`: 클라이언트 연결 해제
  - `control:key`: 키보드 입력 처리
- **브로드캐스트**:
  - `state:update`: 로봇 상태 업데이트 (20Hz)
  - `control:response`: 제어 명령 응답
  - `robot:auto_connected`: 자동 연결 알림
  - `calibration:log`: 캘리브레이션 로그

### 2. API 레이어 (`api/routes.py`)

#### 연결 관련
- `POST /api/connect`: 로봇 연결
- `POST /api/disconnect`: 로봇 연결 해제
- `GET /api/ports`: 시리얼 포트 목록

#### 상태 관련
- `GET /api/state`: 로봇 상태 조회
- `GET /api/voltage`: 전압 정보 조회

#### 캘리브레이션 관련
- `POST /api/calibration/home`: 홈 포지션 이동
- `POST /api/calibration/zero`: 조인트 제로 설정
- `POST /api/calibration/run`: 전체 캘리브레이션 실행
- `POST /api/calibration/wizard/step`: 마법사 단계 실행
- `GET /api/calibration/wizard/status`: 마법사 상태 조회
- `POST /api/calibration/wizard/reset`: 마법사 리셋

#### 제어 관련
- `POST /api/control/start`: 키보드 제어 시작
- `POST /api/control/stop`: 키보드 제어 중지
- `GET /api/control/status`: 제어 상태 조회

#### 조인트 제어
- `POST /api/joint/move`: 조인트 상대 이동
- `POST /api/joint/set`: 조인트 절대 위치 설정

### 3. 로봇 제어 레이어

#### SOArm100Adapter (`robot/so_arm.py`)
- **역할**: SO-100 로봇 하드웨어 인터페이스
- **주요 기능**:
  - 연결 관리 (`connect()`, `disconnect()`)
  - 전압 감지 (`detect_voltage()`, `read_motor_voltage()`)
  - 설정 로드 (`load_default_config()`)
  - PID 게인 적용 (`apply_pid_gains()`, `set_pid_gains()`)
  - 조인트 제어 (`move_joint_delta()`, `move_joint_absolute()`)
  - Cartesian 제어 (`move_cartesian()`)
  - 그리퍼 제어 (`set_gripper()`)
  - 상태 조회 (`get_state()`)

#### KeyboardController (`robot/keyboard_control.py`)
- **역할**: 키보드 입력을 로봇 제어 명령으로 변환
- **주요 기능**:
  - 키 매핑 관리
  - 모드 전환 (Joint/Cartesian/Gripper)
  - 제어 시작/중지
  - E-Stop 처리
  - 속도 조절

#### CalibrationManager (`robot/calibration.py`)
- **역할**: 로봇 캘리브레이션 관리
- **주요 기능**:
  - 홈 포지션 이동 (`home()`)
  - 조인트 제로 설정 (`zero_joints()`)
  - 캘리브레이션 마법사 (`calibrate_step()`)
  - 캘리브레이션 데이터 저장/로드 (`save()`, `load()`)

#### USBScanner (`robot/usb_scanner.py`)
- **역할**: USB 포트 자동 감지
- **주요 기능**:
  - PID 기반 자동 감지 (`detect_robot_port()`)
  - 시리얼 포트 스캔 (`scan_serial_ports()`)

### 4. 프론트엔드 레이어

#### HTML 구조 (`templates/index.html`)
- **레이아웃**:
  - 상단 상태바 (연결 상태, 테마/언어 전환)
  - 좌측 사이드바 (메뉴)
  - 메인 콘텐츠 영역 (섹션별 콘텐츠)
  - 우측 로그 패널 (고정)
- **섹션**:
  - 튜토리얼
  - 연결
  - 캘리브레이션
  - 제어
  - 상태

#### JavaScript 로직 (`static/js/dashboard.js`)
- **Socket.IO 클라이언트**: 실시간 통신
- **UI 이벤트 처리**: 버튼 클릭, 메뉴 전환
- **키보드 입력 처리**: 키 입력 감지 및 전송
- **상태 업데이트**: 로봇 상태 실시간 표시
- **다국어 지원**: 동적 번역 시스템
- **테마 지원**: 테마 전환 및 적용

## 데이터 흐름

### 1. 로봇 연결 흐름

```
사용자 → [연결 버튼 클릭]
  ↓
프론트엔드 → POST /api/connect
  ↓
서버 → SOArm100Adapter.connect()
  ↓
FeetechMotorsBus → 시리얼 통신
  ↓
로봇 하드웨어
  ↓
전압 감지 → 설정 로드 → PID 게인 적용
  ↓
서버 → Socket.IO: robot:auto_connected
  ↓
프론트엔드 → UI 업데이트
```

### 2. 키보드 제어 흐름

```
사용자 → [키보드 입력]
  ↓
프론트엔드 → 키 입력 감지 (e.code 사용)
  ↓
프론트엔드 → Socket.IO: control:key
  ↓
서버 → KeyboardController.handle_key_event()
  ↓
서버 → SOArm100Adapter (조인트/Cartesian/그리퍼 제어)
  ↓
FeetechMotorsBus → 모터 제어
  ↓
로봇 하드웨어
  ↓
서버 → Socket.IO: control:response
  ↓
프론트엔드 → UI 피드백
```

### 3. 상태 업데이트 흐름

```
서버 → state_update_loop() (20Hz)
  ↓
SOArm100Adapter.get_state()
  ↓
Socket.IO: state:update
  ↓
프론트엔드 → UI 업데이트
```

### 4. 캘리브레이션 흐름

```
사용자 → [캘리브레이션 마법사 시작]
  ↓
프론트엔드 → POST /api/calibration/wizard/step
  ↓
서버 → CalibrationManager.calibrate_step()
  ↓
CalibrationManager → SOArm100Adapter (조인트 이동)
  ↓
FeetechMotorsBus → 모터 제어
  ↓
로봇 하드웨어
  ↓
서버 → Socket.IO: calibration:log
  ↓
프론트엔드 → 로그 표시 및 진행 상태 업데이트
```

## 상태 관리

### 전역 인스턴스
- `robot_adapter`: SOArm100Adapter 인스턴스
- `keyboard_controller`: KeyboardController 인스턴스
- `calibration_manager`: CalibrationManager 인스턴스

### app.state
- FastAPI의 `app.state`를 통해 인스턴스 공유
- API 라우트에서 `request.app.state`로 접근

### 클라이언트 상태
- `localStorage`: 사용자 설정 저장 (테마, 언어, 튜토리얼 완료 여부)
- JavaScript 변수: 현재 모드, 연결 상태, 제어 상태 등

## 비동기 처리

### 서버 측
- **FastAPI**: 비동기 함수 지원
- **run_in_executor**: 블로킹 작업을 별도 스레드에서 실행
  - 캘리브레이션 작업
  - 로봇 연결
  - 조인트 이동

### 클라이언트 측
- **이벤트 루프**: 키보드 입력 처리 (50ms 간격)
- **Socket.IO**: 비동기 이벤트 기반 통신

## 에러 처리

### 서버 측
- **예외 처리**: try-except 블록으로 모든 API 엔드포인트 보호
- **에러 응답**: HTTPException 또는 JSON 응답
- **로깅**: 상세한 에러 메시지 및 트레이스백

### 클라이언트 측
- **에러 표시**: 로그 패널에 에러 메시지 표시
- **연결 상태 확인**: 제어 전 연결 상태 확인
- **조인트 제한 확인**: 이동 전 제한 범위 확인

## 성능 최적화

### 서버 측
- **상태 업데이트 주기**: 20Hz (50ms 간격)
- **비동기 처리**: 블로킹 작업을 별도 스레드에서 실행
- **연결 풀링**: FeetechMotorsBus 재사용

### 클라이언트 측
- **키 입력 디바운싱**: 50ms 간격으로 명령 전송
- **이벤트 위임**: 이벤트 리스너 최적화
- **로컬 스토리지**: 사용자 설정 캐싱

## 보안 고려사항

### 현재 구현
- **CORS**: 모든 오리진 허용 (개발 환경)
- **입력 검증**: API 엔드포인트에서 입력 검증
- **조인트 제한**: 하드웨어 제한 확인

### 향후 개선
- **인증/인가**: 사용자 인증 시스템
- **CORS 제한**: 프로덕션 환경에서 특정 오리진만 허용
- **HTTPS**: 보안 통신 지원

