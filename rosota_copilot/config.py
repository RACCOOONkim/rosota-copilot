import os
from pathlib import Path
from typing import Dict, Any

# 프로젝트 루트
PROJECT_ROOT = Path(__file__).parent.parent
DATA_DIR = PROJECT_ROOT / "data"
CALIBRATION_DIR = DATA_DIR / "calibration"
RECORD_DIR = DATA_DIR / "records"

# 기본 설정
DEFAULT_CONFIG: Dict[str, Any] = {
	"server": {
		"host": os.getenv("HOST", "0.0.0.0"),
		"port": int(os.getenv("PORT", "8000")),
	},
	"robot": {
		"default_port": os.getenv("ROBOT_PORT", "/dev/ttyUSB0"),
		"default_baudrate": int(os.getenv("ROBOT_BAUDRATE", "115200")),
		"default_host": os.getenv("ROBOT_HOST", "192.168.1.100"),
		"default_tcp_port": int(os.getenv("ROBOT_TCP_PORT", "502")),
		"connection_timeout": 5.0,
		"state_update_rate": 20.0,  # Hz
	},
	"control": {
		"default_step_size": 5.0,  # degrees or mm
		"min_speed_multiplier": 0.1,
		"max_speed_multiplier": 2.0,
		"key_debounce_ms": 50,
	},
	"calibration": {
		"default_file": str(CALIBRATION_DIR / "default.json"),
	},
	"limits": {
		"joint_limits": [
			[-180, 180],  # Joint 1
			[-180, 180],  # Joint 2
			[-180, 180],  # Joint 3
			[-180, 180],  # Joint 4
			[-180, 180],  # Joint 5
			[-180, 180],  # Joint 6
		],
		"max_joint_velocity": 30.0,  # deg/s
		"max_cartesian_velocity": 100.0,  # mm/s
	},
}

# 디렉토리 생성
DATA_DIR.mkdir(exist_ok=True)
CALIBRATION_DIR.mkdir(exist_ok=True)
RECORD_DIR.mkdir(exist_ok=True)

