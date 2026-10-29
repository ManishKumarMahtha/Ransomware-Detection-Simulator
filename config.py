"""
Application Configuration and Safety Guards for Ransomware Detection Simulator.
Strictly ensures all simulation operations remain within isolated test directories.
"""

import os
from pathlib import Path

# Base Paths
BASE_DIR = Path(__file__).resolve().parent
DATABASE_PATH = BASE_DIR / "database" / "ransomware_sim.db"
SANDBOX_DIR = BASE_DIR / "demo_data" / "sandbox"

# Create directories if they do not exist
DATABASE_PATH.parent.mkdir(parents=True, exist_ok=True)
SANDBOX_DIR.mkdir(parents=True, exist_ok=True)

# Flask Configuration
SECRET_KEY = os.environ.get("FLASK_SECRET_KEY", "cyber-guard-ransomware-sim-secret-key-2026")
DEBUG = False

# Safety: Forbidden System Directories that Monitoring or Simulation must NEVER touch
FORBIDDEN_PATHS = [
    Path(os.environ.get("SystemRoot", "C:\\Windows")).resolve(),
    Path(os.environ.get("ProgramFiles", "C:\\Program Files")).resolve(),
    Path(os.environ.get("ProgramFiles(x86)", "C:\\Program Files (x86)")).resolve(),
    Path("C:\\").resolve(),
    Path(Path.home()).resolve(),  # Root of user home
]

# Detection Engine Defaults (Configurable via UI)
DEFAULT_DETECTION_CONFIG = {
    "burst_window_seconds": 5.0,        # Time window for sliding behavioral analysis
    "rename_threshold": 4,             # Renames in window triggering alert
    "modification_threshold": 6,       # Rapid modifications in window triggering alert
    "total_event_threshold": 10,       # High velocity threshold
    "suspicious_extensions": [
        ".locked", ".crypto", ".crypted", ".enc", ".ransom",
        ".wnry", ".locky", ".cerber", ".crypt", ".dark", ".vault"
    ],
    "rename_weight": 35.0,             # Weight contribution to 0-100 score
    "extension_weight": 40.0,          # Weight contribution for suspicious extensions
    "burst_weight": 25.0,              # Weight contribution for modification burst
    "ml_enabled": True,                # Enable/disable Scikit-Learn ML classifier
    "auto_mitigate_on_critical": True  # Automatically pause/halt simulation if critical threat
}

# Severity Classification Thresholds
SEVERITY_LEVELS = {
    "LOW": (0, 29),
    "MEDIUM": (30, 59),
    "HIGH": (60, 79),
    "CRITICAL": (80, 100)
}


def is_safe_sandbox_path(target_path: Path | str) -> bool:
    """
    Validates that a file or folder path is strictly inside the dedicated sandbox directory.
    Prevents path traversal and modification outside sandbox.
    """
    try:
        resolved_sandbox = SANDBOX_DIR.resolve()
        resolved_target = Path(target_path).resolve()
        # Ensure target is relative to or identical to sandbox
        resolved_target.relative_to(resolved_sandbox)
        return True
    except (ValueError, Exception):
        return False


def validate_monitoring_path(target_path: str) -> tuple[bool, str]:
    """
    Validates a directory path selected for file monitoring.
    Rejects unsafe system paths, non-existent paths, and root drives.
    """
    if not target_path or not str(target_path).strip():
        return False, "Path cannot be empty."

    try:
        p = Path(target_path).resolve()
        if not p.exists():
            return False, f"Directory does not exist: {p}"
        if not p.is_dir():
            return False, f"Path is not a directory: {p}"

        # Check against forbidden system roots
        for forbidden in FORBIDDEN_PATHS:
            if p == forbidden:
                return False, f"Access denied: Monitoring system root '{p}' is prohibited for safety."

        # Do not allow monitoring root of any drive (e.g. C:\ or D:\)
        if len(p.parts) <= 1 or p == Path(p.anchor):
            return False, "Access denied: Root drive monitoring is prohibited. Select a specific subfolder."

        return True, "Path is valid and safe for monitoring."
    except Exception as e:
        return False, f"Invalid path syntax: {str(e)}"
