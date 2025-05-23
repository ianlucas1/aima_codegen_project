"""Tests for virtual environment management."""
import pytest
import subprocess
from pathlib import Path
from unittest.mock import Mock, patch, call

from aima_codegen.venv_manager import VEnvManager
from aima_codegen.exceptions import ToolingError


class TestVEnvManager:
    """Test suite for VEnv management."""
    
    @pytest.fixture
    def temp_project(self, tmp_path):
        """Create temporary project structure."""
        project_path = tmp_path / "test_project"
        project_path.mkdir()
        (project_path / "src").mkdir()
        (project_path / "src" / "requirements.txt").write_text("")
        return project_path
    
    def test_find_python_from_config(self, temp_project):
        """Test finding Python from config."""
        with patch('aima_codegen.venv_manager.config') as mock_config:
            mock_config.get.return_value = "/custom/python3"
            
            manager = VEnvManager(temp_project)
            
            # Mock version check
            with patch.object(manager, '_verify_python_version', return_value=True):
                python_path = manager.find_python()
                assert python_path == "/custom/python3"
    
    def test_find_python_system_search(self, temp_project):
        """Test finding Python from system PATH."""
        with patch('aima_codegen.venv_manager.config') as mock_config:
            mock_config.get.return_value = ""  # No config path
            
            with patch('shutil.which') as mock_which:
                # Mock finding python3.11
                mock_which.side_effect = lambda cmd: {
                    "python3.12": None,
                    "python3.11": "/usr/bin/python3.11",
                    "python3.10": "/usr/bin/python3.10",
                    "python3": "/usr/bin/python3"
                }.get(cmd)
                
                manager = VEnvManager(temp_project)
                
                # Mock version checks
                with patch.object(manager, '_get_python_version') as mock_get_version:
                    mock_get_version.side_effect = lambda path: {
                        "/usr/bin/python3.11": (3, 11, 5),
                        "/usr/bin/python3.10": (3, 10, 8),
                        "/usr/bin/python3": (3, 9, 0)  # Too old
                    }.get(path)
                    
                    python_path = manager.find_python()
                    assert python_path == "/usr/bin/python3.11"
    
    def test_find_python_not_found(self, temp_project):
        """Test error when no suitable Python found."""
        with patch('aima_codegen.venv_manager.config') as mock_config:
            mock_config.get.return_value = ""
            
            with patch('shutil.which', return_value=None):
                manager = VEnvManager(temp_project)
                
                with pytest.raises(RuntimeError) as exc_info:
                    manager.find_python()
                
                assert "FATAL_ERROR: Could not find a suitable Python interpreter" in str(exc_info.value)
    
    def test_create_venv_success(self, temp_project):
        """Test successful venv creation."""
        manager = VEnvManager(temp_project)
        
        with patch('subprocess.run') as mock_run:
            mock_run.return_value = Mock(returncode=0, stdout="", stderr="")
            
            with patch.object(manager, 'get_venv_python') as mock_get_python:
                mock_get_python.return_value = temp_project / ".venv" / "bin" / "python"
                # Create the expected python file
                (temp_project / ".venv" / "bin").mkdir(parents=True)
                (temp_project / ".venv" / "bin" / "python").touch()
                
                manager.create_venv("/usr/bin/python3")
                
                mock_run.assert_called_once_with(
                    ["/usr/bin/python3", "-m", "venv", str(temp_project / ".venv")],
                    capture_output=True,
                    text=True,
                    check=False,
                    timeout=60
                )
    
    def test_create_venv_failure(self, temp_project):
        """Test venv creation failure."""
        manager = VEnvManager(temp_project)
        
        with patch('subprocess.run') as mock_run:
            mock_run.return_value = Mock(
                returncode=1,
                stdout="",
                stderr="Error creating venv"
            )
            
            with pytest.raises(ToolingError) as exc_info:
                manager.create_venv("/usr/bin/python3")
            
            assert "Failed to create virtual environment" in str(exc_info.value)
    
    def test_install_requirements_success(self, temp_project):
        """Test successful requirements installation."""
        manager = VEnvManager(temp_project)
        
        # Write some requirements
        (temp_project / "src" / "requirements.txt").write_text("pytest==7.4.0\nrequests>=2.28.0\n")
        
        with patch('subprocess.run') as mock_run:
            mock_run.return_value = Mock(returncode=0, stdout="Successfully installed", stderr="")
            
            with patch.object(manager, 'get_venv_python') as mock_get_python:
                mock_get_python.return_value = Path("/tmp/.venv/bin/python")
                
                new_hash = manager.install_requirements()
                
                assert new_hash != ""  # Should return hash
                mock_run.assert_called_once()
                
                # Verify pip install command
                call_args = mock_run.call_args[0][0]
                assert call_args[0] == "/tmp/.venv/bin/python"
                assert call_args[1:3] == ["-m", "pip"]
                assert "install" in call_args
                assert "-r" in call_args
    
    def test_install_requirements_unchanged(self, temp_project):
        """Test skipping installation when requirements unchanged."""
        manager = VEnvManager(temp_project)
        
        req_content = "pytest==7.4.0\n"
        (temp_project / "src" / "requirements.txt").write_text(req_content)
        
        # Get current hash
        current_hash = manager._compute_requirements_hash()
        
        with patch('subprocess.run') as mock_run:
            new_hash = manager.install_requirements(requirements_hash=current_hash)
            
            # Should not call pip
            mock_run.assert_not_called()
            assert new_hash == current_hash
    
    def test_run_subprocess_success(self, temp_project):
        """Test successful subprocess execution."""
        manager = VEnvManager(temp_project)
        
        with patch('subprocess.run') as mock_run:
            mock_run.return_value = Mock(
                returncode=0,
                stdout="Test passed",
                stderr="",
                args=["python", "-m", "pytest"]
            )
            
            result = manager.run_subprocess(["python", "-m", "pytest"], timeout=30)
            
            assert result.returncode == 0
            assert result.stdout == "Test passed"
            
            # Verify subprocess.run was called with correct args
            mock_run.assert_called_once_with(
                ["python", "-m", "pytest"],
                capture_output=True,
                text=True,
                check=False,
                timeout=30,
                cwd=temp_project / "src"
            )
    
    def test_run_subprocess_timeout(self, temp_project):
        """Test subprocess timeout handling."""
        manager = VEnvManager(temp_project)
        
        with patch('subprocess.run', side_effect=subprocess.TimeoutExpired(["test"], 30)):
            with pytest.raises(ToolingError) as exc_info:
                manager.run_subprocess(["test"], timeout=30)
            
            assert "Command timed out after 30 seconds" in str(exc_info.value)