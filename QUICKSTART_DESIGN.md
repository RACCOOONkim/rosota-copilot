# SO Arm 100/101 Start Pack - Quick Start 시스템 설계

## 목표
SO Arm 100/101 Start Pack 사용자가 **연결, 캘리브레이션, 조작**을 쉽게 할 수 있는 시스템 구축

## 핵심 기능

### 1. 자동 연결 감지
- **PID 기반 자동 감지**: CH340 칩셋 (PID 21971 또는 29987) 사용
- **포트 자동 스캔**: USB 연결 시 자동으로 로봇 감지
- **연결 상태 표시**: 실시간 연결 상태 및 포트 정보 표시

### 2. 전압 자동 감지 및 설정
- **전압 감지**: 6V 또는 12V 자동 감지
- **기본 설정 자동 로드**: 전압에 맞는 기본 설정 파일 자동 로드
  - `so-100-6V.json` 또는 `so-100-12V.json`
- **PID 게인 설정**: 전압별 최적 PID 게인 자동 적용

### 3. 단계별 캘리브레이션 마법사
phosphobot의 캘리브레이션 프로세스 참고:
- **Step 0**: 초기화 (전압 감지, 기본 설정 로드)
- **Step 1**: Position 1 - 모든 조인트를 0도 위치로 이동
- **Step 2**: Position 2 - CALIBRATION_POSITION으로 이동
- **Step 3**: Position 3 - 최종 검증

각 단계마다:
- 시각적 가이드 (로봇 위치 이미지/애니메이션)
- 진행 상태 표시
- 다음 단계 안내

### 4. 직관적인 조작 인터페이스
- **키보드 제어**: 즉시 사용 가능한 키보드 매핑
- **시각적 피드백**: 누른 키 표시, 조인트 위치 실시간 업데이트
- **안전 기능**: E-Stop, 속도 조절, 제한 범위 확인

## 기술 스택

### 하드웨어 정보
- **모터**: Feetech STS3215 (6개, ID 1-6)
- **통신**: Serial (USB-C)
- **Baudrate**: 1,000,000 (1Mbps)
- **Resolution**: 4096 (12-bit)

### 소프트웨어 구조
```
rosota_copilot/
├── robot/
│   ├── so_arm.py          # SO-100 어댑터 (자동 감지, 전압 감지)
│   ├── calibration.py      # 캘리브레이션 마법사
│   └── motors/
│       └── feetech.py     # FeetechMotorsBus
├── api/
│   └── routes.py          # REST API (연결, 캘리브레이션, 제어)
├── static/
│   └── js/
│       └── dashboard.js    # 프론트엔드 (온보딩, 캘리브레이션 UI)
└── resources/
    └── configs/
        ├── so-100-6V.json  # 6V 기본 설정
        └── so-100-12V.json # 12V 기본 설정
```

## 구현 계획

### Phase 1: 자동 연결 개선
- [x] USB 포트 스캔
- [ ] PID 기반 자동 감지
- [ ] 연결 상태 실시간 표시

### Phase 2: 전압 감지 및 설정
- [ ] 전압 읽기 API
- [ ] 기본 설정 파일 로드
- [ ] PID 게인 자동 설정

### Phase 3: 캘리브레이션 마법사
- [ ] 단계별 UI 구현
- [ ] 시각적 가이드 추가
- [ ] 진행 상태 표시

### Phase 4: 온보딩 튜토리얼
- [ ] 첫 실행 시 튜토리얼 표시
- [ ] 단계별 가이드
- [ ] 도움말 시스템

## 참고 자료
- phosphobot SO-100 구현: `phosphobot/phosphobot/phosphobot/hardware/so100.py`
- 기본 설정: `phosphobot/resources/default/so-100-6V.json`
- 캘리브레이션 예제: `phosphobot/resources/calibration/so-100_6V_config.json`
- 공식 문서: https://docs.phospho.ai/so-101/quickstart

