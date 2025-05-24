"""Utility functions for AIMA CodeGen."""
import re
import os
import signal
import sys
import logging
import json
from pathlib import Path
from typing import Optional
from datetime import datetime, timezone
import subprocess
import importlib

logger = logging.getLogger(__name__)

def slugify(text: str) -> str:
    """Convert text to filesystem-safe slug."""
    # Remove non-alphanumeric characters and replace with hyphens
    slug = re.sub(r'[^\w\s-]', '', text.lower())
    slug = re.sub(r'[-\s]+', '-', slug)
    return slug.strip('-')

def setup_signal_handler(cleanup_func):
    """Setup SIGINT and SIGTERM handlers for graceful shutdown.
    Implements spec_v5.1.md Section 3.8 - Graceful Shutdown
    """
    def signal_handler(signum, frame):
        logger.info("Ctrl+C detected, attempting graceful shutdown...")
        try:
            cleanup_func()
            print("Shutdown complete. Project state saved.")
        except Exception as e:
            logger.error(f"Error during shutdown: {e}")
        sys.exit(0)
    
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

def check_lock_file(lock_path: Path, project_name: str) -> bool:
    """Check if project is locked by another process.
    Implements spec_v5.1.md Section 3.7 - Concurrency Prevention
    Returns True if OK to proceed, False if locked.
    """
    if not lock_path.exists():
        return True
    
    try:
        # Read lock file
        content = lock_path.read_text().strip().split('\n')
        if len(content) < 2:
            # Malformed lock file
            print(f"ERROR: Project '{project_name}' appears to have been shut down incorrectly "
                  f"(stale lock file found). Suggestion: Manually remove the file at "
                  f"'{lock_path}' if you are sure no other process is running.")
            return False
        
        pid_str = content[0]
        timestamp = content[1]
        pid = int(pid_str)
        
        # Check if process exists using psutil
        try:
            import psutil
            if psutil.pid_exists(pid):
                print(f"ERROR: Project '{project_name}' is currently being worked on by "
                      f"process {pid}. Suggestion: Please close the other instance.")
                return False
            else:
                # Stale lock
                print(f"ERROR: Project '{project_name}' appears to have been shut down "
                      f"incorrectly (stale lock file found). Suggestion: Manually remove "
                      f"the file at '{lock_path}' if you are sure no other process is running.")
                return False
                
        except ImportError:
            # Fallback to os.kill
            logger.warning("WARNING: psutil check failed. Falling back to os.kill. "
                         "This may be less reliable on non-Unix systems or with PID reuse. "
                         "Error: ImportError")
            try:
                os.kill(pid, 0)
                # Process exists
                print(f"ERROR: Project '{project_name}' is currently being worked on by "
                      f"process {pid}. Suggestion: Please close the other instance.")
                return False
            except OSError as e:
                if e.errno == 3:  # ESRCH - No such process
                    # Stale lock
                    print(f"ERROR: Project '{project_name}' appears to have been shut down "
                          f"incorrectly (stale lock file found). Suggestion: Manually remove "
                          f"the file at '{lock_path}' if you are sure no other process is running.")
                    return False
                else:
                    # Process exists or permission error
                    print(f"ERROR: Project '{project_name}' is currently being worked on by "
                          f"process {pid}. Suggestion: Please close the other instance.")
                    return False
                    
    except Exception as e:
        # Fatal error
        print("FATAL_ERROR: Cannot verify lock file due to psutil and os.kill failure. "
              "Suggestion: Manually verify no other process is running.")
        return False

def create_lock_file(lock_path: Path):
    """Create lock file with PID and timestamp.
    Implements spec_v5.1.md Section 3.7
    """
    pid = str(os.getpid())
    # RFC 3339 format
    timestamp = datetime.now(timezone.utc).isoformat()
    lock_path.write_text(f"{pid}\n{timestamp}")

def remove_lock_file(lock_path: Path):
    """Remove lock file if it exists."""
    if lock_path.exists():
        lock_path.unlink()

def validate_self_improvement(project_path: Path) -> bool:
    """Validate self-improvement changes before applying."""
    if not (project_path / "SELF_IMPROVEMENT_MODE").exists():
        return True  # Normal project

    # Run existing tests
    result = subprocess.run(
        ["python", "-m", "pytest", "aima_codegen/tests/", "-v"],
        capture_output=True,
        text=True
    )

    if result.returncode != 0:
        logger.error("Self-improvement broke existing tests!")
        return False

    # Check for obvious breaks
    try:
        # Try importing the package
        import aima_codegen
        importlib.reload(aima_codegen)
        return True
    except Exception as e:
        logger.error(f"Self-improvement broke imports: {e}")
        return False