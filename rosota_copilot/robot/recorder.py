"""
로봇 동작 기록 및 재생 관리자
"""
import os
import json
import time
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Optional, Any
from enum import Enum

from ..config import RECORD_DIR


class RecordMode(Enum):
	"""기록 모드"""
	MANUAL = "manual"  # 사용자가 직접 로봇을 움직임
	KEYBOARD = "keyboard"  # 키보드로 제어한 것을 기록


class Recorder:
	"""로봇 동작 기록 및 재생 관리자"""
	
	def __init__(self, robot_adapter):
		"""
		Args:
			robot_adapter: 로봇 어댑터 인스턴스
		"""
		self.robot_adapter = robot_adapter
		self.is_recording = False
		self.is_replaying = False
		self.record_mode: Optional[RecordMode] = None
		self.record_data: List[Dict[str, Any]] = []
		self.start_time: Optional[float] = None
		self.current_record_path: Optional[Path] = None
		
	def start_record(self, mode: RecordMode) -> bool:
		"""
		기록 시작
		
		Args:
			mode: 기록 모드 (MANUAL 또는 KEYBOARD)
		
		Returns:
			성공 여부
		"""
		if self.is_recording:
			return False
		
		if not self.robot_adapter.connected:
			return False
		
		self.is_recording = True
		self.record_mode = mode
		self.record_data = []
		self.start_time = time.time()
		
		# 초기 상태 기록
		initial_state = self.robot_adapter.get_state()
		self.record_data.append({
			"timestamp": 0.0,
			"joint_positions": initial_state.get("joint_positions", [0.0] * 6),
			"action": None,  # Manual 모드에서는 action이 없음
		})
		
		return True
	
	def record_step(self, joint_positions: List[float], action: Optional[Dict[str, Any]] = None):
		"""
		한 스텝 기록
		
		Args:
			joint_positions: 현재 조인트 위치
			action: 키보드 제어 액션 (KEYBOARD 모드일 때만)
		"""
		if not self.is_recording:
			return
		
		timestamp = time.time() - self.start_time
		
		record_entry = {
			"timestamp": timestamp,
			"joint_positions": joint_positions.copy() if isinstance(joint_positions, list) else list(joint_positions),
		}
		
		# KEYBOARD 모드일 때만 action 기록
		if self.record_mode == RecordMode.KEYBOARD and action:
			record_entry["action"] = action
		
		self.record_data.append(record_entry)
	
	def stop_record(self) -> Optional[Path]:
		"""
		기록 중지 및 저장
		
		Returns:
			저장된 파일 경로 (실패 시 None)
		"""
		if not self.is_recording:
			return None
		
		self.is_recording = False
		
		if len(self.record_data) < 2:  # 최소 2개 이상의 데이터 필요
			self.record_data = []
			return None
		
		# 파일명 생성 (타임스탬프 기반)
		timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
		mode_str = self.record_mode.value
		filename = f"record_{mode_str}_{timestamp}.json"
		filepath = RECORD_DIR / filename
		
		# 메타데이터와 함께 저장
		record_file = {
			"metadata": {
				"mode": self.record_mode.value,
				"created_at": datetime.now().isoformat(),
				"duration": self.record_data[-1]["timestamp"],
				"num_steps": len(self.record_data),
				"robot_type": "SO Arm 100",
			},
			"data": self.record_data
		}
		
		try:
			with open(filepath, "w", encoding="utf-8") as f:
				json.dump(record_file, f, indent=2)
			
			self.current_record_path = filepath
			self.record_data = []
			return filepath
		except Exception as e:
			print(f"[Recorder] Failed to save record: {e}")
			return None
	
	def discard_record(self):
		"""현재 기록 버리기"""
		if self.is_recording:
			self.is_recording = False
			self.record_data = []
			self.current_record_path = None
	
	def load_record(self, filepath: Path) -> Optional[Dict[str, Any]]:
		"""
		기록 파일 로드
		
		Args:
			filepath: 기록 파일 경로
		
		Returns:
			로드된 데이터 (실패 시 None)
		"""
		try:
			with open(filepath, "r", encoding="utf-8") as f:
				return json.load(f)
		except Exception as e:
			print(f"[Recorder] Failed to load record: {e}")
			return None
	
	def replay(self, filepath: Path, speed: float = 1.0) -> bool:
		"""
		기록 재생
		
		Args:
			filepath: 기록 파일 경로
			speed: 재생 속도 배율 (1.0 = 정상 속도)
		
		Returns:
			성공 여부
		"""
		if self.is_replaying:
			return False
		
		if not self.robot_adapter.connected:
			return False
		
		record_data = self.load_record(filepath)
		if not record_data:
			return False
		
		# 비동기로 재생 (별도 태스크에서 실행)
		import asyncio
		asyncio.create_task(self._replay_async(record_data, speed))
		
		return True
	
	async def _replay_async(self, record_data: Dict[str, Any], speed: float):
		"""비동기 재생 루프"""
		self.is_replaying = True
		
		try:
			data = record_data.get("data", [])
			if len(data) < 2:
				self.is_replaying = False
				return
			
			# 첫 번째 위치로 이동
			initial_positions = data[0]["joint_positions"]
			for i, pos in enumerate(initial_positions):
				if i < 6:
					self.robot_adapter.move_joint_absolute(i, pos)
			
			await asyncio.sleep(1.0)  # 초기 이동 대기
			
			# 재생 루프
			for i in range(1, len(data)):
				if not self.is_replaying:
					break
				
				current = data[i]
				prev = data[i - 1]
				
				# 시간 간격 계산
				time_delta = (current["timestamp"] - prev["timestamp"]) / speed
				
				# 조인트 위치로 이동
				positions = current["joint_positions"]
				for joint_idx, target_pos in enumerate(positions):
					if joint_idx < 6:
						self.robot_adapter.move_joint_absolute(joint_idx, target_pos)
				
				# 다음 스텝까지 대기
				await asyncio.sleep(max(0.01, time_delta))
		
		except Exception as e:
			print(f"[Recorder] Replay error: {e}")
		finally:
			self.is_replaying = False
	
	def stop_replay(self):
		"""재생 중지"""
		self.is_replaying = False
	
	def list_records(self) -> List[Dict[str, Any]]:
		"""
		저장된 기록 파일 목록 반환
		
		Returns:
			기록 파일 정보 리스트
		"""
		records = []
		
		if not RECORD_DIR.exists():
			return records
		
		for filepath in sorted(RECORD_DIR.glob("record_*.json"), reverse=True):
			try:
				# 파일 메타데이터만 읽기 (전체 파일 로드하지 않음)
				with open(filepath, "r", encoding="utf-8") as f:
					data = json.load(f)
					metadata = data.get("metadata", {})
					
					records.append({
						"filename": filepath.name,
						"filepath": str(filepath),
						"mode": metadata.get("mode", "unknown"),
						"created_at": metadata.get("created_at", ""),
						"duration": metadata.get("duration", 0.0),
						"num_steps": metadata.get("num_steps", 0),
						"size": filepath.stat().st_size,
					})
			except Exception as e:
				print(f"[Recorder] Failed to read record metadata: {e}")
		
		return records
	
	def delete_record(self, filepath: Path) -> bool:
		"""
		기록 파일 삭제
		
		Args:
			filepath: 기록 파일 경로
		
		Returns:
			성공 여부
		"""
		try:
			if filepath.exists() and filepath.is_file():
				filepath.unlink()
				return True
			return False
		except Exception as e:
			print(f"[Recorder] Failed to delete record: {e}")
			return False

