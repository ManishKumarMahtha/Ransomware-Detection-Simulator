"""
Safe Simulation Engine for Ransomware Detection Simulator.
Strictly confined to the dedicated sandbox directory.
Simulates benign user operations or suspicious ransomware attacks for educational demonstrations.
"""

import os
import time
import shutil
import logging
import threading
from collections import deque
from pathlib import Path
from config import SANDBOX_DIR, is_safe_sandbox_path
from simulation.synthetic_events import DUMMY_BENIGN_FILES, SIMULATED_CIPHER_TEXT, SIMULATED_RANSOM_NOTE

logger = logging.getLogger(__name__)


class SimulationEngine:
    """
    Stateful background engine that executes synthetic file operations in the sandbox.
    Supports Benign, Ransomware Burst, Stealth, and Extension Tampering profiles.
    """
    def __init__(self):
        self.state = "IDLE"  # "IDLE", "RUNNING", "PAUSED", "STOPPED"
        self.current_profile = "none"
        self.speed_multiplier = 1.0
        self.progress_percent = 0
        self.total_steps = 0
        self.current_step = 0
        self.logs = deque(maxlen=200)
        self.event_callback = None  # Hook to notify detection engine of events

        self._stop_event = threading.Event()
        self._pause_event = threading.Event()
        self._thread = None
        self._lock = threading.Lock()

        # Ensure sandbox exists
        SANDBOX_DIR.mkdir(parents=True, exist_ok=True)

    def set_event_callback(self, callback):
        """Registers a listener for file events generated during simulation."""
        self.event_callback = callback

    def _log(self, level: str, message: str):
        """Appends a timestamped log to the simulation terminal feed."""
        timestamp = time.strftime("%H:%M:%S")
        entry = {
            "timestamp": timestamp,
            "level": level.upper(),
            "message": message
        }
        self.logs.append(entry)

    def _emit_event(self, event_type: str, file_path: str, old_path: str = None, details: str = ""):
        """Notifies the callback and logs the event."""
        if self.event_callback:
            try:
                self.event_callback(event_type, file_path, old_path, details)
            except Exception as e:
                logger.error(f"Error in event callback: {e}")

    def _wait_step(self, base_delay: float):
        """Handles pause and variable speed delays safely."""
        delay = max(0.05, base_delay / max(0.1, self.speed_multiplier))
        steps = int(delay / 0.05)
        for _ in range(max(1, steps)):
            if self._stop_event.is_set():
                return False
            while self._pause_event.is_set():
                if self._stop_event.is_set():
                    return False
                time.sleep(0.1)
            time.sleep(0.05)
        return not self._stop_event.is_set()

    def start(self, profile: str = "benign", speed: float = 1.0) -> tuple[bool, str]:
        """Starts a simulation run if not already active."""
        with self._lock:
            if self.state == "RUNNING":
                return False, "A simulation is already actively running. Stop or reset it first."

            self.current_profile = profile.lower()
            self.speed_multiplier = max(0.2, min(5.0, float(speed)))
            self.progress_percent = 0
            self.current_step = 0
            self._stop_event.clear()
            self._pause_event.clear()
            self.state = "RUNNING"
            self._log("INFO", f"Initiating '{self.current_profile}' simulation with speed {self.speed_multiplier}x.")

            self._thread = threading.Thread(target=self._run_simulation, daemon=True)
            self._thread.start()
            return True, f"Simulation '{profile}' started successfully."

    def pause(self) -> tuple[bool, str]:
        """Pauses the current simulation."""
        with self._lock:
            if self.state != "RUNNING":
                return False, f"Cannot pause: simulator is in {self.state} state."
            self._pause_event.set()
            self.state = "PAUSED"
            self._log("WARN", "Simulation execution paused by operator.")
            return True, "Simulation paused."

    def resume(self) -> tuple[bool, str]:
        """Resumes a paused simulation."""
        with self._lock:
            if self.state != "PAUSED":
                return False, f"Cannot resume: simulator is in {self.state} state."
            self._pause_event.clear()
            self.state = "RUNNING"
            self._log("INFO", "Simulation execution resumed.")
            return True, "Simulation resumed."

    def stop(self) -> tuple[bool, str]:
        """Stops the active simulation."""
        with self._lock:
            if self.state in ("IDLE", "STOPPED"):
                return False, "Simulator is already stopped or idle."
            self._stop_event.set()
            self._pause_event.clear()
            self.state = "STOPPED"
            self._log("WARN", "Simulation stopped by operator or automated mitigation.")
            return True, "Simulation halted."

    def reset(self) -> tuple[bool, str]:
        """Safely cleans dummy files inside sandbox and resets state."""
        self.stop()
        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=1.0)

        with self._lock:
            try:
                # Strictly sanitize sandbox: remove only files inside sandbox dir
                for item in SANDBOX_DIR.iterdir():
                    if is_safe_sandbox_path(item):
                        if item.is_file() or item.is_symlink():
                            item.unlink()
                        elif item.is_dir():
                            shutil.rmtree(item)

                self.state = "IDLE"
                self.progress_percent = 0
                self.current_step = 0
                self.total_steps = 0
                self.logs.clear()
                self._log("INFO", "Sandbox sanitized. All dummy simulation files safely purged.")
                return True, "Sandbox reset successfully. Ready for new demonstration."
            except Exception as e:
                return False, f"Error resetting sandbox: {str(e)}"

    def get_status(self) -> dict:
        """Returns the current state and telemetry for UI polling."""
        return {
            "state": self.state,
            "profile": self.current_profile,
            "speed": self.speed_multiplier,
            "progress_percent": self.progress_percent,
            "current_step": self.current_step,
            "total_steps": self.total_steps,
            "sandbox_path": str(SANDBOX_DIR),
            "files_in_sandbox": [f.name for f in SANDBOX_DIR.iterdir() if f.is_file()],
            "logs": list(self.logs)
        }

    # =========================================================================
    # SIMULATION PROFILES WORKFLOW
    # =========================================================================
    def _run_simulation(self):
        """Worker executing selected profile."""
        try:
            # First ensure sandbox has clean initial dummy files
            self._populate_initial_files()

            if self.current_profile == "benign":
                self._run_benign_profile()
            elif self.current_profile == "ransomware_burst":
                self._run_ransomware_burst_profile()
            elif self.current_profile == "stealth":
                self._run_stealth_profile()
            elif self.current_profile == "extension_tampering":
                self._run_extension_tampering_profile()
            else:
                self._log("ERROR", f"Unknown profile: {self.current_profile}")

        except Exception as e:
            self._log("ERROR", f"Simulation error: {str(e)}")
            logger.error(f"Simulation execution failure: {e}", exc_info=True)
        finally:
            with self._lock:
                if self.state == "RUNNING":
                    self.state = "STOPPED"
                    self.progress_percent = 100
                    self._log("INFO", "Simulation completed.")

    def _populate_initial_files(self):
        """Populates sandbox with baseline benign documents."""
        self._log("INFO", "Staging initial benign user documents in sandbox directory...")
        for filename, content in DUMMY_BENIGN_FILES:
            target = SANDBOX_DIR / filename
            if not is_safe_sandbox_path(target):
                continue
            with open(target, "w", encoding="utf-8") as f:
                f.write(content)
            self._emit_event("CREATE", str(target), details="Staging baseline dummy file")
        time.sleep(0.3)

    def _run_benign_profile(self):
        """Normal user activity: slow, paced modifications and benign renames."""
        self._log("INFO", "Executing Benign User Profile: Normal human typing speed, low velocity.")
        actions = [
            ("MODIFY", "annual_budget_2026.xlsx.txt", "\n[Edit by Analyst]: Added revised Q2 marketing estimate."),
            ("MODIFY", "research_paper_draft.docx.txt", "\n[Edit by Author]: Updated references section with IEEE standards."),
            ("RENAME", "research_paper_draft.docx.txt", "research_paper_final.docx.txt"),
            ("CREATE", "meeting_notes_today.txt", "Attendees: Team Lead, Developer, Reviewer.\nDiscussion: Graduation project defense demo."),
            ("MODIFY", "meeting_notes_today.txt", "\nAction items assigned."),
            ("MODIFY", "source_code_main.py.txt", "\n# Code inspection completed."),
            ("DELETE", "meeting_notes_today.txt", "")
        ]
        self.total_steps = len(actions)

        for i, action in enumerate(actions, 1):
            if not self._wait_step(1.5):
                break
            self.current_step = i
            self.progress_percent = int((i / self.total_steps) * 100)

            act_type, target_name, data = action
            target_path = SANDBOX_DIR / target_name

            if not is_safe_sandbox_path(target_path):
                continue

            if act_type == "MODIFY" and target_path.exists():
                with open(target_path, "a", encoding="utf-8") as f:
                    f.write(data)
                self._emit_event("MODIFY", str(target_path), details="Benign user content update")
                self._log("INFO", f"[Normal User Activity] Appended data to {target_name}")

            elif act_type == "RENAME" and target_path.exists():
                new_path = SANDBOX_DIR / data
                if is_safe_sandbox_path(new_path):
                    target_path.rename(new_path)
                    self._emit_event("RENAME", str(new_path), old_path=str(target_path), details="Benign document rename")
                    self._log("INFO", f"[Normal User Activity] Renamed {target_name} -> {data}")

            elif act_type == "CREATE":
                with open(target_path, "w", encoding="utf-8") as f:
                    f.write(data)
                self._emit_event("CREATE", str(target_path), details="User created standard text file")
                self._log("INFO", f"[Normal User Activity] Created {target_name}")

            elif act_type == "DELETE" and target_path.exists():
                target_path.unlink()
                self._emit_event("DELETE", str(target_path), details="User deleted temporary file")
                self._log("INFO", f"[Normal User Activity] Deleted {target_name}")

    def _run_ransomware_burst_profile(self):
        """Simulates rapid encryption burst: fast file tampering and mass renaming to .locked."""
        self._log("WARN", "EXECUTING RANSOMWARE BURST SIMULATION: High-velocity synthetic tampering initiated!")
        files = [f for f in SANDBOX_DIR.iterdir() if f.is_file() and not f.name.endswith(".locked")]
        self.total_steps = len(files) * 2 + 1

        step = 0
        # Phase 1: Rapid Simulated Modification (simulating in-place encryption overwrite)
        for f in files:
            if not self._wait_step(0.12):  # Fast bursts
                return
            step += 1
            self.current_step = step
            self.progress_percent = int((step / self.total_steps) * 100)

            if not is_safe_sandbox_path(f):
                continue

            try:
                with open(f, "w", encoding="utf-8") as file_handle:
                    file_handle.write(SIMULATED_CIPHER_TEXT)
                self._emit_event("MODIFY", str(f), details="Simulated high-entropy cipher write")
                self._log("WARN", f"[Rapid Modification Burst] Overwrote {f.name} with simulated ciphertext")
            except Exception as e:
                self._log("ERROR", f"Error modifying {f.name}: {e}")

        # Phase 2: Rapid Renaming to .locked extension
        for f in files:
            if not self._wait_step(0.15):
                return
            step += 1
            self.current_step = step
            self.progress_percent = int((step / self.total_steps) * 100)

            if not is_safe_sandbox_path(f) or not f.exists():
                continue

            try:
                locked_name = f.name + ".locked"
                new_path = SANDBOX_DIR / locked_name
                if is_safe_sandbox_path(new_path):
                    f.rename(new_path)
                    self._emit_event("RENAME", str(new_path), old_path=str(f), details="Renamed to ransomware extension .locked")
                    self._log("ALERT", f"[Extension Tampering] Renamed {f.name} -> {locked_name}")
            except Exception as e:
                self._log("ERROR", f"Error renaming {f.name}: {e}")

        # Phase 3: Drop synthetic ransom note
        if self._wait_step(0.2):
            note_path = SANDBOX_DIR / "README_RESTORE_FILES_DEMO.txt"
            if is_safe_sandbox_path(note_path):
                with open(note_path, "w", encoding="utf-8") as f:
                    f.write(SIMULATED_RANSOM_NOTE)
                self._emit_event("CREATE", str(note_path), details="Dropped simulated ransom demand note")
                self._log("ALERT", "[Attack Artifact] Dropped README_RESTORE_FILES_DEMO.txt")

    def _run_stealth_profile(self):
        """Simulates slow drip stealth ransomware: spaced operations to evade naive thresholds."""
        self._log("WARN", "Executing Stealth Ransomware Simulation: Lower velocity, spaced intervals.")
        files = [f for f in SANDBOX_DIR.iterdir() if f.is_file() and not f.name.endswith(".enc")]
        self.total_steps = len(files)

        for i, f in enumerate(files, 1):
            if not self._wait_step(0.9):  # 0.9s delay
                return
            self.current_step = i
            self.progress_percent = int((i / self.total_steps) * 100)

            if not is_safe_sandbox_path(f) or not f.exists():
                continue

            try:
                # Modify
                with open(f, "w", encoding="utf-8") as fh:
                    fh.write(SIMULATED_CIPHER_TEXT)
                self._emit_event("MODIFY", str(f), details="Stealth simulated ciphertext write")

                # Rename to .enc
                new_path = SANDBOX_DIR / (f.name + ".enc")
                if is_safe_sandbox_path(new_path):
                    f.rename(new_path)
                    self._emit_event("RENAME", str(new_path), old_path=str(f), details="Renamed to stealth extension .enc")
                    self._log("WARN", f"[Stealth Encryption] Renamed {f.name} -> {new_path.name}")
            except Exception as e:
                self._log("ERROR", f"Error in stealth step: {e}")

    def _run_extension_tampering_profile(self):
        """Bursts of rapid extension renaming to .crypto and .crypted."""
        self._log("ALERT", "Executing Rapid Extension Tampering Profile.")
        files = [f for f in SANDBOX_DIR.iterdir() if f.is_file()]
        self.total_steps = len(files)

        for i, f in enumerate(files, 1):
            if not self._wait_step(0.2):
                return
            self.current_step = i
            self.progress_percent = int((i / self.total_steps) * 100)

            if not is_safe_sandbox_path(f) or not f.exists():
                continue

            target_ext = ".crypto" if i % 2 == 0 else ".crypted"
            new_path = SANDBOX_DIR / (f.name + target_ext)
            if is_safe_sandbox_path(new_path):
                f.rename(new_path)
                self._emit_event("RENAME", str(new_path), old_path=str(f), details=f"Bulk rename to {target_ext}")
                self._log("ALERT", f"[Mass Rename] {f.name} -> {new_path.name}")


# Global singleton instance
simulator = SimulationEngine()
