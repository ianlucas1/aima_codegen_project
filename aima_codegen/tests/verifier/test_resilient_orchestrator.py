"""Test ResilientOrchestrator fault tolerance features."""
import time
import signal
import multiprocessing
import pytest
from unittest.mock import MagicMock, patch
from aima_codegen.orchestrator import ResilientOrchestrator, WaypointStatus
from aima_codegen.models import ProjectState


def create_test_project_state():
    """Create a ProjectState with minimum required fields for testing."""
    return ProjectState(
        project_name="test_project",
        project_slug="test-project",
        total_budget_usd=10.0,
        initial_prompt="Test prompt",
        venv_path="/tmp/test_venv",
        python_path="/usr/bin/python3"
    )


# Module-level functions that can be pickled
def mock_agent_func_success(checkpoint):
    """Mock agent function that returns success."""
    return {"result": "success", "data": "test"}


def mock_agent_func_failure(checkpoint):
    """Mock agent function that raises an exception."""
    raise Exception("Test failure")


def mock_agent_func_flaky(checkpoint):
    """Mock agent function that fails twice then succeeds."""
    # Use a file to track call count since we can't use nonlocal in multiprocessing
    import tempfile
    count_file = tempfile.gettempdir() + "/test_flaky_count.txt"
    try:
        with open(count_file, 'r') as f:
            count = int(f.read())
    except (FileNotFoundError, ValueError):
        count = 0
    
    count += 1
    with open(count_file, 'w') as f:
        f.write(str(count))
    
    if count < 3:
        raise Exception("Temporary failure")
    return {"success": True}


def mock_agent_func_slow(checkpoint):
    """Mock agent function that sleeps longer than timeout."""
    time.sleep(5)
    return {"status": "completed"}


class TestResilientOrchestrator:
    """Test fault tolerance and resilience features."""

    def test_waypoint_execution_success(self):
        """Test successful waypoint execution."""
        orchestrator = ResilientOrchestrator()
        
        # Mock the circuit breaker to avoid multiprocessing
        with patch.object(orchestrator, '_execute_with_circuit_breaker') as mock_execute:
            mock_execute.return_value = {"result": "success", "data": "test"}
            
            result = orchestrator.execute_waypoint("test_waypoint", mock_agent_func_success)
            
            assert result == {"result": "success", "data": "test"}
            assert orchestrator.waypoints["test_waypoint"] == WaypointStatus.SUCCESS

    def test_waypoint_execution_failure_non_critical(self):
        """Test non-critical waypoint failure handling."""
        orchestrator = ResilientOrchestrator()
        
        # Mock the circuit breaker to simulate failure
        with patch.object(orchestrator, '_execute_with_circuit_breaker') as mock_execute:
            mock_execute.side_effect = Exception("Test failure")
            
            result = orchestrator.execute_waypoint("test_waypoint", mock_agent_func_failure, critical=False)
            
            assert result is None
            assert orchestrator.waypoints["test_waypoint"] == WaypointStatus.FAILED

    def test_waypoint_execution_failure_critical(self):
        """Test critical waypoint failure handling."""
        orchestrator = ResilientOrchestrator()
        
        # Mock methods
        with patch.object(orchestrator, '_execute_with_circuit_breaker') as mock_execute:
            mock_execute.side_effect = Exception("Critical failure")
            with patch.object(orchestrator, '_handle_critical_failure') as mock_handle:
                mock_handle.return_value = {"partial": "result"}
                
                result = orchestrator.execute_waypoint("critical_waypoint", mock_agent_func_failure, critical=True)
                
                assert result == {"partial": "result"}
                assert orchestrator.waypoints["critical_waypoint"] == WaypointStatus.FAILED
                mock_handle.assert_called_once()

    def test_circuit_breaker_retry(self):
        """Test circuit breaker retry mechanism with mock."""
        orchestrator = ResilientOrchestrator()
        
        # Test retry logic without multiprocessing
        call_count = 0
        
        def mock_func(*args, **kwargs):  # Accept any args/kwargs
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                raise Exception("Temporary failure")
            return {"success": True}
        
        # Mock the Pool to avoid multiprocessing
        with patch('multiprocessing.Pool') as mock_pool:
            mock_async_result = MagicMock()
            mock_async_result.get.side_effect = mock_func
            mock_pool.return_value.__enter__.return_value.apply_async.return_value = mock_async_result
            
            result = orchestrator._execute_with_circuit_breaker(lambda x: x, None, timeout=10)
            
            assert result == {"success": True}
            assert call_count == 3

    def test_graceful_shutdown_sigint(self):
        """Test graceful shutdown with SIGINT."""
        orchestrator = ResilientOrchestrator()
        
        # Mock state manager
        orchestrator.state_manager = MagicMock()
        orchestrator.project_state = create_test_project_state()
        
        # Simulate SIGINT
        orchestrator._shutdown_handler(signal.SIGINT, None)
        
        assert orchestrator.stop_event.is_set()
        orchestrator.state_manager.save.assert_called_once()

    def test_graceful_shutdown_sigterm(self):
        """Test graceful shutdown with SIGTERM."""
        orchestrator = ResilientOrchestrator()
        
        # Mock state manager
        orchestrator.state_manager = MagicMock()
        orchestrator.project_state = create_test_project_state()
        
        # Simulate SIGTERM
        orchestrator._shutdown_handler(signal.SIGTERM, None)
        
        assert orchestrator.stop_event.is_set()
        orchestrator.state_manager.save.assert_called_once()

    def test_timeout_handling(self):
        """Test timeout handling in circuit breaker."""
        orchestrator = ResilientOrchestrator()
        
        # Mock Pool to simulate timeout
        with patch('multiprocessing.Pool') as mock_pool:
            mock_async_result = MagicMock()
            mock_async_result.get.side_effect = multiprocessing.TimeoutError("Timeout")
            mock_pool.return_value.__enter__.return_value.apply_async.return_value = mock_async_result
            
            with pytest.raises(multiprocessing.TimeoutError):
                orchestrator._execute_with_circuit_breaker(mock_agent_func_slow, None, timeout=0.1)

    def test_checkpoint_saving(self):
        """Test checkpoint saving functionality."""
        orchestrator = ResilientOrchestrator()
        orchestrator.project_state = create_test_project_state()
        orchestrator.state_manager = MagicMock()
        
        # Add some checkpoints
        orchestrator.checkpoints['waypoint1'] = {'data': 'test1'}
        orchestrator.checkpoints['waypoint2'] = {'data': 'test2'}
        
        # Test save checkpoint
        orchestrator._save_checkpoint()
        
        # Verify state manager was called
        orchestrator.state_manager.save.assert_called_once_with(orchestrator.project_state)

    def test_execution_summary(self):
        """Test execution summary generation."""
        orchestrator = ResilientOrchestrator()
        
        # Set up waypoint statuses
        orchestrator.waypoints = {
            'wp1': WaypointStatus.SUCCESS,
            'wp2': WaypointStatus.SUCCESS,
            'wp3': WaypointStatus.FAILED,
            'wp4': WaypointStatus.PARTIAL,
            'wp5': WaypointStatus.PENDING
        }
        orchestrator.checkpoints = {'wp1': {}, 'wp2': {}}
        
        summary = orchestrator.get_execution_summary()
        
        assert summary['total_waypoints'] == 5
        assert summary['successful'] == 2
        assert summary['failed'] == 1
        assert summary['partial'] == 1
        assert summary['checkpoints'] == 2 