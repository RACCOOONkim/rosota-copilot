import os
import asyncio
import socketio
from socketio.async_server import AsyncServer
from socketio.asgi import ASGIApp
from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from starlette.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
from .api.routes import api_router
from .robot.so_arm_v2 import SOArm100AdapterV2
from .robot.keyboard_control import KeyboardController
from .robot.calibration import CalibrationManager
from .robot.motor_setup import MotorSetupManager
from .config import DEFAULT_CONFIG

load_dotenv()

# Global robot instances
robot_adapter = SOArm100AdapterV2()

# Socket.IO는 나중에 정의되므로, 전역 변수로 접근
sio = None

# 로그 콜백 함수 (Socket.IO로 전송)
async def send_calibration_log(message: str, level: str = "info"):
	"""캘리브레이션 로그를 Socket.IO로 전송"""
	global sio
	if sio:
		await sio.emit("calibration:log", {"message": message, "level": level})

# CalibrationManager 초기화 (로그 콜백 설정)
# 주의: async 함수를 동기 콜백으로 사용할 수 없으므로, 별도 처리 필요
def calibration_log_callback(message: str, level: str = "info"):
	"""캘리브레이션 로그 콜백 (동기 함수)"""
	# 이벤트 루프에서 실행되도록 태스크 생성
	try:
		loop = asyncio.get_event_loop()
		if loop.is_running():
			# 실행 중인 루프에 태스크 추가
			asyncio.create_task(send_calibration_log(message, level))
		else:
			# 루프가 없으면 새로 생성
			loop.run_until_complete(send_calibration_log(message, level))
	except (RuntimeError, AttributeError):
		# 이벤트 루프가 없거나 문제가 있으면 print만
		print(f"[{level.upper()}] {message}")

calibration_manager = CalibrationManager(robot_adapter, log_callback=calibration_log_callback)
keyboard_controller = KeyboardController(robot_adapter)
motor_setup_manager = MotorSetupManager()

# State update task
state_update_task = None


def create_app() -> FastAPI:
	origins = ["*"]
	app = FastAPI(title="Rosota Copilot", version="0.1.0")
	app.add_middleware(
		CORSMiddleware,
		allow_origins=origins,
		allow_credentials=True,
		allow_methods=["*"],
		allow_headers=["*"],
	)

	# REST routes
	app.include_router(api_router, prefix="/api")

	# Static & templates
	# PyInstaller로 패키징된 경우 환경 변수에서 경로 가져오기
	if os.environ.get('ROSOTA_STATIC_DIR'):
		static_dir = os.environ['ROSOTA_STATIC_DIR']
		templates_dir = os.environ.get('ROSOTA_TEMPLATES_DIR', 
		                              os.path.join(os.path.dirname(__file__), "templates"))
	else:
		static_dir = os.path.join(os.path.dirname(__file__), "static")
		templates_dir = os.path.join(os.path.dirname(__file__), "templates")
	app.mount("/static", StaticFiles(directory=static_dir), name="static")

	# Share instances via app.state
	app.state.robot_adapter = robot_adapter
	app.state.keyboard_controller = keyboard_controller
	app.state.calibration_manager = calibration_manager
	app.state.motor_setup_manager = motor_setup_manager

	# Basic index
	@app.get("/", response_class=HTMLResponse)
	async def index():
		index_path = os.path.join(templates_dir, "index.html")
		if not os.path.exists(index_path):
			# PyInstaller로 패키징된 경우 대체 경로 시도
			index_path = os.path.join(os.path.dirname(__file__), "templates", "index.html")
		with open(index_path, "r", encoding="utf-8") as f:
			return HTMLResponse(f.read())

	return app


# Socket.IO (ASGI)
sio = AsyncServer(cors_allowed_origins="*", async_mode="asgi")
socket_app = ASGIApp(sio)


