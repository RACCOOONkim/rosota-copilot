from typing import Any, Dict, List, Optional
import time
import math
import numpy as np
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
		try:
			if not port:
				return False
			
			baud = baudrate or self.BAUDRATE
			
			# FeetechMotorsBus를 사용한 실제 연결
			if HAS_FEETECH:
				try:
					# PortHandler와 PacketHandler 초기화
					self.port_handler = scs.PortHandler(port)
					self.packet_handler = scs.PacketHandler(1.0)  # Protocol version 1.0
					
					# 포트 열기
					if not self.port_handler.openPort():
						print(f"Failed to open port {port}")
						return False
					
					# 보드레이트 설정
					if not self.port_handler.setBaudRate(baud):
						print(f"Failed to set baudrate {baud}")
						self.port_handler.closePort()
						return False
					
					# 연결 테스트: 여러 서보 ID를 시도하여 연결 확인
					# 포트가 열렸으면 일단 연결 성공으로 간주 (서보가 꺼져있을 수 있음)
					connection_ok = False
					for servo_id in self.SERVO_IDS:
						try:
							# Present_Position 읽기 시도 (address 56)
							dxl_present_position, dxl_comm_result, dxl_error = self.packet_handler.read2ByteTxRx(
								self.port_handler, servo_id, 56
							)
							
							if dxl_comm_result == scs.COMM_SUCCESS:
								connection_ok = True
								print(f"Successfully verified connection to servo ID {servo_id}")
								break
							else:
								# 다른 서보 ID 시도
								continue
						except Exception as e:
							# 서보 ID가 없거나 통신 실패 - 다음 ID 시도
							continue
					
					# 연결 테스트 실패 시에도 포트가 열렸으면 연결 성공으로 간주
					# (서보가 꺼져있거나 설정 문제일 수 있음, 나중에 토크 활성화 시 작동할 수 있음)
					if not connection_ok:
						print(f"Warning: Could not verify servo communication, but port is open. Will attempt connection anyway.")
						# 포트가 열렸으므로 연결 성공으로 간주
						connection_ok = True
					
					# 연결 성공 후 토크 활성화 시도
					if connection_ok:
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
					print(f"SO-100 connected successfully on {port} at {baud} baud")
					return True
					
				except Exception as e:
					print(f"Error connecting to SO-100: {e}")
					if self.port_handler:
						try:
							self.port_handler.closePort()
						except:
							pass
					return False
			else:
				# SDK가 없으면 시뮬레이션 모드
				print("Warning: scservo_sdk not available, using simulation mode")
				self.connected = True
				self.connection_info = {
					"port": port,
					"host": None,
					"baudrate": baud,
					"connected_at": time.time()
				}
				return True
				
		except Exception as e:
			print(f"Connection error: {e}")
			self.connected = False
			return False

	def disconnect(self) -> None:
		"""로봇 연결 해제"""
		if self.port_handler:
			try:
				# 모든 서보 토크 비활성화
				for servo_id in self.SERVO_IDS:
					try:
						self.packet_handler.write1ByteTxRx(
							self.port_handler, servo_id, 40, 0  # Torque_Enable = 0
						)
					except:
						pass
				self.port_handler.closePort()
			except Exception as e:
				print(f"Error disconnecting: {e}")
		
		self.port_handler = None
		self.packet_handler = None
		self.connected = False
		self.connection_info = {}

	def _degrees_to_steps(self, degrees: float) -> int:
		"""
		각도를 스텝으로 변환
		SO-100은 0~4095 스텝이 0~360도에 해당
		중앙값 2048이 180도 (또는 0도, 설정에 따라 다름)
		"""
		# 각도를 0~360 범위로 정규화
		degrees = degrees % 360.0
		if degrees < 0:
			degrees += 360.0
		
		# 0~360도를 0~4095 스텝으로 변환
		steps = int((degrees / 360.0) * self.RESOLUTION)
		# 0~4095 범위로 제한
		return max(0, min(self.RESOLUTION - 1, steps))

	def _steps_to_degrees(self, steps: int) -> float:
		"""
		스텝을 각도로 변환
		SO-100은 0~4095 스텝이 0~360도
		"""
		# 스텝을 0~4095 범위로 정규화
		if steps < 0:
			steps = steps + self.RESOLUTION
		steps = steps % self.RESOLUTION
		
		# 0~4095 스텝을 0~360도로 변환
		degrees = (steps / self.RESOLUTION) * 360.0
		return degrees

	def _read_joint_position(self, joint_index: int) -> Optional[float]:
		"""특정 조인트의 현재 위치 읽기 (도 단위)"""
		if not self.connected or not HAS_SCSERVO or not self.port_handler:
			return None
		
		if joint_index < 0 or joint_index >= len(self.SERVO_IDS):
			return None
		
		servo_id = self.SERVO_IDS[joint_index]
		
		try:
			# Present_Position 읽기 (address 56, 2 bytes)
			dxl_present_position, dxl_comm_result, dxl_error = self.packet_handler.read2ByteTxRx(
				self.port_handler, servo_id, 56
			)
			
			if dxl_comm_result != scs.COMM_SUCCESS:
				# 통신 실패 시 None 반환 (캐시된 값 사용)
				return None
			
			# 스텝을 각도로 변환
			degrees = self._steps_to_degrees(dxl_present_position)
			# 캘리브레이션 오프셋 적용
			degrees -= math.degrees(self.calibration_offsets[joint_index])
			
			return degrees
			
		except Exception as e:
			# 에러 발생 시 None 반환 (캐시된 값 사용)
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
		if HAS_SCSERVO and self.port_handler:
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
		"""
		if not self.connected:
			print(f"Robot not connected, cannot move joint {joint_index}")
			return False
		
		if joint_index < 0 or joint_index >= 6:
			print(f"Invalid joint index: {joint_index}")
			return False
		
		# 실제 하드웨어에 명령 전송
		if HAS_SCSERVO and self.port_handler:
			servo_id = self.SERVO_IDS[joint_index]
			
			try:
				# 현재 위치 읽기 (실제 하드웨어에서)
				current_steps, comm_result, dxl_error = self.packet_handler.read2ByteTxRx(
					self.port_handler, servo_id, 56  # Present_Position
				)
				
				if comm_result != scs.COMM_SUCCESS:
					print(f"Failed to read current position for joint {joint_index}: {self.packet_handler.getTxRxResult(comm_result)}")
					# 읽기 실패 시 시뮬레이션 값 사용
					current_deg = self._sim_joint_positions[joint_index]
				else:
					# 스텝을 각도로 변환
					current_deg = self._steps_to_degrees(current_steps)
					# 캘리브레이션 오프셋 제거
					current_deg -= math.degrees(self.calibration_offsets[joint_index])
					# 캐시 업데이트
					self._sim_joint_positions[joint_index] = current_deg
				
				# 새 위치 계산
				new_position = current_deg + delta_deg
				
				# 제한 확인
				limits = self.joint_limits[joint_index]
				if new_position < limits[0] or new_position > limits[1]:
					print(f"Joint {joint_index} limit exceeded: {new_position} not in {limits}")
					return False  # 제한 초과
				
				# 목표 위치를 스텝으로 변환
				# 캘리브레이션 오프셋 추가
				calibrated_pos = new_position + math.degrees(self.calibration_offsets[joint_index])
				goal_steps = self._degrees_to_steps(calibrated_pos)
				
				# 토크 확인 및 활성화
				torque_enabled, comm_result, dxl_error = self.packet_handler.read1ByteTxRx(
					self.port_handler, servo_id, 40  # Torque_Enable
				)
				
				if comm_result == scs.COMM_SUCCESS and torque_enabled == 0:
					# 토크가 비활성화되어 있으면 활성화
					print(f"Torque disabled for joint {joint_index}, enabling...")
					self.packet_handler.write1ByteTxRx(
						self.port_handler, servo_id, 40, 1  # Torque_Enable = 1
					)
				
				# Goal_Position 쓰기 (address 42, 2 bytes)
				dxl_comm_result, dxl_error = self.packet_handler.write2ByteTxRx(
					self.port_handler, servo_id, 42, goal_steps
				)
				
				if dxl_comm_result != scs.COMM_SUCCESS:
					print(f"Failed to write joint {joint_index} (servo {servo_id}): {self.packet_handler.getTxRxResult(dxl_comm_result)}")
					return False
				
				if dxl_error != 0:
					print(f"Servo error for joint {joint_index}: {self.packet_handler.getRxPacketError(dxl_error)}")
					# 에러가 있어도 명령은 전송됨
				
				# 시뮬레이션 상태 업데이트
				self._sim_joint_positions[joint_index] = new_position
				return True
				
			except Exception as e:
				print(f"Error moving joint {joint_index}: {e}")
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
		if not self.connected or not HAS_SCSERVO or not self.port_handler:
			print("Cannot enable torque: not connected or SDK not available")
			return False
		
		try:
			success_count = 0
			for servo_id in self.SERVO_IDS:
				# Torque_Enable = 1 (address 40)
				dxl_comm_result, dxl_error = self.packet_handler.write1ByteTxRx(
					self.port_handler, servo_id, 40, 1
				)
				if dxl_comm_result == scs.COMM_SUCCESS:
					success_count += 1
					print(f"Torque enabled for servo {servo_id}")
				else:
					print(f"Failed to enable torque for servo {servo_id}: {self.packet_handler.getTxRxResult(dxl_comm_result)}")
			
			if success_count > 0:
				print(f"Torque enabled for {success_count}/{len(self.SERVO_IDS)} servos")
				return True
			else:
				print("Failed to enable torque for any servo")
				return False
		except Exception as e:
			print(f"Error enabling torque: {e}")
			import traceback
			traceback.print_exc()
			return False

	def disable_torque(self) -> bool:
		"""모든 서보 토크 비활성화"""
		if not self.connected or not HAS_SCSERVO or not self.port_handler:
			return False
		
		try:
			for servo_id in self.SERVO_IDS:
				# Torque_Enable = 0 (address 40)
				self.packet_handler.write1ByteTxRx(
					self.port_handler, servo_id, 40, 0
				)
			return True
		except Exception as e:
			print(f"Error disabling torque: {e}")
			return False
