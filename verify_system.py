"""
End-to-End Automated Verification Script for Ransomware Detection Simulator.
Strictly exercises and validates all requirements requested by the user.
"""

import sys
import time
import json
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).resolve().parent))

from app import app
from config import SANDBOX_DIR, is_safe_sandbox_path, validate_monitoring_path
from database.db import init_db, get_db_connection, get_incidents, get_dashboard_metrics
from simulation.simulator import simulator
from detection.pipeline import detection_coordinator
from monitoring.file_monitor import file_monitor


def run_verification():
    print("=" * 70)
    print("STARTING FULL END-TO-END VERIFICATION")
    print("=" * 70)

    # 1. Initialize Database
    init_db()
    print("[PASS] Step 1: Database initialized successfully.")

    # 2. Test Client HTTP Responses
    client = app.test_client()

    # Verify Login page returns 200
    res_login = client.get("/login")
    assert res_login.status_code == 200, f"Expected 200 for /login, got {res_login.status_code}"
    assert b"Ransomware Detection SOC" in res_login.data
    print("[PASS] Step 2A: /login returns HTTP 200 with authentication interface.")

    # Authenticate as admin
    login_payload = {"username": "admin", "password": "admin123"}
    res_auth = client.post("/api/auth/login", json=login_payload)
    assert res_auth.status_code == 200, f"Auth failed with {res_auth.status_code}"
    auth_data = res_auth.get_json()
    assert auth_data["success"] is True
    print("[PASS] Step 2B: Admin authentication successful (user role: admin).")

    # Verify Dashboard page returns 200
    res_dash = client.get("/dashboard")
    assert res_dash.status_code == 200, f"Expected 200 for /dashboard, got {res_dash.status_code}"
    assert b"Real-Time Threat Detection Dashboard" in res_dash.data
    print("[PASS] Step 2C: /dashboard returns HTTP 200 for authenticated session.")

    # Verify All Other Pages Return 200
    for page in ["/simulation", "/monitoring", "/alerts", "/incidents", "/settings", "/reports", "/education"]:
        res_page = client.get(page)
        assert res_page.status_code == 200, f"Page {page} returned {res_page.status_code}"
    print("[PASS] Step 2D: All 9 application pages return HTTP 200 OK.")

    # 3. Verify Simulation & Detection Behavior
    print("\n--- Verifying Simulation Engine & Threat Scoring ---")
    simulator.reset()
    detection_coordinator.clear_window()

    # Test A: Benign Simulation
    print("Testing Profile: Benign User Activity...")
    success, msg = simulator.start(profile="benign", speed=4.0)
    assert success is True, msg
    time.sleep(2.0)  # Let benign actions run
    simulator.stop()

    # Check sandbox files are harmless
    sandbox_files = list(SANDBOX_DIR.glob("*"))
    assert len(sandbox_files) > 0, "No files found in sandbox."
    for f in sandbox_files:
        assert is_safe_sandbox_path(f), f"File {f} is outside sandbox!"
        with open(f, "r", encoding="utf-8", errors="ignore") as fh:
            content = fh.read()
            assert len(content) > 0, f"File {f.name} is empty"
            # Verify harmless benign text content
            assert not f.name.endswith(".exe") and not f.name.endswith(".dll")
    print(f"[PASS] Step 3A: Benign simulation generated {len(sandbox_files)} harmless dummy files strictly within sandbox.")

    # Test B: Ransomware Burst Attack
    print("Testing Profile: Ransomware Burst Attack...")
    simulator.reset()
    detection_coordinator.clear_window()
    success, msg = simulator.start(profile="ransomware_burst", speed=3.0)
    assert success is True, msg
    time.sleep(2.5)  # Let attack burst execute
    simulator.stop()

    # Verify alerts generated
    alerts = detection_coordinator.get_recent_alerts(limit=10)
    assert len(alerts) > 0, "No alerts were generated for ransomware burst!"
    latest_alert = alerts[0]
    print(f"[PASS] Step 3B: Ransomware burst triggered alert! Threat Score: {latest_alert['threat_score']}/100, Severity: {latest_alert['severity']}")
    assert latest_alert["threat_score"] >= 70, f"Expected threat score >= 70, got {latest_alert['threat_score']}"
    assert "formula" in latest_alert
    print(f"      Scoring Attribution Formula: {latest_alert['formula']}")

    # 4. Verify SQLite Persistence & Incident Storage
    print("\n--- Verifying SQLite Persistence ---")
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) as count FROM security_events")
    event_count = cursor.fetchone()["count"]
    cursor.execute("SELECT COUNT(*) as count FROM incidents")
    incident_count = cursor.fetchone()["count"]
    conn.close()

    assert event_count > 0, "No security events recorded in SQLite!"
    assert incident_count > 0, "No incidents recorded in SQLite!"
    print(f"[PASS] Step 4A: SQLite contains {event_count} raw security events and {incident_count} persistent incidents.")

    # 5. Verify CSV Export
    print("\n--- Verifying CSV Report Export ---")
    res_csv = client.get("/api/reports/export/csv")
    assert res_csv.status_code == 200
    assert "text/csv" in res_csv.content_type
    csv_text = res_csv.data.decode("utf-8")
    lines = [line.strip() for line in csv_text.splitlines() if line.strip()]
    assert len(lines) >= 2, f"CSV should contain at least header and one incident, got {len(lines)} lines"
    assert "Incident ID,Timestamp,Severity,Threat Score" in lines[0]
    print(f"[PASS] Step 5A: CSV export generated successfully ({len(lines)-1} incident rows exported).")

    # 6. Verify Path Validation & Safety Boundaries
    print("\n--- Verifying Path Traversal and Safety Guards ---")
    safe_ok, _ = validate_monitoring_path(str(SANDBOX_DIR))
    assert safe_ok is True, "Valid sandbox path was rejected."

    root_ok, root_msg = validate_monitoring_path("C:\\")
    assert root_ok is False, "Root drive C:\\ was incorrectly accepted!"
    assert "prohibited" in root_msg.lower()

    win_ok, win_msg = validate_monitoring_path("C:\\Windows")
    assert win_ok is False, "C:\\Windows was incorrectly accepted!"
    assert "prohibited" in win_msg.lower()

    fake_ok, fake_msg = validate_monitoring_path("C:\\NonExistent_Cyber_Dir_999")
    assert fake_ok is False, "Non-existent path was accepted!"
    assert "does not exist" in fake_msg.lower()

    print("[PASS] Step 6A: File monitoring path validator successfully rejected C:\\, C:\\Windows, and invalid paths.")

    # Clean reset
    simulator.reset()
    detection_coordinator.clear_window()
    print("[PASS] Step 7: Sandbox sanitized and reset.")

    print("\n" + "=" * 70)
    print("ALL VERIFICATION CHECKS COMPLETED WITH ZERO ERRORS.")
    print("=" * 70)


if __name__ == "__main__":
    run_verification()
