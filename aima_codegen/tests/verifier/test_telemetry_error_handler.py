"""Test TelemetryAwareErrorHandler functionality."""
import pytest
from unittest.mock import patch, MagicMock
from aima_codegen.error_handler import TelemetryAwareErrorHandler
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


class TestTelemetryErrorHandler:
    """Test telemetry-aware error handling."""

    def test_default_feedback_injection(self):
        """Test injecting default feedback_json when missing."""
        state = create_test_project_state()
        handler = TelemetryAwareErrorHandler(state)
        
        # Simulate missing feedback_json
        context = {
            'function_name': 'test_func',
            'requirements': 'Should work'
        }
        
        # Handle error with missing feedback
        error = KeyError('feedback_json')
        handler.handle_error(error, context, 'codegen')
        
        # Should inject default feedback
        assert 'feedback_json' in context
        assert context['feedback_json']['error_type'] == 'KeyError'
        assert context['feedback_json']['recovery_action'] == 'injected_default'

    def test_error_logging_and_recovery(self):
        """Test error logging and recovery strategies."""
        state = create_test_project_state()
        handler = TelemetryAwareErrorHandler(state)
        
        # Test various error types
        errors = [
            (ValueError("Invalid input"), "validation"),
            (RuntimeError("Process failed"), "runtime"),
            (TimeoutError("Operation timed out"), "timeout")
        ]
        
        for error, expected_category in errors:
            context = {'operation': 'test'}
            handler.handle_error(error, context, 'test_agent')
            
            # Check error was logged
            assert len(handler.error_history) > 0
            last_error = handler.error_history[-1]
            assert last_error['error_type'] == type(error).__name__
            assert last_error['agent'] == 'test_agent'

    def test_recovery_strategy_selection(self):
        """Test selection of appropriate recovery strategies."""
        state = create_test_project_state()
        handler = TelemetryAwareErrorHandler(state)
        
        # Test timeout recovery
        timeout_error = TimeoutError("Agent timeout")
        strategy = handler.get_recovery_strategy(timeout_error)
        assert strategy['action'] == 'retry_with_extended_timeout'
        
        # Test KeyError recovery
        key_error = KeyError('missing_key')
        strategy = handler.get_recovery_strategy(key_error)
        assert strategy['action'] == 'inject_defaults'
        
        # Test generic error recovery
        generic_error = Exception("Unknown error")
        strategy = handler.get_recovery_strategy(generic_error)
        assert strategy['action'] == 'log_and_continue'

    def test_telemetry_collection(self):
        """Test telemetry data collection during error handling."""
        state = create_test_project_state()
        handler = TelemetryAwareErrorHandler(state)
        
        # Generate some errors
        for i in range(5):
            error = ValueError(f"Error {i}")
            handler.handle_error(error, {'index': i}, 'test_agent')
        
        # Get telemetry summary
        telemetry = handler.get_telemetry_summary()
        
        assert telemetry['total_errors'] == 5
        assert 'ValueError' in telemetry['error_types']
        assert telemetry['error_types']['ValueError'] == 5
        assert 'test_agent' in telemetry['errors_by_agent']

    def test_circuit_breaker_integration(self):
        """Test integration with circuit breaker patterns."""
        state = create_test_project_state()
        handler = TelemetryAwareErrorHandler(state)
        
        # Simulate repeated failures
        for i in range(10):
            error = RuntimeError("Repeated failure")
            handler.handle_error(error, {}, 'failing_agent')
        
        # Check if circuit breaker recommendation is triggered
        recommendation = handler.should_circuit_break('failing_agent')
        assert recommendation is True
        
        # Check threshold
        assert handler.get_agent_error_count('failing_agent') >= 5

    def test_error_pattern_detection(self):
        """Test detection of error patterns."""
        state = create_test_project_state()
        handler = TelemetryAwareErrorHandler(state)
        
        # Create a pattern of errors
        for i in range(3):
            handler.handle_error(ValueError("Invalid format"), {'input': f'data{i}'}, 'parser')
            handler.handle_error(KeyError('missing_field'), {'input': f'data{i}'}, 'parser')
        
        # Detect patterns
        patterns = handler.detect_error_patterns()
        
        assert len(patterns) > 0
        assert any(p['pattern_type'] == 'repeated_error' for p in patterns)
        assert any(p['agent'] == 'parser' for p in patterns) 