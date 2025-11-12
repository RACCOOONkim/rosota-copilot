# 설정 가이드

## 문제 해결: FeetechMotorsBus Import 오류

현재 `rosota-lerobot`은 phosphobot의 `FeetechMotorsBus` 구현을 사용합니다.

### 해결 방법

**방법 1: phosphobot을 로컬에서 사용 (개발용)**

phosphobot이 같은 디렉토리에 있다면, 다음 명령으로 phosphobot을 설치하세요:

```bash
cd /Users/kwangtaikim/Desktop/Rosota_lerobot/phosphobot/phosphobot
pip install -e . --no-deps  # 의존성 없이 설치 (feetech만 사용)
```

그런 다음 rosotaLerobot을 설치:

```bash
cd /Users/kwangtaikim/Desktop/Rosota_lerobot/rosotaLerobot
pip install -e .
```

**방법 2: phosphobot 패키지 설치 (권장)**

```bash
pip install phosphobot
cd /Users/kwangtaikim/Desktop/Rosota_lerobot/rosotaLerobot
pip install -e .
```

**방법 3: 임시 해결책 - feetech 모듈 직접 복사**

phosphobot의 feetech 관련 파일을 rosotaLerobot에 복사:

```bash
# feetech 관련 파일 복사
cp -r ../phosphobot/phosphobot/phosphobot/hardware/motors ./src/rosota_lerobot/robot/
```

그리고 `so100.py`에서 import 경로를 수정하세요.

## 현재 상태

- ✅ 프로젝트 구조 완성
- ✅ 핵심 기능 구현 완료
- ⚠️ FeetechMotorsBus import 문제 (phosphobot 의존성 필요)

