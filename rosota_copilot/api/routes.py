from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel
from typing import Optional, List
import numpy as np
from ..config import CALIBRATION_DIR
from ..robot.usb_scanner import detect_robot_port, scan_serial_ports
from ..robot.motor_setup import SetupStatus
import serial.tools.list_ports

api_router = APIRouter()


class ConnectRequest(BaseModel):
	port: Optional[str] = None
	host: Optional[str] = None
	baudrate: Optional[int] = None


@api_router.get("/health")
async def health():
	return {"ok": True, "service": "rosota-copilot"}


@api_router.post("/connect")
async def connect_robot(req: ConnectRequest, request: Request):
	"""로봇 연결"""
	try:
		robot_adapter = request.app.state.robot_adapter
		# 포트/호스트가 없으면 자동 탐지 시도
		port = req.port
		host = req.host
		baud = req.baudrate or 115200
		if not port and not host:
			port = detect_robot_port()
			if not port:
				return {
					"ok": False,
					"error": "No robot port detected",
					"ports": scan_serial_ports(),
				}

		# SOArm100AdapterV2는 port만 받음
		if port:
			success = robot_adapter.connect(port=port)
		elif host:
			# TCP/IP 연결은 아직 지원하지 않음
			raise HTTPException(status_code=400, detail="TCP/IP connection not supported with SOArm100AdapterV2")
		else:
			raise HTTPException(status_code=400, detail="Port or host required")
		if success:
			# 캘리브레이션 매니저에 로봇 어댑터 연결
			calibration_manager = request.app.state.calibration_manager
			calibration_manager.robot = robot_adapter
			
			# 캘리브레이션 데이터 자동 로드 (조인트 제한값 업데이트)
			try:
				from ..config import CALIBRATION_DIR
				import os
				calib_file = os.path.join(CALIBRATION_DIR, "calibration.json")
				if os.path.exists(calib_file):
					calibration_manager.load(calib_file)
			except Exception as e:
				# 캘리브레이션 파일이 없거나 로드 실패해도 연결은 성공
				print(f"[API] Warning: Could not load calibration data: {e}")
			
			# 전압 정보 포함
			voltage_info = {
				"detected_voltage": getattr(robot_adapter, 'detected_voltage', None),
				"config_loaded": robot_adapter.config is not None
			}
			return {
				"ok": True,
				"details": {
					"port": port,
					"host": host,
					"baudrate": baud,
					"status": "Connected",
					**voltage_info
				}
			}
		else:
			return {
				"ok": False,
				"error": "Connection failed",
				"ports": scan_serial_ports(),
			}
	except Exception as e:
		raise HTTPException(status_code=500, detail=str(e))


@api_router.post("/calibration/wizard/step")
async def calibration_wizard_step(request: Request):
	"""캘리브레이션 마법사 단계 실행"""
	try:
		robot_adapter = request.app.state.robot_adapter
		calibration_manager = request.app.state.calibration_manager
		if not robot_adapter.connected:
			raise HTTPException(status_code=400, detail="Robot not connected")
		
		# 비동기로 실행
		import asyncio
		loop = asyncio.get_event_loop()
		status, message = await loop.run_in_executor(None, calibration_manager.calibrate_step)
		
		return {
			"ok": status != "error",
			"status": status,
			"message": message,
			"step": calibration_manager.calibration_current_step,
			"max_steps": calibration_manager.calibration_max_steps
		}
	except HTTPException:
		raise
	except Exception as e:
		import traceback
		traceback.print_exc()
		raise HTTPException(status_code=500, detail=str(e))


@api_router.get("/calibration/wizard/status")
async def calibration_wizard_status(request: Request):
	"""캘리브레이션 마법사 상태 조회"""
	try:
		calibration_manager = request.app.state.calibration_manager
		return {
			"ok": True,
			"current_step": calibration_manager.calibration_current_step,
			"max_steps": calibration_manager.calibration_max_steps
		}
	except Exception as e:
		raise HTTPException(status_code=500, detail=str(e))


