from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel
from typing import Optional
import numpy as np
from ..config import CALIBRATION_DIR
from ..robot.usb_scanner import detect_robot_port, scan_serial_ports

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

		success = robot_adapter.connect(port=port, host=host, baudrate=baud)
		if success:
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
		return {"ok": True, "message": "Calibration wizard reset"}
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

