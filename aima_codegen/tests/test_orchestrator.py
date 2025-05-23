"""Tests for the Orchestrator component.
Tests spec_v5.1.md critical paths including waypoint execution, revision loops, and state management.
"""
import pytest
from unittest.mock import Mock, patch, MagicMock
from pathlib import Path
import tempfile
import shutil
import json

from aima_codegen.orchestrator import Orchestrator
from aima_codegen.models import ProjectState, Waypoint, RevisionFeedback, LLMResponse
from aima_codegen.exceptions import ToolingError, BudgetExceededError, LLMOutputError


class TestOrchestrator:
    """Test suite for Orchestrator functionality."""
    
    @pytest.fixture
    def temp_dir(self):
        """Create a temporary directory for tests."""
        temp_dir = tempfile.mkdtemp()
        yield Path(temp_dir)
        shutil.rmtree(temp_dir)
    
    @pytest.fixture
    def mock_config(self):
        """Mock configuration."""
        config = Mock()
        config.get.return_value = "test_value"
        config.config_path = Path("/tmp/test_config.ini")
        config.model_costs_path = Path("/tmp/test_model_costs.json")
        return config
    
    @pytest.fixture
    def orchestrator(self, mock_config):
        """Create orchestrator instance with mocked config."""
        with patch('aima_codegen.orchestrator.config', mock_config):
            orch = Orchestrator()
            orch.config = mock_config
            return orch
    
    def test_init_project_success(self, orchestrator, temp_dir, monkeypatch):
        """Test successful project initialization."""
        # Mock home directory
        monkeypatch.setattr(Path, "home", lambda: temp_dir)
        
        # Mock VEnv manager
        with patch('aima_codegen.orchestrator.VEnvManager') as mock_venv:
            mock_venv_instance = Mock()
            mock_venv_instance.find_python.return_value = "/usr/bin/python3"
            mock_venv_instance.create_venv.return_value = None
            mock_venv.return_value = mock_venv_instance
            
            # Initialize project
            success = orchestrator.init_project("Test Project", 10.0)
            
            assert success is True
            assert orchestrator.project_state is not None
            assert orchestrator.project_state.project_name == "Test Project"
            assert orchestrator.project_state.project_slug == "test-project"
            assert orchestrator.project_state.total_budget_usd == 10.0
            
            # Check directory structure
            project_path = temp_dir / ".AIMA_CodeGen" / "projects" / "test-project"
            assert project_path.exists()
            assert (project_path / "src").exists()
            assert (project_path / "src" / "tests").exists()
            assert (project_path / "waypoints").exists()
            assert (project_path / "logs").exists()
    
    def test_init_project_already_exists(self, orchestrator, temp_dir, monkeypatch):
        """Test project initialization when project already exists."""
        monkeypatch.setattr(Path, "home", lambda: temp_dir)
        
        # Create existing project directory
        project_path = temp_dir / ".AIMA_CodeGen" / "projects" / "test-project"
        project_path.mkdir(parents=True)
        
        success = orchestrator.init_project("Test Project", 10.0)
        assert success is False
    
    def test_load_project_success(self, orchestrator, temp_dir, monkeypatch):
        """Test successful project loading."""
        monkeypatch.setattr(Path, "home", lambda: temp_dir)
        
        # Create project structure
        project_path = temp_dir / ".AIMA_CodeGen" / "projects" / "test-project"
        project_path.mkdir(parents=True)
        
        # Create project state
        state = ProjectState(
            project_name="Test Project",
            project_slug="test-project",
            total_budget_usd=10.0,
            initial_prompt="Test prompt",
            venv_path=str(project_path / ".venv"),
            python_path="/usr/bin/python3"
        )
        
        state_file = project_path / "project_state.json"
        state_file.write_text(json.dumps(state.model_dump(), default=str))
        
        # Mock lock file check
        with patch('aima_codegen.orchestrator.check_lock_file', return_value=True):
            success = orchestrator.load_project("Test Project")
            
            assert success is True
            assert orchestrator.project_state is not None
            assert orchestrator.project_state.project_name == "Test Project"
    
    def test_load_project_not_found(self, orchestrator, temp_dir, monkeypatch):
        """Test loading non-existent project."""
        monkeypatch.setattr(Path, "home", lambda: temp_dir)
        
        success = orchestrator.load_project("Nonexistent Project")
        assert success is False
    
    def test_load_project_locked(self, orchestrator, temp_dir, monkeypatch):
        """Test loading project that is already locked."""
        monkeypatch.setattr(Path, "home", lambda: temp_dir)
        
        # Create project
        project_path = temp_dir / ".AIMA_CodeGen" / "projects" / "test-project"
        project_path.mkdir(parents=True)
        
        # Mock lock file check to return False (locked)
        with patch('aima_codegen.orchestrator.check_lock_file', return_value=False):
            success = orchestrator.load_project("Test Project")
            assert success is False
    
    def test_execute_waypoint_success(self, orchestrator, temp_dir):
        """Test successful waypoint execution."""
        # Setup project state
        orchestrator.project_path = temp_dir
        orchestrator.project_state = ProjectState(
            project_name="Test",
            project_slug="test",
            total_budget_usd=10.0,
            initial_prompt="Test",
            venv_path=str(temp_dir / ".venv"),
            python_path="/usr/bin/python3"
        )
        
        # Create source directory
        (temp_dir / "src").mkdir()
        (temp_dir / "src" / "requirements.txt").write_text("")
        
        # Create waypoint
        waypoint = Waypoint(
            id="wp_001",
            description="Test waypoint",
            agent_type="CodeGen"
        )
        
        # Mock dependencies
        orchestrator.venv_manager = Mock()
        orchestrator.venv_manager._compute_requirements_hash.return_value = "hash123"
        orchestrator.venv_manager.run_subprocess.return_value = Mock(returncode=0, stdout="", stderr="")
        orchestrator.venv_manager.get_venv_python.return_value = Path("/usr/bin/python3")
        
        orchestrator.budget_tracker = Mock()
        orchestrator.budget_tracker.pre_call_check.return_value = True
        orchestrator.budget_tracker.update_spent.return_value = 0.01
        
        orchestrator.llm_service = Mock()
        orchestrator.llm_service.count_tokens.return_value = 100
        
        orchestrator.codegen = Mock()
        orchestrator.codegen.execute.return_value = {
            "success": True,
            "code": {"src/test.py": "def test(): pass"},
            "dependencies": [],
            "tokens_used": 200,
            "cost": 0.01
        }
        
        # Execute waypoint
        with patch.object(orchestrator, '_verify_waypoint', return_value={"success": True}):
            success = orchestrator._execute_single_waypoint(waypoint)
        
        assert success is True
        assert waypoint.status == "SUCCESS"
    
    def test_execute_waypoint_with_revision(self, orchestrator, temp_dir):
        """Test waypoint execution with revision loop."""
        # Setup similar to above
        orchestrator.project_path = temp_dir
        orchestrator.project_state = ProjectState(
            project_name="Test",
            project_slug="test",
            total_budget_usd=10.0,
            initial_prompt="Test",
            venv_path=str(temp_dir / ".venv"),
            python_path="/usr/bin/python3"
        )
        
        (temp_dir / "src").mkdir()
        (temp_dir / "src" / "requirements.txt").write_text("")
        
        waypoint = Waypoint(
            id="wp_001",
            description="Test waypoint",
            agent_type="CodeGen"
        )
        
        # Mock dependencies
        orchestrator.venv_manager = Mock()
        orchestrator.budget_tracker = Mock()
        orchestrator.budget_tracker.pre_call_check.return_value = True
        orchestrator.llm_service = Mock()
        orchestrator.codegen = Mock()
        
        # First attempt fails, second succeeds
        orchestrator.codegen.execute.side_effect = [
            {
                "success": True,
                "code": {"src/test.py": "def test() pass"},  # Syntax error
                "dependencies": [],
                "tokens_used": 200
            },
            {
                "success": True,
                "code": {"src/test.py": "def test(): pass"},  # Fixed
                "dependencies": [],
                "tokens_used": 200
            }
        ]
        
        # First verification fails, second succeeds
        verification_results = [
            {"success": False, "error_type": "syntax", "syntax_error": "Invalid syntax"},
            {"success": True}
        ]
        
        with patch.object(orchestrator, '_verify_waypoint', side_effect=verification_results):
            success = orchestrator._execute_single_waypoint(waypoint)
        
        assert success is True
        assert waypoint.status == "SUCCESS"
        assert waypoint.revision_attempts == 1
        assert len(waypoint.feedback_history) == 1
    
    def test_execute_waypoint_max_revisions_exceeded(self, orchestrator, temp_dir):
        """Test waypoint execution when max revisions are exceeded."""
        orchestrator.project_path = temp_dir
        orchestrator.project_state = ProjectState(
            project_name="Test",
            project_slug="test",
            total_budget_usd=10.0,
            initial_prompt="Test",
            venv_path=str(temp_dir / ".venv"),
            python_path="/usr/bin/python3"
        )
        
        (temp_dir / "src").mkdir()
        (temp_dir / "src" / "requirements.txt").write_text("")
        
        waypoint = Waypoint(
            id="wp_001",
            description="Test waypoint",
            agent_type="CodeGen"
        )
        
        # Mock dependencies
        orchestrator.venv_manager = Mock()
        orchestrator.budget_tracker = Mock()
        orchestrator.budget_tracker.pre_call_check.return_value = True
        orchestrator.llm_service = Mock()
        orchestrator.codegen = Mock()
        orchestrator.codegen.execute.return_value = {
            "success": True,
            "code": {"src/test.py": "def test() pass"},
            "dependencies": [],
            "tokens_used": 200
        }
        
        # All verifications fail
        with patch.object(orchestrator, '_verify_waypoint', 
                         return_value={"success": False, "error_type": "syntax", "syntax_error": "Error"}):
            success = orchestrator._execute_single_waypoint(waypoint)
        
        assert success is False
        assert waypoint.status == "FAILED_REVISIONS"
        assert waypoint.revision_attempts == 3
    
    def test_budget_enforcement(self, orchestrator):
        """Test budget enforcement during LLM calls."""
        orchestrator.project_state = ProjectState(
            project_name="Test",
            project_slug="test",
            total_budget_usd=1.0,
            current_spent_usd=0.95,
            initial_prompt="Test",
            venv_path="/tmp/.venv",
            python_path="/usr/bin/python3"
        )
        
        orchestrator.budget_tracker = Mock()
        orchestrator.budget_tracker.pre_call_check.return_value = False  # Budget check fails
        
        orchestrator.llm_service = Mock()
        orchestrator.planner = Mock()
        
        # Try to plan waypoints - should fail due to budget
        waypoints = orchestrator._plan_waypoints("Test prompt")
        
        assert waypoints == []
        orchestrator.budget_tracker.pre_call_check.assert_called_once()