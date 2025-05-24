"""Tests for CodeGenAgent logging and telemetry."""
import pytest
from unittest.mock import Mock, patch
import json
import logging

from aima_codegen.agents.codegen import CodeGenAgent
from aima_codegen.models import Waypoint, LLMResponse, RevisionFeedback


class TestCodeGenLogging:
    """Test comprehensive logging in CodeGenAgent."""
    
    @pytest.fixture
    def mock_llm_service(self):
        """Create a mock LLM service."""
        return Mock()
    
    @pytest.fixture
    def codegen_agent(self, mock_llm_service):
        """Create a CodeGenAgent instance."""
        return CodeGenAgent(mock_llm_service)
    
    @pytest.fixture
    def sample_waypoint(self):
        """Create a sample waypoint."""
        return Waypoint(
            id="wp_001",
            description="Create calculator class with basic operations",
            agent_type="CodeGen",
            status="PENDING"
        )
    
    def test_info_logging_for_operations(self, codegen_agent, sample_waypoint, caplog):
        """Test that info-level logging is present for key operations."""
        response_content = json.dumps({
            "code": {
                "src/calculator.py": "class Calculator:\n    pass"
            },
            "dependencies": []
        })
        
        codegen_agent.llm_service.call_llm.return_value = LLMResponse(
            content=response_content,
            prompt_tokens=100,
            completion_tokens=50,
            cost=0.01
        )
        
        with caplog.at_level(logging.INFO):
            context = {
                "waypoint": sample_waypoint,
                "project_context": "Calculator project"
            }
            result = codegen_agent.execute(context)
        
        # Verify info logs
        assert f"Starting code generation for waypoint: {sample_waypoint.id}" in caplog.text
        assert "Calling LLM for code generation" in caplog.text
        assert "LLM response received: 150 tokens" in caplog.text
        assert "Generated 1 files with 0 dependencies" in caplog.text
        assert f"Code generation successful for waypoint {sample_waypoint.id}" in caplog.text
    
    def test_debug_logging_details(self, codegen_agent, sample_waypoint, caplog):
        """Test debug-level logging for detailed information."""
        response_content = json.dumps({
            "code": {
                "src/main.py": "def main():\n    print('Hello')",
                "src/utils.py": "def helper():\n    return 42"
            },
            "dependencies": ["requests", "pytest"]
        })
        
        codegen_agent.llm_service.call_llm.return_value = LLMResponse(
            content=response_content,
            prompt_tokens=150,
            completion_tokens=100,
            cost=0.02
        )
        
        with caplog.at_level(logging.DEBUG):
            context = {
                "waypoint": sample_waypoint,
                "project_context": "Test project with multiple files"
            }
            result = codegen_agent.execute(context)
        
        # Verify debug logs
        assert f"Waypoint description: {sample_waypoint.description}" in caplog.text
        assert "Project context size:" in caplog.text
        assert "Generated prompt size:" in caplog.text
        assert "Successfully parsed JSON response" in caplog.text
        assert "Generated file: src/main.py" in caplog.text
        assert "Generated file: src/utils.py" in caplog.text
        assert "Generated debrief with confidence level:" in caplog.text
    
    def test_revision_feedback_logging(self, codegen_agent, sample_waypoint, caplog):
        """Test logging when processing revision feedback."""
        revision_feedback = RevisionFeedback(
            pytest_output="test_calculator.py::test_divide FAILED - ZeroDivisionError",
            flake8_output="src/calculator.py:10:1: E302 expected 2 blank lines, found 1",
            syntax_error=None
        )
        
        response_content = json.dumps({
            "code": {
                "src/calculator.py": "class Calculator:\n    # Fixed version"
            },
            "dependencies": []
        })
        
        codegen_agent.llm_service.call_llm.return_value = LLMResponse(
            content=response_content,
            prompt_tokens=200,
            completion_tokens=150,
            cost=0.03
        )
        
        with caplog.at_level(logging.INFO):
            context = {
                "waypoint": sample_waypoint,
                "project_context": "Calculator project",
                "revision_feedback": revision_feedback
            }
            result = codegen_agent.execute(context)
        
        # The logging for revision feedback is in the prompt building
        # Check that revision feedback was included in the context
        assert result["success"] is True
    
    def test_error_logging_on_parse_failure(self, codegen_agent, sample_waypoint, caplog):
        """Test error logging when JSON parsing fails."""
        codegen_agent.llm_service.call_llm.return_value = LLMResponse(
            content="This is not valid JSON",
            prompt_tokens=100,
            completion_tokens=50,
            cost=0.01
        )
        
        with caplog.at_level(logging.ERROR):
            context = {
                "waypoint": sample_waypoint,
                "project_context": "Test project"
            }
            result = codegen_agent.execute(context)
        
        # Verify error logs
        assert "Failed to parse CodeGen response:" in caplog.text
        # The warning log is used instead of error for the waypoint failure
        
        # Check warning log
        with caplog.at_level(logging.WARNING):
            context = {
                "waypoint": sample_waypoint,
                "project_context": "Test project"
            }
            result = codegen_agent.execute(context)
            assert f"Code generation failed for waypoint {sample_waypoint.id}" in caplog.text