@api_router.post("/calibration/wizard/reset")
async def calibration_wizard_reset(request: Request):
	"""캘리브레이션 마법사 리셋"""
	try:
		calibration_manager = request.app.state.calibration_manager
		calibration_manager.calibration_current_step = 0
		calibration_manager.joint_min_positions = [None] * 6
		calibration_manager.joint_max_positions = [None] * 6
		calibration_manager.realtime_min_positions = [None] * 6
		calibration_manager.realtime_max_positions = [None] * 6
		calibration_manager.current_joint_index = 0
		return {"ok": True, "message": "Calibration wizard reset"}
	except Exception as e:
		raise HTTPException(status_code=500, detail=str(e))


@api_router.post("/calibration/wizard/record-min")
async def calibration_record_min(request: Request):
	"""현재 조인트의 최소 위치 기록"""
	try:
		calibration_manager = request.app.state.calibration_manager
		success = calibration_manager.record_joint_min()
		if not success:
			raise HTTPException(status_code=400, detail="Cannot record min position at this step")
		
		status = calibration_manager.get_calibration_status()
		return {
			"ok": True,
			"message": "Minimum position recorded",
			"status": status
		}
	except HTTPException:
		raise
	except Exception as e:
		raise HTTPException(status_code=500, detail=str(e))


@api_router.post("/calibration/wizard/record-max")
async def calibration_record_max(request: Request):
	"""현재 조인트의 최대 위치 기록"""
	try:
		calibration_manager = request.app.state.calibration_manager
		success = calibration_manager.record_joint_max()
		if not success:
			raise HTTPException(status_code=400, detail="Cannot record max position at this step")
		
		status = calibration_manager.get_calibration_status()
		return {
			"ok": True,
			"message": "Maximum position recorded",
			"status": status
		}
	except HTTPException:
		raise
	except Exception as e:
		raise HTTPException(status_code=500, detail=str(e))


@api_router.get("/calibration/wizard/realtime")
async def calibration_realtime(request: Request):
	"""실시간 조인트 위치 및 min/max 정보 조회"""
	try:
		calibration_manager = request.app.state.calibration_manager
		status = calibration_manager.update_realtime_positions()
		return {
			"ok": True,
			"status": status
		}
	except Exception as e:
		raise HTTPException(status_code=500, detail=str(e))


@api_router.post("/calibration/wizard/auto-record")
async def calibration_auto_record(request: Request):
	"""현재 조인트의 실시간 추적된 min/max를 자동으로 기록"""
	try:
		calibration_manager = request.app.state.calibration_manager
		success = calibration_manager.auto_record_current_joint()
		if not success:
			raise HTTPException(status_code=400, detail="Cannot auto-record at this step")
		
		status = calibration_manager.get_calibration_status()
		return {
			"ok": True,
			"message": "Auto-recorded min/max positions",
			"status": status
		}
	except HTTPException:
		raise
	except Exception as e:
		raise HTTPException(status_code=500, detail=str(e))


@api_router.post("/disconnect")
async def disconnect_robot(request: Request):
	"""로봇 연결 해제"""
	try:
		robot_adapter = request.app.state.robot_adapter
		robot_adapter.disconnect()
		return {"ok": True}
	except Exception as e:
		raise HTTPException(status_code=500, detail=str(e))


@api_router.get("/state")
async def get_state(request: Request):
	"""현재 로봇 상태 반환"""
	try:
		robot_adapter = request.app.state.robot_adapter
		keyboard_controller = request.app.state.keyboard_controller
		state = robot_adapter.get_state()
		control_status = keyboard_controller.get_status()
		return {
			**state,
			"control": control_status,
			"connection": robot_adapter.connection_info,
		}
	except Exception as e:
		raise HTTPException(status_code=500, detail=str(e))


@api_router.get("/voltage")
async def get_voltage(request: Request):
	"""로봇 전압 읽기"""
	try:
		robot_adapter = request.app.state.robot_adapter
		if not robot_adapter.connected:
			raise HTTPException(status_code=400, detail="Robot not connected")
		
		voltage = robot_adapter.detect_voltage()
		voltages = []
		for servo_id in robot_adapter.SERVO_IDS:
			v = robot_adapter.read_motor_voltage(servo_id)
			if v is not None:
				voltages.append(v)
		
		return {
			"ok": True,
			"detected_voltage": voltage,
			"motor_voltages": voltages,
			"average_voltage": float(np.mean(voltages)) if voltages else None
		}
	except Exception as e:
		raise HTTPException(status_code=500, detail=str(e))


