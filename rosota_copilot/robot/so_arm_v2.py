"""
SO-100 Robot Adapter (V2 - Simplified)
완전히 새로 작성한 간단한 버전
"""
import numpy as np
from typing import Dict, List, Optional, Tuple
from loguru import logger


class SOArm100AdapterV2:
	"""SO-100 로봇 어댑터 (간소화 버전)"""
	
	# 조인트 이름 정의
	JOINT_NAMES = ["shoulder_pan", "shoulder_lift", "elbow_flex", "wrist_flex", "wrist_roll", "gripper"]
	
	# 모터 설정
	MOTORS = {
		"shoulder_pan": (1, "sts3215"),
		"shoulder_lift": (2, "sts3215"),
		"elbow_flex": (3, "sts3215"),
		"wrist_flex": (4, "sts3215"),
		"wrist_roll": (5, "sts3215"),
		"gripper": (6, "sts3215"),
	}

	# 기본 제한값 (매우 넓게 설정 - 소프트웨어 제한 없음)
	DEFAULT_LIMITS = [
		[-180.0, 180.0],  # shoulder_pan
		[-180.0, 180.0],  # shoulder_lift
		[-180.0, 180.0],  # elbow_flex
		[-180.0, 180.0],  # wrist_flex
		[-180.0, 180.0],  # wrist_roll
		[-180.0, 180.0],  # gripper
	]

	def __init__(self):
		self.connected = False
		self.motors_bus = None
		self.port = None
		self.baudrate = 115200
		self.connection_info = None  # 연결 정보
		
		# 조인트 제한값 (캘리브레이션에서 업데이트 가능)
		self.joint_limits = [limits.copy() for limits in self.DEFAULT_LIMITS]
		
		# 현재 조인트 위치 캐시
		self._joint_positions = [0.0] * 6
		
		logger.info("[SOArmV2] Adapter initialized")

	def connect(self, port: str) -> bool:
		"""로봇 연결"""
		try:
			from .motors.feetech import FeetechMotorsBus, CalibrationMode
			
			logger.info(f"[SOArmV2] Connecting to {port} at {self.baudrate} baud...")
			
			# FeetechMotorsBus 생성
			self.motors_bus = FeetechMotorsBus(
				port=port,
				motors=self.MOTORS,
			)
			
			# 기본 캘리브레이션 설정 (homing_offset = 0)
			calibration_data = {
				"motor_names": list(self.MOTORS.keys()),
				"calib_mode": [CalibrationMode.DEGREE.name] * len(self.MOTORS),
				"drive_mode": [0] * len(self.MOTORS),
				"homing_offset": [0] * len(self.MOTORS),
			}
			self.motors_bus.set_calibration(calibration_data)
			
			# 연결 테스트
			self.motors_bus.connect()
			
			# 토크 활성화
			self.motors_bus.write("Torque_Enable", [1] * len(self.MOTORS))
			
			self.connected = True
			self.port = port
			self.connection_info = {"port": port, "baudrate": self.baudrate}
			
			# 초기 위치 읽기
			self._update_positions()
			
			logger.info(f"[SOArmV2] Connected successfully!")
			logger.info(f"[SOArmV2] Initial positions: {self._joint_positions}")
			return True
			
		except Exception as e:
			logger.error(f"[SOArmV2] Connection failed: {e}")
			self.connected = False
			return False
	
	def disconnect(self):
		"""로봇 연결 해제"""
		if self.motors_bus:
			try:
				# 토크 비활성화
				self.motors_bus.write("Torque_Enable", [0] * len(self.MOTORS))
				self.motors_bus.disconnect()
			except:
				pass
		self.connected = False
		logger.info("[SOArmV2] Disconnected")
	
	def _update_positions(self) -> bool:
		"""모든 조인트의 현재 위치 읽기"""
		if not self.connected or not self.motors_bus:
			return False
		
		try:
			# 한 번에 모든 조인트 읽기
			positions = self.motors_bus.read("Present_Position")
			
			if positions is not None and len(positions) == 6:
				self._joint_positions = [float(p) for p in positions]
				return True
			else:
				logger.warning(f"[SOArmV2] Failed to read positions: {positions}")
				return False
				
		except Exception as e:
			logger.error(f"[SOArmV2] Error reading positions: {e}")
			return False
	
	def get_joint_position(self, joint_index: int) -> Optional[float]:
		"""특정 조인트의 현재 위치 읽기"""
		if not self.connected or not self.motors_bus:
			return None
		
		if joint_index < 0 or joint_index >= 6:
			return None
		
		try:
			motor_name = self.JOINT_NAMES[joint_index]
			position = self.motors_bus.read("Present_Position", motor_names=motor_name)
			
			if isinstance(position, np.ndarray) and len(position) > 0:
				pos = float(position[0])
				self._joint_positions[joint_index] = pos
				return pos
			elif isinstance(position, (int, float)):
				pos = float(position)
				self._joint_positions[joint_index] = pos
				return pos
			else:
				return None
				
		except Exception as e:
			logger.debug(f"[SOArmV2] Error reading joint {joint_index}: {e}")
			return None
	
	def move_joint_absolute(self, joint_index: int, target_deg: float) -> bool:
		"""
		조인트를 절대 위치로 이동
		
		Args:
			joint_index: 조인트 인덱스 (0-5)
			target_deg: 목표 각도 (도)
		
		Returns:
			성공 여부
		"""
		if not self.connected or not self.motors_bus:
			logger.error("[SOArmV2] Robot not connected")
			return False
		
		if joint_index < 0 or joint_index >= 6:
			logger.error(f"[SOArmV2] Invalid joint index: {joint_index}")
			return False
		
		# 제한 확인
		limits = self.joint_limits[joint_index]
		if target_deg < limits[0] or target_deg > limits[1]:
			logger.warning(
				f"[SOArmV2] Joint {joint_index} target {target_deg:.2f}° exceeds limits "
				f"[{limits[0]:.2f}, {limits[1]:.2f}]"
			)
			return False
		
		try:
			motor_name = self.JOINT_NAMES[joint_index]
			
			# 토크 확인 및 활성화
			torque = self.motors_bus.read("Torque_Enable", motor_names=motor_name)
			if isinstance(torque, np.ndarray):
				torque = torque[0] if len(torque) > 0 else 0
			
			if torque != 1:
				logger.info(f"[SOArmV2] Enabling torque for {motor_name}")
				self.motors_bus.write("Torque_Enable", [1], motor_names=motor_name)
			
			# 위치 명령 전송 (매우 단순!)
			logger.debug(f"[SOArmV2] Moving {motor_name} (joint {joint_index}) to {target_deg:.2f}°")
			self.motors_bus.write("Goal_Position", [target_deg], motor_names=motor_name)
			
			# 캐시 업데이트 (명령 전송 후)
			self._joint_positions[joint_index] = target_deg
			
			logger.debug(f"[SOArmV2] Command sent successfully")
			return True
			
		except Exception as e:
			logger.error(f"[SOArmV2] Error moving joint {joint_index}: {e}")
			return False
	
	def move_joint_delta(self, joint_index: int, delta_deg: float) -> bool:
		"""
		조인트를 상대 위치로 이동
		
		Args:
			joint_index: 조인트 인덱스 (0-5)
			delta_deg: 이동 각도 (도, 양수/음수)
		
		Returns:
			성공 여부
		"""
		# 현재 위치 읽기
		current_pos = self.get_joint_position(joint_index)
		
		if current_pos is None:
			# 읽기 실패 시 캐시 사용
			logger.warning(f"[SOArmV2] Failed to read joint {joint_index}, using cached position")
			current_pos = self._joint_positions[joint_index]
		
		# 목표 위치 계산
		target_pos = current_pos + delta_deg
		
		logger.debug(
			f"[SOArmV2] Joint {joint_index}: {current_pos:.2f}° + {delta_deg:.2f}° = {target_pos:.2f}°"
		)
		
		# 절대 위치로 이동
		return self.move_joint_absolute(joint_index, target_pos)
	
	def get_state(self) -> Dict:
		"""로봇 상태 반환"""
		# 위치 업데이트
		self._update_positions()
		
		return {
			"connected": self.connected,
			"joint_positions": self._joint_positions.copy(),
			"joint_names": self.JOINT_NAMES,
			"joint_limits": [limits.copy() for limits in self.joint_limits],
		}
	
	def enable_torque(self):
		"""모든 모터의 토크 활성화"""
		if self.connected and self.motors_bus:
			try:
				self.motors_bus.write("Torque_Enable", [1] * len(self.MOTORS))
				logger.info("[SOArmV2] Torque enabled for all motors")
			except Exception as e:
				logger.error(f"[SOArmV2] Failed to enable torque: {e}")
	
	def disable_torque(self):
		"""모든 모터의 토크 비활성화"""
		if self.connected and self.motors_bus:
			try:
				self.motors_bus.write("Torque_Enable", [0] * len(self.MOTORS))
				logger.info("[SOArmV2] Torque disabled for all motors")
			except Exception as e:
				logger.error(f"[SOArmV2] Failed to disable torque: {e}")
	
	def set_joint_limits(self, limits: List[List[float]]):
		"""조인트 제한값 설정"""
		if len(limits) == 6:
			self.joint_limits = [l.copy() for l in limits]
			logger.info(f"[SOArmV2] Joint limits updated: {self.joint_limits}")

