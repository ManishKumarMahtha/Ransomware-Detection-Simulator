"""
Unit tests for Safe Simulation Engine and Sandbox Confinement.
"""

import time
from pathlib import Path
from config import SANDBOX_DIR, is_safe_sandbox_path
from simulation.simulator import simulator


def test_sandbox_path_validation():
    """Verifies that is_safe_sandbox_path strictly enforces the dedicated sandbox directory."""
    inside_file = SANDBOX_DIR / "sample_doc.txt"
    outside_file = Path("C:/Windows/System32/calc.exe")
    parent_traversal = SANDBOX_DIR / ".." / "system.ini"

    assert is_safe_sandbox_path(inside_file) is True
    assert is_safe_sandbox_path(outside_file) is False
    assert is_safe_sandbox_path(parent_traversal) is False


def test_simulation_lifecycle_controls():
    """Verifies start, pause, resume, stop, and reset controls."""
    # Ensure clean state
    simulator.reset()
    assert simulator.state == "IDLE"

    # Start Benign simulation with high speed for quick test
    success, msg = simulator.start(profile="benign", speed=4.0)
    assert success is True
    assert simulator.state == "RUNNING"

    # Pause
    success, msg = simulator.pause()
    assert success is True
    assert simulator.state == "PAUSED"

    # Resume
    success, msg = simulator.resume()
    assert success is True
    assert simulator.state == "RUNNING"

    # Stop
    success, msg = simulator.stop()
    assert success is True
    assert simulator.state == "STOPPED"

    # Reset
    success, msg = simulator.reset()
    assert success is True
    assert simulator.state == "IDLE"


def test_multiple_simulations_prevented():
    """Verifies that launching concurrent simulations is safely rejected."""
    simulator.reset()
    success1, _ = simulator.start(profile="benign", speed=0.5)
    assert success1 is True

    # Attempt second concurrent start
    success2, msg = simulator.start(profile="ransomware_burst", speed=1.0)
    assert success2 is False
    assert "already actively running" in msg

    simulator.stop()
    simulator.reset()