@api_router.post("/calibration/home")
async def calibration_home(request: Request):
	"""홈 포지션으로 이동"""
	try:
		robot_adapter = request.app.state.robot_adapter
		calibration_manager = request.app.state.calibration_manager
		if not robot_adapter.connected:
			raise HTTPException(status_code=400, detail="Robot not connected")
		
		# 비동기로 실행 (블로킹 방지)
		import asyncio
		loop = asyncio.get_event_loop()
		success = await loop.run_in_executor(None, calibration_manager.home)
		
		if success:
			return {"ok": True, "message": "Home movement completed successfully"}
		else:
			raise HTTPException(status_code=500, detail="Home movement failed")
	except HTTPException:
		raise
	except Exception as e:
		import traceback
		traceback.print_exc()
		raise HTTPException(status_code=500, detail=str(e))


@api_router.post("/calibration/zero")
async def calibration_zero(request: Request):
	"""조인트 제로 설정"""
	try:
		robot_adapter = request.app.state.robot_adapter
		calibration_manager = request.app.state.calibration_manager
		if not robot_adapter.connected:
			raise HTTPException(status_code=400, detail="Robot not connected")
		
		# 비동기로 실행
		import asyncio
		loop = asyncio.get_event_loop()
		success = await loop.run_in_executor(None, calibration_manager.zero_joints)
		
		if success:
			# 현재 오프셋 정보 반환
			offsets = calibration_manager.data.get("joint_offsets", [0.0] * 6)
			return {
				"ok": True,
				"message": "Joints zeroed successfully",
				"offsets": offsets
			}
		else:
			raise HTTPException(status_code=500, detail="Zero failed")
	except HTTPException:
		raise
	except Exception as e:
		import traceback
		traceback.print_exc()
		raise HTTPException(status_code=500, detail=str(e))


@api_router.post("/calibration/run")
async def calibration_run(request: Request):
	"""전체 캘리브레이션 실행"""
	try:
		robot_adapter = request.app.state.robot_adapter
		calibration_manager = request.app.state.calibration_manager
		if not robot_adapter.connected:
			raise HTTPException(status_code=400, detail="Robot not connected")
		
		# 비동기로 실행
		import asyncio
		loop = asyncio.get_event_loop()
		
		# 홈 이동
		home_success = await loop.run_in_executor(None, calibration_manager.home)
		if not home_success:
			raise HTTPException(status_code=500, detail="Home movement failed")
		
		# 제로 설정
		zero_success = await loop.run_in_executor(None, calibration_manager.zero_joints)
		if not zero_success:
			raise HTTPException(status_code=500, detail="Zero joints failed")
		
		# 저장
		import os
		os.makedirs(CALIBRATION_DIR, exist_ok=True)
		calibration_file = os.path.join(CALIBRATION_DIR, "calibration.json")
		calibration_manager.save(calibration_file)
		
		return {
			"ok": True,
			"message": "Calibration completed successfully",
			"file": calibration_file,
			"offsets": calibration_manager.data.get("joint_offsets", [0.0] * 6)
		}
	except HTTPException:
		raise
	except Exception as e:
		import traceback
		traceback.print_exc()
		raise HTTPException(status_code=500, detail=str(e))


@api_router.get("/calibration/load")
async def calibration_load(request: Request):
	"""캘리브레이션 데이터 로드"""
	try:
		calibration_manager = request.app.state.calibration_manager
		calibration_file = CALIBRATION_DIR / "default.json"
		if not calibration_file.exists():
			raise HTTPException(status_code=404, detail="Calibration file not found")
		calibration_manager.load(str(calibration_file))
		return {
			"ok": True,
			"data": calibration_manager.data
		}
	except Exception as e:
		raise HTTPException(status_code=500, detail=str(e))


@api_router.get("/ports")
async def list_ports():
	"""사용 가능한 시리얼 포트 목록"""
	return {"ok": True, "ports": scan_serial_ports()}


class JointMoveRequest(BaseModel):
	joint_index: int
	delta_deg: float


class JointSetRequest(BaseModel):
	joint_index: int
	target_deg: float


