"""
Safe File System Monitoring Module using Python Watchdog.
Monitors a user-selected test directory safely without reading file contents or traversing forbidden paths.
"""

import time
import logging
import threading
from collections import deque
from pathlib import Path

try:
    from watchdog.observers import Observer
    from watchdog.events import FileSystemEventHandler
    WATCHDOG_AVAILABLE = True
except ImportError:
    WATCHDOG_AVAILABLE = False
    FileSystemEventHandler = object

from config import validate_monitoring_path, SANDBOX_DIR

logger = logging.getLogger(__name__)


class SafeWatchdogHandler(FileSystemEventHandler):
    """
    Handles file system events from watchdog without inspecting file contents.
    Dispatches events to the monitor's callback.
    """
    def __init__(self, callback):
        super().__init__()
        self.callback = callback

    def on_created(self, event):
        if not event.is_directory:
            self.callback("CREATE", event.src_path)

    def on_modified(self, event):
        if not event.is_directory:
            self.callback("MODIFY", event.src_path)

    def on_deleted(self, event):
        if not event.is_directory:
            self.callback("DELETE", event.src_path)

    def on_moved(self, event):
        if not event.is_directory:
            self.callback("RENAME", event.dest_path, old_path=event.src_path)


class DirectoryMonitor:
    """
    Safe file monitor that observes directory changes using Python Watchdog.
    Prevents unauthorized path monitoring and directory traversal.
    """
    def __init__(self):
        self.is_monitoring = False
        self.monitored_path = str(SANDBOX_DIR)
        self.observer = None
        self.event_callback = None
        self.event_count = 0
        self.start_time = None
        self.recent_events = deque(maxlen=100)
        self._lock = threading.Lock()

    def set_event_callback(self, callback):
        """Sets callback function for event dispatching."""
        self.event_callback = callback

    def _handle_event(self, event_type: str, file_path: str, old_path: str = None):
        """Dispatches event to callback and records metadata."""
        with self._lock:
            self.event_count += 1
            entry = {
                "timestamp": time.strftime("%H:%M:%S"),
                "event_type": event_type,
                "file_name": Path(file_path).name,
                "path": file_path,
                "old_name": Path(old_path).name if old_path else None
            }
            self.recent_events.append(entry)

        if self.event_callback:
            try:
                self.event_callback(event_type, file_path, old_path, details=f"Watchdog OS Event: {event_type}")
            except Exception as e:
                logger.error(f"Error handling watchdog event: {e}")

    def start_monitoring(self, directory_path: str = None) -> tuple[bool, str]:
        """
        Validates target path and starts Watchdog observer.
        """
        if not WATCHDOG_AVAILABLE:
            return False, "Watchdog library is not available in the current environment."

        with self._lock:
            if self.is_monitoring:
                return False, f"Monitoring is already active on {self.monitored_path}. Stop it first."

            target = directory_path or str(SANDBOX_DIR)
            is_valid, reason = validate_monitoring_path(target)
            if not is_valid:
                return False, f"Monitoring path rejected: {reason}"

            try:
                self.monitored_path = str(Path(target).resolve())
                self.observer = Observer()
                handler = SafeWatchdogHandler(self._handle_event)
                self.observer.schedule(handler, path=self.monitored_path, recursive=False)
                self.observer.start()

                self.is_monitoring = True
                self.start_time = time.time()
                self.event_count = 0
                return True, f"Started monitoring safe directory: {self.monitored_path}"
            except Exception as e:
                logger.error(f"Failed to start watchdog observer: {e}")
                self.is_monitoring = False
                return False, f"Failed to initialize observer: {str(e)}"

    def stop_monitoring(self) -> tuple[bool, str]:
        """Stops the active Watchdog observer."""
        with self._lock:
            if not self.is_monitoring or not self.observer:
                return False, "File monitoring is not currently active."

            try:
                self.observer.stop()
                self.observer.join(timeout=1.0)
                self.observer = None
                self.is_monitoring = False
                return True, f"Stopped monitoring on {self.monitored_path}"
            except Exception as e:
                logger.error(f"Error stopping observer: {e}")
                return False, f"Error stopping observer: {str(e)}"

    def get_status(self) -> dict:
        """Returns monitoring metrics for UI polling."""
        with self._lock:
            uptime = int(time.time() - self.start_time) if (self.is_monitoring and self.start_time) else 0
            return {
                "is_monitoring": self.is_monitoring,
                "monitored_path": self.monitored_path,
                "default_sandbox_path": str(SANDBOX_DIR),
                "event_count": self.event_count,
                "uptime_seconds": uptime,
                "recent_events": list(self.recent_events)
            }


# Global singleton instance
file_monitor = DirectoryMonitor()
