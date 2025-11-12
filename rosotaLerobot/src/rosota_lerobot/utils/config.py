"""Configuration management for robot settings."""

import json
import os
from pathlib import Path
from typing import List, Optional

from pydantic import BaseModel


class PIDGain(BaseModel):
    """PID gain configuration for a servo."""

    p_gain: float
    i_gain: float
    d_gain: float


class RobotConfig(BaseModel):
    """Robot configuration model."""

    name: str
    servos_voltage: float
    servos_offsets: List[float]
    servos_calibration_position: List[float]
    servos_offsets_signs: List[float]
    pid_gains: List[PIDGain]
    gripping_threshold: int
    non_gripping_threshold: int

    @classmethod
    def from_json(cls, filepath: str) -> Optional["RobotConfig"]:
        """Load configuration from JSON file."""
        if not os.path.exists(filepath):
            return None
        with open(filepath, "r") as f:
            data = json.load(f)
        return cls(**data)

    def save_json(self, filepath: str) -> None:
        """Save configuration to JSON file."""
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        with open(filepath, "w") as f:
            json.dump(self.model_dump(), f, indent=2)

    @classmethod
    def get_default_path(cls, robot_name: str, voltage: str) -> Path:
        """Get path to default configuration file."""
        # Get the package directory
        current_dir = Path(__file__).parent
        # Go up: utils -> rosota_lerobot -> src -> rosotaLerobot
        package_dir = current_dir.parent.parent.parent
        resources_dir = package_dir / "resources" / "default"
        return resources_dir / f"{robot_name}-{voltage}.json"

    @classmethod
    def get_user_config_path(cls, robot_name: str, serial_id: str) -> Path:
        """Get path to user-specific configuration file."""
        home_dir = Path.home()
        config_dir = home_dir / ".rosota_lerobot" / "calibration"
        return config_dir / f"{robot_name}_{serial_id}_config.json"

