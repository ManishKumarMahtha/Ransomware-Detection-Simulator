"""
SQLite Database Layer for Ransomware Detection Simulator.
Handles persistence of incidents, security events, configurations, and user authentication.
"""

import json
import sqlite3
import hashlib
from datetime import datetime
from pathlib import Path
from config import DATABASE_PATH, DEFAULT_DETECTION_CONFIG


def get_db_connection():
    """Returns a SQLite connection configured with Row factory."""
    conn = sqlite3.connect(DATABASE_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def hash_password(password: str) -> str:
    """Computes SHA-256 hash with static salt for demo authentication."""
    salt = "cyber_ransomware_simulator_demo_salt"
    return hashlib.sha256((salt + password).encode("utf-8")).hexdigest()


def init_db():
    """Initializes all database tables and seeds demo credentials and default configuration."""
    conn = get_db_connection()
    cursor = conn.cursor()

    # Users Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE NOT NULL,
        password_hash TEXT NOT NULL,
        full_name TEXT NOT NULL,
        role TEXT NOT NULL DEFAULT 'analyst',
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)

    # Incidents Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS incidents (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        incident_id TEXT UNIQUE NOT NULL,
        timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        severity TEXT NOT NULL,
        threat_score INTEGER NOT NULL,
        primary_reason TEXT NOT NULL,
        reasons_json TEXT NOT NULL,
        event_type TEXT NOT NULL,
        status TEXT NOT NULL DEFAULT 'Open',
        details_json TEXT NOT NULL,
        mitigated_at TIMESTAMP
    )
    """)

    # Security Events Log (Raw activity stream)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS security_events (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        event_type TEXT NOT NULL,
        file_path TEXT NOT NULL,
        file_extension TEXT,
        threat_score INTEGER DEFAULT 0,
        is_flagged INTEGER DEFAULT 0,
        details TEXT
    )
    """)

    # Persistent System Settings
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS system_config (
        key TEXT PRIMARY KEY,
        value TEXT NOT NULL,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)

    # Simulation Runs
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS simulation_runs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        run_id TEXT UNIQUE NOT NULL,
        profile TEXT NOT NULL,
        started_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        ended_at TIMESTAMP,
        total_events INTEGER DEFAULT 0,
        threats_detected INTEGER DEFAULT 0,
        status TEXT DEFAULT 'RUNNING'
    )
    """)

    conn.commit()

    # Seed Default Users if empty
    cursor.execute("SELECT COUNT(*) as count FROM users")
    if cursor.fetchone()["count"] == 0:
        cursor.execute("""
        INSERT INTO users (username, password_hash, full_name, role)
        VALUES (?, ?, ?, ?)
        """, ("admin", hash_password("admin123"), "Lead SOC Administrator", "admin"))

        cursor.execute("""
        INSERT INTO users (username, password_hash, full_name, role)
        VALUES (?, ?, ?, ?)
        """, ("analyst", hash_password("cyber2026"), "Security Analyst", "analyst"))

    # Seed Default Settings if empty
    cursor.execute("SELECT COUNT(*) as count FROM system_config")
    if cursor.fetchone()["count"] == 0:
        for key, val in DEFAULT_DETECTION_CONFIG.items():
            val_str = json.dumps(val) if not isinstance(val, (str, int, float, bool)) else str(val)
            cursor.execute("""
            INSERT INTO system_config (key, value) VALUES (?, ?)
            """, (key, val_str))

    conn.commit()
    conn.close()


def authenticate_user(username, password):
    """Verifies user credentials. Returns user dict or None."""
    conn = get_db_connection()
    cursor = conn.cursor()
    pwd_hash = hash_password(password)
    cursor.execute("SELECT id, username, full_name, role FROM users WHERE username = ? AND password_hash = ?",
                   (username, pwd_hash))
    user = cursor.fetchone()
    conn.close()
    return dict(user) if user else None


def get_all_settings():
    """Retrieves all configuration settings from the database."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT key, value FROM system_config")
    rows = cursor.fetchall()
    conn.close()

    settings = dict(DEFAULT_DETECTION_CONFIG)
    for r in rows:
        k, v = r["key"], r["value"]
        try:
            if k == "suspicious_extensions":
                settings[k] = json.loads(v)
            elif k in ("burst_window_seconds", "rename_weight", "extension_weight", "burst_weight"):
                settings[k] = float(v)
            elif k in ("rename_threshold", "modification_threshold", "total_event_threshold"):
                settings[k] = int(v)
            elif k in ("ml_enabled", "auto_mitigate_on_critical"):
                settings[k] = v.lower() in ("true", "1")
            else:
                settings[k] = v
        except Exception:
            settings[k] = v
    return settings


def update_setting(key: str, value):
    """Updates a single setting in the database."""
    conn = get_db_connection()
    cursor = conn.cursor()
    val_str = json.dumps(value) if isinstance(value, list) else str(value)
    cursor.execute("""
    INSERT INTO system_config (key, value, updated_at) VALUES (?, ?, CURRENT_TIMESTAMP)
    ON CONFLICT(key) DO UPDATE SET value = excluded.value, updated_at = CURRENT_TIMESTAMP
    """, (key, val_str))
    conn.commit()
    conn.close()


def log_security_event(event_type: str, file_path: str, file_extension: str, threat_score: int, is_flagged: bool, details: str = ""):
    """Logs an individual file system event."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
    INSERT INTO security_events (event_type, file_path, file_extension, threat_score, is_flagged, details)
    VALUES (?, ?, ?, ?, ?, ?)
    """, (event_type, file_path, file_extension, threat_score, 1 if is_flagged else 0, details))
    event_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return event_id


