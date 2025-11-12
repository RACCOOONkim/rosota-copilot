"""Keyboard control for robot."""

import time
from typing import Optional

import numpy as np
from loguru import logger
from pynput import keyboard

from ..robot.so100 import SO100Robot


class KeyboardController:
    """Keyboard-based robot controller."""

    def __init__(self, robot: SO100Robot):
        """Initialize keyboard controller."""
        self.robot = robot
        self.running = False
        self.listener: Optional[keyboard.Listener] = None

        # Current joint positions (radians)
        self.joint_positions = np.zeros(6)
        self.step_size = 0.1  # radians per key press

        # Key states
        self.pressed_keys = set()

    def start(self):
        """Start keyboard control."""
        if not self.robot.is_connected:
            logger.error("Robot is not connected!")
            return

        if not self.robot.config:
            logger.error("Robot not calibrated! Run calibration first.")
            return

        # Enable torque
        self.robot.enable_torque()

        # Read current positions
        self.joint_positions = self.robot.read_joints_radians()
        if np.isnan(self.joint_positions).any():
            logger.warning("Could not read current positions. Starting from zero.")
            self.joint_positions = np.zeros(6)

        logger.info("Starting keyboard control...")
        logger.info("Controls:")
        logger.info("  Arrow Up/Down: Joint 1 (shoulder pan)")
        logger.info("  Arrow Left/Right: Joint 2 (shoulder lift)")
        logger.info("  W/S: Joint 3 (elbow)")
        logger.info("  A/D: Joint 4 (wrist flex)")
        logger.info("  Q/E: Joint 5 (wrist roll)")
        logger.info("  Space: Toggle gripper")
        logger.info("  Esc: Exit")

        self.running = True
        self.listener = keyboard.Listener(
            on_press=self._on_press, on_release=self._on_release
        )
        self.listener.start()

        # Control loop
        try:
            while self.running:
                self._update_robot()
                time.sleep(0.05)  # 20 Hz control loop
        except KeyboardInterrupt:
            logger.info("Stopping keyboard control...")
        finally:
            self.stop()

    def stop(self):
        """Stop keyboard control."""
        self.running = False
        if self.listener:
            self.listener.stop()
        logger.info("Keyboard control stopped")

    def _on_press(self, key):
        """Handle key press."""
        try:
            self.pressed_keys.add(key)
        except AttributeError:
            pass

    def _on_release(self, key):
        """Handle key release."""
        try:
            self.pressed_keys.discard(key)

            # Handle single-press actions
            if key == keyboard.Key.space:
                self._toggle_gripper()
            elif key == keyboard.Key.esc:
                self.running = False
        except AttributeError:
            pass

    def _update_robot(self):
        """Update robot based on pressed keys."""
        if not self.running:
            return

        # Update joint positions based on pressed keys
        if keyboard.Key.up in self.pressed_keys:
            self.joint_positions[0] += self.step_size
        if keyboard.Key.down in self.pressed_keys:
            self.joint_positions[0] -= self.step_size
        if keyboard.Key.right in self.pressed_keys:
            self.joint_positions[1] += self.step_size
        if keyboard.Key.left in self.pressed_keys:
            self.joint_positions[1] -= self.step_size

        try:
            if keyboard.KeyCode.from_char("w") in self.pressed_keys:
                self.joint_positions[2] += self.step_size
            if keyboard.KeyCode.from_char("s") in self.pressed_keys:
                self.joint_positions[2] -= self.step_size
            if keyboard.KeyCode.from_char("a") in self.pressed_keys:
                self.joint_positions[3] += self.step_size
            if keyboard.KeyCode.from_char("d") in self.pressed_keys:
                self.joint_positions[3] -= self.step_size
            if keyboard.KeyCode.from_char("q") in self.pressed_keys:
                self.joint_positions[4] += self.step_size
            if keyboard.KeyCode.from_char("e") in self.pressed_keys:
                self.joint_positions[4] -= self.step_size
        except (AttributeError, ValueError):
            pass

        # Clamp joint positions to reasonable limits
        self.joint_positions = np.clip(self.joint_positions, -np.pi, np.pi)

        # Write to robot
        try:
            self.robot.write_joints_radians(self.joint_positions, enable_gripper=True)
        except Exception as e:
            logger.warning(f"Error writing to robot: {e}")

    def _toggle_gripper(self):
        """Toggle gripper open/closed."""
        try:
            current_gripper = self.joint_positions[5]
            # Simple toggle: if close to 0, open; otherwise close
            if abs(current_gripper) < 0.1:
                self.robot.control_gripper(1.0)  # Open
                logger.info("Gripper: OPEN")
            else:
                self.robot.control_gripper(0.0)  # Close
                logger.info("Gripper: CLOSE")
        except Exception as e:
            logger.warning(f"Error controlling gripper: {e}")