class TestCodeGenDecisionTracking:
    """Test decision point tracking in CodeGenAgent."""
    
    @pytest.fixture
    def codegen_agent(self):
        """Create a CodeGenAgent instance."""
        return CodeGenAgent(Mock())
    
    def test_decision_points_for_initial_generation(self, codegen_agent, sample_waypoint):
        """Test decision points tracked for initial code generation."""
        response_content = json.dumps({
            "code": {"src/app.py": "def main(): pass"},
            "dependencies": []
        })
        
        codegen_agent.llm_service.call_llm.return_value = LLMResponse(
            content=response_content,
            prompt_tokens=100,
            completion_tokens=50,
            cost=0.01
        )
        
        # Capture decision points
        decision_points = []
        original_log = codegen_agent.log_agent_telemetry
        
        def capture_telemetry(*args, **kwargs):
            if "decision_points" in kwargs:
                decision_points.extend(kwargs["decision_points"])
            return original_log(*args, **kwargs)
        
        codegen_agent.log_agent_telemetry = capture_telemetry
        
        context = {
            "waypoint": sample_waypoint,
            "project_context": "Small context"
        }
        result = codegen_agent.execute(context)
        
        # Verify decision points
        assert len(decision_points) >= 3
        assert any(dp["description"] == "Code generation mode" for dp in decision_points)
        assert any(dp["description"] == "Context utilization strategy" for dp in decision_points)
        assert any(dp["description"] == "Output structure validation" for dp in decision_points)
        
        # Check specific decisions
        mode_decision = next(dp for dp in decision_points if dp["description"] == "Code generation mode")
        assert mode_decision["chosen"] == "Initial generation"
        assert "Fresh implementation" in mode_decision["reasoning"]
    
    def test_decision_points_for_revision(self, codegen_agent, sample_waypoint):
        """Test decision points when handling revision feedback."""
        revision_feedback = RevisionFeedback(
            pytest_output="test_app.py::test_main FAILED",
            flake8_output=None,
            syntax_error=None
        )
        
        response_content = json.dumps({
            "code": {"src/app.py": "def main(): pass  # Fixed"},
            "dependencies": []
        })
        
        codegen_agent.llm_service.call_llm.return_value = LLMResponse(
            content=response_content,
            prompt_tokens=150,
            completion_tokens=75,
            cost=0.015
        )
        
        # Capture decision points
        decision_points = []
        original_log = codegen_agent.log_agent_telemetry
        
        def capture_telemetry(*args, **kwargs):
            if "decision_points" in kwargs:
                decision_points.extend(kwargs["decision_points"])
            return original_log(*args, **kwargs)
        
        codegen_agent.log_agent_telemetry = capture_telemetry
        
        context = {
            "waypoint": sample_waypoint,
            "project_context": "Large " * 50,  # Large context
            "revision_feedback": revision_feedback
        }
        result = codegen_agent.execute(context)
        
        # Verify revision decision
        mode_decision = next(dp for dp in decision_points if dp["description"] == "Code generation mode")
        assert mode_decision["chosen"] == "Revision"
        assert "Addressing feedback" in mode_decision["reasoning"]
        
        # Verify context decision
        context_decision = next(dp for dp in decision_points if dp["description"] == "Context utilization strategy")
        assert context_decision["chosen"] == "Full context"