def create_incident(severity: str, threat_score: int, primary_reason: str, reasons: list, event_type: str, details: dict):
    """Creates and persists a high-fidelity security incident."""
    conn = get_db_connection()
    cursor = conn.cursor()

    now = datetime.now()
    # Generate human-readable incident id: e.g. INC-2026-0042
    cursor.execute("SELECT COUNT(*) as count FROM incidents")
    count = cursor.fetchone()["count"] + 1
    incident_id = f"INC-{now.strftime('%Y')}-{count:04d}"

    cursor.execute("""
    INSERT INTO incidents (incident_id, severity, threat_score, primary_reason, reasons_json, event_type, status, details_json)
    VALUES (?, ?, ?, ?, ?, ?, 'Open', ?)
    """, (incident_id, severity, threat_score, primary_reason, json.dumps(reasons), event_type, json.dumps(details)))

    conn.commit()
    conn.close()
    return incident_id


def get_incidents(severity_filter=None, status_filter=None, limit=100):
    """Retrieves incidents filtered by severity or status."""
    conn = get_db_connection()
    cursor = conn.cursor()

    query = "SELECT * FROM incidents WHERE 1=1"
    params = []

    if severity_filter and severity_filter != "ALL":
        query += " AND severity = ?"
        params.append(severity_filter.upper())

    if status_filter and status_filter != "ALL":
        query += " AND status = ?"
        params.append(status_filter)

    query += " ORDER BY id DESC LIMIT ?"
    params.append(limit)

    cursor.execute(query, tuple(params))
    rows = cursor.fetchall()
    conn.close()

    result = []
    for r in rows:
        d = dict(r)
        d["reasons"] = json.loads(d["reasons_json"]) if d.get("reasons_json") else []
        d["details"] = json.loads(d["details_json"]) if d.get("details_json") else {}
        result.append(d)
    return result


def get_incident_by_id(incident_id: str):
    """Retrieves a single incident by its string ID (e.g. INC-2026-0001)."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM incidents WHERE incident_id = ?", (incident_id,))
    row = cursor.fetchone()
    conn.close()

    if not row:
        return None
    d = dict(row)
    d["reasons"] = json.loads(d["reasons_json"]) if d.get("reasons_json") else []
    d["details"] = json.loads(d["details_json"]) if d.get("details_json") else {}
    return d


def update_incident_status(incident_id: str, new_status: str):
    """Updates the status of an incident (e.g., Open, Investigated, Mitigated, False Positive)."""
    conn = get_db_connection()
    cursor = conn.cursor()
    mitigated_at = datetime.now() if new_status in ("Mitigated", "Resolved") else None
    cursor.execute("""
    UPDATE incidents SET status = ?, mitigated_at = ? WHERE incident_id = ?
    """, (new_status, mitigated_at, incident_id))
    conn.commit()
    conn.close()
    return True


def get_dashboard_metrics():
    """Computes real-time statistics for the dashboard cards and charts."""
    conn = get_db_connection()
    cursor = conn.cursor()

    # Total files currently in sandbox
    from config import SANDBOX_DIR
    try:
        total_sandbox_files = len([f for f in SANDBOX_DIR.glob("*") if f.is_file()])
    except Exception:
        total_sandbox_files = 0

    # Total security events
    cursor.execute("SELECT COUNT(*) as total FROM security_events")
    total_events = cursor.fetchone()["total"]

    # Safe events vs Flagged events
    cursor.execute("SELECT COUNT(*) as safe_count FROM security_events WHERE is_flagged = 0")
    safe_activities = cursor.fetchone()["safe_count"]

    cursor.execute("SELECT COUNT(*) as suspicious_count FROM security_events WHERE is_flagged = 1")
    suspicious_activities = cursor.fetchone()["suspicious_count"]

    # Threats (Incidents)
    cursor.execute("SELECT COUNT(*) as total_threats FROM incidents")
    threats_detected = cursor.fetchone()["total_threats"]

    # Severity distribution
    cursor.execute("SELECT severity, COUNT(*) as count FROM incidents GROUP BY severity")
    sev_rows = cursor.fetchall()
    severity_distribution = {"LOW": 0, "MEDIUM": 0, "HIGH": 0, "CRITICAL": 0}
    for r in sev_rows:
        sev = r["severity"].upper()
        if sev in severity_distribution:
            severity_distribution[sev] = r["count"]

    # Recent 10 security events
    cursor.execute("SELECT * FROM security_events ORDER BY id DESC LIMIT 10")
    recent_events = [dict(r) for r in cursor.fetchall()]

    # Recent 5 incidents
    cursor.execute("SELECT * FROM incidents ORDER BY id DESC LIMIT 5")
    recent_incidents = []
    for r in cursor.fetchall():
        d = dict(r)
        d["reasons"] = json.loads(d["reasons_json"]) if d.get("reasons_json") else []
        recent_incidents.append(d)

    # Activity timeline (last 20 events with threat scores)
    cursor.execute("SELECT id, timestamp, threat_score, event_type FROM security_events ORDER BY id DESC LIMIT 20")
    timeline_rows = [dict(r) for r in cursor.fetchall()]
    timeline_rows.reverse()

    conn.close()

    return {
        "total_monitored_files": total_sandbox_files,
        "total_events": total_events,
        "safe_activities": safe_activities,
        "suspicious_activities": suspicious_activities,
        "threats_detected": threats_detected,
        "severity_distribution": severity_distribution,
        "recent_events": recent_events,
        "recent_incidents": recent_incidents,
        "timeline": timeline_rows
    }
