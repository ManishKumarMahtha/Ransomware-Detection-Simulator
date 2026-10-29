"""
Flask Application and REST APIs for Ransomware Detection Simulator.
A complete, defensive cybersecurity educational platform for CSE AI/ML major project demonstrations.
"""

import os
import csv
import io
import json
from datetime import datetime
from functools import wraps
from flask import (
    Flask,
    render_template,
    request,
    jsonify,
    session,
    redirect,
    url_for,
    Response,
    send_file
)

from config import (
    SECRET_KEY,
    DEBUG,
    SANDBOX_DIR,
    DEFAULT_DETECTION_CONFIG,
    validate_monitoring_path
)
from database.db import (
    init_db,
    authenticate_user,
    get_all_settings,
    update_setting,
    get_incidents,
    get_incident_by_id,
    update_incident_status,
    get_dashboard_metrics,
    get_db_connection
)
from simulation.simulator import simulator
from monitoring.file_monitor import file_monitor
from detection.pipeline import detection_coordinator
from detection.ml_model import ml_classifier

# Initialize Flask App
app = Flask(__name__)
app.secret_key = SECRET_KEY
app.config["DEBUG"] = DEBUG

# Connect File Monitor to Central Detection Coordinator
file_monitor.set_event_callback(detection_coordinator.process_event)


# =========================================================================
# AUTHENTICATION HELPERS
# =========================================================================
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if "user" not in session:
            if request.path.startswith("/api/"):
                return jsonify({"error": "Authentication required"}), 401
            return redirect(url_for("login_page"))
        return f(*args, **kwargs)
    return decorated_function


# =========================================================================
# WEB PAGES
# =========================================================================
@app.route("/login")
def login_page():
    if "user" in session:
        return redirect(url_for("dashboard_page"))
    return render_template("login.html")


@app.route("/")
@app.route("/dashboard")
@login_required
def dashboard_page():
    return render_template("dashboard.html", active_page="dashboard", user=session["user"])


@app.route("/simulation")
@login_required
def simulation_page():
    return render_template("simulation.html", active_page="simulation", user=session["user"])


@app.route("/monitoring")
@login_required
def monitoring_page():
    return render_template("monitoring.html", active_page="monitoring", user=session["user"])


@app.route("/alerts")
@login_required
def alerts_page():
    return render_template("alerts.html", active_page="alerts", user=session["user"])


@app.route("/incidents")
@login_required
def incidents_page():
    return render_template("incidents.html", active_page="incidents", user=session["user"])


@app.route("/settings")
@login_required
def settings_page():
    return render_template("settings.html", active_page="settings", user=session["user"])


@app.route("/reports")
@login_required
def reports_page():
    return render_template("reports.html", active_page="reports", user=session["user"])


@app.route("/education")
@login_required
def education_page():
    return render_template("education.html", active_page="education", user=session["user"])


# =========================================================================
# AUTHENTICATION APIS
# =========================================================================
@app.route("/api/auth/login", methods=["POST"])
def api_login():
    data = request.get_json() or {}
    username = data.get("username", "").strip()
    password = data.get("password", "").strip()

    user = authenticate_user(username, password)
    if user:
        session["user"] = user
        return jsonify({"success": True, "message": "Login successful", "user": user})
    return jsonify({"success": False, "message": "Invalid username or password"}), 401


@app.route("/api/auth/logout", methods=["POST", "GET"])
def api_logout():
    session.pop("user", None)
    return redirect(url_for("login_page"))


# =========================================================================
# DASHBOARD APIS
# =========================================================================
@app.route("/api/dashboard/stats", methods=["GET"])
@login_required
def api_dashboard_stats():
    metrics = get_dashboard_metrics()
    metrics["simulator_state"] = simulator.state
    metrics["monitoring_active"] = file_monitor.is_monitoring
    metrics["ml_available"] = ml_classifier.is_trained
    return jsonify(metrics)


# =========================================================================
# SIMULATION APIS
# =========================================================================
@app.route("/api/simulation/start", methods=["POST"])
@login_required
def api_simulation_start():
    data = request.get_json() or {}
    profile = data.get("profile", "benign")
    speed = float(data.get("speed", 1.0))

    success, message = simulator.start(profile=profile, speed=speed)
    status_code = 200 if success else 400
    return jsonify({"success": success, "message": message}), status_code


