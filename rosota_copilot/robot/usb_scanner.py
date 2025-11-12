"""
USB 포트 스캔 및 로봇 자동 감지
"""
import platform
from typing import List, Optional, Dict
import subprocess


def scan_serial_ports() -> List[Dict[str, str]]:
	"""
	시스템의 시리얼 포트를 스캔하여 반환
	"""
	ports = []
	
	system = platform.system()
	
	if system == "Darwin":  # macOS
		import os
		# 일반적인 USB 시리얼 포트 패턴 (macOS)
		common_patterns = [
			"/dev/cu.usbserial*",
			"/dev/cu.usbmodem*",
			"/dev/tty.usbserial*",
			"/dev/tty.usbmodem*",
			"/dev/cu.SLAB_USBtoUART",
			"/dev/tty.SLAB_USBtoUART",
		]
		
		# /dev 디렉토리에서 USB 시리얼 포트 찾기
		dev_dir = "/dev"
		if os.path.exists(dev_dir):
			try:
				for name in os.listdir(dev_dir):
					# USB 시리얼 관련 포트 필터링
					if any(pattern.replace("/dev/", "").replace("*", "") in name for pattern in common_patterns):
						port_path = os.path.join(dev_dir, name)
						if os.path.exists(port_path):
							ports.append({
								"port": port_path,
								"description": "USB Serial Device"
							})
			except Exception:
				pass
		
		# 일반적인 USB 시리얼 포트 직접 확인
		common_ports = [
			"/dev/cu.usbserial",
			"/dev/cu.usbmodem",
			"/dev/tty.usbserial",
			"/dev/tty.usbmodem",
		]
		for port in common_ports:
			if os.path.exists(port):
				ports.append({
					"port": port,
					"description": "USB Serial Port"
				})
	
	elif system == "Linux":
		# Linux: /dev/ttyUSB*, /dev/ttyACM* 등
		import os
		dev_dir = "/dev"
		if os.path.exists(dev_dir):
			for name in os.listdir(dev_dir):
				if name.startswith(("ttyUSB", "ttyACM", "ttyS")):
					port_path = os.path.join(dev_dir, name)
					if os.path.exists(port_path):
						ports.append({
							"port": port_path,
							"description": "USB Serial Port"
						})
	
	elif system == "Windows":
		# Windows: COM 포트
		try:
			import serial.tools.list_ports
			available_ports = serial.tools.list_ports.comports()
			for port in available_ports:
				ports.append({
					"port": port.device,
					"description": port.description
				})
		except (ImportError, ModuleNotFoundError):
			# pyserial이 없으면 기본 COM 포트 시도
			import os
			for i in range(1, 21):  # COM1 ~ COM20
				port_name = f"COM{i}"
				# 실제로 존재하는 포트만 추가 (Windows에서는 확인 어려우므로 모두 추가)
				ports.append({
					"port": port_name,
					"description": "Serial Port"
				})
	
	return ports


def detect_robot_port() -> Optional[str]:
	"""
	SO-100 로봇 포트 자동 감지
	PID 기반 감지: CH340 칩셋 (PID 21971 또는 29987)
	phosphobot의 SO100Hardware.from_port 방식 참고
	"""
	try:
		import serial.tools.list_ports
	except ImportError:
		# pyserial이 없으면 기본 방식 사용
		ports = scan_serial_ports()
		if ports:
			return ports[0]["port"]
		return None
	
	# SO-100은 CH340 칩셋을 사용하며 PID가 21971 또는 29987
	SO100_PIDS = [21971, 29987]
	
	# PID 기반 감지
	for port_info in serial.tools.list_ports.comports():
		if hasattr(port_info, 'pid') and port_info.pid in SO100_PIDS:
			print(f"SO-100 detected on {port_info.device} (PID: {port_info.pid})")
			return port_info.device
	
	# PID 기반 감지 실패 시, 포트 이름으로 감지 시도
	ports = scan_serial_ports()
	for port_info in ports:
		port_name = port_info.get("port", "").lower()
		description = port_info.get("description", "").lower()
		# USB Serial, CH340, cu.usbmodem 등의 키워드로 감지
		if any(keyword in port_name or keyword in description 
		       for keyword in ["usb", "ch340", "cu.usbmodem", "tty.usbserial"]):
			print(f"Possible SO-100 detected on {port_info['port']} (name-based detection)")
			return port_info["port"]
	
	# 모든 감지 실패 시 첫 번째 포트 반환 (기존 동작)
	if ports:
		print(f"No SO-100 detected, using first available port: {ports[0]['port']}")
		return ports[0]["port"]
	return None

