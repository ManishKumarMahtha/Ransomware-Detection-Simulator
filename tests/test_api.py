"""
Integration and API endpoint tests using Flask Test Client.
"""

import pytest
from app import app
from database.db import init_db


@pytest.fixture
def client():
    app.config["TESTING"] = True
    app.config["DEBUG"] = False
    with app.test_client() as client:
        with app.app_context():
            init_db()
        yield client


def test_login_flow(client):
    """Verifies authentication API behavior with valid and invalid credentials."""
    # 1. Invalid credentials
    res = client.post("/api/auth/login", json={"username": "wrong", "password": "bad"})
    assert res.status_code == 401
    assert res.get_json()["success"] is False

    # 2. Valid admin demo credentials
    res = client.post("/api/auth/login", json={"username": "admin", "password": "admin123"})
    assert res.status_code == 200
    assert res.get_json()["success"] is True


def test_protected_routes_require_login(client):
    """Verifies that accessing protected endpoints unauthenticated returns 401 or redirect."""
    res = client.get("/api/dashboard/stats")
    assert res.status_code == 401

    res = client.get("/")
    assert res.status_code == 302
    assert "/login" in res.headers["Location"]


def test_authenticated_dashboard_stats(client):
    """Verifies dashboard metrics endpoint when authenticated."""
    # Authenticate
    client.post("/api/auth/login", json={"username": "admin", "password": "admin123"})

    res = client.get("/api/dashboard/stats")
    assert res.status_code == 200
    data = res.get_json()
    assert "total_monitored_files" in data
    assert "safe_activities" in data
    assert "suspicious_activities" in data
    assert "threats_detected" in data
    assert "severity_distribution" in data


def test_settings_persistence(client):
    """Verifies retrieving and updating detection thresholds."""
    client.post("/api/auth/login", json={"username": "admin", "password": "admin123"})

    # Update threshold
    res = client.post("/api/settings", json={"burst_window_seconds": 6.5, "rename_threshold": 5})
    assert res.status_code == 200
    assert res.get_json()["success"] is True

    # Retrieve and verify
    res = client.get("/api/settings")
    assert res.status_code == 200
    data = res.get_json()
    assert data["burst_window_seconds"] == 6.5
    assert data["rename_threshold"] == 5


def test_csv_export_endpoint(client):
    """Verifies that CSV export returns text/csv with attachment header."""
    client.post("/api/auth/login", json={"username": "admin", "password": "admin123"})

    res = client.get("/api/reports/export/csv")
    assert res.status_code == 200
    assert "text/csv" in res.content_type
    assert "attachment" in res.headers["Content-Disposition"]
    assert b"Incident ID,Timestamp,Severity" in res.data
