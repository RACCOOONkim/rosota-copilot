"""
모터 설정 관리
LeRobot의 모터 설정 기능을 웹 인터페이스로 통합
"""
import time
from typing import Optional, Dict, List, Tuple
from enum import Enum

try:
	from .motors.feetech import FeetechMotorsBus, SCS_SERIES_BAUDRATE_TABLE, MODEL_BAUDRATE_TABLE
	HAS_FEETECH = True
except ImportError:
	HAS_FEETECH = False
	print("Warning: FeetechMotorsBus not available.")


class SetupStatus(Enum):
	"""설정 진행 상태"""
	IDLE = "idle"
	FINDING_PORT = "finding_port"
	PORT_FOUND = "port_found"
	CONFIGURING_MOTOR = "configuring_motor"
	MOTOR_CONFIGURED = "motor_configured"
	COMPLETED = "completed"
	ERROR = "error"


class MotorSetupManager:
	"""
	모터 설정 관리 클래스
	LeRobot의 모터 설정 프로세스를 관리
	"""
	
	# SO-100 모터 설정 (follower와 leader 동일)
	MOTOR_CONFIG = {
		"follower": [
			{"name": "gripper", "id": 6, "description": "Gripper motor"},
			{"name": "wrist_roll", "id": 5, "description": "Wrist roll motor"},
			{"name": "wrist_flex", "id": 4, "description": "Wrist flex motor"},
			{"name": "elbow_flex", "id": 3, "description": "Elbow flex motor"},
			{"name": "shoulder_lift", "id": 2, "description": "Shoulder lift motor"},
			{"name": "shoulder_pan", "id": 1, "description": "Shoulder pan motor"},
		],
		"leader": [
			{"name": "gripper", "id": 6, "description": "Gripper motor"},
			{"name": "wrist_roll", "id": 5, "description": "Wrist roll motor"},
			{"name": "wrist_flex", "id": 4, "description": "Wrist flex motor"},
			{"name": "elbow_flex", "id": 3, "description": "Elbow flex motor"},
			{"name": "shoulder_lift", "id": 2, "description": "Shoulder lift motor"},
			{"name": "shoulder_pan", "id": 1, "description": "Shoulder pan motor"},
		]
	}
	
	BAUDRATE = 1_000_000  # 1Mbps
	MOTOR_MODEL = "sts3215"
	
	def __init__(self):
		self.status = SetupStatus.IDLE
		self.current_port: Optional[str] = None
		self.robot_type: Optional[str] = None  # "follower" or "leader"
		self.current_motor_index = 0
		self.error_message: Optional[str] = None
		self.motors_bus: Optional[FeetechMotorsBus] = None
		
	def reset(self):
		"""설정 상태 초기화"""
		if self.motors_bus and self.motors_bus.is_connected:
			try:
				self.motors_bus.disconnect()
			except:
				pass
		self.status = SetupStatus.IDLE
		self.current_port = None
		self.robot_type = None
		self.current_motor_index = 0
		self.error_message = None
		self.motors_bus = None
	
	def find_port_by_disconnect(self, ports_before: List[str]) -> Optional[str]:
		"""
		LeRobot 방식: 연결 전후 포트 비교로 MotorsBus 포트 찾기
		
		이 방법이 필요한 이유:
		1. 여러 USB 장치가 연결되어 있을 때 MotorsBus 포트를 정확히 식별하기 위해
		2. 포트 이름만으로는 MotorsBus를 구분하기 어려울 수 있음
		3. 연결 전후 포트 목록을 비교하여 사라진 포트가 MotorsBus 포트
		
		Args:
			ports_before: 연결 전 포트 목록
			
		Returns:
			찾은 포트 또는 None
		"""
		if not HAS_FEETECH:
			raise RuntimeError("FeetechMotorsBus not available")
		
		import serial.tools.list_ports
		time.sleep(0.5)  # 포트 해제 대기
		
		ports_after = [p.device for p in serial.tools.list_ports.comports()]
		ports_diff = list(set(ports_before) - set(ports_after))
		
		if len(ports_diff) == 1:
			return ports_diff[0]
		elif len(ports_diff) == 0:
			raise OSError(
				f"Could not detect the port. No difference was found. "
				f"This usually means:\n"
				f"1. The USB cable was not disconnected\n"
				f"2. Another device was connected at the same time\n"
				f"3. The port is still in use by another process\n"
				f"Before: {ports_before}, After: {ports_after}"
			)
		else:
			raise OSError(
				f"Could not detect the port. More than one port was found: {ports_diff}\n"
				f"This usually means multiple USB devices were disconnected. "
				f"Please disconnect only the MotorsBus USB cable."
			)
	
	def find_port_by_pid(self) -> Optional[str]:
		"""
		PID 기반 포트 찾기 (USB 케이블 분리 불필요)
		SO-100 MotorsBus는 CH340 칩셋을 사용하며 PID가 21971 또는 29987
		
		Returns:
			찾은 포트 또는 None
		"""
		try:
			import serial.tools.list_ports
		except ImportError:
			return None
		
		# SO-100 MotorsBus PID (CH340 칩셋)
		SO100_PIDS = [21971, 29987]
		
		for port_info in serial.tools.list_ports.comports():
			if hasattr(port_info, 'pid') and port_info.pid in SO100_PIDS:
				return port_info.device
		
		return None
	
	def configure_single_motor(
		self,
		port: str,
		motor_id: int,
		baudrate: int = BAUDRATE
	) -> Dict:
		"""
		단일 모터 설정 (ID와 baudrate)
		
		Args:
			port: MotorsBus 포트
			motor_id: 설정할 모터 ID (1-6)
			baudrate: 설정할 baudrate (기본값: 1,000,000)
			
		Returns:
			설정 결과 딕셔너리
		"""
		if not HAS_FEETECH:
			raise RuntimeError("FeetechMotorsBus not available")
		
		# 모터 설정 (임시로 설정할 ID 사용)
		motor_name = "motor"
		motors = {motor_name: (motor_id, self.MOTOR_MODEL)}
		
		motors_bus = FeetechMotorsBus(port=port, motors=motors)
		
		try:
			motors_bus.connect()
			
			# 모든 baudrate 스캔하여 현재 모터 찾기
			all_baudrates = set(SCS_SERIES_BAUDRATE_TABLE.values())
			found_motor_index = -1
			
			for baud in all_baudrates:
				motors_bus.set_bus_baudrate(baud)
				present_ids = motors_bus.find_motor_indices(list(range(1, 10)))
				
				if len(present_ids) > 1:
					raise ValueError(
						"More than one motor ID detected. Please disconnect all but one motor."
					)
				
				if len(present_ids) == 1:
					if found_motor_index != -1:
						raise ValueError(
							"More than one motor ID detected. Please disconnect all but one motor."
						)
					found_motor_index = present_ids[0]
					break
			
			if found_motor_index == -1:
				raise ValueError("No motors detected. Please ensure you have one motor connected.")
			
			# Lock 해제 (ID와 baudrate 쓰기 가능하도록)
			motors_bus.write_with_motor_ids(
				motors_bus.motor_models, found_motor_index, "Lock", 0
			)
			
			# Baudrate 설정
			if baudrate != self.BAUDRATE:
				baudrate_idx = list(SCS_SERIES_BAUDRATE_TABLE.values()).index(baudrate)
				motors_bus.write_with_motor_ids(
					motors_bus.motor_models, found_motor_index, "Baud_Rate", baudrate_idx
				)
				time.sleep(0.5)
				motors_bus.set_bus_baudrate(baudrate)
				
				# 확인
				present_baudrate_idx = motors_bus.read_with_motor_ids(
					motors_bus.motor_models, found_motor_index, "Baud_Rate", num_retry=2
				)
				if present_baudrate_idx != baudrate_idx:
					raise OSError("Failed to write baudrate.")
			
			# ID 설정
			motors_bus.write_with_motor_ids(
				motors_bus.motor_models, found_motor_index, "Lock", 0
			)
			motors_bus.write_with_motor_ids(
				motors_bus.motor_models, found_motor_index, "ID", motor_id
			)
			
			# 확인
			present_idx = motors_bus.read_with_motor_ids(
				motors_bus.motor_models, motor_id, "ID", num_retry=2
			)
			if present_idx != motor_id:
				raise OSError("Failed to write motor ID.")
			
			# 추가 설정 (Feetech 특화)
			motors_bus.write("Lock", 0)
			motors_bus.write("Maximum_Acceleration", 254)
			
			# Offset 초기화 (선택적)
			# 주의: 이 단계는 모터를 2048 위치로 이동시킵니다.
			# 하지만 나중에 캘리브레이션에서 소프트웨어 레벨의 오프셋을 설정하므로
			# 이 하드웨어 Offset 설정은 선택적입니다.
			# LeRobot 표준 프로세스를 따르기 위해 포함되어 있지만,
			# 모터가 움직이지 않게 하려면 아래 4줄을 주석 처리하세요.
			# motors_bus.write("Goal_Position", 2048)
			# time.sleep(2)
			# motors_bus.write("Offset", 0)
			# time.sleep(2)
			
			return {
				"success": True,
				"motor_id": motor_id,
				"found_index": found_motor_index,
				"baudrate": baudrate
			}
			
		except Exception as e:
			return {
				"success": False,
				"error": str(e),
				"motor_id": motor_id
			}
		finally:
			motors_bus.disconnect()
	
	def reset_motor_id(
		self,
		port: str,
		target_id: int,
		reset_to_id: int = 1,
		baudrate: int = BAUDRATE
	) -> Dict:
		"""
		모터 ID를 기본값으로 리셋
		
		Args:
			port: MotorsBus 포트
			target_id: 리셋할 모터의 현재 ID
			reset_to_id: 리셋할 ID (기본값: 1)
			baudrate: baudrate (기본값: 1,000,000)
			
		Returns:
			리셋 결과 딕셔너리
		"""
		if not HAS_FEETECH:
			raise RuntimeError("FeetechMotorsBus not available")
		
		motor_name = "motor"
		motors = {motor_name: (target_id, self.MOTOR_MODEL)}
		
		motors_bus = FeetechMotorsBus(port=port, motors=motors)
		
		try:
			motors_bus.connect()
			motors_bus.set_bus_baudrate(baudrate)
			
			# 현재 ID로 모터 찾기 시도
			try:
				# Lock 해제
				motors_bus.write_with_motor_ids(
					motors_bus.motor_models, target_id, "Lock", 0
				)
				
				# ID를 기본값으로 변경
				motors_bus.write_with_motor_ids(
					motors_bus.motor_models, target_id, "ID", reset_to_id
				)
				time.sleep(0.1)
				
				# 확인
				present_idx = motors_bus.read_with_motor_ids(
					motors_bus.motor_models, reset_to_id, "ID", num_retry=2
				)
				if present_idx != reset_to_id:
					raise OSError("Failed to reset motor ID.")
				
				return {
					"success": True,
					"old_id": target_id,
					"new_id": reset_to_id,
					"message": f"Motor ID reset from {target_id} to {reset_to_id}"
				}
			except ConnectionError:
				# 현재 ID로 찾을 수 없으면, 모든 baudrate 스캔
				all_baudrates = set(SCS_SERIES_BAUDRATE_TABLE.values())
				found_motor_index = -1
				
				for baud in all_baudrates:
					motors_bus.set_bus_baudrate(baud)
					present_ids = motors_bus.find_motor_indices(list(range(1, 10)))
					
					if len(present_ids) == 1:
						found_motor_index = present_ids[0]
						break
				
				if found_motor_index == -1:
					raise ValueError("No motors detected. Please ensure you have one motor connected.")
				
				# Lock 해제
				motors_bus.write_with_motor_ids(
					motors_bus.motor_models, found_motor_index, "Lock", 0
				)
				
				# ID를 기본값으로 변경
				motors_bus.write_with_motor_ids(
					motors_bus.motor_models, found_motor_index, "ID", reset_to_id
				)
				time.sleep(0.1)
				
				# 확인
				present_idx = motors_bus.read_with_motor_ids(
					motors_bus.motor_models, reset_to_id, "ID", num_retry=2
				)
				if present_idx != reset_to_id:
					raise OSError("Failed to reset motor ID.")
				
				return {
					"success": True,
					"old_id": found_motor_index,
					"new_id": reset_to_id,
					"message": f"Motor ID reset from {found_motor_index} to {reset_to_id}"
				}
			
		except Exception as e:
			return {
				"success": False,
				"error": str(e),
				"target_id": target_id
			}
		finally:
			motors_bus.disconnect()
	
	def check_motor_id(
		self,
		port: str,
		baudrate: int = BAUDRATE
	) -> Dict:
		"""
		연결된 모터의 ID 확인
		
		Args:
			port: MotorsBus 포트
			baudrate: baudrate (기본값: 1,000,000)
			
		Returns:
			모터 ID 확인 결과 딕셔너리
		"""
		if not HAS_FEETECH:
			raise RuntimeError("FeetechMotorsBus not available")
		
		# 임시 모터 설정 (ID를 모르므로 임의의 ID 사용)
		motor_name = "motor"
		motors = {motor_name: (1, self.MOTOR_MODEL)}
		
		motors_bus = FeetechMotorsBus(port=port, motors=motors)
		
		try:
			motors_bus.connect()
			
			# 모든 가능한 baudrate에서 모터 찾기
			all_baudrates = set(SCS_SERIES_BAUDRATE_TABLE.values())
			found_motors = []
			
			for baud in all_baudrates:
				try:
					motors_bus.set_bus_baudrate(baud)
					# ID 1-10 범위에서 모터 찾기
					present_ids = motors_bus.find_motor_indices(list(range(1, 11)))
					
					for motor_id in present_ids:
						# 각 모터의 실제 ID 읽기
						try:
							actual_id = motors_bus.read_with_motor_ids(
								motors_bus.motor_models, motor_id, "ID", num_retry=2
							)
							if actual_id not in [m["id"] for m in found_motors]:
								found_motors.append({
									"id": actual_id,
									"baudrate": baud
								})
						except:
							pass
				except:
					continue
			
			if len(found_motors) == 0:
				return {
					"success": False,
					"error": "No motors detected. Please ensure a motor is connected."
				}
			elif len(found_motors) > 1:
				return {
					"success": True,
					"motors": found_motors,
					"warning": f"Multiple motors detected ({len(found_motors)}). Please connect only one motor."
				}
			else:
				return {
					"success": True,
					"motor_id": found_motors[0]["id"],
					"baudrate": found_motors[0]["baudrate"]
				}
				
		except Exception as e:
			return {
				"success": False,
				"error": str(e)
			}
		finally:
			motors_bus.disconnect()
	
	def get_motor_list(self, robot_type: str) -> List[Dict]:
		"""로봇 타입에 따른 모터 목록 반환"""
		return self.MOTOR_CONFIG.get(robot_type, [])
	
	def get_status(self) -> Dict:
		"""현재 설정 상태 반환"""
		motor_list = []
		if self.robot_type:
			motor_list = self.get_motor_list(self.robot_type)
		
		return {
			"status": self.status.value,
			"port": self.current_port,
			"robot_type": self.robot_type,
			"current_motor_index": self.current_motor_index,
			"total_motors": len(motor_list),
			"current_motor": motor_list[self.current_motor_index] if motor_list and self.current_motor_index < len(motor_list) else None,
			"error": self.error_message,
			"motors": motor_list
		}