@app.route("/api/simulation/pause", methods=["POST"])
@login_required
def api_simulation_pause():
    success, message = simulator.pause()
    return jsonify({"success": success, "message": message})


@app.route("/api/simulation/resume", methods=["POST"])
@login_required
def api_simulation_resume():
    success, message = simulator.resume()
    return jsonify({"success": success, "message": message})


@app.route("/api/simulation/stop", methods=["POST"])
@login_required
def api_simulation_stop():
    success, message = simulator.stop()
    return jsonify({"success": success, "message": message})


@app.route("/api/simulation/reset", methods=["POST"])
@login_required
def api_simulation_reset():
    success, message = simulator.reset()
    detection_coordinator.clear_window()
    return jsonify({"success": success, "message": message})


@app.route("/api/simulation/status", methods=["GET"])
@login_required
def api_simulation_status():
    return jsonify(simulator.get_status())


# =========================================================================
# FILE MONITORING APIS
# =========================================================================
@app.route("/api/monitoring/start", methods=["POST"])
@login_required
def api_monitoring_start():
    data = request.get_json() or {}
    directory_path = data.get("directory_path", str(SANDBOX_DIR)).strip()

    success, message = file_monitor.start_monitoring(directory_path)
    status_code = 200 if success else 400
    return jsonify({"success": success, "message": message}), status_code


@app.route("/api/monitoring/stop", methods=["POST"])
@login_required
def api_monitoring_stop():
    success, message = file_monitor.stop_monitoring()
    return jsonify({"success": success, "message": message})


@app.route("/api/monitoring/status", methods=["GET"])
@login_required
def api_monitoring_status():
    return jsonify(file_monitor.get_status())


@app.route("/api/monitoring/validate-path", methods=["POST"])
@login_required
def api_monitoring_validate_path():
    data = request.get_json() or {}
    path = data.get("directory_path", "")
    is_valid, msg = validate_monitoring_path(path)
    return jsonify({"is_valid": is_valid, "message": msg})


# =========================================================================
# ALERTS & INCIDENT APIS
# =========================================================================
@app.route("/api/alerts", methods=["GET"])
@login_required
def api_get_alerts():
    limit = int(request.args.get("limit", 15))
    alerts = detection_coordinator.get_recent_alerts(limit=limit)
    return jsonify({"alerts": alerts})


@app.route("/api/incidents", methods=["GET"])
@login_required
def api_get_incidents():
    severity = request.args.get("severity", "ALL")
    status = request.args.get("status", "ALL")
    limit = int(request.args.get("limit", 100))

    incidents = get_incidents(severity_filter=severity, status_filter=status, limit=limit)
    return jsonify({"incidents": incidents})


@app.route("/api/incidents/<incident_id>", methods=["GET"])
@login_required
def api_get_incident_detail(incident_id):
    inc = get_incident_by_id(incident_id)
    if not inc:
        return jsonify({"error": "Incident not found"}), 404
    return jsonify({"incident": inc})


@app.route("/api/incidents/<incident_id>/status", methods=["POST"])
@login_required
def api_update_incident_status(incident_id):
    data = request.get_json() or {}
    new_status = data.get("status", "Investigated")
    valid_statuses = ["Open", "Under Investigation", "Investigated", "Mitigated", "False Positive"]
    if new_status not in valid_statuses:
        return jsonify({"error": f"Invalid status. Must be one of {valid_statuses}"}), 400

    update_incident_status(incident_id, new_status)
    return jsonify({"success": True, "message": f"Incident {incident_id} marked as {new_status}"})


# =========================================================================
# SETTINGS & CONFIGURATION APIS
# =========================================================================
@app.route("/api/settings", methods=["GET"])
@login_required
def api_get_settings():
    settings = get_all_settings()
    settings["ml_model_status"] = {
        "available": ml_classifier.is_trained,
        "sample_count": ml_classifier.training_sample_count,
        "feature_importances": ml_classifier.feature_importances
    }
    return jsonify(settings)