async def state_update_loop():
	"""주기적으로 로봇 상태를 브로드캐스트"""
	update_rate = DEFAULT_CONFIG["robot"]["state_update_rate"]
	interval = 1.0 / update_rate
	
	while True:
		try:
			if robot_adapter.connected:
				state = robot_adapter.get_state()
				# 연결 정보 추가
				state["connection"] = robot_adapter.connection_info
				await sio.emit("state:update", state)
			else:
				# 연결되지 않은 경우에도 상태 전송 (연결 해제 알림)
				await sio.emit("state:update", {
					"status": "Disconnected",
					"connection": None
				})
			await asyncio.sleep(interval)
		except Exception as e:
			print(f"State update error: {e}")
			await asyncio.sleep(interval)


def bind_socketio_events():
	@sio.event
	async def connect(sid, environ):
		"""클라이언트 연결 시 호출"""
		try:
			await sio.emit("server:hello", {"message": "Rosota Copilot connected"}, to=sid)
			print(f"[Server] Client connected: {sid}")
			print(f"[Server] Socket.IO server ready. Client SID: {sid}")
			print(f"[Server] Environment: {environ.get('REMOTE_ADDR', 'unknown')}")
		except Exception as e:
			print(f"[Server] Error in connect handler: {e}")
			import traceback
			traceback.print_exc()

	@sio.event
	async def disconnect(sid):
		"""클라이언트 연결 해제 시 호출"""
		print(f"[Server] Client disconnected: {sid}")

	@sio.on("control:key")
	async def handle_control_key(sid, data):
		"""키보드 입력 처리"""
		try:
			key = data.get("key", "").lower()
			event_type = data.get("event_type", "keydown")
			timestamp = data.get("timestamp", 0)
			
			# 디버깅 로그
			print(f"[Server] Received control:key event - key: '{key}', event_type: '{event_type}', "
			      f"running: {keyboard_controller.running}, connected: {robot_adapter.connected}, "
			      f"timestamp: {timestamp}")
			
			if not robot_adapter.connected:
				print(f"[Server] Robot not connected, ignoring key '{key}'")
				await sio.emit("control:response", {
					"action": "error",
					"message": "Robot not connected"
				}, to=sid)
				return
			
			if not keyboard_controller.running and key not in ["m", " "]:
				# 제어가 시작되지 않았을 때는 로그만 남기고 응답은 보내지 않음 (너무 많은 메시지 방지)
				print(f"[Server] Keyboard controller not running, ignoring key '{key}' (except m/space)")
				return
			
			# 키보드 컨트롤러로 처리
			print(f"[Server] Calling keyboard_controller.handle_key_event('{key}', '{event_type}')")
			print(f"[Server] Controller state: running={keyboard_controller.running}, mode={keyboard_controller.mode.value}, estop={keyboard_controller.estop_active}")
			result = keyboard_controller.handle_key_event(key, event_type)
			
			if result:
				# 디버깅 로그
				print(f"[Server] Key event result: {result}")
				await sio.emit("control:response", result, to=sid)
				
				# 모드 변경 시 모든 클라이언트에 알림
				if result.get("action") == "mode_change":
					await sio.emit("control:response", result)
			else:
				# 결과가 None인 경우 (무시된 키) - 로그만 남기고 응답은 보내지 않음
				if event_type == "keydown":
					print(f"[Server] Key '{key}' was ignored (not in mapping or debounced)")
					# 키가 매핑에 있는지 확인
					if key in keyboard_controller.key_mapping:
						print(f"[Server] Key '{key}' is in mapping but returned None. Check mode/running/estop.")
					else:
						print(f"[Server] Key '{key}' is not in key_mapping")
					# 응답은 보내지 않음 (너무 많은 메시지 방지)
		except Exception as e:
			import traceback
			traceback.print_exc()
			print(f"[Server] Control key error: {e}")
			await sio.emit("robot:error", {"message": str(e)}, to=sid)

	@sio.on("control:slider")
	async def handle_control_slider(sid, data):
		"""슬라이더 제어 처리"""
		try:
			joint_index = data.get("joint_index")
			target_position = data.get("target_position")
			
			if joint_index is None or target_position is None:
				await sio.emit("robot:error", {
					"message": "Missing joint_index or target_position"
				}, to=sid)
				return
			
			if not robot_adapter.connected:
				await sio.emit("robot:error", {
					"message": "Robot not connected"
				}, to=sid)
				return
			
			# 조인트를 절대 위치로 이동
			success = robot_adapter.move_joint_absolute(joint_index, target_position)
			
			if success:
				print(f"[Server] Slider control: Joint {joint_index} moved to {target_position}°")
			else:
				await sio.emit("robot:error", {
					"message": f"Failed to move joint {joint_index} to {target_position}°"
				}, to=sid)
		except Exception as e:
			import traceback
			traceback.print_exc()
			print(f"[Server] Control slider error: {e}")
			await sio.emit("robot:error", {"message": str(e)}, to=sid)


