# Rosota LeRobot

SO-100과 SO-101 로봇을 위한 최소한의 제어 시스템입니다.

## 기능

- 🔌 **로봇 연결**: USB 시리얼 포트를 통한 자동 감지 및 연결
- 🔧 **캘리브레이션**: 3단계 캘리브레이션 프로세스
- ⌨️ **키보드 제어**: 간단한 키보드 입력으로 로봇 제어

## 설치

### 필수 요구사항

이 프로젝트는 `phosphobot`의 `FeetechMotorsBus` 구현을 사용합니다. 다음 중 하나를 선택하세요:

**옵션 1: 로컬 phosphobot 사용 (권장)**
```bash
# phosphobot이 같은 디렉토리에 있는 경우
cd /Users/kwangtaikim/Desktop/Rosota_lerobot
# rosotaLerobot은 자동으로 ../phosphobot을 찾습니다
cd rosotaLerobot
pip install -e .
```

**옵션 2: phosphobot 패키지 설치**
```bash
pip install phosphobot
cd rosotaLerobot
pip install -e .
```

**옵션 3: feetech-servo-sdk 사용 (실험적)**
```bash
pip install feetech-servo-sdk
cd rosotaLerobot
pip install -e .
```

## 사용법

### 1. 로봇 연결
```bash
rosota-lerobot connect
```

### 2. 캘리브레이션
```bash
rosota-lerobot calibrate
```

### 3. 키보드 제어
```bash
rosota-lerobot control
```

## 키보드 제어 키

- **화살표 키**: 조인트 1, 2 제어
- **W/S**: 조인트 3 제어
- **A/D**: 조인트 4 제어
- **Q/E**: 조인트 5 제어
- **Space**: 그리퍼 열기/닫기
- **Esc**: 종료

