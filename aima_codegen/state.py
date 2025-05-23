"""State persistence management.
Implements spec_v5.1.md Section 5.2 - Global Project State
"""
import os
import json
import logging
from pathlib import Path
from typing import Optional
import tempfile

from .models import ProjectState

logger = logging.getLogger(__name__)

class StateManager:
    """Manages project state persistence with atomic updates."""
    
    def __init__(self, project_path: Path):
        self.project_path = project_path
        self.state_file = project_path / "project_state.json"
    
    def save(self, state: ProjectState):
        """Save state atomically using temp file + rename.
        Implements spec_v5.1.md Section 5.2 - Atomic Updates
        """
        # Create temp file in same directory for atomic rename
        temp_fd, temp_path = tempfile.mkstemp(
            dir=self.project_path,
            prefix=".project_state_",
            suffix=".tmp"
        )
        
        try:
            # Write to temp file
            with os.fdopen(temp_fd, 'w') as f:
                json.dump(state.model_dump(), f, indent=2, default=str)
            
            # Atomic rename
            os.rename(temp_path, self.state_file)
            logger.debug(f"State saved to {self.state_file}")
            
        except Exception as e:
            # Clean up temp file on error
            if os.path.exists(temp_path):
                os.unlink(temp_path)
            raise RuntimeError(f"Failed to save state: {e}")
    
    def load(self) -> Optional[ProjectState]:
        """Load project state from file."""
        if not self.state_file.exists():
            return None
        
        try:
            with open(self.state_file, 'r') as f:
                data = json.load(f)
            return ProjectState(**data)
        except Exception as e:
            logger.error(f"Failed to load state: {e}")
            raise RuntimeError(
                f"ERROR: Failed to load project state from '{self.state_file}'. "
                f"Error: {e}"
            )
    
    def exists(self) -> bool:
        """Check if state file exists."""
        return self.state_file.exists()