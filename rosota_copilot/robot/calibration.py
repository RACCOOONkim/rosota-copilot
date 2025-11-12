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
	
	def calibrate_step(self) -> tuple[str, str]:
		"""
		단계별 캘리브레이션 (phosphobot 방식)
		Returns: (status, message) where status is "success", "in_progress", or "error"
		"""
		if not self.robot or not self.robot.connected:
			self.calibration_current_step = 0
			return ("error", "Robot not connected. Cannot calibrate.")
		
		import math
		import numpy as np
		
		# Step 0: 초기화 (전압 감지, 기본 설정 로드)
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
			
			self.calibration_current_step = 1
			return (
				"in_progress",
				f"Step {self.calibration_current_step}/{self.calibration_max_steps}: Position 1 - 초기 위치 설정\n\n"
				"📋 작업 내용:\n"
				"• 모든 조인트를 0도 위치로 수동으로 이동하세요\n"
				"• 로봇이 완전히 펼쳐진 상태 (straight position)가 되어야 합니다\n"
				"• 각 조인트가 중립 위치에 있는지 확인하세요\n\n"
				"⚠️ 주의사항:\n"
				"• 로봇을 부드럽게 움직이세요\n"
				"• 조인트 제한 범위를 초과하지 않도록 주의하세요\n"
				"• 위치가 정확하면 'Next Step' 버튼을 클릭하세요"
			)
		
		# Step 1: Position 1 - 현재 위치를 읽어서 오프셋으로 저장
		if self.calibration_current_step == 1:
			state = self.robot.get_state()
			current_joints = state.get("joint_positions", [0.0] * 6)
			
			# 오프셋 계산 (현재 위치를 0으로 만들기 위한 값)
			self.data["joint_offsets"] = [math.radians(-j) for j in current_joints]
			self._log(f"Position 1 recorded. Offsets: {[f'{o:.4f}' for o in self.data['joint_offsets']]}", "info")
			
			# CALIBRATION_POSITION으로 이동 안내
			calib_deg = [math.degrees(a) for a in getattr(self.robot, 'CALIBRATION_POSITION', [0.0] * 6)]
			self.calibration_current_step = 2
			return (
				"in_progress",
				f"Step {self.calibration_current_step}/{self.calibration_max_steps}: Position 2 - 캘리브레이션 위치 설정\n\n"
				f"📋 작업 내용:\n"
				f"• 다음 각도로 로봇을 수동으로 이동하세요:\n"
				f"  - Joint 1: {calib_deg[0]:.1f}°\n"
				f"  - Joint 2: {calib_deg[1]:.1f}°\n"
				f"  - Joint 3: {calib_deg[2]:.1f}°\n"
				f"  - Joint 4: {calib_deg[3]:.1f}°\n"
				f"  - Joint 5: {calib_deg[4]:.1f}°\n"
				f"  - Joint 6: {calib_deg[5]:.1f}°\n\n"
				"✅ Position 1이 성공적으로 기록되었습니다.\n\n"
				"⚠️ 주의사항:\n"
				"• 각 조인트를 정확한 각도로 이동하세요\n"
				"• 위치가 정확하면 'Next Step' 버튼을 클릭하세요"
			)
		
		# Step 2: Position 2 - 캘리브레이션 포지션 읽기
		if self.calibration_current_step == 2:
			state = self.robot.get_state()
			current_joints = state.get("joint_positions", [0.0] * 6)
			
			# 캘리브레이션 포지션 저장 (스텝 단위로 변환 필요)
			# TODO: 실제 스텝 값으로 저장 (FeetechMotorsBus 사용)
			self._log(f"Position 2 recorded. Joints: {[f'{j:.2f}°' for j in current_joints]}", "info")
			
			# FeetechMotorsBus 캘리브레이션 업데이트
			if hasattr(self.robot, 'motors_bus') and self.robot.motors_bus:
				try:
					from .motors.feetech import CalibrationMode
					# 현재 위치를 기준으로 homing_offset 계산
					# TODO: 실제 스텝 값으로 변환
					calibration_data = {
						"motor_names": list(self.robot.MOTORS.keys()),
						"calib_mode": [CalibrationMode.DEGREE.name] * len(self.robot.MOTORS),
						"drive_mode": [0] * len(self.robot.MOTORS),
						"homing_offset": [0] * len(self.robot.MOTORS),  # TODO: 실제 계산
					}
					self.robot.motors_bus.set_calibration(calibration_data)
					self._log("FeetechMotorsBus calibration updated", "success")
				except Exception as e:
					self._log(f"Warning: Failed to update FeetechMotorsBus calibration: {e}", "warning")
			
			self.calibration_current_step = 3
			return (
				"in_progress",
				f"Step {self.calibration_current_step}/{self.calibration_max_steps}: 최종 검증 및 저장\n\n"
				"📋 작업 내용:\n"
				"• 캘리브레이션 데이터가 성공적으로 기록되었습니다\n"
				"• 현재 조인트 위치:\n"
				f"  - Joint 1: {current_joints[0]:.2f}°\n"
				f"  - Joint 2: {current_joints[1]:.2f}°\n"
				f"  - Joint 3: {current_joints[2]:.2f}°\n"
				f"  - Joint 4: {current_joints[3]:.2f}°\n"
				f"  - Joint 5: {current_joints[4]:.2f}°\n"
				f"  - Joint 6: {current_joints[5]:.2f}°\n\n"
				"✅ 다음 단계에서 캘리브레이션 데이터를 저장하고 완료합니다.\n\n"
				"💡 팁: 'Next Step' 버튼을 클릭하면 캘리브레이션이 완료됩니다."
			)
		
		# Step 3: 완료 및 저장
		if self.calibration_current_step == 3:
			# 토크 재활성화
			self.robot.enable_torque()
			self._log("Torque re-enabled", "info")
			
			# 캘리브레이션 데이터 저장
			from ..config import CALIBRATION_DIR
			os.makedirs(CALIBRATION_DIR, exist_ok=True)
			calib_file = os.path.join(CALIBRATION_DIR, "calibration.json")
			self.save(calib_file)
			self._log(f"Calibration saved to {calib_file}", "success")
			
			self.calibration_current_step = 0
			return (
				"success",
				"Calibration completed successfully! The robot is now calibrated and ready to use."
			)
		
		return ("error", "Unknown calibration step")

