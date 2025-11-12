"""Robot connection management."""

import time
from typing import List, Optional

from loguru import logger
from serial.tools import list_ports
from serial.tools.list_ports_common import ListPortInfo

from .so100 import SO100Robot


class RobotConnectionManager:
    """Manages robot connections and discovery."""

    def __init__(self):
        self.robots: List[SO100Robot] = []
        self.last_scan_time: float = 0

    def scan_ports(self) -> List[ListPortInfo]:
        """Scan for available serial ports."""
        ports = list_ports.comports()
        self.last_scan_time = time.time()
        return ports

    def find_robots(self) -> List[SO100Robot]:
        """Find and connect to SO-100/SO-101 robots."""
        ports = self.scan_ports()
        robots = []

        for port in ports:
            # SO-100 uses PID 21971 or 29987
            if port.pid in [21971, 29987]:
                serial_number = port.serial_number or "unknown"
                logger.info(f"Found SO-100/SO-101 on {port.device} (Serial: {serial_number})")

                robot = SO100Robot(device_name=port.device, serial_id=serial_number)
                if robot.connect():
                    robots.append(robot)
                    logger.success(f"Connected to robot on {port.device}")
                else:
                    logger.warning(f"Failed to connect to robot on {port.device}")

        self.robots = robots
        return robots

    def get_robot(self, index: int = 0) -> Optional[SO100Robot]:
        """Get robot by index."""
        if 0 <= index < len(self.robots):
            return self.robots[index]
        return None

    def disconnect_all(self):
        """Disconnect all robots."""
        for robot in self.robots:
            robot.disconnect()
        self.robots = []