bind_socketio_events()

# Uvicorn entrypoint
app = create_app()


def asgi():
	"""
	ASGI callable that multiplexes FastAPI and Socket.IO under one server.
	Mount Socket.IO at /socket.io (default) and serve FastAPI at root.
	"""
	from starlette.applications import Starlette
	from starlette.routing import Mount, Route
	from starlette.responses import Response
	
	# Socket.IO와 FastAPI를 별도로 마운트
	# Socket.IO는 /socket.io 경로에, FastAPI는 루트에
	star = Starlette(
		on_startup=[startup],
		on_shutdown=[shutdown],
		routes=[
			Mount("/socket.io", app=socket_app),
			Mount("/", app=app),
		],
	)
	return star


async def auto_connect_robot():
	"""USB 포트를 스캔하여 로봇 자동 연결"""
	from .robot.usb_scanner import detect_robot_port
	
	if robot_adapter.connected:
		return
	
	# USB 포트 스캔 및 자동 연결 시도
	port = detect_robot_port()
	if port:
		print(f"Auto-detected robot port: {port}")
		try:
			success = robot_adapter.connect(port=port)
			if success:
				print(f"Auto-connected to robot on {port}")
				# 캘리브레이션 매니저에 로봇 어댑터 연결
				calibration_manager.robot = robot_adapter
				
				# 캘리브레이션 데이터 자동 로드 (조인트 제한값 업데이트)
				try:
					from .config import CALIBRATION_DIR
					import os
					calib_file = os.path.join(CALIBRATION_DIR, "calibration.json")
					if os.path.exists(calib_file):
						calibration_manager.load(calib_file)
						print(f"[Server] Calibration data loaded from {calib_file}")
				except Exception as e:
					# 캘리브레이션 파일이 없거나 로드 실패해도 연결은 성공
					print(f"[Server] Warning: Could not load calibration data: {e}")
					import traceback
					traceback.print_exc()
				
				# 모든 클라이언트에 연결 상태 알림
				try:
					await sio.emit("robot:auto_connected", {
						"port": port,
						"status": "Connected"
					})
				except Exception as e:
					print(f"[Server] Warning: Could not emit auto_connected event: {e}")
			else:
				print(f"Failed to auto-connect to {port}")
		except Exception as e:
			print(f"Auto-connect error: {e}")
			import traceback
			traceback.print_exc()
	else:
		print("No robot port detected")


async def startup():
	"""서버 시작 시 실행"""
	global state_update_task
	# 상태 업데이트 태스크 시작
	state_update_task = asyncio.create_task(state_update_loop())
	print("State update loop started")
	
	# USB 자동 연결 시도
	await auto_connect_robot()
	
	# 주기적으로 USB 포트 스캔 (5초마다)
	async def periodic_scan():
		while True:
			await asyncio.sleep(5)  # 5초마다 스캔
			if not robot_adapter.connected:
				await auto_connect_robot()
	
	asyncio.create_task(periodic_scan())


async def shutdown():
	"""서버 종료 시 실행"""
	global state_update_task
	if state_update_task:
		state_update_task.cancel()
		try:
			await state_update_task
		except asyncio.CancelledError:
			pass
	if robot_adapter.connected:
		robot_adapter.disconnect()
	print("Server shutdown complete")


if __name__ == "__main__":
	import uvicorn

	host = os.environ.get("HOST", "0.0.0.0")
	port = int(os.environ.get("PORT", "8000"))  # 80는 권한 이슈 있을 수 있어 기본 8000
	# reload를 사용하려면 import 문자열을 전달해야 함
	# asgi()는 팩토리이므로 --factory/factory=True 필요
	uvicorn.run("rosota_copilot.server:asgi", host=host, port=port, reload=True, factory=True)
