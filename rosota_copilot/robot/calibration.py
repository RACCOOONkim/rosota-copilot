from typing import Dict, Any, Optional, Callable
import json
import os


class CalibrationManager:
	"""
	로봇 캘리브레이션 관리
	홈 포지션, 조인트 제로, TCP 오프셋 등을 관리합니다.
	"""

	def __init__(self, robot_adapter: Optional[Any] = None, log_callback: Optional[Callable[[str, str], None]] = None):
		self.robot = robot_adapter
		self.log_callback = log_callback  # 로그 콜백 함수 (message, level)
		self.data: Dict[str, Any] = {
			"joint_offsets": [0.0, 0.0, 0.0, 0.0, 0.0, 0.0],
			"tcp_offset": {"x": 0.0, "y": 0.0, "z": 0.0, "rx": 0.0, "ry": 0.0, "rz": 0.0},
			"home_pose": {"joints": [0.0, 0.0, 0.0, 0.0, 0.0, 0.0]},
		}
		# 캘리브레이션 마법사 상태
		self.calibration_current_step = 0
		self.calibration_max_steps = 3
		# LeRobot 방식: 각 조인트의 최소/최대값 측정용
		self.joint_min_positions = [None] * 6  # 각 조인트의 최소 위치 (기록된 값)
		self.joint_max_positions = [None] * 6  # 각 조인트의 최대 위치 (기록된 값)
		self.current_joint_index = 0  # 현재 측정 중인 조인트 인덱스
		# 실시간 추적용 (조인트를 움직이는 동안 자동으로 업데이트)
		self.realtime_min_positions = [None] * 6  # 실시간 최소값 추적
		self.realtime_max_positions = [None] * 6  # 실시간 최대값 추적
		self.realtime_current_positions = [0.0] * 6  # 실시간 현재 위치
	
	def _log(self, message: str, level: str = "info"):
		"""로그 출력 (콜백이 있으면 콜백 호출, 없으면 print)"""
		if self.log_callback:
			self.log_callback(message, level)
		else:
			print(f"[{level.upper()}] {message}")

	def home(self) -> bool:
		"""
		로봇을 홈 포지션으로 이동
		SO-100의 경우 각 조인트를 홈 포지션으로 이동
		"""
		if not self.robot or not self.robot.connected:
			self._log("Cannot move to home: robot not connected", "error")
			return False
		
		home_joints = self.data["home_pose"]["joints"]
		success = True
		import time
		
		self._log("Starting home movement...", "info")
		self._log(f"Target home position: {home_joints}", "info")
		
		# 각 조인트를 홈 포지션으로 이동
		for i, target_deg in enumerate(home_joints):
			if i >= 6:  # 6개 조인트만
				break
			
			# 현재 위치 가져오기
			state = self.robot.get_state()
			current_pos = state.get("joint_positions", [0.0] * 6)[i]
			
			# 목표 위치까지 이동
			delta = target_deg - current_pos
			if abs(delta) > 0.1:  # 0.1도 이상 차이만 이동
				joint_name = self.robot.JOINT_NAMES[i] if hasattr(self.robot, 'JOINT_NAMES') else f"Joint {i+1}"
				self._log(f"Moving {joint_name} from {current_pos:.1f}° to {target_deg:.1f}° (delta: {delta:.1f}°)", "info")
				result = self.robot.move_joint_delta(i, delta)
				if not result:
					self._log(f"Failed to move {joint_name} to home position", "error")
					success = False
				else:
					self._log(f"{joint_name} moved successfully, waiting for stabilization...", "info")
					# 조인트 이동 대기 (서보가 목표 위치에 도달할 시간)
					time.sleep(0.5)  # 각 조인트 이동 대기 시간 증가
			else:
				joint_name = self.robot.JOINT_NAMES[i] if hasattr(self.robot, 'JOINT_NAMES') else f"Joint {i+1}"
				self._log(f"{joint_name} already at home position ({current_pos:.1f}°)", "info")
		
		if success:
			self._log("Home movement completed successfully", "success")
		else:
			self._log("Home movement completed with errors", "warning")
		
		return success

	def zero_joints(self) -> bool:
		"""
		현재 위치를 제로 포지션으로 설정 (엔코더 오프셋)
		SO-100의 경우 현재 위치를 기준으로 캘리브레이션 오프셋 저장
		"""
		if not self.robot or not self.robot.connected:
			self._log("Cannot zero joints: robot not connected", "error")
			return False
		
		self._log("Reading current joint positions...", "info")
		
		# 현재 조인트 위치 읽기
		state = self.robot.get_state()
		current_joints = state.get("joint_positions", [0.0] * 6)
		
		self._log(f"Current joint positions: {[f'{j:.2f}°' for j in current_joints]}", "info")
		
		# 오프셋으로 저장 (현재 위치를 0으로 만들기 위한 값, 라디안 단위)
		import math
		self.data["joint_offsets"] = [math.radians(-j) for j in current_joints]
		
		self._log(f"Calculated offsets (radians): {[f'{o:.4f}' for o in self.data['joint_offsets']]}", "info")
		
		# SO-100 어댑터의 캘리브레이션 오프셋 업데이트
		if hasattr(self.robot, 'calibration_offsets'):
			self.robot.calibration_offsets = self.data["joint_offsets"]
			self._log("Calibration offsets applied to robot adapter", "success")
		else:
			self._log("Warning: robot adapter does not have calibration_offsets attribute", "warning")
		
		# FeetechMotorsBus의 캘리브레이션도 업데이트
		if hasattr(self.robot, 'motors_bus') and self.robot.motors_bus:
			try:
				from rosota_copilot.robot.motors.feetech import CalibrationMode
				calibration_data = {
					"motor_names": list(self.robot.MOTORS.keys()),
					"calib_mode": [CalibrationMode.DEGREE.name] * len(self.robot.MOTORS),
					"drive_mode": [0] * len(self.robot.MOTORS),
					"homing_offset": [0] * len(self.robot.MOTORS),  # TODO: 실제 homing offset 계산
				}
				self.robot.motors_bus.set_calibration(calibration_data)
				self._log("FeetechMotorsBus calibration updated", "success")
			except Exception as e:
				self._log(f"Warning: Failed to update FeetechMotorsBus calibration: {e}", "warning")
		
		self._log("Joints zeroed successfully", "success")
		return True

	def set_tcp_offset(self, x: float, y: float, z: float, rx: float, ry: float, rz: float) -> None:
		"""TCP (Tool Center Point) 오프셋 설정"""
		self.data["tcp_offset"] = {"x": x, "y": y, "z": z, "rx": rx, "ry": ry, "rz": rz}

	def set_home_pose(self, joints: list) -> None:
		"""홈 포지션 설정"""
		if len(joints) == 6:
			self.data["home_pose"]["joints"] = joints

	def save(self, path: str) -> None:
		"""캘리브레이션 데이터를 파일로 저장"""
		os.makedirs(os.path.dirname(path), exist_ok=True)
		with open(path, "w", encoding="utf-8") as f:
			json.dump(self.data, f, ensure_ascii=False, indent=2)

	def load(self, path: str) -> None:
		"""캘리브레이션 데이터를 파일에서 로드"""
		if not os.path.exists(path):
			raise FileNotFoundError(f"Calibration file not found: {path}")
		with open(path, "r", encoding="utf-8") as f:
			self.data = json.load(f)
		
		# 조인트 범위가 있으면 로봇의 joint_limits 업데이트
		if "joint_ranges" in self.data and self.robot:
			joint_ranges = self.data["joint_ranges"]
			if "min" in joint_ranges and "max" in joint_ranges:
				# joint_limits 업데이트 (각도 단위)
				new_limits = []
				for i in range(6):
					min_val = joint_ranges["min"][i] if i < len(joint_ranges["min"]) else -180
					max_val = joint_ranges["max"][i] if i < len(joint_ranges["max"]) else 180
					new_limits.append([min_val, max_val])
				
				if hasattr(self.robot, 'joint_limits'):
					old_limits = self.robot.joint_limits.copy() if hasattr(self.robot.joint_limits, 'copy') else self.robot.joint_limits[:]
					self.robot.joint_limits = new_limits
					self._log(f"Joint limits updated from calibration:", "info")
					for i in range(6):
						joint_name = self.robot.JOINT_NAMES[i] if hasattr(self.robot, 'JOINT_NAMES') else f"Joint {i+1}"
						self._log(f"  {joint_name}: {old_limits[i]} -> {new_limits[i]}", "info")
		
		# 캘리브레이션 오프셋 적용
		if "joint_offsets" in self.data and self.robot:
			if hasattr(self.robot, 'calibration_offsets'):
				self.robot.calibration_offsets = self.data["joint_offsets"]
				self._log("Calibration offsets applied to robot adapter", "info")
		
		# FeetechMotorsBus 기본 캘리브레이션 사용 (로드 시)
		# homing_offset은 사용하지 않음 (Feetech 모터는 -180° ~ +180° 지원)
		if hasattr(self.robot, 'motors_bus') and self.robot.motors_bus:
			try:
				from .motors.feetech import CalibrationMode
				
				self._log("Resetting to default calibration (homing_offset = 0)", "info")
				
				# 기본 캘리브레이션 데이터 설정
				calibration_data = {
					"motor_names": list(self.robot.MOTORS.keys()),
					"calib_mode": [CalibrationMode.DEGREE.name] * len(self.robot.MOTORS),
					"drive_mode": [0] * len(self.robot.MOTORS),
					"homing_offset": [0] * len(self.robot.MOTORS),  # 모두 0으로 리셋
				}
				self.robot.motors_bus.set_calibration(calibration_data)
				self._log("Default calibration applied!", "success")
			except Exception as e:
				self._log(f"Warning: Failed to reset calibration: {e}", "warning")
		
		# 캘리브레이션 로드 시에는 소프트웨어 제한만 사용
		if "joint_ranges" in self.data and self.robot:
			joint_ranges = self.data["joint_ranges"]
			if "min" in joint_ranges and "max" in joint_ranges:
				self._log("Calibration loaded - using software limits only", "info")
	
	def calibrate_step(self) -> tuple[str, str]:
		"""
		단계별 캘리브레이션 (LeRobot 방식)
		참고: https://huggingface.co/docs/lerobot/so101
		
		LeRobot 방식:
		1. 모든 조인트를 중간 위치로 이동
		2. 각 조인트를 전체 범위로 움직이면서 최소/최대값 측정
		3. 캘리브레이션 데이터 저장
		
		Returns: (status, message) where status is "success", "in_progress", or "error"
		"""
		if not self.robot or not self.robot.connected:
			self.calibration_current_step = 0
			return ("error", "Robot not connected. Cannot calibrate.")
		
		import math
		import time
		
		# Step 0: 초기화 (토크 비활성화)
		if self.calibration_current_step == 0:
			# 전압 감지
			voltage = self.robot.detect_voltage()
			self._log(f"Detected voltage: {voltage}", "info")
			
			# 기본 설정 로드
			if not self.robot.config:
				self.robot.load_default_config(voltage)
			
			# 토크 비활성화 (수동으로 로봇을 움직일 수 있도록)
			self.robot.disable_torque()
			self._log("Torque disabled. You can now move the robot manually.", "info")
			
			# 조인트 범위 초기화
			self.joint_min_positions = [None] * 6
			self.joint_max_positions = [None] * 6
			self.realtime_min_positions = [None] * 6
			self.realtime_max_positions = [None] * 6
			self.realtime_current_positions = [0.0] * 6
			self.current_joint_index = 0
			
			self.calibration_current_step = 1
			return (
				"in_progress",
				f"Step {self.calibration_current_step}/{self.calibration_max_steps}: 중간 위치로 이동\n\n"
				"📋 작업 내용:\n"
				"• 모든 조인트를 중간 위치로 수동으로 이동하세요\n"
				"• 각 조인트의 최소값과 최대값의 중간 위치입니다\n"
				"• 로봇을 부드럽게 움직이세요\n\n"
				"⚠️ 주의사항:\n"
				"• 조인트 제한 범위를 초과하지 않도록 주의하세요\n"
				"• 위치가 정확하면 'Next Step' 버튼을 클릭하세요"
			)
		
		# Step 1: 중간 위치 확인 및 조인트 범위 측정 시작
		if self.calibration_current_step == 1:
			# 현재 위치 읽기 (중간 위치 확인용)
			state = self.robot.get_state()
			current_joints = state.get("joint_positions", [0.0] * 6)
			
			# 조인트 제한값 가져오기
			joint_limits = getattr(self.robot, 'joint_limits', [[-180, 180]] * 6)
			
			# 중간 위치 계산 및 표시
			middle_positions = []
			for i in range(6):
				min_limit, max_limit = joint_limits[i] if i < len(joint_limits) else [-180, 180]
				middle = (min_limit + max_limit) / 2
				middle_positions.append(middle)
			
			self._log(f"Middle positions: {[f'{m:.1f}°' for m in middle_positions]}", "info")
			self._log(f"Current positions: {[f'{j:.1f}°' for j in current_joints]}", "info")
			
			# 첫 번째 조인트 측정 시작
			self.current_joint_index = 0
			self.calibration_current_step = 2
			
			joint_name = self.robot.JOINT_NAMES[0] if hasattr(self.robot, 'JOINT_NAMES') else "Joint 1"
			return (
				"in_progress",
				f"Step {self.calibration_current_step}/{self.calibration_max_steps}: 조인트 범위 측정\n\n"
				f"📋 현재 측정 중: {joint_name} (조인트 {self.current_joint_index + 1}/6)\n\n"
				"📋 작업 내용:\n"
				f"• {joint_name}를 최소 위치로 이동하세요\n"
				"• 최소 위치에 도달하면 'Record Min' 버튼을 클릭하세요\n"
				"• 그 다음 최대 위치로 이동하고 'Record Max' 버튼을 클릭하세요\n\n"
				"💡 팁:\n"
				"• 각 조인트를 천천히 움직이며 전체 범위를 확인하세요\n"
				"• 최소/최대 위치를 정확히 기록하는 것이 중요합니다"
			)
		
		# Step 2: 각 조인트의 최소/최대값 측정
		if self.calibration_current_step == 2:
			# 이 단계는 프론트엔드에서 "Record Min" / "Record Max" 버튼으로 처리
			# 여기서는 다음 조인트로 넘어가는 로직만 처리
			# 실제 측정은 별도 API 엔드포인트에서 처리
			
			# 모든 조인트 측정 완료 확인
			if self.current_joint_index >= 6:
				self.calibration_current_step = 3
				return (
					"in_progress",
					f"Step {self.calibration_current_step}/{self.calibration_max_steps}: 캘리브레이션 데이터 저장\n\n"
					"📋 작업 내용:\n"
					"• 모든 조인트의 범위가 측정되었습니다\n"
					"• 측정된 범위:\n"
					+ "\n".join([
						f"  - {self.robot.JOINT_NAMES[i] if hasattr(self.robot, 'JOINT_NAMES') else f'Joint {i+1}'}: "
						f"{self.joint_min_positions[i]:.1f}° ~ {self.joint_max_positions[i]:.1f}°"
						for i in range(6) if self.joint_min_positions[i] is not None and self.joint_max_positions[i] is not None
					]) + "\n\n"
					"✅ 'Next Step' 버튼을 클릭하면 캘리브레이션 데이터를 저장하고 완료합니다."
				)
			
			# 다음 조인트로 넘어가기 (프론트엔드에서 호출)
			joint_name = self.robot.JOINT_NAMES[self.current_joint_index] if hasattr(self.robot, 'JOINT_NAMES') else f"Joint {self.current_joint_index + 1}"
			return (
				"in_progress",
				f"Step {self.calibration_current_step}/{self.calibration_max_steps}: 조인트 범위 측정\n\n"
				f"📋 현재 측정 중: {joint_name} (조인트 {self.current_joint_index + 1}/6)\n\n"
				"📋 작업 내용:\n"
				f"• {joint_name}를 최소 위치로 이동하세요\n"
				"• 최소 위치에 도달하면 'Record Min' 버튼을 클릭하세요\n"
				"• 그 다음 최대 위치로 이동하고 'Record Max' 버튼을 클릭하세요\n\n"
				"💡 팁:\n"
				"• 각 조인트를 천천히 움직이며 전체 범위를 확인하세요\n"
				"• 최소/최대 위치를 정확히 기록하는 것이 중요합니다"
			)
		
		# Step 3: 완료 및 저장
		if self.calibration_current_step == 3:
			# 측정된 범위를 기반으로 오프셋 계산
			# 중간 위치를 0으로 만드는 오프셋 계산
			import math
			
			# 각 조인트의 중간값 계산
			joint_middles = []
			for i in range(6):
				if self.joint_min_positions[i] is not None and self.joint_max_positions[i] is not None:
					middle = (self.joint_min_positions[i] + self.joint_max_positions[i]) / 2
					joint_middles.append(middle)
					# 오프셋: 중간 위치를 0으로 만들기 위한 값
					self.data["joint_offsets"][i] = math.radians(-middle)
				else:
					joint_middles.append(0.0)
					self.data["joint_offsets"][i] = 0.0
			
		# 측정된 범위를 데이터에 저장
		self.data["joint_ranges"] = {
			"min": [self.joint_min_positions[i] if self.joint_min_positions[i] is not None else -180 for i in range(6)],
			"max": [self.joint_max_positions[i] if self.joint_max_positions[i] is not None else 180 for i in range(6)],
			"middle": joint_middles
		}
		
		# homing_offset은 사용하지 않음 (Feetech 모터는 -180° ~ +180° 지원)
		
		# SO-100 어댑터의 캘리브레이션 오프셋 업데이트
		if hasattr(self.robot, 'calibration_offsets'):
			self.robot.calibration_offsets = self.data["joint_offsets"]
			self._log("Calibration offsets applied to robot adapter", "success")
		
		# 조인트 제한값 업데이트 (측정된 범위를 제한값으로 사용)
		if hasattr(self.robot, 'joint_limits'):
			new_limits = []
			for i in range(6):
				min_val = self.joint_min_positions[i] if self.joint_min_positions[i] is not None else -180
				max_val = self.joint_max_positions[i] if self.joint_max_positions[i] is not None else 180
				new_limits.append([min_val, max_val])
			self.robot.joint_limits = new_limits
			self._log(f"Joint limits updated from calibration: {new_limits}", "success")
		
		# FeetechMotorsBus 기본 캘리브레이션 사용 (homing_offset = 0)
		# Feetech STS3215는 이미 -180° ~ +180° 범위를 지원하므로
		# homing_offset 없이 소프트웨어 제한만으로 충분함
		if hasattr(self.robot, 'motors_bus') and self.robot.motors_bus:
			try:
				from .motors.feetech import CalibrationMode
				
				self._log("Using default calibration (no homing_offset)", "info")
				
				# 기본 캘리브레이션 데이터 설정
				calibration_data = {
					"motor_names": list(self.robot.MOTORS.keys()),
					"calib_mode": [CalibrationMode.DEGREE.name] * len(self.robot.MOTORS),
					"drive_mode": [0] * len(self.robot.MOTORS),
					"homing_offset": [0] * len(self.robot.MOTORS),  # 모두 0으로 리셋
				}
				self.robot.motors_bus.set_calibration(calibration_data)
				self._log("Default calibration applied!", "success")
			except Exception as e:
				self._log(f"Warning: Failed to update FeetechMotorsBus calibration: {e}", "warning")
		
		# 토크 재활성화
		self.robot.enable_torque()
		self._log("Torque re-enabled", "info")
		
		# 캘리브레이션 데이터 저장
		from ..config import CALIBRATION_DIR
		os.makedirs(CALIBRATION_DIR, exist_ok=True)
		calib_file = os.path.join(CALIBRATION_DIR, "calibration.json")
		self.save(calib_file)
		self._log(f"Calibration saved to {calib_file}", "success")
		
		# 상태 초기화
		self.calibration_current_step = 0
		self.joint_min_positions = [None] * 6
		self.joint_max_positions = [None] * 6
		self.current_joint_index = 0
		
		return (
			"success",
			"Calibration completed successfully! The robot is now calibrated and ready to use.\n\n"
			"측정된 조인트 범위:\n"
			+ "\n".join([
				f"  - {self.robot.JOINT_NAMES[i] if hasattr(self.robot, 'JOINT_NAMES') else f'Joint {i+1}'}: "
				f"{self.data['joint_ranges']['min'][i]:.1f}° ~ {self.data['joint_ranges']['max'][i]:.1f}° "
				f"(중간: {self.data['joint_ranges']['middle'][i]:.1f}°)"
				for i in range(6)
			])
		)
		
		return ("error", "Unknown calibration step")
	
	def update_realtime_positions(self) -> Dict[str, Any]:
		"""
		실시간으로 조인트 위치를 업데이트하고 min/max 추적
		조인트를 움직이는 동안 자동으로 호출되어야 함
		"""
		if self.calibration_current_step != 2:
			return {
				"current_joint_index": self.current_joint_index,
				"positions": [0.0] * 6,
				"min_positions": [None] * 6,
				"max_positions": [None] * 6
			}
		
		state = self.robot.get_state()
		current_joints = state.get("joint_positions", [0.0] * 6)
		
		# 실시간 위치 업데이트
		self.realtime_current_positions = current_joints.copy()
		
		# 실시간 min/max 추적 (모든 조인트에 대해)
		for i in range(6):
			pos = current_joints[i]
			
			# 최소값 업데이트
			if self.realtime_min_positions[i] is None or pos < self.realtime_min_positions[i]:
				self.realtime_min_positions[i] = pos
			
			# 최대값 업데이트
			if self.realtime_max_positions[i] is None or pos > self.realtime_max_positions[i]:
				self.realtime_max_positions[i] = pos
		
		return {
			"current_joint_index": self.current_joint_index,
			"positions": self.realtime_current_positions,
			"min_positions": self.realtime_min_positions,
			"max_positions": self.realtime_max_positions,
			"recorded_min": self.joint_min_positions,
			"recorded_max": self.joint_max_positions
		}
	
	def record_joint_min(self) -> bool:
		"""현재 조인트의 최소 위치 기록 (실시간 추적된 최소값 또는 현재 위치)"""
		if self.calibration_current_step != 2:
			return False
		
		if self.current_joint_index < 6:
			# 실시간 추적된 최소값이 있으면 사용, 없으면 현재 위치 사용
			if self.realtime_min_positions[self.current_joint_index] is not None:
				recorded_value = self.realtime_min_positions[self.current_joint_index]
			else:
				state = self.robot.get_state()
				current_joints = state.get("joint_positions", [0.0] * 6)
				recorded_value = current_joints[self.current_joint_index]
			
			self.joint_min_positions[self.current_joint_index] = recorded_value
			joint_name = self.robot.JOINT_NAMES[self.current_joint_index] if hasattr(self.robot, 'JOINT_NAMES') else f"Joint {self.current_joint_index + 1}"
			self._log(f"{joint_name} minimum position recorded: {recorded_value:.2f}°", "info")
			return True
		
		return False
	
	def record_joint_max(self) -> bool:
		"""현재 조인트의 최대 위치 기록 (실시간 추적된 최대값 또는 현재 위치)"""
		if self.calibration_current_step != 2:
			return False
		
		if self.current_joint_index >= 6:
			return False
		
		# 실시간 추적된 최대값이 있으면 사용, 없으면 현재 위치 사용
		if self.realtime_max_positions[self.current_joint_index] is not None:
			recorded_value = self.realtime_max_positions[self.current_joint_index]
		else:
			state = self.robot.get_state()
			current_joints = state.get("joint_positions", [0.0] * 6)
			recorded_value = current_joints[self.current_joint_index]
		
		self.joint_max_positions[self.current_joint_index] = recorded_value
		joint_name = self.robot.JOINT_NAMES[self.current_joint_index] if hasattr(self.robot, 'JOINT_NAMES') else f"Joint {self.current_joint_index + 1}"
		self._log(f"{joint_name} maximum position recorded: {recorded_value:.2f}°", "info")
		
		# 최소/최대 모두 기록되었으면 다음 조인트로
		if self.joint_min_positions[self.current_joint_index] is not None:
			# 다음 조인트로 넘어가기 전에 실시간 추적 초기화
			self.realtime_min_positions[self.current_joint_index] = None
			self.realtime_max_positions[self.current_joint_index] = None
			self.current_joint_index += 1
		
		return True
	
	def next_joint(self) -> bool:
		"""현재 조인트 측정을 건너뛰고 다음 조인트로 이동"""
		if self.calibration_current_step != 2:
			return False
		
		if self.current_joint_index < 6:
			# 실시간 추적 초기화
			self.realtime_min_positions[self.current_joint_index] = None
			self.realtime_max_positions[self.current_joint_index] = None
			self.current_joint_index += 1
			return True
		
		return False
	
	def get_current_joint_index(self) -> int:
		"""현재 측정 중인 조인트 인덱스 반환"""
		return self.current_joint_index
	
	def auto_record_current_joint(self) -> bool:
		"""
		현재 조인트의 실시간 추적된 min/max를 자동으로 기록
		조인트를 움직인 후 호출하면 자동으로 최소/최대값을 기록
		"""
		if self.calibration_current_step != 2:
			return False
		
		if self.current_joint_index >= 6:
			return False
		
		# 최소값 자동 기록
		if self.realtime_min_positions[self.current_joint_index] is not None:
			self.joint_min_positions[self.current_joint_index] = self.realtime_min_positions[self.current_joint_index]
		
		# 최대값 자동 기록
		if self.realtime_max_positions[self.current_joint_index] is not None:
			self.joint_max_positions[self.current_joint_index] = self.realtime_max_positions[self.current_joint_index]
		
		# 최소/최대 모두 기록되었으면 다음 조인트로
		if (self.joint_min_positions[self.current_joint_index] is not None and 
			self.joint_max_positions[self.current_joint_index] is not None):
			joint_name = self.robot.JOINT_NAMES[self.current_joint_index] if hasattr(self.robot, 'JOINT_NAMES') else f"Joint {self.current_joint_index + 1}"
			self._log(f"{joint_name} auto-recorded: {self.joint_min_positions[self.current_joint_index]:.2f}° ~ {self.joint_max_positions[self.current_joint_index]:.2f}°", "info")
			
			# 다음 조인트로 넘어가기 전에 실시간 추적 초기화
			self.realtime_min_positions[self.current_joint_index] = None
			self.realtime_max_positions[self.current_joint_index] = None
			self.current_joint_index += 1
			return True
		
		return False
	
	def get_calibration_status(self) -> Dict[str, Any]:
		"""캘리브레이션 상태 및 실시간 위치 정보 반환"""
		return {
			"current_step": self.calibration_current_step,
			"max_steps": self.calibration_max_steps,
			"current_joint_index": self.current_joint_index,
			"realtime_positions": self.realtime_current_positions,
			"realtime_min": self.realtime_min_positions,
			"realtime_max": self.realtime_max_positions,
			"recorded_min": self.joint_min_positions,
			"recorded_max": self.joint_max_positions
		}

