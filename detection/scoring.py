"""
Threat Scoring Engine for Ransomware Detection Simulator.
Calculates a transparent, explainable threat score from 0 to 100 with clear mathematical attribution.
"""

from detection.rules import evaluate_rules


def calculate_threat_score(metrics: dict, config: dict, ml_result: dict = None) -> dict:
    """
    Computes an explainable threat score (0-100) based on weighted heuristic behavioral indicators.
    
    Formula:
        Score = min(100, Rename_Contribution + Extension_Contribution + Burst_Contribution + Velocity_Bonus)
    """
    rename_weight = float(config.get("rename_weight", 35.0))
    ext_weight = float(config.get("extension_weight", 40.0))
    burst_weight = float(config.get("burst_weight", 25.0))

    rename_thresh = max(1, int(config.get("rename_threshold", 4)))
    mod_thresh = max(1, int(config.get("modification_threshold", 6)))
    velocity_thresh = max(1.0, float(config.get("total_event_threshold", 10)) / float(config.get("burst_window_seconds", 5.0)))

    # 1. Rename Component (up to rename_weight)
    rename_ratio = min(1.0, metrics["renames_count"] / rename_thresh)
    rename_score = round(rename_ratio * rename_weight, 1)

    # 2. Suspicious Extension Component (up to ext_weight)
    # Even 1 suspicious extension change is highly abnormal in benign workloads
    if metrics["suspicious_ext_count"] == 0:
        ext_score = 0.0
    elif metrics["suspicious_ext_count"] == 1:
        ext_score = round(ext_weight * 0.7, 1)
    else:
        ext_score = ext_weight

    # 3. Modification Burst Component (up to burst_weight)
    mod_ratio = min(1.0, metrics["modifications_count"] / mod_thresh)
    burst_score = round(mod_ratio * burst_weight, 1)

    # 4. Event Velocity Factor (bonus up to 10 points)
    vel_ratio = min(1.0, metrics["velocity"] / velocity_thresh)
    velocity_score = round(vel_ratio * 10.0, 1) if vel_ratio > 0.8 else 0.0

    raw_heuristic_score = rename_score + ext_score + burst_score + velocity_score
    total_score = min(100, int(round(raw_heuristic_score)))

    # If ML prediction is available and enabled, factor in ML confidence
    ml_bonus = 0
    if ml_result and ml_result.get("enabled"):
        if ml_result.get("is_ransomware") and ml_result.get("confidence", 0) > 0.75:
            # If heuristic is on the borderline, ML model provides confidence adjustment
            if total_score < 40 and (metrics["renames_count"] > 1 or metrics["suspicious_ext_count"] > 0):
                ml_bonus = 15
                total_score = min(100, total_score + ml_bonus)

    # Determine Severity Level
    if total_score >= 80:
        severity = "CRITICAL"
    elif total_score >= 60:
        severity = "HIGH"
    elif total_score >= 30:
        severity = "MEDIUM"
    else:
        severity = "LOW"

    # Evaluate Human-Readable Explanations
    reasons, triggers = evaluate_rules(metrics, config)

    # Create explicit mathematical formula string for viva / demo display
    formula_str = (
        f"Score = min(100, Rename[{rename_score}/{rename_weight}] + "
        f"Extension[{ext_score}/{ext_weight}] + "
        f"Burst[{burst_score}/{burst_weight}] + "
        f"Velocity[{velocity_score}/10]"
        f"{f' + ML_Boost[{ml_bonus}]' if ml_bonus else ''}) "
        f"= {total_score} -> {severity}"
    )

    if not reasons and total_score < 30:
        reasons.append("File activity within benign baseline parameters. No anomalous encryption indicators observed.")

    return {
        "threat_score": total_score,
        "severity": severity,
        "is_flagged": total_score >= 30,
        "reasons": reasons,
        "triggers": triggers,
        "breakdown": {
            "rename_score": rename_score,
            "extension_score": ext_score,
            "burst_score": burst_score,
            "velocity_score": velocity_score,
            "ml_bonus": ml_bonus,
            "raw_sum": raw_heuristic_score,
            "formula_string": formula_str
        },
        "metrics": metrics
    }