@api_router.post("/joint/move")
async def joint_move(req: JointMoveRequest, request: Request):
	"""조인트 상대 이동"""
	try:
		robot_adapter = request.app.state.robot_adapter
		if not robot_adapter.connected:
			raise HTTPException(status_code=400, detail="Robot not connected")
		ok = robot_adapter.move_joint_delta(req.joint_index, req.delta_deg)
		if not ok:
			raise HTTPException(status_code=400, detail="Move rejected (limits or connection)")
		return {"ok": True}
	except HTTPException:
		raise
	except Exception as e:
		raise HTTPException(status_code=500, detail=str(e))


@api_router.post("/joint/set")
async def joint_set(req: JointSetRequest, request: Request):
	"""조인트 절대 위치 설정 (시뮬레이션 모드: 현재값과 차이를 delta로 처리)"""
	try:
		robot_adapter = request.app.state.robot_adapter
		if not robot_adapter.connected:
			raise HTTPException(status_code=400, detail="Robot not connected")
		state = robot_adapter.get_state()
		current = state.get("joint_positions", [0.0] * 6)
		if req.joint_index < 0 or req.joint_index >= len(current):
			raise HTTPException(status_code=400, detail="Invalid joint index")
		delta = req.target_deg - current[req.joint_index]
		ok = robot_adapter.move_joint_delta(req.joint_index, delta)
		if not ok:
			raise HTTPException(status_code=400, detail="Set rejected (limits or connection)")
		return {"ok": True}
	except HTTPException:
		raise
	except Exception as e:
		raise HTTPException(status_code=500, detail=str(e))


@api_router.post("/control/start")
async def control_start(request: Request):
	"""키보드 제어 시작"""
	try:
		keyboard_controller = request.app.state.keyboard_controller
		result = keyboard_controller.start()
		if result.get("action") == "error":
			raise HTTPException(status_code=400, detail=result.get("message", "Failed to start control"))
		return {"ok": True, **result}
	except HTTPException:
		raise
	except Exception as e:
		raise HTTPException(status_code=500, detail=str(e))


@api_router.post("/control/stop")
async def control_stop(request: Request):
	"""키보드 제어 중지"""
	try:
		keyboard_controller = request.app.state.keyboard_controller
		result = keyboard_controller.stop()
		return {"ok": True, **result}
	except Exception as e:
		raise HTTPException(status_code=500, detail=str(e))


@api_router.get("/control/status")
async def control_status(request: Request):
	"""키보드 제어 상태 조회"""
	try:
		keyboard_controller = request.app.state.keyboard_controller
		status = keyboard_controller.get_status()
		return {"ok": True, "status": status}
	except Exception as e:
		raise HTTPException(status_code=500, detail=str(e))


# ========== Motor Setup API ==========

class FindPortRequest(BaseModel):
	ports_before: List[str]


class ConfigureMotorRequest(BaseModel):
	port: str
	motor_id: int
	baudrate: Optional[int] = None


class SetupStartRequest(BaseModel):
	robot_type: str  # "follower" or "leader"


class ResetMotorRequest(BaseModel):
	port: str
	target_id: int
	reset_to_id: Optional[int] = 1
	baudrate: Optional[int] = None


class CheckMotorIdRequest(BaseModel):
	port: str
	baudrate: Optional[int] = None


@api_router.post("/setup/find-port")
async def find_port(req: FindPortRequest, request: Request):
	"""포트 찾기 (LeRobot 방식: 연결 전후 비교 또는 PID 기반)"""
	try:
		motor_setup_manager = request.app.state.motor_setup_manager
		
		# 먼저 PID 기반으로 찾기 시도 (USB 케이블 분리 불필요)
		port = motor_setup_manager.find_port_by_pid()
		
		if port:
			# PID 기반으로 찾았으면 바로 사용
			motor_setup_manager.current_port = port
			motor_setup_manager.status = SetupStatus.PORT_FOUND
			return {
				"ok": True,
				"port": port,
				"method": "pid",
				"message": f"Port found by PID: {port} (No need to disconnect USB cable)"
			}
		
		# PID 기반 실패 시 LeRobot 방식 (USB 케이블 분리 필요)
		import asyncio
		loop = asyncio.get_event_loop()
		port = await loop.run_in_executor(
			None,
			motor_setup_manager.find_port_by_disconnect,
			req.ports_before
		)
		
		motor_setup_manager.current_port = port
		motor_setup_manager.status = SetupStatus.PORT_FOUND
		
		return {
			"ok": True,
			"port": port,
			"method": "disconnect",
			"message": f"Port found by disconnect method: {port}"
		}
	except Exception as e:
		import traceback
		traceback.print_exc()
		raise HTTPException(status_code=500, detail=str(e))


