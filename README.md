# Ransomware Detection Simulator (CyberGuard)

### B.Tech Computer Science Engineering (AI/ML) Major Project

![Defensive Cybersecurity](https://img.shields.io/badge/Security-Defensive%20Simulation-06b6d4)
![Python 3.10+](https://img.shields.io/badge/Python-3.10%20%7C%203.11%20%7C%203.12%20%7C%203.14-38bdf8)
![Flask](https://img.shields.io/badge/Backend-Flask%203.1-success)
![Scikit-Learn](https://img.shields.io/badge/AI%2FML-Scikit--Learn%20RandomForest-orange)
![Tests](https://img.shields.io/badge/Tests-15%20Passed%20(100%25)-brightgreen)

A defensive cybersecurity application that simulates ransomware-like behavior in an isolated, safe test sandbox and detects suspicious file activity in real time using multi-factor behavioral heuristics and machine learning telemetry.

---

## 1. Safety Guarantees & Constraints

> [!IMPORTANT]
> **Defensive Demonstration Only**:
> - **Never Real Ransomware**: The application does not contain malicious binaries, worms, or cryptors.
> - **Zero Host File Modification**: All file creation, renaming, and modification operations are strictly confined to `demo_data/sandbox/`.
> - **No Encryption of Real Data**: Synthetic dummy text and synthetic simulated cipher blocks are used exclusively.
> - **No Antivirus Disabling**: Antivirus software, OS protections, and volume shadow copies are never disabled.

---

## 2. Key Architecture & Features

- **Professional Dark Cybersecurity SOC Dashboard**:
  - Live KPI cards: Sandbox Files, Benign Operations, Suspicious Events, Threats Detected.
  - Chart.js real-time threat timeline and severity doughnut distribution.
  - Live auto-refreshing security event feed.
- **Safe Behavioral Simulation Engine**:
  - Profiles: *Benign User Activity*, *Ransomware Burst Attack*, *Slow Stealth Drip*, *Rapid Extension Tampering*.
  - Controls: Start, Pause, Resume, Stop, and Reset.
  - Live progress tracking, speed multiplier (0.5x to 4.0x), and terminal console stream.
- **Explainable Behavioral Detection Engine**:
  - Sliding time window (1 to 60s configurable).
  - Metrics: Renames/sec, modification bursts, velocity, and known ransomware extension tampering (`.locked`, `.crypto`, `.crypted`, `.enc`, etc.).
  - Mathematical 0–100 threat scoring with explicit step-by-step formula attribution.
  - Severity classification: **Low** (0–29), **Medium** (30–59), **High** (60–79), **Critical** (80–100).
- **Explainable AI/ML Module**:
  - Supervised Random Forest Classifier trained on synthetic telemetry.
  - Feature importance breakdown: events/sec, rename rate, extension change ratio, modification burst rate.
- **Safe Real-Time File Monitoring**:
  - Python `watchdog` monitoring with strict path traversal prevention.
  - Rejects root drives (`C:\`) and system folders (`C:\Windows`).
- **Incident Forensics & Compliance Export**:
  - Detailed incident modal with forensic telemetry and timeline.
  - One-click CSV Export and JSON Audit Log export.

---

## 3. Technology Stack

| Layer | Technologies |
| :--- | :--- |
| **Frontend** | HTML5, CSS3, JavaScript (ES6+), Bootstrap 5.3, Bootstrap Icons, Chart.js 4.4 |
| **Backend** | Python (3.10–3.14), Flask 3.1, Jinja2 |
| **Monitoring** | Python Watchdog 6.0 |
| **Database** | SQLite 3 (Persistent relational store) |
| **Machine Learning** | Scikit-learn 1.9, NumPy, SciPy |
| **Automated Testing** | Pytest 9.2 (15 automated tests) |

---

## 4. Windows 10/11 Setup & Run Instructions

### Step 1: Open Terminal / PowerShell
Open **PowerShell** or **Command Prompt** in this project folder:
```powershell
cd "c:\Users\Manish\Desktop\ransomware detection stimulation"
```

### Step 2: Check Python Installation
```powershell
python --version
```
*(Ensure Python 3.10+ is installed).*

### Step 3: Create & Activate Virtual Environment
```powershell
# Create virtual environment
python -m venv venv

# Activate virtual environment in PowerShell
.\venv\Scripts\Activate.ps1
```
*(If PowerShell shows execution policy restrictions, run: `Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass`)*

### Step 4: Install Dependencies
```powershell
pip install -r requirements.txt
```

### Step 5: Start the Application Server
```powershell
python app.py
```

### Step 6: Open the Application in Browser
Open your browser and navigate to:
```
http://127.0.0.1:5000
```

---

## 5. Demo Credentials

| Role | Username | Password | Purpose |
| :--- | :--- | :--- | :--- |
| **Lead SOC Administrator** | `admin` | `admin123` | Full administrative control, config modification, mitigation |
| **Security Analyst** | `analyst` | `cyber2026` | Read-only telemetry, monitoring, and forensic review |

*Convenient 1-click credential fill buttons are provided on the login page for viva demonstration.*

---

## 6. Running Automated Tests

To verify all detection rules, simulation guards, API endpoints, and path validators:
```powershell
.\venv\Scripts\pytest.exe -v
```

**Test Execution Results:**
```
tests/test_api.py::test_login_flow PASSED
tests/test_api.py::test_protected_routes_require_login PASSED
tests/test_api.py::test_authenticated_dashboard_stats PASSED
tests/test_api.py::test_settings_persistence PASSED
tests/test_api.py::test_csv_export_endpoint PASSED
tests/test_detection.py::test_benign_events_produce_low_threat_score PASSED
tests/test_detection.py::test_ransomware_burst_triggers_critical_alert PASSED
tests/test_detection.py::test_sliding_window_purges_expired_events PASSED
tests/test_detection.py::test_ml_classifier_predicts_behavior PASSED
tests/test_monitoring.py::test_validate_monitoring_path_accepts_sandbox PASSED
tests/test_monitoring.py::test_validate_monitoring_path_rejects_unsafe_paths PASSED
tests/test_monitoring.py::test_file_monitor_start_and_stop PASSED
tests/test_simulation.py::test_sandbox_path_validation PASSED
tests/test_simulation.py::test_simulation_lifecycle_controls PASSED
tests/test_simulation.py::test_multiple_simulations_prevented PASSED

============================= 15 passed in 23.20s =============================
```

---

## 7. Faculty Demonstration Walkthrough

1. **Login & Dashboard Overview**:
   - Log in as `admin` using the 1-click button.
   - Show the KPI cards, system health indicators, and empty baseline charts.
2. **Benign Simulation (Baseline)**:
   - Navigate to **Simulation Engine**.
   - Select **Benign User Activity** and click **Start**.
   - Note the low velocity, harmless edits, and Low threat score (< 30).
3. **Ransomware Burst Attack (Detection & Alert)**:
   - Switch profile to **Ransomware Burst Attack** and click **Start**.
   - Observe simulated mass overwriting and rapid renaming to `.locked`.
   - The red **CRITICAL THREAT DETECTED** banner triggers on the dashboard.
   - If auto-mitigation is enabled, the simulation automatically pauses!
4. **Threat Alerts & Mathematical Explainability**:
   - Navigate to **Threat Alerts** or **Incident History**.
   - Click **Details** on an incident to show the exact mathematical formula string and Scikit-Learn ML feature attribution vector.
5. **Safe File Monitoring**:
   - Navigate to **File Monitoring**.
   - Demonstrate that invalid paths (e.g. `C:\Windows`) are safely rejected.
   - Start monitoring on the sandbox directory to stream live OS-level Watchdog hooks.
6. **Reports & CSV Export**:
   - Go to **Reports & Export** and download the CSV report to demonstrate forensic logging and compliance.
