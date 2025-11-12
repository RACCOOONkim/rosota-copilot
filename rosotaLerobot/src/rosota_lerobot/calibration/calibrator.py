"""Robot calibration logic."""

from typing import Literal, Tuple

import numpy as np
from loguru import logger

from ..robot.so100 import SO100Robot
from ..utils.config import RobotConfig


class Calibrator:
    """Handles robot calibration process."""

    def __init__(self, robot: SO100Robot):
        """Initialize calibrator."""
        self.robot = robot

    def calibrate(self) -> Tuple[Literal["success", "in_progress", "error"], str]:
        """Run calibration step."""
        if not self.robot.is_connected:
            self.robot.calibration_current_step = 0
            return "error", "Robot is not connected."

        # Step 0: Initialize
        if self.robot.calibration_current_step == 0:
            voltage = self.robot.detect_voltage()
            default_path = RobotConfig.get_default_path(self.robot.name, voltage)
            default_config = RobotConfig.from_json(str(default_path))

            if not default_config:
                return "error", f"Default config not found for {voltage}"

            self.robot.config = default_config
            self.robot.disable_torque()
            self.robot.calibration_current_step = 1

            return (
                "in_progress",
                f"Step 1/{self.robot.calibration_max_steps}: "
                "Place robot in POSITION 1 (initial position). "
                "All joints should be at zero position. Press Enter to continue.",
            )

        # Step 1: Read initial position
        if self.robot.calibration_current_step == 1:
            self.robot.calibrate_motors()  # Set offset to middle
            positions = self.robot.read_group_motor_position()

            if np.isnan(positions).any():
                self.robot.calibration_current_step = 0
                return "error", "Failed to read joint positions. Check connections."

            if not self.robot.config:
                return "error", "Config not initialized"

            self.robot.config.servos_offsets = positions.tolist()
            logger.info(f"Initial positions: {self.robot.config.servos_offsets}")

            self.robot.calibration_current_step = 2
            return (
                "in_progress",
                f"Step 2/{self.robot.calibration_max_steps}: "
                "Place robot in POSITION 2 (calibration position). "
                "Follow the calibration position angles. Press Enter to continue.",
            )

        # Step 2: Read calibration position and compute signs
        if self.robot.calibration_current_step == 2:
            positions = self.robot.read_group_motor_position()

            if np.isnan(positions).any():
                self.robot.calibration_current_step = 0
                return "error", "Failed to read joint positions. Check connections."

            if not self.robot.config:
                return "error", "Config not initialized"

            self.robot.config.servos_calibration_position = positions.tolist()
            logger.info(f"Calibration positions: {self.robot.config.servos_calibration_position}")

            # Check if positions changed
            offsets = np.array(self.robot.config.servos_offsets)
            calib_pos = np.array(self.robot.config.servos_calibration_position)
            if np.allclose(offsets, calib_pos):
                self.robot.calibration_current_step = 0
                return "error", "Positions did not change. Move robot to calibration position."

            # Compute signs
            calib_rad = np.array(self.robot.CALIBRATION_POSITION)
            diff = calib_pos - offsets
            self.robot.config.servos_offsets_signs = np.sign(diff / calib_rad).tolist()
            logger.info(f"Computed signs: {self.robot.config.servos_offsets_signs}")

            # Save config
            config_path = RobotConfig.get_user_config_path(
                self.robot.name, self.robot.SERIAL_ID
            )
            self.robot.config.save_json(str(config_path))
            logger.success(f"Calibration saved to {config_path}")

            self.robot.calibration_current_step = 0
            return (
                "success",
                f"Step {self.robot.calibration_max_steps}/{self.robot.calibration_max_steps}: "
                "Calibration completed successfully!",
            )

        return "error", f"Invalid calibration step: {self.robot.calibration_current_step}"

