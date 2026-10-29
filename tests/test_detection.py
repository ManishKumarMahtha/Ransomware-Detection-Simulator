"""
Unit tests for Detection Engine and Threat Scoring.
"""

import time
import pytest
from detection.rules import BehavioralWindow, BehavioralEvent, evaluate_rules
from detection.scoring import calculate_threat_score
from detection.ml_model import ml_classifier
from config import DEFAULT_DETECTION_CONFIG


def test_benign_events_produce_low_threat_score():
    """Verifies that slow, normal file operations result in Low severity and score < 30."""
    window = BehavioralWindow(window_seconds=5.0)

    # Simulate 2 slow benign modifications
    window.add_event(BehavioralEvent("MODIFY", "document.txt"))
    window.add_event(BehavioralEvent("CREATE", "notes.txt"))

    metrics = window.get_metrics(DEFAULT_DETECTION_CONFIG["suspicious_extensions"])
    result = calculate_threat_score(metrics, DEFAULT_DETECTION_CONFIG)

    assert result["threat_score"] < 30
    assert result["severity"] == "LOW"
    assert result["is_flagged"] is False
    assert len(result["reasons"]) > 0


def test_ransomware_burst_triggers_critical_alert():
    """Verifies that rapid renaming to .locked triggers Critical threat score (> 80)."""
    window = BehavioralWindow(window_seconds=5.0)

    # Simulate rapid renames to .locked and modification burst
    for i in range(8):
        window.add_event(BehavioralEvent("MODIFY", f"file_{i}.txt"))
        window.add_event(BehavioralEvent("RENAME", f"file_{i}.txt.locked", old_path=f"file_{i}.txt"))

    metrics = window.get_metrics(DEFAULT_DETECTION_CONFIG["suspicious_extensions"])
    result = calculate_threat_score(metrics, DEFAULT_DETECTION_CONFIG)

    assert result["threat_score"] >= 80
    assert result["severity"] == "CRITICAL"
    assert result["is_flagged"] is True
    assert result["triggers"]["rename_burst"] is True
    assert result["triggers"]["suspicious_extension"] is True


def test_sliding_window_purges_expired_events():
    """Verifies that events older than the sliding window duration are purged."""
    window = BehavioralWindow(window_seconds=2.0)

    old_time = time.time() - 5.0
    window.add_event(BehavioralEvent("MODIFY", "old_file.txt", timestamp=old_time))
    window.add_event(BehavioralEvent("CREATE", "new_file.txt", timestamp=time.time()))

    metrics = window.get_metrics(DEFAULT_DETECTION_CONFIG["suspicious_extensions"])
    assert metrics["total_events"] == 1
    assert metrics["creations_count"] == 1
    assert metrics["modifications_count"] == 0


def test_ml_classifier_predicts_behavior():
    """Verifies that the Scikit-learn Random Forest model generates an explainable prediction."""
    # Test high-velocity ransomware-like telemetry vector
    ransomware_metrics = {
        "velocity": 12.5,
        "renames_count": 8,
        "window_duration": 5.0,
        "suspicious_ext_count": 6,
        "total_events": 16,
        "modifications_count": 8,
        "unique_extensions": 3
    }
    prediction = ml_classifier.predict(ransomware_metrics)

    if prediction["enabled"]:
        assert prediction["is_ransomware"] is True
        assert prediction["confidence"] >= 50.0
        assert "events_per_sec" in prediction["feature_vector"]
        assert len(prediction["top_features"]) > 0
