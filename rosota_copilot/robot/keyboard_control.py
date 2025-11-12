from typing import Dict, Optional, Callable
from enum import Enum
import time
from collections import deque


class ControlMode(Enum):
	JOINT = "joint"
	CARTESIAN = "cartesian"
	GRIPPER = "gripper"


class KeyboardController:
	"""
	키보드 입력을 로봇 제어 명령으로 변환하는 컨트롤러.
	브라우저에서 키 입력을 받아 처리합니다.
	"""

	def __init__(self, robot_adapter):
		self.robot = robot_adapter
		self.mode = ControlMode.JOINT
		self.running = False
		self.estop_active = False
		self.speed_multiplier = 1.0  # 0.1 ~ 2.0
		self.step_size = 5.0  # degrees or mm
		
		# 키 매핑 정의
		self.key_mapping: Dict[str, Callable] = {
			# 모드 전환
			"m": self._toggle_mode,
			" ": self._emergency_stop,
			
			# Joint 모드 (6 DOF)
			"i": lambda: self._move_joint(0, +1),  # Joint 1 증가
			"k": lambda: self._move_joint(0, -1),  # Joint 1 감소
			"j": lambda: self._move_joint(1, +1),  # Joint 2 증가
			"l": lambda: self._move_joint(1, -1),  # Joint 2 감소
			"u": lambda: self._move_joint(2, +1),  # Joint 3 증가
			"o": lambda: self._move_joint(2, -1),  # Joint 3 감소
			"7": lambda: self._move_joint(3, +1),  # Joint 4 증가
			"9": lambda: self._move_joint(3, -1),  # Joint 4 감소
			"8": lambda: self._move_joint(4, +1),  # Joint 5 증가
			"0": lambda: self._move_joint(4, -1),  # Joint 5 감소
			"y": lambda: self._move_joint(5, +1),  # Joint 6 증가
			"h": lambda: self._move_joint(5, -1),  # Joint 6 감소
			
			# Cartesian 모드
			"w": lambda: self._move_cartesian(0, +1),  # X+
			"s": lambda: self._move_cartesian(0, -1),  # X-
			"a": lambda: self._move_cartesian(1, -1),  # Y-
			"d": lambda: self._move_cartesian(1, +1),  # Y+
			"q": lambda: self._move_cartesian(2, +1),  # Z+
			"e": lambda: self._move_cartesian(2, -1),  # Z-
			"r": lambda: self._move_cartesian(3, +1),  # Roll+
			"f": lambda: self._move_cartesian(3, -1),  # Roll-
			"t": lambda: self._move_cartesian(4, +1),  # Pitch+
			"g": lambda: self._move_cartesian(4, -1),  # Pitch-
			"z": lambda: self._move_cartesian(5, +1),  # Yaw+
			"x": lambda: self._move_cartesian(5, -1),  # Yaw-
			
			# Gripper
			"c": self._toggle_gripper,
			
			# 속도 조절
			"+": lambda: self._adjust_speed(1.1),
			"=": lambda: self._adjust_speed(1.1),  # + 키 (shift 없을 때)
			"-": lambda: self._adjust_speed(0.9),
			"_": lambda: self._adjust_speed(0.9),  # - 키 (shift 없을 때)
		}
		
		# 활성 키 추적 (키를 누르고 있는 동안)
		self.active_keys: set = set()
		self.last_key_time: Dict[str, float] = {}

	def _toggle_mode(self):
		"""모드 전환: Joint -> Cartesian -> Gripper -> Joint"""
		modes = [ControlMode.JOINT, ControlMode.CARTESIAN, ControlMode.GRIPPER]
		current_idx = modes.index(self.mode)
		self.mode = modes[(current_idx + 1) % len(modes)]
		return {"action": "mode_change", "mode": self.mode.value}

	def _emergency_stop(self):
		"""긴급 정지"""
		self.estop_active = not self.estop_active
		if self.estop_active:
			# 모든 모션 중지
			# TODO: 실제 로봇에 E-Stop 명령 전송
			pass
		return {"action": "estop", "active": self.estop_active}

	def start(self) -> Dict:
		"""키보드 제어 시작"""
		if not self.robot.connected:
			return {"action": "error", "message": "Robot not connected"}
		
		print(f"[KeyboardController] Starting control. Robot connected: {self.robot.connected}")
		self.running = True
		self.estop_active = False
		# 활성 키 초기화
		self.active_keys.clear()
		self.last_key_time.clear()
		print(f"[KeyboardController] Control started. Running: {self.running}")
		return {
			"action": "control_started",
			"message": "Keyboard control started",
			"status": self.get_status()
		}
	
	def stop(self) -> Dict:
		"""키보드 제어 중지"""
		self.running = False
		# 활성 키 초기화
		self.active_keys.clear()
		self.last_key_time.clear()
		return {
			"action": "control_stopped",
			"message": "Keyboard control stopped",
			"status": self.get_status()
		}

	def _move_joint(self, joint_index: int, direction: int):
		"""조인트 이동"""
		if not self.running:
			print(f"[KeyboardController] Move joint {joint_index} ignored: control not running")
			return None
		if self.mode != ControlMode.JOINT:
			print(f"[KeyboardController] Move joint {joint_index} ignored: wrong mode ({self.mode.value})")
			return None
		if self.estop_active:
			print(f"[KeyboardController] Move joint {joint_index} ignored: E-Stop active")
			return None
		
		delta = direction * self.step_size * self.speed_multiplier
		print(f"[KeyboardController] Moving joint {joint_index} by {delta:.2f}°")
		
		# 현재 위치 확인 (디버깅용)
		state = self.robot.get_state()
		current_pos = state.get("joint_positions", [0.0] * 6)[joint_index] if state else None
		if current_pos is not None:
			limits = self.robot.joint_limits[joint_index]
			print(f"[KeyboardController] Joint {joint_index} current: {current_pos:.2f}°, limits: [{limits[0]:.2f}, {limits[1]:.2f}]")
		
		success = self.robot.move_joint_delta(joint_index, delta)
		print(f"[KeyboardController] Joint {joint_index} move result: {success}")
		return {
			"action": "joint_move",
			"joint": joint_index,
			"delta": delta,
			"success": success,
		}

	def _move_cartesian(self, axis: int, direction: int):
		"""Cartesian 이동 (0:X, 1:Y, 2:Z, 3:Roll, 4:Pitch, 5:Yaw)"""
		if not self.running:
			return None
		if self.mode != ControlMode.CARTESIAN or self.estop_active:
			return None
		
		delta = [0.0] * 6
		step = self.step_size * self.speed_multiplier
		if axis < 3:  # 위치 (mm)
			delta[axis] = direction * step
		else:  # 회전 (deg)
			delta[axis] = direction * step * 0.1  # 회전은 더 작은 스텝
		
		success = self.robot.move_cartesian_delta(*delta)
		return {
			"action": "cartesian_move",
			"axis": axis,
			"delta": delta,
			"success": success,
		}

	def _toggle_gripper(self):
		"""그리퍼 토글"""
		if not self.running:
			return None
		if self.estop_active:
			return None
		# TODO: 현재 그리퍼 상태 확인 후 토글
		success = self.robot.set_gripper(0.5)  # 임시
		return {"action": "gripper_toggle", "success": success}

	def _adjust_speed(self, multiplier: float):
		"""속도 조절"""
		self.speed_multiplier = max(0.1, min(2.0, self.speed_multiplier * multiplier))
		return {"action": "speed_change", "multiplier": self.speed_multiplier}

	def handle_key_event(self, key: str, event_type: str = "keydown") -> Optional[Dict]:
		"""
		키 이벤트 처리
		key: 키 이름 (소문자 권장)
		event_type: "keydown" or "keyup"
		"""
		# 제어가 시작되지 않았으면 키 입력 무시 (단, 모드 전환/긴급정지는 허용)
		key_lower = key.lower()
		control_keys = ["m", " "]  # 모드 전환, 긴급 정지
		
		if event_type == "keydown":
			if key_lower in self.key_mapping:
				# 제어가 시작되지 않았고, 제어 키가 아니면 무시
				if not self.running and key_lower not in control_keys:
					return {"action": "ignored", "message": "Control not started. Press Start Control first."}
				
				# 중복 방지: 같은 키가 너무 빠르게 반복되지 않도록
				# 제어 루프가 50ms마다 실행되므로 디바운스를 30ms로 줄임
				now = time.time()
				last_time = self.last_key_time.get(key_lower, 0)
				if now - last_time < 0.03:  # 30ms 디바운스 (제어 루프 50ms보다 작게)
					return None
				self.last_key_time[key_lower] = now
				
				handler = self.key_mapping[key_lower]
				return handler()
		
		elif event_type == "keyup":
			if key_lower in self.active_keys:
				self.active_keys.discard(key_lower)
		
		return None

	def get_status(self) -> Dict:
		"""현재 컨트롤러 상태 반환"""
		return {
			"mode": self.mode.value,
			"estop_active": self.estop_active,
			"speed_multiplier": self.speed_multiplier,
			"step_size": self.step_size,
			"running": self.running,
		}