@app.route("/api/settings", methods=["POST"])
@login_required
def api_save_settings():
    data = request.get_json() or {}
    try:
        # Validate and persist settings
        if "burst_window_seconds" in data:
            val = float(data["burst_window_seconds"])
            if val < 1.0 or val > 60.0:
                return jsonify({"error": "Window seconds must be between 1 and 60"}), 400
            update_setting("burst_window_seconds", val)

        if "rename_threshold" in data:
            val = int(data["rename_threshold"])
            if val < 1 or val > 50:
                return jsonify({"error": "Rename threshold must be between 1 and 50"}), 400
            update_setting("rename_threshold", val)

        if "modification_threshold" in data:
            val = int(data["modification_threshold"])
            if val < 1 or val > 100:
                return jsonify({"error": "Modification threshold must be between 1 and 100"}), 400
            update_setting("modification_threshold", val)

        if "total_event_threshold" in data:
            val = int(data["total_event_threshold"])
            update_setting("total_event_threshold", val)

        if "rename_weight" in data:
            update_setting("rename_weight", float(data["rename_weight"]))

        if "extension_weight" in data:
            update_setting("extension_weight", float(data["extension_weight"]))

        if "burst_weight" in data:
            update_setting("burst_weight", float(data["burst_weight"]))

        if "ml_enabled" in data:
            update_setting("ml_enabled", bool(data["ml_enabled"]))

        if "auto_mitigate_on_critical" in data:
            update_setting("auto_mitigate_on_critical", bool(data["auto_mitigate_on_critical"]))

        if "suspicious_extensions" in data:
            exts = data["suspicious_extensions"]
            if isinstance(exts, str):
                exts = [e.strip() if e.strip().startswith(".") else "." + e.strip() for e in exts.split(",") if e.strip()]
            update_setting("suspicious_extensions", exts)

        return jsonify({"success": True, "message": "Security settings saved successfully."})
    except Exception as e:
        return jsonify({"error": f"Failed to update settings: {str(e)}"}), 400


@app.route("/api/settings/reset", methods=["POST"])
@login_required
def api_reset_settings():
    for key, val in DEFAULT_DETECTION_CONFIG.items():
        update_setting(key, val)
    return jsonify({"success": True, "message": "Settings reset to default demonstration baseline."})


# =========================================================================
# REPORTS & EXPORT APIS
# =========================================================================
@app.route("/api/reports/export/csv", methods=["GET"])
@login_required
def api_export_csv():
    incidents = get_incidents(limit=1000)

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow([
        "Incident ID",
        "Timestamp",
        "Severity",
        "Threat Score",
        "Event Type",
        "Status",
        "Primary Detection Reason",
        "All Reasons",
        "Target File"
    ])

    for inc in incidents:
        file_path = inc.get("details", {}).get("file_path", "")
        reasons_combined = "; ".join(inc.get("reasons", []))
        writer.writerow([
            inc["incident_id"],
            inc["timestamp"],
            inc["severity"],
            inc["threat_score"],
            inc["event_type"],
            inc["status"],
            inc["primary_reason"],
            reasons_combined,
            file_path
        ])

    output.seek(0)
    filename = f"ransomware_incidents_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
    return Response(
        output.getvalue(),
        mimetype="text/csv",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )


@app.route("/api/reports/export/audit-json", methods=["GET"])
@login_required
def api_export_audit_json():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM security_events ORDER BY id DESC LIMIT 500")
    events = [dict(r) for r in cursor.fetchall()]
    conn.close()

    payload = {
        "export_timestamp": datetime.now().isoformat(),
        "total_records": len(events),
        "audit_events": events
    }
    return jsonify(payload)


# =========================================================================
# INITIALIZATION HOOK
# =========================================================================
with app.app_context():
    init_db()


if __name__ == "__main__":
    init_db()
    print("=" * 65)
    print("  RANSOMWARE DETECTION SIMULATOR - CSE AI/ML MAJOR PROJECT")
    print("  Safe Academic Defensive Cybersecurity Platform")
    print("=" * 65)
    print("  Local URL:        http://127.0.0.1:5000")
    print("  Demo Admin User:  admin / admin123")
    print("  Demo Analyst:     analyst / cyber2026")
    print("  Dedicated Sandbox:", SANDBOX_DIR)
    print("=" * 65)
    app.run(host="127.0.0.1", port=5000, debug=False, use_reloader=False)
