"""Tests for state management."""
import pytest
import json
import tempfile
from pathlib import Path
from datetime import datetime

from aima_codegen.state import StateManager
from aima_codegen.models import ProjectState, Waypoint


class TestStateManager:
    """Test suite for state persistence."""
    
    @pytest.fixture
    def temp_dir(self):
        """Create temporary directory for tests."""
        with tempfile.TemporaryDirectory() as tmpdir:
            yield Path(tmpdir)
    
    @pytest.fixture
    def project_state(self):
        """Create sample project state."""
        return ProjectState(
            project_name="Test Project",
            project_slug="test-project",
            total_budget_usd=50.0,
            current_spent_usd=5.25,
            initial_prompt="Create a calculator",
            venv_path="/tmp/test-project/.venv",
            python_path="/usr/bin/python3",
            waypoints=[
                Waypoint(
                    id="wp_001",
                    description="Create calculator module",
                    agent_type="CodeGen",
                    status="SUCCESS"
                ),
                Waypoint(
                    id="wp_002",
                    description="Write tests",
                    agent_type="TestWriter",
                    status="PENDING"
                )
            ]
        )
    
    def test_save_state(self, temp_dir, project_state):
        """Test saving project state."""
        manager = StateManager(temp_dir)
        manager.save(project_state)
        
        # Check file exists
        state_file = temp_dir / "project_state.json"
        assert state_file.exists()
        
        # Verify content
        with open(state_file) as f:
            data = json.load(f)
        
        assert data["project_name"] == "Test Project"
        assert data["project_slug"] == "test-project"
        assert data["total_budget_usd"] == 50.0
        assert data["current_spent_usd"] == 5.25
        assert len(data["waypoints"]) == 2
    
    def test_load_state(self, temp_dir, project_state):
        """Test loading project state."""
        manager = StateManager(temp_dir)
        
        # Save first
        manager.save(project_state)
        
        # Load and verify
        loaded_state = manager.load()
        
        assert loaded_state is not None
        assert loaded_state.project_name == project_state.project_name
        assert loaded_state.total_budget_usd == project_state.total_budget_usd
        assert len(loaded_state.waypoints) == 2
        assert loaded_state.waypoints[0].id == "wp_001"
        assert loaded_state.waypoints[0].status == "SUCCESS"
    
    def test_load_nonexistent_state(self, temp_dir):
        """Test loading when state file doesn't exist."""
        manager = StateManager(temp_dir)
        loaded_state = manager.load()
        assert loaded_state is None
    
    def test_atomic_save(self, temp_dir, project_state):
        """Test atomic save with temp file."""
        manager = StateManager(temp_dir)
        state_file = temp_dir / "project_state.json"
        
        # Create initial state
        manager.save(project_state)
        initial_mtime = state_file.stat().st_mtime
        
        # Modify and save again
        project_state.current_spent_usd = 10.0
        manager.save(project_state)
        
        # Verify file was replaced (mtime changed)
        assert state_file.stat().st_mtime != initial_mtime
        
        # Verify content updated
        loaded = manager.load()
        assert loaded.current_spent_usd == 10.0
    
    def test_save_error_cleanup(self, temp_dir, project_state):
        """Test temp file cleanup on save error."""
        manager = StateManager(temp_dir)
        
        # Make directory read-only to cause save error
        import os
        os.chmod(temp_dir, 0o555)
        
        try:
            with pytest.raises(RuntimeError):
                manager.save(project_state)
            
            # Verify no temp files left behind
            temp_files = list(temp_dir.glob(".project_state_*.tmp"))
            assert len(temp_files) == 0
        finally:
            # Restore permissions
            os.chmod(temp_dir, 0o755)