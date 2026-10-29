"""
Central Detection Pipeline and Incident Coordinator.
Ingests file system events, passes them through the sliding behavioral window,
computes threat scores, triggers ML analysis, persists incidents, and enforces automated containment.
"""

import time
import logging
import threading
from collections import deque
from pathlib import Path

from config import DEFAULT_DETECTION_CONFIG
from database.db import (
    log_security_event,
    create_incident,
    get_all_settings
)
from detection.rules import BehavioralWindow, BehavioralEvent
from detection.scoring import calculate_threat_score
from detection.ml_model import ml_classifier
from simulation.simulator import simulator

logger = logging.getLogger(__name__)


class DetectionCoordinator:
    """
    Coordinates real-time behavioral telemetry, threat scoring, incident recording,
    and automated defensive response.
    """
    def __init__(self):
        self.window = BehavioralWindow(window_seconds=5.0)
        self.recent_alerts = deque(maxlen=50)
        self.last_incident_time = 0
        self.incident_debounce_seconds = 2.0
        self._lock = threading.Lock()

    def get_config(self) -> dict:
        """Loads latest dynamic configuration from database or defaults."""
        try:
            return get_all_settings()
        except Exception:
            return DEFAULT_DETECTION_CONFIG

    def process_event(self, event_type: str, file_path: str, old_path: str = None, details: str = "") -> dict:
        """
        Processes a single file event through the detection engine.
        Returns the scoring result dictionary.
        """
        with self._lock:
            config = self.get_config()
            self.window.window_seconds = float(config.get("burst_window_seconds", 5.0))

            # 1. Create Behavioral Event & update sliding window
            event = BehavioralEvent(event_type, file_path, old_path=old_path)
            self.window.add_event(event)

            # 2. Extract metrics
            suspicious_exts = config.get("suspicious_extensions", DEFAULT_DETECTION_CONFIG["suspicious_extensions"])
            metrics = self.window.get_metrics(suspicious_exts)

            # 3. ML Evaluation (if enabled in settings)
            ml_result = None
            if config.get("ml_enabled", True):
                try:
                    ml_result = ml_classifier.predict(metrics)
                except Exception as e:
                    logger.error(f"ML evaluation error: {e}")

            # 4. Calculate Threat Score & Evaluate Rules
            score_res = calculate_threat_score(metrics, config, ml_result=ml_result)
            threat_score = score_res["threat_score"]
            severity = score_res["severity"]
            is_flagged = score_res["is_flagged"]

            # 5. Persist raw event to database
            ext = Path(file_path).suffix.lower() if file_path else ""
            try:
                log_security_event(
                    event_type=event_type,
                    file_path=file_path,
                    file_extension=ext,
                    threat_score=threat_score,
                    is_flagged=is_flagged,
                    details=details
                )
            except Exception as e:
                logger.error(f"Error persisting security event: {e}")

            # 6. Incident Generation & Throttling
            now = time.time()
            if is_flagged and (now - self.last_incident_time > self.incident_debounce_seconds or threat_score >= 80):
                self.last_incident_time = now
                primary_reason = score_res["reasons"][0] if score_res["reasons"] else "Suspicious file activity"

                incident_details = {
                    "file_path": file_path,
                    "old_path": old_path,
                    "metrics": metrics,
                    "breakdown": score_res["breakdown"],
                    "ml_result": ml_result
                }

                try:
                    incident_id = create_incident(
                        severity=severity,
                        threat_score=threat_score,
                        primary_reason=primary_reason,
                        reasons=score_res["reasons"],
                        event_type=event_type,
                        details=incident_details
                    )

                    alert_entry = {
                        "incident_id": incident_id,
                        "timestamp": time.strftime("%H:%M:%S"),
                        "severity": severity,
                        "threat_score": threat_score,
                        "primary_reason": primary_reason,
                        "reasons": score_res["reasons"],
                        "file_path": file_path,
                        "formula": score_res["breakdown"]["formula_string"],
                        "ml_prediction": ml_result.get("prediction") if ml_result else "N/A"
                    }
                    self.recent_alerts.appendleft(alert_entry)

                    # 7. Simulated Defensive Containment (Auto-mitigate if configured)
                    if threat_score >= 80 and config.get("auto_mitigate_on_critical", True):
                        if simulator.state == "RUNNING":
                            simulator.pause()
                            simulator._log("ALERT", f"[AUTO-DEFENSE] Critical threat detected ({threat_score}/100)! Process automatically suspended for containment.")

                except Exception as e:
                    logger.error(f"Error recording security incident: {e}")

            return score_res

    def get_recent_alerts(self, limit: int = 15) -> list:
        """Retrieves in-memory alerts for rapid dashboard polling."""
        with self._lock:
            return list(self.recent_alerts)[:limit]

    def clear_window(self):
        """Resets the sliding window."""
        with self._lock:
            self.window.clear()


# Global singleton instance
detection_coordinator = DetectionCoordinator()

# Connect simulator and monitor callbacks to pipeline
simulator.set_event_callback(detection_coordinator.process_event)
