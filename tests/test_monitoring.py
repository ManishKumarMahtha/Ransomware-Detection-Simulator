"""
Unit tests for Safe File Monitoring and Boundary Checking.
"""

from pathlib import Path
from config import validate_monitoring_path, SANDBOX_DIR
from monitoring.file_monitor import file_monitor


def test_validate_monitoring_path_accepts_sandbox():
    """Verifies that the dedicated sandbox directory is accepted."""
    is_valid, msg = validate_monitoring_path(str(SANDBOX_DIR))
    assert is_valid is True
    assert "safe for monitoring" in msg


def test_validate_monitoring_path_rejects_unsafe_paths():
    """Verifies rejection of system roots, root drives, and non-existent paths."""
    # 1. Non-existent path
    is_valid, msg = validate_monitoring_path("C:/NonExistentPath_Test_123456")
    assert is_valid is False
    assert "does not exist" in msg

    # 2. Root drive
    is_valid, msg = validate_monitoring_path("C:\\")
    assert is_valid is False
    assert "prohibited" in msg.lower()

    # 3. Windows system directory
    is_valid, msg = validate_monitoring_path("C:\\Windows")
    assert is_valid is False
    assert "prohibited" in msg.lower()


def test_file_monitor_start_and_stop():
    """Verifies file monitor starts and stops cleanly."""
    file_monitor.stop_monitoring()

    success, msg = file_monitor.start_monitoring(str(SANDBOX_DIR))
    assert success is True
    assert file_monitor.is_monitoring is True

    # Check status payload
    status = file_monitor.get_status()
    assert status["is_monitoring"] is True
    assert status["monitored_path"] == str(SANDBOX_DIR.resolve())

    # Stop monitor
    success, msg = file_monitor.stop_monitoring()
    assert success is True
    assert file_monitor.is_monitoring is False
