"""
Behavioral Detection Rules for Ransomware Detection Simulator.
Maintains a sliding time window of recent file events and evaluates behavioral indicators.
"""

import time
from collections import deque
from pathlib import Path


class BehavioralEvent:
    """Represents a single file system event in the sliding window."""
    def __init__(self, event_type: str, file_path: str, old_path: str = None, timestamp: float = None):
        self.timestamp = timestamp or time.time()
        self.event_type = event_type.upper()  # 'CREATE', 'MODIFY', 'DELETE', 'RENAME'
        self.file_path = file_path
        self.old_path = old_path
        self.extension = Path(file_path).suffix.lower() if file_path else ""
        self.old_extension = Path(old_path).suffix.lower() if old_path else ""


class BehavioralWindow:
    """Thread-safe sliding window tracking event velocity and behavioral patterns."""
    def __init__(self, window_seconds: float = 5.0):
        self.window_seconds = window_seconds
        self.events: deque[BehavioralEvent] = deque()

    def add_event(self, event: BehavioralEvent):
        """Adds an event and purges events outside the time window."""
        self.events.append(event)
        self.purge_expired()

    def purge_expired(self, current_time: float = None):
        """Removes events older than window_seconds."""
        now = current_time or time.time()
        cutoff = now - self.window_seconds
        while self.events and self.events[0].timestamp < cutoff:
            self.events.popleft()

    def clear(self):
        """Clears all events from the window."""
        self.events.clear()

    def get_metrics(self, suspicious_extensions: list[str]) -> dict:
        """
        Calculates behavioral rates and metrics over the current window.
        """
        self.purge_expired()
        total = len(self.events)
        if total == 0:
            return {
                "total_events": 0,
                "renames_count": 0,
                "modifications_count": 0,
                "creations_count": 0,
                "deletions_count": 0,
                "suspicious_ext_count": 0,
                "unique_extensions": 0,
                "velocity": 0.0,
                "window_duration": self.window_seconds,
                "suspicious_files": []
            }

        now = time.time()
        oldest = self.events[0].timestamp
        active_duration = max(0.2, now - oldest)
        velocity = total / active_duration

        renames = 0
        mods = 0
        creates = 0
        deletes = 0
        suspicious_ext = 0
        extensions_seen = set()
        suspicious_files = []

        suspicious_ext_set = set(ext.lower() for ext in suspicious_extensions)

        for ev in self.events:
            if ev.extension:
                extensions_seen.add(ev.extension)

            if ev.event_type == "RENAME":
                renames += 1
                # Check if file extension was changed to a suspicious extension
                if ev.extension in suspicious_ext_set:
                    suspicious_ext += 1
                    suspicious_files.append({
                        "file": Path(ev.file_path).name,
                        "old": Path(ev.old_path).name if ev.old_path else "",
                        "ext": ev.extension
                    })
            elif ev.event_type == "MODIFY":
                mods += 1
            elif ev.event_type == "CREATE":
                creates += 1
                if ev.extension in suspicious_ext_set:
                    suspicious_ext += 1
                    suspicious_files.append({
                        "file": Path(ev.file_path).name,
                        "ext": ev.extension
                    })
            elif ev.event_type == "DELETE":
                deletes += 1

        return {
            "total_events": total,
            "renames_count": renames,
            "modifications_count": mods,
            "creations_count": creates,
            "deletions_count": deletes,
            "suspicious_ext_count": suspicious_ext,
            "unique_extensions": len(extensions_seen),
            "velocity": round(velocity, 2),
            "window_duration": self.window_seconds,
            "suspicious_files": suspicious_files
        }


def evaluate_rules(metrics: dict, config: dict) -> tuple[list[str], dict]:
    """
    Evaluates individual detection heuristics against metrics.
    Returns:
      reasons: List of explanatory strings for faculty demonstration.
      rule_triggers: Dict of boolean flags for each rule.
    """
    reasons = []
    triggers = {
        "rename_burst": False,
        "suspicious_extension": False,
        "modification_burst": False,
        "excessive_velocity": False,
        "multi_factor_anomaly": False
    }

    rename_thresh = config.get("rename_threshold", 4)
    mod_thresh = config.get("modification_threshold", 6)
    velocity_thresh = config.get("total_event_threshold", 10) / config.get("burst_window_seconds", 5.0)

    # Rule 1: High File-Renaming Frequency
    if metrics["renames_count"] >= rename_thresh:
        triggers["rename_burst"] = True
        reasons.append(
            f"High file-renaming frequency detected: {metrics['renames_count']} renames in sliding "
            f"window (threshold: {rename_thresh} renames/{config.get('burst_window_seconds', 5.0)}s)."
        )

    # Rule 2: Suspicious Ransomware Extension Changes
    if metrics["suspicious_ext_count"] > 0:
        triggers["suspicious_extension"] = True
        ext_list = list(set(f["ext"] for f in metrics["suspicious_files"] if "ext" in f))
        reasons.append(
            f"Rapid extension tampering: {metrics['suspicious_ext_count']} file(s) renamed/created with "
            f"ransomware-associated extension(s) ({', '.join(ext_list)})."
        )

    # Rule 3: Burst Modification Operations
    if metrics["modifications_count"] >= mod_thresh:
        triggers["modification_burst"] = True
        reasons.append(
            f"Unusual modification burst: {metrics['modifications_count']} file modifications recorded within "
            f"{config.get('burst_window_seconds', 5.0)} seconds (threshold: {mod_thresh})."
        )

    # Rule 4: Excessive Event Velocity
    if metrics["velocity"] >= velocity_thresh:
        triggers["excessive_velocity"] = True
        reasons.append(
            f"Abnormal event velocity: {metrics['velocity']} events/sec exceeding normal user baseline "
            f"threshold ({round(velocity_thresh, 1)} events/sec)."
        )

    # Rule 5: Multi-Factor Attack Combination
    triggered_count = sum([triggers["rename_burst"], triggers["suspicious_extension"], triggers["modification_burst"]])
    if triggered_count >= 2:
        triggers["multi_factor_anomaly"] = True
        reasons.append(
            "Compound behavioral anomaly: Multiple simultaneous threat indicators detected, strongly correlating "
            "with active automated encryption behavior."
        )

    return reasons, triggers
