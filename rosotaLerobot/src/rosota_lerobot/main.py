"""Main CLI entry point."""

import sys
from typing import Optional

import typer
from loguru import logger
from rich import print as rprint

from .calibration import Calibrator
from .control import KeyboardController
from .robot import RobotConnectionManager

app = typer.Typer(help="Rosota LeRobot - SO-100/SO-101 Control System")


@app.command()
def connect(
    device: Optional[str] = typer.Option(None, "--device", "-d", help="Device path (e.g., /dev/ttyUSB0)"),
):
    """Connect to SO-100/SO-101 robot."""
    rprint("[bold green]Rosota LeRobot[/bold green]")
    rprint("Connecting to robot...\n")

    manager = RobotConnectionManager()
    robots = manager.find_robots()

    if not robots:
        rprint("[red]No robots found![/red]")
        rprint("Please check:")
        rprint("  1. Robot is powered on")
        rprint("  2. USB cable is connected")
        rprint("  3. Correct permissions (may need sudo on Linux)")
        sys.exit(1)

    rprint(f"[green]Found {len(robots)} robot(s):[/green]")
    for i, robot in enumerate(robots):
        rprint(f"  [{i}] {robot.name} on {robot.device_name} (Serial: {robot.SERIAL_ID})")

    rprint("\n[green]Connection successful![/green]")


@app.command()
def calibrate(
    robot_id: int = typer.Option(0, "--robot-id", "-r", help="Robot ID to calibrate"),
):
    """Calibrate the robot."""
    rprint("[bold green]Robot Calibration[/bold green]\n")

    manager = RobotConnectionManager()
    robots = manager.find_robots()

    if not robots:
        rprint("[red]No robots found![/red]")
        sys.exit(1)

    if robot_id >= len(robots):
        rprint(f"[red]Invalid robot ID: {robot_id}[/red]")
        sys.exit(1)

    robot = robots[robot_id]
    calibrator = Calibrator(robot)

    rprint("[yellow]Starting calibration process...[/yellow]\n")
    rprint("This will guide you through 3 steps:\n")

    while True:
        status, message = calibrator.calibrate()

        if status == "error":
            rprint(f"[red]Error: {message}[/red]")
            sys.exit(1)
        elif status == "success":
            rprint(f"[green]{message}[/green]")
            break
        else:  # in_progress
            rprint(f"[yellow]{message}[/yellow]")
            input()  # Wait for user to press Enter

    rprint("\n[green]Calibration completed![/green]")


@app.command()
def control(
    robot_id: int = typer.Option(0, "--robot-id", "-r", help="Robot ID to control"),
):
    """Start keyboard control."""
    rprint("[bold green]Keyboard Control[/bold green]\n")

    manager = RobotConnectionManager()
    robots = manager.find_robots()

    if not robots:
        rprint("[red]No robots found![/red]")
        sys.exit(1)

    if robot_id >= len(robots):
        rprint(f"[red]Invalid robot ID: {robot_id}[/red]")
        sys.exit(1)

    robot = robots[robot_id]

    if not robot.config:
        rprint("[red]Robot not calibrated![/red]")
        rprint("Please run: rosota-lerobot calibrate")
        sys.exit(1)

    controller = KeyboardController(robot)
    controller.start()


@app.command()
def info():
    """Show system information."""
    rprint("[bold green]System Information[/bold green]\n")

    manager = RobotConnectionManager()
    ports = manager.scan_ports()

    rprint(f"Available serial ports: {len(ports)}")
    for port in ports:
        rprint(f"  - {port.device} (PID: {port.pid}, Serial: {port.serial_number or 'N/A'})")

    robots = manager.find_robots()
    rprint(f"\nConnected robots: {len(robots)}")
    for i, robot in enumerate(robots):
        rprint(f"  [{i}] {robot.name} on {robot.device_name}")
        rprint(f"      Serial: {robot.SERIAL_ID}")
        rprint(f"      Connected: {robot.is_connected}")
        rprint(f"      Calibrated: {robot.config is not None}")


def cli():
    """CLI entry point."""
    app()


if __name__ == "__main__":
    cli()

