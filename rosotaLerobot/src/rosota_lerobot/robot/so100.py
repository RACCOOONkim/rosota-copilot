"""SO-100/SO-101 robot hardware interface."""

import time
from typing import Dict, List, Literal, Optional, Tuple

import numpy as np
import serial
from loguru import logger

# Import FeetechMotorsBus from local motors module
# We've copied the feetech implementation from phosphobot for independence
from .motors.feetech import FeetechMotorsBus

from ..utils.config import RobotConfig


class SO100Robot:
    """SO-100/SO-101 robot controller."""

    name = "so-100"
    SERVO_IDS = [1, 2, 3, 4, 5, 6]
    RESOLUTION = 4096  # 12-bit resolution
    BAUDRATE = 1000000

    # Motor configuration
    motors: Dict[str, List] = {
        "shoulder_pan": [1, "sts3215"],
        "shoulder_lift": [2, "sts3215"],
        "elbow_flex": [3, "sts3215"],
        "wrist_flex": [4, "sts3215"],
        "wrist_roll": [5, "sts3215"],
        "gripper": [6, "sts3215"],
    }

    # Calibration position (in radians)
    CALIBRATION_POSITION = [
        np.pi / 2,
        np.pi / 2,
        -np.pi / 2,
        -np.pi / 2,
        np.pi / 2,
        np.pi / 2,
    ]

    def __init__(self, device_name: str, serial_id: str = "unknown"):
        """Initialize SO-100 robot."""
        self.device_name = device_name
        self.SERIAL_ID = serial_id
        self.motors_bus: Optional[FeetechMotorsBus] = None
        self.is_connected = False
        self.config: Optional[RobotConfig] = None
        self.calibration_current_step = 0
        self.calibration_max_steps = 3
        self.motor_communication_errors = 0

    @property
    def servo_id_to_motor_name(self) -> Dict[int, str]:
        """Map servo ID to motor name."""
        return {v[0]: k for k, v in self.motors.items()}

    def connect(self) -> bool:
        """Connect to the robot."""
        try:
            self.motors_bus = FeetechMotorsBus(
                port=self.device_name, motors=self.motors
            )
            self.motors_bus.connect()
            self.is_connected = True
            self.load_config()
            logger.success(f"Connected to {self.name} on {self.device_name}")
            return True
        except serial.SerialException as e:
            logger.error(f"Failed to connect: {e}")
            self.is_connected = False
            return False
        except Exception as e:
            logger.error(f"Unexpected error during connection: {e}")
            self.is_connected = False
            return False

    def disconnect(self):
        """Disconnect from the robot."""
        if self.motors_bus and self.is_connected:
            try:
                self.disable_torque()
                self.motors_bus.disconnect()
            except Exception as e:
                logger.warning(f"Error disconnecting: {e}")
        self.is_connected = False

    def load_config(self):
        """Load robot configuration."""
        # Try user config first
        user_config_path = RobotConfig.get_user_config_path(self.name, self.SERIAL_ID)
        if user_config_path.exists():
            self.config = RobotConfig.from_json(str(user_config_path))
            if self.config:
                logger.info(f"Loaded user config from {user_config_path}")
                return

        # Try default config based on voltage
        voltage = self.detect_voltage()
        default_path = RobotConfig.get_default_path(self.name, voltage)
        if default_path.exists():
            self.config = RobotConfig.from_json(str(default_path))
            if self.config:
                logger.info(f"Loaded default config for {voltage}")
                return

        logger.warning("No configuration found. Calibration required.")

    def detect_voltage(self) -> str:
        """Detect robot voltage (6V or 12V)."""
        if not self.is_connected:
            return "6V"

        try:
            voltages = []
            for servo_id in self.SERVO_IDS:
                voltage = self.read_motor_voltage(servo_id)
                if voltage:
                    voltages.append(voltage)

            if voltages:
                avg_voltage = np.mean(voltages)
                return "12V" if avg_voltage >= 9.0 else "6V"
        except Exception:
            pass

        return "6V"

    def read_motor_voltage(self, servo_id: int) -> Optional[float]:
        """Read motor voltage."""
        if not self.is_connected or not self.motors_bus:
            return None
        try:
            voltage = self.motors_bus.read(
                "Present_Voltage",
                motor_names=self.servo_id_to_motor_name[servo_id],
            )
            return float(voltage) / 10.0  # Convert from 0.1V units
        except Exception as e:
            logger.warning(f"Error reading voltage: {e}")
            return None

    def enable_torque(self):
        """Enable all motor torque."""
        if not self.is_connected or not self.motors_bus:
            return

        if not self.config:
            logger.warning("No config loaded. Cannot enable torque.")
            return

        try:
            self.motors_bus.write("Torque_Enable", 1)
            # Set PID gains
            for servo_id, pid in enumerate(self.config.pid_gains):
                self._set_pid_gains(servo_id + 1, int(pid.p_gain), int(pid.i_gain), int(pid.d_gain))
            self.motor_communication_errors = 0
            logger.info("Torque enabled")
        except Exception as e:
            logger.error(f"Error enabling torque: {e}")

    def disable_torque(self):
        """Disable all motor torque."""
        if not self.is_connected or not self.motors_bus:
            return
        try:
            self.motors_bus.write("Torque_Enable", 0)
            self.motor_communication_errors = 0
            logger.info("Torque disabled")
        except Exception as e:
            logger.error(f"Error disabling torque: {e}")

    def _set_pid_gains(self, servo_id: int, p_gain: int, i_gain: int, d_gain: int):
        """Set PID gains for a servo."""
        if not self.motors_bus:
            return
        try:
            motor_name = self.servo_id_to_motor_name[servo_id]
            self.motors_bus.write("P_Coefficient", p_gain, motor_names=motor_name)
            self.motors_bus.write("I_Coefficient", i_gain, motor_names=motor_name)
            self.motors_bus.write("D_Coefficient", d_gain, motor_names=motor_name)
        except Exception as e:
            logger.warning(f"Error setting PID gains: {e}")

    def read_motor_position(self, servo_id: int) -> Optional[int]:
        """Read motor position in motor units."""
        if not self.is_connected or not self.motors_bus:
            return None
        try:
            position = self.motors_bus.read(
                "Present_Position",
                motor_names=self.servo_id_to_motor_name[servo_id],
            )
            self.motor_communication_errors = 0
            return int(position) if position is not None else None
        except Exception as e:
            logger.warning(f"Error reading position: {e}")
            self.motor_communication_errors += 1
            return None

    def write_motor_position(self, servo_id: int, units: int):
        """Write motor position in motor units."""
        if not self.is_connected or not self.motors_bus:
            return
        try:
            self.motors_bus.write(
                "Goal_Position",
                values=[units],
                motor_names=self.servo_id_to_motor_name[servo_id],
            )
            self.motor_communication_errors = 0
        except Exception as e:
            logger.warning(f"Error writing position: {e}")
            self.motor_communication_errors += 1

    def read_group_motor_position(self) -> np.ndarray:
        """Read all motor positions."""
        if not self.is_connected or not self.motors_bus:
            return np.ones(6) * np.nan

        motor_names = list(self.motors.keys())
        try:
            positions = self.motors_bus.read("Present_Position", motor_names=motor_names)
            self.motor_communication_errors = 0
            return np.array(positions) if positions is not None else np.ones(6) * np.nan
        except Exception as e:
            logger.warning(f"Error reading group position: {e}")
            self.motor_communication_errors += 1
            return np.ones(6) * np.nan

    def write_group_motor_position(self, positions: np.ndarray, enable_gripper: bool = True):
        """Write positions to all motors."""
        if not self.is_connected or not self.motors_bus:
            return

        values = positions.tolist()
        motor_names = list(self.motors.keys())

        if not enable_gripper:
            values = values[:-1]
            motor_names = motor_names[:-1]

        try:
            self.motors_bus.write("Goal_Position", values=values, motor_names=motor_names)
            self.motor_communication_errors = 0
        except Exception as e:
            logger.warning(f"Error writing group position: {e}")
            self.motor_communication_errors += 1

    def motor_units_to_radians(self, units: np.ndarray) -> np.ndarray:
        """Convert motor units to radians."""
        if not self.config:
            raise ValueError("Configuration not loaded. Run calibration first.")

        offsets = np.array(self.config.servos_offsets[: len(units)])
        signs = np.array(self.config.servos_offsets_signs[: len(units)])
        return (units - offsets) * signs * (2 * np.pi / (self.RESOLUTION - 1))

    def radians_to_motor_units(self, radians: np.ndarray) -> np.ndarray:
        """Convert radians to motor units."""
        if not self.config:
            raise ValueError("Configuration not loaded. Run calibration first.")

        signs = np.array(self.config.servos_offsets_signs[: len(radians)])
        offsets = np.array(self.config.servos_offsets[: len(radians)])
        units = radians * signs * ((self.RESOLUTION - 1) / (2 * np.pi)) + offsets
        return units.astype(int)

    def read_joints_radians(self) -> np.ndarray:
        """Read joint positions in radians."""
        units = self.read_group_motor_position()
        if np.isnan(units).any():
            return np.ones(6) * np.nan
        return self.motor_units_to_radians(units)

    def write_joints_radians(self, radians: np.ndarray, enable_gripper: bool = True):
        """Write joint positions in radians."""
        units = self.radians_to_motor_units(radians)
        self.write_group_motor_position(units, enable_gripper=enable_gripper)

    def control_gripper(self, open_command: float):
        """Control gripper (0=closed, 1=open)."""
        if not self.config:
            raise ValueError("Configuration not loaded. Run calibration first.")

        open_position = self.config.servos_calibration_position[-1]
        close_position = self.config.servos_offsets[-1]
        target_position = int(close_position + (open_position - close_position) * open_command)
        target_position = np.clip(target_position, 0, self.RESOLUTION - 1)
        self.write_motor_position(self.SERVO_IDS[-1], target_position)

    def calibrate_motors(self):
        """Set motor offset to middle position (RESOLUTION/2) for calibration."""
        if not self.is_connected or not self.motors_bus:
            logger.warning("Robot is not connected.")
            return

        try:
            # Set torque enable to 128 (calibration mode)
            self.motors_bus.write("Torque_Enable", 128)
            time.sleep(1)
            logger.info("Motors set to calibration mode")
        except Exception as e:
            logger.error(f"Error setting calibration mode: {e}")

