# 모터 설정 기능 통합 분석

## LeRobot "Configure the motors" 기능 분석

### 1. 포트 찾기 (`lerobot-find-port`)
- **방식**: USB 케이블 연결 전후 포트 비교
- **프로세스**:
  1. 현재 연결된 포트 목록 확인
  2. 사용자에게 USB 케이블 제거 요청
  3. 다시 포트 목록 확인
  4. 차이점으로 MotorsBus 포트 식별

### 2. 모터 설정 (`lerobot-setup-motors`)
- **목적**: 각 모터에 고유 ID와 baudrate 설정
- **프로세스**:
  1. 각 모터를 컨트롤러에 **단독 연결**
  2. 모터 ID 설정 (1-6)
  3. Baudrate 설정 (1,000,000)
  4. EEPROM에 저장 (Lock 해제 → 설정 → Lock)

**SO-100 Follower 모터 순서:**
- gripper (ID: 6)
- wrist_roll (ID: 5)
- wrist_flex (ID: 4)
- elbow_flex (ID: 3)
- shoulder_lift (ID: 2)
- shoulder_pan (ID: 1)

**SO-100 Leader 모터 순서:**
- 동일 (follower와 같은 순서)

## 현재 프로젝트 상태

### ✅ 이미 구현된 기능
1. **FeetechMotorsBus 클래스** (`rosota_copilot/robot/motors/feetech.py`)
   - `write_with_motor_ids()`: 모터 ID 설정 가능
   - `read_with_motor_ids()`: 모터 ID 읽기 가능
   - `set_bus_baudrate()`: Bus baudrate 설정 가능
   - `find_motor_indices()`: 연결된 모터 ID 찾기

2. **포트 스캔 기능** (`rosota_copilot/robot/usb_scanner.py`)
   - `scan_serial_ports()`: 시리얼 포트 스캔
   - `detect_robot_port()`: PID 기반 자동 감지
   - ⚠️ **부족**: LeRobot 방식 (연결 전후 비교) 없음

3. **API 구조** (`rosota_copilot/api/routes.py`)
   - REST API 엔드포인트 구조 존재
   - Socket.IO 통합 가능

4. **참고 구현** (`phosphobot/scripts/feetech/configure_motor.py`)
   - 모터 설정 로직이 이미 구현되어 있음
   - Lock 해제 → ID/Baudrate 설정 → Lock 프로세스

### ❌ 부족한 기능
1. **포트 찾기 (LeRobot 방식)**
   - 연결 전후 포트 비교 기능 없음

2. **모터 설정 마법사**
   - 단계별 모터 설정 UI 없음
   - 백엔드 API 엔드포인트 없음

3. **웹 UI 통합**
   - 모터 설정 페이지/모달 없음

## 통합 가능성 평가

### ✅ **통합 가능 (High Confidence)**

**이유:**
1. 핵심 기능 (`FeetechMotorsBus`)이 이미 구현되어 있음
2. 참고할 수 있는 구현 (`phosphobot/scripts/feetech/configure_motor.py`)이 있음
3. API 구조가 이미 존재하여 확장 가능
4. 웹 UI 구조가 있어 통합 용이

### 구현 계획

#### 1. 백엔드 구현
- **파일**: `rosota_copilot/robot/motor_setup.py` (새로 생성)
  - `find_port_by_disconnect()`: LeRobot 방식 포트 찾기
  - `MotorSetupManager`: 모터 설정 관리 클래스
  - `configure_single_motor()`: 단일 모터 설정

- **API 엔드포인트** (`rosota_copilot/api/routes.py`에 추가):
  - `POST /setup/find-port`: 포트 찾기
  - `POST /setup/motor`: 단일 모터 설정
  - `GET /setup/status`: 설정 진행 상태
  - `POST /setup/reset`: 설정 초기화

#### 2. 프론트엔드 구현
- **UI**: 모터 설정 마법사 (캘리브레이션 마법사와 유사)
  - 단계별 가이드
  - 각 모터별 설정 진행 표시
  - 실시간 상태 업데이트

#### 3. Socket.IO 이벤트
- `setup:port-found`: 포트 찾기 완료
- `setup:motor-configured`: 모터 설정 완료
- `setup:error`: 에러 발생

## 구현 우선순위

### Phase 1: 핵심 기능 (필수)
1. ✅ 포트 찾기 기능 (LeRobot 방식)
2. ✅ 단일 모터 설정 API
3. ✅ 기본 웹 UI (단계별 가이드)

### Phase 2: 개선 (선택)
1. ⚪ 설정 진행 상태 저장/복원
2. ⚪ 설정 검증 기능
3. ⚪ 에러 복구 가이드

## 예상 구현 시간
- **백엔드**: 2-3시간
- **프론트엔드**: 2-3시간
- **테스트 및 디버깅**: 1-2시간
- **총 예상 시간**: 5-8시간

## 주의사항
1. **하드웨어 요구사항**:
   - 각 모터를 단독으로 연결해야 함
   - 전원 공급 필요
   - USB 케이블 연결/해제 필요

2. **사용자 경험**:
   - 명확한 단계별 가이드 필요
   - 에러 메시지가 명확해야 함
   - 진행 상태 시각화 필요

3. **안전성**:
   - 설정 중 다른 작업 방지
   - 설정 실패 시 롤백 가능

## 결론
**✅ 통합 가능하며, 구현이 용이함**

현재 프로젝트 구조가 잘 갖춰져 있어 LeRobot의 모터 설정 기능을 통합하기에 적합합니다. 핵심 기능이 이미 구현되어 있고, 참고할 수 있는 코드도 있어 빠르게 구현할 수 있습니다.