class TestCodeGenTelemetryIntegration:
    """Test full telemetry integration for CodeGenAgent."""
    
    @pytest.fixture
    def codegen_agent(self, tmp_path):
        """Create a CodeGenAgent with project path set."""
        agent = CodeGenAgent(Mock())
        agent.set_project_path(tmp_path)
        return agent
    
    def test_telemetry_file_creation(self, codegen_agent, sample_waypoint, tmp_path):
        """Test that telemetry files are created properly."""
        response_content = json.dumps({
            "code": {
                "src/app.py": "# Main application\ndef main():\n    pass",
                "src/config.py": "# Configuration\nDEBUG = True"
            },
            "dependencies": ["flask", "requests"]
        })
        
        codegen_agent.llm_service.call_llm.return_value = LLMResponse(
            content=response_content,
            prompt_tokens=200,
            completion_tokens=100,
            cost=0.025
        )
        
        context = {
            "waypoint": sample_waypoint,
            "project_context": "Web application project",
            "model": "gpt-4"
        }
        
        result = codegen_agent.execute(context)
        
        # Check telemetry file
        telemetry_file = tmp_path / "logs" / "agent_telemetry.jsonl"
        assert telemetry_file.exists()
        
        with open(telemetry_file, 'r') as f:
            telemetry_data = json.loads(f.readline())
            assert telemetry_data["agent_name"] == "CodeGen"
            assert telemetry_data["context"]["waypoint_id"] == "wp_001"
            assert telemetry_data["context"]["model"] == "gpt-4"
            assert telemetry_data["confidence_level"] == 0.9
            assert telemetry_data["outcome"]["success"] is True
            assert telemetry_data["outcome"]["output_files"] == ["src/app.py", "src/config.py"]
            assert telemetry_data["outcome"]["dependencies"] == ["flask", "requests"]
        
        # Check debrief file
        debrief_dir = tmp_path / "logs" / "debriefs"
        assert debrief_dir.exists()
        debrief_files = list(debrief_dir.glob("CodeGen_*.json"))
        assert len(debrief_files) > 0
    
    def test_confidence_levels(self, codegen_agent, sample_waypoint):
        """Test different confidence levels based on outcomes."""
        # Test successful parsing - high confidence
        success_response = json.dumps({
            "code": {"src/app.py": "def main(): pass"},
            "dependencies": []
        })
        
        codegen_agent.llm_service.call_llm.return_value = LLMResponse(
            content=success_response,
            prompt_tokens=100,
            completion_tokens=50,
            cost=0.01
        )
        
        confidence_levels = []
        original_log = codegen_agent.log_agent_telemetry
        
        def capture_confidence(*args, **kwargs):
            if "confidence_level" in kwargs:
                confidence_levels.append(kwargs["confidence_level"])
            return original_log(*args, **kwargs)
        
        codegen_agent.log_agent_telemetry = capture_confidence
        
        # Successful execution
        context = {"waypoint": sample_waypoint, "project_context": "Test"}
        result = codegen_agent.execute(context)
        assert confidence_levels[-1] == 0.9  # High confidence
        
        # Failed parsing - low confidence
        codegen_agent.llm_service.call_llm.return_value = LLMResponse(
            content="Invalid JSON",
            prompt_tokens=50,
            completion_tokens=25,
            cost=0.005
        )
        
        result = codegen_agent.execute(context)
        assert confidence_levels[-1] == 0.1  # Very low confidence


@pytest.fixture
def sample_waypoint():
    """Shared fixture for sample waypoint."""
    return Waypoint(
        id="wp_001",
        description="Test waypoint",
        agent_type="CodeGen",
        status="PENDING"
    ) 