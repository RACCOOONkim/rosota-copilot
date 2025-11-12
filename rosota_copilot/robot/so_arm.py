from typing import Any, Dict, List, Optional
import time
import math
import numpy as np
import os
from ..config import DEFAULT_CONFIG

# SO-100은 Feetech 모터를 사용하며 FeetechMotorsBus를 사용합니다
# phosphobot의 구현을 참고
try:
	from .motors.feetech import FeetechMotorsBus
	HAS_FEETECH = True
except ImportError:
	HAS_FEETECH = False
	print("Warning: FeetechMotorsBus not available. SO-100 control will be simulated.")


class SOArm100Adapter:
	"""
	SO Arm 100 로봇 어댑터
	Feetech STS3215 모터를 사용하는 SO-100 로봇 제어
	phosphobot의 SO-100 구현을 참고
	"""

	# SO-100 설정 (phosphobot 참고)
	BAUDRATE = 1000000  # 1Mbps
	RESOLUTION = 4096  # 12-bit resolution
	
	# 모터 설정 (phosphobot 참고)
	MOTORS = {
		"shoulder_pan": [1, "sts3215"],    # Joint 1
		"shoulder_lift": [2, "sts3215"],   # Joint 2
		"elbow_flex": [3, "sts3215"],      # Joint 3
		"wrist_flex": [4, "sts3215"],     # Joint 4
		"wrist_roll": [5, "sts3215"],     # Joint 5
		"gripper": [6, "sts3215"],         # Joint 6 (그리퍼)
	}
	
	# 조인트 이름 매핑
	JOINT_NAMES = list(MOTORS.keys())
	SERVO_IDS = [v[0] for v in MOTORS.values()]
	
	# 캘리브레이션 포지션 (phosphobot 참고, 라디안 단위)
	CALIBRATION_POSITION = [
		math.pi / 2,   # Joint 1: 90도
		math.pi / 2,   # Joint 2: 90도
		-math.pi / 2,  # Joint 3: -90도
		-math.pi / 2,  # Joint 4: -90도
		math.pi / 2,   # Joint 5: 90도
		math.pi / 2,   # Joint 6: 90도
	]

	def __init__(self) -> None:
		self.connected: bool = False
		self.connection_info: Dict[str, Any] = {}
		
		# FeetechMotorsBus 사용
		self.motors_bus: Optional[FeetechMotorsBus] = None
		
		# 시뮬레이션용 상태 (실제 연결 실패 시 사용)
		self._sim_joint_positions = [0.0] * 6
		self._sim_tcp_pose = {"x": 0.0, "y": 0.0, "z": 0.0, "rx": 0.0, "ry": 0.0, "rz": 0.0}
		self._sim_gripper = {"opened": True, "width": 0.03}
		
		# 제한값
		self.joint_limits = DEFAULT_CONFIG["limits"]["joint_limits"]
		self.max_joint_velocity = DEFAULT_CONFIG["limits"]["max_joint_velocity"]
		
		# 캘리브레이션 오프셋 (라디안)
		self.calibration_offsets = [0.0] * 6
		
		# 로봇 설정 (전압, PID 게인 등)
		self.config: Optional[Dict[str, Any]] = None
		self.detected_voltage: Optional[str] = None  # "6V" or "12V"
	
	@property
	def servo_id_to_motor_name(self) -> Dict[int, str]:
		"""서보 ID를 모터 이름으로 매핑"""
		return {v[0]: k for k, v in self.MOTORS.items()}

	def connect(self, port: Optional[str] = None, host: Optional[str] = None, baudrate: Optional[int] = None) -> bool:
		"""
		로봇 연결
		SO-100은 Serial 통신만 지원 (TCP 미지원)
		phosphobot의 FeetechMotorsBus 사용
		"""
		if not port:
			return False
		
		baud = baudrate or self.BAUDRATE
		
		# FeetechMotorsBus를 사용한 실제 연결
		if HAS_FEETECH:
			try:
				# FeetechMotorsBus 초기화 및 연결
				self.motors_bus = FeetechMotorsBus(port=port, motors=self.MOTORS)
				self.motors_bus.connect()
				
				# 기본 캘리브레이션 설정 (FeetechMotorsBus가 필요로 함)
				# phosphobot 방식: 모든 모터를 DEGREE 모드로 설정
				from .motors.feetech import CalibrationMode
				calibration_data = {
					"motor_names": list(self.MOTORS.keys()),
					"calib_mode": [CalibrationMode.DEGREE.name] * len(self.MOTORS),
					"drive_mode": [0] * len(self.MOTORS),  # 0 = non-inverted
					"homing_offset": [0] * len(self.MOTORS),  # 나중에 zero_joints에서 업데이트
				}
				self.motors_bus.set_calibration(calibration_data)
				print("FeetechMotorsBus calibration set")
				
				# 전압 감지 및 기본 설정 로드
				voltage = self.detect_voltage()
				self.load_default_config(voltage)
				
				# 연결 성공 후 토크 활성화 시도
				try:
					self.enable_torque()
					print("Torque enabled for all servos")
				except Exception as e:
					print(f"Warning: Failed to enable torque: {e}. You may need to enable torque manually.")
				
				self.connected = True
				self.connection_info = {
					"port": port,
					"host": None,
					"baudrate": baud,
					"connected_at": time.time()
				}
				print(f"SO-100 connected successfully on {port} at {baud} baud using FeetechMotorsBus")
				return True
			except Exception as e:
				print(f"Error connecting to SO-100: {e}")
				import traceback
				traceback.print_exc()
				if self.motors_bus:
					try:
						self.motors_bus.disconnect()
					except:
						pass
				self.motors_bus = None
				return False
		else:
			# FeetechMotorsBus가 없으면 시뮬레이션 모드
			print("Warning: FeetechMotorsBus not available, using simulation mode")
			self.connected = True
			self.connection_info = {
				"port": port,
				"host": None,
				"baudrate": baud,
				"connected_at": time.time()
			}
			return True

	def disconnect(self) -> None:
		"""로봇 연결 해제"""
		if self.motors_bus:
			try:
				# 토크 비활성화
				self.disable_torque()
				# 연결 해제
				self.motors_bus.disconnect()
			except Exception as e:
				print(f"Error disconnecting: {e}")
		
		self.motors_bus = None
		self.connected = False
		self.connection_info = {}

	def _degrees_to_steps(self, degrees: float) -> int:
		"""
		각도를 스텝으로 변환
		phosphobot 방식: degrees / 180 * resolution / 2
		FeetechMotorsBus는 revert_calibration을 사용하므로, 여기서는 원시 스텝으로 변환
		"""
		# -180~180도를 -2048~2048 스텝으로 변환
		steps = int(degrees / 180.0 * (self.RESOLUTION / 2))
		return steps

	def _steps_to_degrees(self, steps: int) -> float:
		"""
		스텝을 각도로 변환
		phosphobot 방식: steps / (resolution / 2) * 180
		"""
		# -2048~2048 스텝을 -180~180도로 변환
		degrees = steps / (self.RESOLUTION / 2) * 180.0
		return degrees

	def _read_joint_position(self, joint_index: int) -> Optional[float]:
		"""특정 조인트의 현재 위치 읽기 (도 단위)"""
		if not self.connected or not self.motors_bus:
			return None
		
		if joint_index < 0 or joint_index >= len(self.JOINT_NAMES):
			return None
		
		motor_name = self.JOINT_NAMES[joint_index]
		
		try:
			# FeetechMotorsBus를 사용하여 위치 읽기
			# FeetechMotorsBus.read는 apply_calibration을 적용하여 각도(도)로 반환함
			position = self.motors_bus.read("Present_Position", motor_names=motor_name)
			if isinstance(position, np.ndarray):
				position = position[0] if len(position) > 0 else None
			if position is None:
				return None
			
			# FeetechMotorsBus는 이미 각도(도)로 변환된 값을 반환함
			degrees = float(position)
			
			# zero_joints에서 설정한 calibration_offsets는 이미 FeetechMotorsBus의
			# 캘리브레이션에 포함되어야 하므로, 여기서는 추가로 빼지 않음
			# 대신 zero_joints에서 FeetechMotorsBus의 캘리브레이션을 업데이트해야 함
			return degrees
			
		except Exception as e:
			print(f"Error reading joint {joint_index}: {e}")
			import traceback
			traceback.print_exc()
			return None

	def get_state(self) -> Dict[str, Any]:
		"""
		현재 로봇 상태 반환
		실제 하드웨어에서 읽거나 시뮬레이션 데이터 반환
		"""
		if not self.connected:
			return {
				"joint_positions": [0.0] * 6,
				"joint_velocities": [0.0] * 6,
				"tcp_pose": {"x": 0.0, "y": 0.0, "z": 0.0, "rx": 0.0, "ry": 0.0, "rz": 0.0},
				"gripper": {"opened": True, "width": 0.03},
				"status": "Disconnected",
				"errors": [],
			}
		
		# 실제 하드웨어에서 읽기
		if self.motors_bus:
			joint_positions = []
			for i in range(6):
				pos = self._read_joint_position(i)
				if pos is not None:
					joint_positions.append(pos)
					self._sim_joint_positions[i] = pos  # 캐시 업데이트
				else:
					joint_positions.append(self._sim_joint_positions[i])  # 캐시 사용
		else:
			# 시뮬레이션 모드
			joint_positions = self._sim_joint_positions.copy()
		
		return {
			"joint_positions": joint_positions,
			"joint_velocities": [0.0] * 6,  # TODO: 실제 속도 읽기
			"tcp_pose": self._sim_tcp_pose.copy(),
			"gripper": self._sim_gripper.copy(),
			"status": "Connected",
			"errors": [],
		}

	def move_joint_delta(self, joint_index: int, delta_deg: float) -> bool:
		"""
		조인트 상대 이동
		실제 하드웨어에 명령 전송
		phosphobot의 FeetechMotorsBus 사용
		"""
		if not self.connected:
			print(f"[SOArm] Robot not connected, cannot move joint {joint_index}")
			return False
		
		if joint_index < 0 or joint_index >= 6:
			print(f"[SOArm] Invalid joint index: {joint_index}")
			return False
		
		# 실제 하드웨어에 명령 전송
		if self.motors_bus:
			motor_name = self.JOINT_NAMES[joint_index]
			
			try:
				# 토크 상태 확인 및 필요시 활성화
				try:
					import numpy as np
					torque_status = self.motors_bus.read("Torque_Enable", motor_names=motor_name)
					if isinstance(torque_status, np.ndarray):
						torque_status = torque_status[0] if len(torque_status) > 0 else 0
					if torque_status != 1:
						print(f"[SOArm] Torque disabled for {motor_name}, enabling...")
						self.motors_bus.write("Torque_Enable", values=[1], motor_names=motor_name)
						print(f"[SOArm] Torque enabled for {motor_name}")
				except Exception as e:
					print(f"[SOArm] Warning: Could not check/enable torque: {e}")
					# 토크 확인 실패해도 계속 진행
				
				# 현재 위치 읽기
				current_pos = self._read_joint_position(joint_index)
				if current_pos is None:
					print(f"[SOArm] Could not read current position for joint {joint_index}, using cached value")
					current_pos = self._sim_joint_positions[joint_index]
				
				# 새 위치 계산
				new_position = current_pos + delta_deg
				
				# 제한 확인
				limits = self.joint_limits[joint_index]
				if new_position < limits[0] or new_position > limits[1]:
					limit_type = "lower" if new_position < limits[0] else "upper"
					print(f"[SOArm] Joint {joint_index} ({motor_name}) limit exceeded: {new_position:.2f}° not in [{limits[0]:.2f}, {limits[1]:.2f}] (current: {current_pos:.2f}°, delta: {delta_deg:.2f}°, {limit_type} limit)")
					return False  # 제한 초과
				
				# FeetechMotorsBus.write는 각도(도) 값을 받아서 revert_calibration을 자동으로 적용함
				# calibration_offsets는 FeetechMotorsBus의 캘리브레이션에 포함되어야 하므로
				# 여기서는 직접 각도 값을 전달
				print(f"[SOArm] Moving joint {joint_index} ({motor_name}): {current_pos:.2f}° -> {new_position:.2f}° (delta: {delta_deg:.2f}°)")
				self.motors_bus.write("Goal_Position", values=[new_position], motor_names=motor_name)
				print(f"[SOArm] Joint {joint_index} write command sent successfully")
				
				# 시뮬레이션 상태 업데이트
				self._sim_joint_positions[joint_index] = new_position
				return True
				
			except Exception as e:
				print(f"[SOArm] Error moving joint {joint_index}: {e}")
				import traceback
				traceback.print_exc()
				return False
		else:
			# 시뮬레이션 모드
			current_pos = self._sim_joint_positions[joint_index]
			new_position = current_pos + delta_deg
			limits = self.joint_limits[joint_index]
			if new_position < limits[0] or new_position > limits[1]:
				return False
			self._sim_joint_positions[joint_index] = new_position
			return True

	def move_cartesian_delta(self, dx: float, dy: float, dz: float, drx: float, dry: float, drz: float) -> bool:
		"""
		Cartesian 상대 이동
		SO-100은 직접 IK가 없으므로 조인트 제어로 변환 필요
		현재는 시뮬레이션만 지원
		"""
		if not self.connected:
			return False
		
		# TODO: IK 계산 또는 로봇 컨트롤러 호출
		# 현재는 시뮬레이션만
		self._sim_tcp_pose["x"] += dx
		self._sim_tcp_pose["y"] += dy
		self._sim_tcp_pose["z"] += dz
		self._sim_tcp_pose["rx"] += drx
		self._sim_tcp_pose["ry"] += dry
		self._sim_tcp_pose["rz"] += drz
		
		return True

	def read_motor_voltage(self, servo_id: int) -> Optional[float]:
		"""
		모터 전압 읽기
		Feetech 서보의 Present_Voltage를 읽어서 실제 전압(V)으로 변환
		"""
		if not self.connected or not self.motors_bus:
			return None
		
		try:
			motor_name = self.servo_id_to_motor_name.get(servo_id)
			if not motor_name:
				return None
			
			voltage = self.motors_bus.read("Present_Voltage", motor_names=motor_name)
			if isinstance(voltage, np.ndarray):
				voltage = voltage[0] if len(voltage) > 0 else None
			if voltage is None:
				return None
			
			# Feetech 서보는 0.1V 단위로 저장하므로 10으로 나눔
			return float(voltage) / 10.0
		except Exception as e:
			print(f"Error reading motor voltage for servo {servo_id}: {e}")
			return None
	
	def detect_voltage(self) -> str:
		"""
		로봇 전압 감지 (6V 또는 12V)
		모든 모터의 전압을 읽어서 평균값으로 판단
		"""
		if not self.connected:
			return "6V"  # 기본값
		
		try:
			voltages = []
			for servo_id in self.SERVO_IDS:
				voltage = self.read_motor_voltage(servo_id)
				if voltage is not None:
					voltages.append(voltage)
			
			if voltages:
				avg_voltage = np.mean(voltages)
				# 9V 이상이면 12V, 그 이하면 6V로 판단
				detected = "12V" if avg_voltage >= 9.0 else "6V"
				print(f"Detected voltage: {detected} (average: {avg_voltage:.2f}V)")
				self.detected_voltage = detected
				return detected
		except Exception as e:
			print(f"Error detecting voltage: {e}")
		
		# 감지 실패 시 기본값
		self.detected_voltage = "6V"
		return "6V"
	
	def load_default_config(self, voltage: Optional[str] = None) -> bool:
		"""
		기본 설정 파일 로드
		전압에 따라 so-100-6V.json 또는 so-100-12V.json 로드
		"""
		import json
		import os
		
		# 전압이 지정되지 않으면 자동 감지
		if voltage is None:
			voltage = self.detect_voltage()
		
		# 설정 파일 경로
		config_dir = os.path.join(os.path.dirname(__file__), "..", "resources", "configs")
		config_file = os.path.join(config_dir, f"so-100-{voltage}.json")
		
		# 설정 파일이 없으면 기본값 사용
		if not os.path.exists(config_file):
			print(f"Config file not found: {config_file}, using default values")
			self.config = {
				"name": "so-100",
				"servos_voltage": 6.0 if voltage == "6V" else 12.0,
				"servos_offsets": [2048.0] * 6,
				"servos_calibration_position": [2048.0] * 6,
				"servos_offsets_signs": [1.0] * 6,
				"pid_gains": [
					{"p_gain": 20.0, "i_gain": 0.0, "d_gain": 32.0}
				] * 6,
				"gripping_threshold": 80,
				"non_gripping_threshold": 10
			}
			return False
		
		try:
			with open(config_file, 'r') as f:
				self.config = json.load(f)
			print(f"Loaded default config from {config_file}")
			
			# PID 게인 자동 적용
			if self.config and "pid_gains" in self.config:
				self.apply_pid_gains()
			
			return True
		except Exception as e:
			print(f"Error loading config file: {e}")
			return False
	
	def apply_pid_gains(self) -> bool:
		"""
		설정 파일에서 PID 게인을 읽어서 모든 모터에 적용
		phosphobot의 _set_pid_gains_motors 방식 참고
		"""
		if not self.connected or not self.motors_bus:
			print("Cannot apply PID gains: robot not connected")
			return False
		
		if not self.config or "pid_gains" not in self.config:
			print("Cannot apply PID gains: config not loaded")
			return False
		
		pid_gains = self.config["pid_gains"]
		if len(pid_gains) != 6:
			print(f"Invalid PID gains: expected 6, got {len(pid_gains)}")
			return False
		
		# 토크가 활성화되어 있는지 확인
		try:
			torque_status = self.motors_bus.read(
				"Torque_Enable", motor_names=list(self.MOTORS.keys())
			)
			# numpy array인 경우 all() 사용, 그렇지 않으면 직접 확인
			if hasattr(torque_status, 'all'):
				torque_enabled = torque_status.all() == 1
			else:
				torque_enabled = all(t == 1 for t in torque_status.values()) if isinstance(torque_status, dict) else False
		except Exception as e:
			print(f"Warning: Could not read torque status: {e}. Attempting to apply PID gains anyway.")
			torque_enabled = True  # 일단 시도
		
		if not torque_enabled:
			print("Warning: Torque is disabled. Enabling torque to apply PID gains...")
			try:
				self.enable_torque()
				time.sleep(0.1)  # 토크 활성화 대기
			except Exception as e:
				print(f"Error enabling torque: {e}")
				return False
		
		# 각 모터에 PID 게인 적용
		success = True
		for i, (motor_name, pid_gain) in enumerate(zip(self.MOTORS.keys(), pid_gains)):
			try:
				p_gain = int(pid_gain.get("p_gain", 20))
				i_gain = int(pid_gain.get("i_gain", 0))
				d_gain = int(pid_gain.get("d_gain", 32))
				
				# PID 게인 범위 확인 (0-255)
				p_gain = max(0, min(255, p_gain))
				i_gain = max(0, min(255, i_gain))
				d_gain = max(0, min(255, d_gain))
				
				# FeetechMotorsBus를 사용하여 PID 게인 설정
				self.motors_bus.write("P_Coefficient", p_gain, motor_names=[motor_name])
				time.sleep(0.01)
				self.motors_bus.write("I_Coefficient", i_gain, motor_names=[motor_name])
				time.sleep(0.01)
				self.motors_bus.write("D_Coefficient", d_gain, motor_names=[motor_name])
				time.sleep(0.01)
				
				print(f"Applied PID gains to {motor_name} (Joint {i+1}): P={p_gain}, I={i_gain}, D={d_gain}")
			except Exception as e:
				print(f"Error applying PID gains to {motor_name}: {e}")
				success = False
		
		if success:
			print("PID gains applied successfully to all motors")
		else:
			print("Warning: Some PID gains may not have been applied")
		
		return success
	
	def set_pid_gains(self, joint_index: int, p_gain: int, i_gain: int, d_gain: int) -> bool:
		"""
		특정 조인트의 PID 게인 설정
		joint_index: 0-5 (Joint 1-6)
		p_gain, i_gain, d_gain: 0-255 범위의 정수
		"""
		if not self.connected or not self.motors_bus:
			print("Cannot set PID gains: robot not connected")
			return False
		
		if joint_index < 0 or joint_index >= 6:
			print(f"Invalid joint index: {joint_index} (must be 0-5)")
			return False
		
		# PID 게인 범위 확인
		p_gain = max(0, min(255, int(p_gain)))
		i_gain = max(0, min(255, int(i_gain)))
		d_gain = max(0, min(255, int(d_gain)))
		
		# 모터 이름 가져오기
		motor_name = list(self.MOTORS.keys())[joint_index]
		
		try:
			# 토크 활성화 확인
			torque_status = self.motors_bus.read(
				"Torque_Enable", motor_names=[motor_name]
			)
			if hasattr(torque_status, 'get'):
				torque_enabled = torque_status.get(motor_name, 0) == 1
			else:
				torque_enabled = torque_status == 1 if isinstance(torque_status, (int, float)) else False
			
			if not torque_enabled:
				print(f"Warning: Torque is disabled for {motor_name}. Enabling torque...")
				self.enable_torque()
				time.sleep(0.1)
			
			# PID 게인 설정
			self.motors_bus.write("P_Coefficient", p_gain, motor_names=[motor_name])
			time.sleep(0.01)
			self.motors_bus.write("I_Coefficient", i_gain, motor_names=[motor_name])
			time.sleep(0.01)
			self.motors_bus.write("D_Coefficient", d_gain, motor_names=[motor_name])
			time.sleep(0.01)
			
			print(f"Set PID gains for {motor_name} (Joint {joint_index+1}): P={p_gain}, I={i_gain}, D={d_gain}")
			
			# 설정 파일 업데이트
			if self.config and "pid_gains" in self.config:
				self.config["pid_gains"][joint_index] = {
					"p_gain": float(p_gain),
					"i_gain": float(i_gain),
					"d_gain": float(d_gain)
				}
			
			return True
		except Exception as e:
			print(f"Error setting PID gains for {motor_name}: {e}")
			return False
	
	def set_gripper(self, open_fraction: float) -> bool:
		"""
		그리퍼 제어
		open_fraction: 0.0 (닫힘) ~ 1.0 (열림)
		그리퍼는 Joint 6 (servo ID 6)
		"""
		if not self.connected:
			return False
		
		open_fraction = max(0.0, min(1.0, open_fraction))
		
		# 그리퍼는 0~180도 범위로 매핑
		gripper_angle = open_fraction * 180.0  # 0도 = 닫힘, 180도 = 열림
		
		# Joint 6으로 이동
		current_state = self.get_state()
		current_gripper = current_state["joint_positions"][5]
		delta = gripper_angle - current_gripper
		
		return self.move_joint_delta(5, delta)

	def enable_torque(self) -> bool:
		"""모든 서보 토크 활성화"""
		if not self.connected or not self.motors_bus:
			print("Cannot enable torque: not connected or motors_bus not available")
			return False
		
		try:
			# FeetechMotorsBus를 사용하여 토크 활성화
			self.motors_bus.write("Torque_Enable", 1)
			print("Torque enabled for all servos")
			return True
		except Exception as e:
			print(f"Error enabling torque: {e}")
			import traceback
			traceback.print_exc()
			return False

	def disable_torque(self) -> bool:
		"""모든 서보 토크 비활성화"""
		if not self.connected or not self.motors_bus:
			return False
		
		try:
			# FeetechMotorsBus를 사용하여 토크 비활성화
			self.motors_bus.write("Torque_Enable", 0)
			return True
		except Exception as e:
			print(f"Error disabling torque: {e}")
			return False

