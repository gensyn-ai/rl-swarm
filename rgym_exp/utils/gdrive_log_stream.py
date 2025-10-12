"""
Real-time log streaming to Google Drive.

This module provides utilities to stream stdout/stderr logs to Google Drive
in real-time, ensuring logs are preserved even if the process crashes or
the Colab session disconnects.
"""

import os
import sys
import threading
import time
from typing import IO, Optional


class TeeStream:
    """
    Stream that writes to multiple destinations simultaneously.

    Writes to both console and a file, with periodic flushing to ensure
    data is saved even if the process terminates unexpectedly.
    """

    def __init__(self, console_stream: IO, file_path: str, flush_interval: float = 30.0):
        """
        Initialize TeeStream.

        Args:
            console_stream: Original stream (sys.stdout or sys.stderr)
            file_path: Path to log file in Google Drive
            flush_interval: Seconds between auto-flushes (default 30s)
        """
        self.console = console_stream
        self.file_path = file_path
        self.flush_interval = flush_interval

        # Create directory if needed
        os.makedirs(os.path.dirname(file_path), exist_ok=True)

        # Open file in append mode with line buffering
        self.file = open(file_path, 'a', buffering=1)

        # Track last flush time
        self.last_flush = time.time()

    def write(self, message: str):
        """Write message to both console and file."""
        # Write to console
        self.console.write(message)

        # Write to file
        self.file.write(message)

        # Auto-flush if interval elapsed
        if time.time() - self.last_flush >= self.flush_interval:
            self.flush()

    def flush(self):
        """Flush both console and file buffers."""
        self.console.flush()
        self.file.flush()
        os.fsync(self.file.fileno())  # Force write to disk
        self.last_flush = time.time()

    def close(self):
        """Close the file stream."""
        self.flush()
        self.file.close()

    def fileno(self):
        """Return file descriptor (required for some Python internals)."""
        return self.console.fileno()

    def isatty(self):
        """Check if connected to terminal."""
        return self.console.isatty()


class GDriveLogStreamer:
    """
    Manages real-time streaming of logs to Google Drive.

    Redirects stdout/stderr to write to both console and GDrive files,
    with periodic background flushing to ensure logs are saved.
    """

    def __init__(
        self,
        log_dir: str,
        flush_interval: float = 30.0,
        background_flush: bool = True
    ):
        """
        Initialize log streamer.

        Args:
            log_dir: Directory in Google Drive for logs
            flush_interval: Seconds between flushes (default 30s)
            background_flush: Enable background flush thread (default True)
        """
        self.log_dir = log_dir
        self.flush_interval = flush_interval
        self.background_flush = background_flush

        # Create log directory
        os.makedirs(log_dir, exist_ok=True)

        # Save original streams
        self.original_stdout = sys.stdout
        self.original_stderr = sys.stderr

        # Create tee streams
        self.stdout_tee = TeeStream(
            self.original_stdout,
            os.path.join(log_dir, 'stdout.log'),
            flush_interval
        )
        self.stderr_tee = TeeStream(
            self.original_stderr,
            os.path.join(log_dir, 'stderr.log'),
            flush_interval
        )

        # Replace sys streams
        sys.stdout = self.stdout_tee
        sys.stderr = self.stderr_tee

        # Background flush thread
        self.flush_thread: Optional[threading.Thread] = None
        self.stop_flushing = threading.Event()

        if background_flush:
            self._start_flush_thread()

        print(f"📝 Log streaming enabled: {log_dir}")
        print(f"   Flushing every {flush_interval}s to Google Drive")

    def _start_flush_thread(self):
        """Start background thread for periodic flushing."""
        def flush_loop():
            while not self.stop_flushing.is_set():
                time.sleep(self.flush_interval)
                if not self.stop_flushing.is_set():
                    self.flush()

        self.flush_thread = threading.Thread(target=flush_loop, daemon=True)
        self.flush_thread.start()

    def flush(self):
        """Manually flush all streams."""
        self.stdout_tee.flush()
        self.stderr_tee.flush()

    def close(self):
        """Stop streaming and restore original streams."""
        # Stop background thread
        if self.flush_thread:
            self.stop_flushing.set()
            self.flush_thread.join(timeout=5.0)

        # Final flush
        self.flush()

        # Restore original streams
        sys.stdout = self.original_stdout
        sys.stderr = self.original_stderr

        # Close tee streams
        self.stdout_tee.close()
        self.stderr_tee.close()

        print(f"📝 Log streaming stopped: {self.log_dir}")

    def __enter__(self):
        """Context manager entry."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.close()


def setup_log_streaming(
    gdrive_path: str,
    experiment_name: str,
    node_id: str,
    flush_interval: float = 30.0
) -> GDriveLogStreamer:
    """
    Convenience function to set up log streaming.

    Args:
        gdrive_path: Base Google Drive path
        experiment_name: Experiment name
        node_id: Node identifier
        flush_interval: Seconds between flushes

    Returns:
        GDriveLogStreamer instance
    """
    log_dir = os.path.join(gdrive_path, 'experiments', experiment_name, 'logs', node_id)
    return GDriveLogStreamer(log_dir, flush_interval, background_flush=True)