@api_router.post("/setup/motor")
async def configure_motor(req: ConfigureMotorRequest, request: Request):
	"""단일 모터 설정"""
	try:
		motor_setup_manager = request.app.state.motor_setup_manager
		baudrate = req.baudrate or motor_setup_manager.BAUDRATE
		
		# 비동기로 실행
		import asyncio
		loop = asyncio.get_event_loop()
		result = await loop.run_in_executor(
			None,
			motor_setup_manager.configure_single_motor,
			req.port,
			req.motor_id,
			baudrate
		)
		
		if result["success"]:
			return {
				"ok": True,
				"motor_id": result["motor_id"],
				"found_index": result.get("found_index"),
				"baudrate": result["baudrate"],
				"message": f"Motor {result['motor_id']} configured successfully"
			}
		else:
			raise HTTPException(
				status_code=500,
				detail=result.get("error", "Motor configuration failed")
			)
	except HTTPException:
		raise
	except Exception as e:
		import traceback
		traceback.print_exc()
		raise HTTPException(status_code=500, detail=str(e))


@api_router.post("/setup/reset-motor")
async def reset_motor(req: ResetMotorRequest, request: Request):
	"""모터 ID 리셋 (기본값으로 초기화)"""
	try:
		motor_setup_manager = request.app.state.motor_setup_manager
		baudrate = req.baudrate or motor_setup_manager.BAUDRATE
		
		# 비동기로 실행
		import asyncio
		loop = asyncio.get_event_loop()
		result = await loop.run_in_executor(
			None,
			motor_setup_manager.reset_motor_id,
			req.port,
			req.target_id,
			req.reset_to_id or 1,
			baudrate
		)
		
		if result["success"]:
			return {
				"ok": True,
				"old_id": result["old_id"],
				"new_id": result["new_id"],
				"message": result["message"]
			}
		else:
			raise HTTPException(
				status_code=500,
				detail=result.get("error", "Motor reset failed")
			)
	except HTTPException:
		raise
	except Exception as e:
		import traceback
		traceback.print_exc()
		raise HTTPException(status_code=500, detail=str(e))


@api_router.post("/setup/check-motor-id")
async def check_motor_id(req: CheckMotorIdRequest, request: Request):
	"""연결된 모터의 ID 확인"""
	try:
		motor_setup_manager = request.app.state.motor_setup_manager
		baudrate = req.baudrate or motor_setup_manager.BAUDRATE
		
		# 비동기로 실행
		import asyncio
		loop = asyncio.get_event_loop()
		result = await loop.run_in_executor(
			None,
			motor_setup_manager.check_motor_id,
			req.port,
			baudrate
		)
		
		if result["success"]:
			return {
				"ok": True,
				"motor_id": result.get("motor_id"),
				"baudrate": result.get("baudrate"),
				"motors": result.get("motors"),
				"warning": result.get("warning")
			}
		else:
			raise HTTPException(
				status_code=500,
				detail=result.get("error", "Failed to check motor ID")
			)
	except HTTPException:
		raise
	except Exception as e:
		import traceback
		traceback.print_exc()
		raise HTTPException(status_code=500, detail=str(e))


@api_router.post("/setup/start")
async def setup_start(req: SetupStartRequest, request: Request):
	"""모터 설정 시작"""
	try:
		# 모터 설정 시작 시 로봇 연결 자동 해제 (포트 충돌 방지)
		robot_adapter = request.app.state.robot_adapter
		if robot_adapter.connected:
			robot_adapter.disconnect()
		
		motor_setup_manager = request.app.state.motor_setup_manager
		motor_setup_manager.reset()
		motor_setup_manager.robot_type = req.robot_type
		motor_setup_manager.status = SetupStatus.IDLE
		
		return {
			"ok": True,
			"robot_type": req.robot_type,
			"motors": motor_setup_manager.get_motor_list(req.robot_type),
			"message": f"Motor setup started for {req.robot_type}. Robot connection has been disconnected to avoid port conflicts."
		}
	except Exception as e:
		raise HTTPException(status_code=500, detail=str(e))


@api_router.get("/setup/status")
async def setup_status(request: Request):
	"""모터 설정 상태 조회"""
	try:
		motor_setup_manager = request.app.state.motor_setup_manager
		status = motor_setup_manager.get_status()
		
		# 모터 설정 완료 여부 확인 (6개 모터 모두 설정되었는지)
		configured_count = len(status.get("configured_motors", []))
		is_configured = configured_count >= 6
		
		return {
			"ok": True,
			"is_configured": is_configured,
			"configured_count": configured_count,
			**status
		}
	except Exception as e:
		raise HTTPException(status_code=500, detail=str(e))


@api_router.get("/calibration/status")
async def calibration_status(request: Request):
	"""캘리브레이션 상태 조회 (로봇 하드웨어에서 직접 확인)"""
	try:
		calibration_manager = request.app.state.calibration_manager
		robot = request.app.state.robot
		from ..config import CALIBRATION_DIR
		import os
		
		calib_file = os.path.join(CALIBRATION_DIR, "calibration.json")
		has_calibration_file = os.path.exists(calib_file)
		
		# 로봇이 연결되어 있는지 확인
		is_connected = robot is not None and robot.connected
		
		is_calibrated = False
		calibration_valid = False
		joint_ranges_valid = False
		
		# 1단계: 캘리브레이션 파일 존재 확인
		if has_calibration_file:
			try:
				calibration_manager.load(calib_file)
				has_joint_ranges = "joint_ranges" in calibration_manager.data
				joint_ranges_valid = has_joint_ranges
				
				# 2단계: 로봇이 연결되어 있으면 실제 하드웨어에서 조인트 위치 읽기 시도
				# (캘리브레이션 유효성 검증용 - 실제로 하드웨어와 통신 가능한지 확인)
				if is_connected and has_joint_ranges:
					try:
						# 현재 조인트 위치 읽기 (하드웨어 통신 가능 여부 확인)
						state = robot.get_state()
						current_positions = state.get("joint_positions", [])
						
						if len(current_positions) == 6:
							# 하드웨어에서 위치를 성공적으로 읽었음
							# 캘리브레이션은 유효 (파일이 있고 joint_ranges가 있으면)
							calibration_valid = True
							is_calibrated = has_joint_ranges
						else:
							# 조인트 위치를 읽을 수 없음 (하드웨어 통신 문제 가능)
							calibration_valid = False
							# 파일은 있지만 하드웨어 검증 실패
							is_calibrated = has_joint_ranges  # 파일 기반으로는 유효
					except Exception as e:
						# 하드웨어 읽기 실패 시 파일 기반으로만 판단
						print(f"[API] Warning: Could not read joint positions from robot hardware: {e}")
						calibration_valid = False
						is_calibrated = has_joint_ranges  # 파일 기반으로는 유효
				else:
					# 로봇이 연결되지 않았으면 파일 기반으로만 판단
					calibration_valid = None  # 검증 불가
					is_calibrated = has_joint_ranges
			except Exception as e:
				print(f"[API] Warning: Could not load calibration file: {e}")
				is_calibrated = False
		
		return {
			"ok": True,
			"is_calibrated": is_calibrated,
			"has_calibration_file": has_calibration_file,
			"joint_ranges_valid": joint_ranges_valid,
			"calibration_valid": calibration_valid if is_connected else None,  # 로봇 연결 시에만 검증
			"robot_connected": is_connected
		}
	except Exception as e:
		raise HTTPException(status_code=500, detail=str(e))


@api_router.post("/setup/reset")
async def setup_reset(request: Request):
	"""모터 설정 초기화"""
	try:
		motor_setup_manager = request.app.state.motor_setup_manager
		motor_setup_manager.reset()
		return {
			"ok": True,
			"message": "Motor setup reset"
		}
	except Exception as e:
		raise HTTPException(status_code=500, detail=str(e))


@api_router.get("/setup/ports-before")
async def get_ports_before():
	"""포트 찾기 전 포트 목록 반환"""
	try:
		ports = [p.device for p in serial.tools.list_ports.comports()]
		return {
			"ok": True,
			"ports": ports
		}
	except Exception as e:
		raise HTTPException(status_code=500, detail=str(e))

