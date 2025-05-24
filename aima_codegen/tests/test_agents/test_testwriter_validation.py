"""Tests for TestWriterAgent validation and dependency management."""
import pytest
from unittest.mock import Mock
import json
import logging

from aima_codegen.agents.testwriter import TestWriterAgent
from aima_codegen.models import Waypoint, LLMResponse, RevisionFeedback


class TestTestWriterValidation:
    """Test pytest dependency validation and markdown stripping."""
    
    @pytest.fixture
    def mock_llm_service(self):
        """Create a mock LLM service."""
        return Mock()
    
    @pytest.fixture
    def testwriter_agent(self, mock_llm_service):
        """Create a TestWriterAgent instance."""
        return TestWriterAgent(mock_llm_service)
    
    @pytest.fixture
    def sample_waypoint(self):
        """Create a sample waypoint."""
        return Waypoint(
            id="wp_002",
            description="Write tests for calculator class",
            agent_type="TestWriter",
            status="PENDING"
        )
    
    def test_pytest_dependency_added_when_missing(self, testwriter_agent, sample_waypoint, caplog):
        """Test that pytest is added to dependencies when missing."""
        response_content = json.dumps({
            "code": {
                "tests/test_calculator.py": "def test_add():\n    assert 1 + 1 == 2"
            },
            "dependencies": []  # Missing pytest
        })
        
        testwriter_agent.llm_service.call_llm.return_value = LLMResponse(
            content=response_content,
            prompt_tokens=100,
            completion_tokens=50,
            cost=0.01
        )
        
        context = {
            "waypoint": sample_waypoint,
            "source_code": "def add(a, b): return a + b",
            "project_context": "Calculator project"
        }
        
        # Set log level to INFO to capture the log message
        with caplog.at_level(logging.INFO):
            result = testwriter_agent.execute(context)
        
        assert result["success"] is True
        assert "pytest" in result["dependencies"]
        assert "Adding pytest to dependencies as it was missing" in caplog.text
    
    def test_pytest_dependency_preserved_when_present(self, testwriter_agent, sample_waypoint):
        """Test that pytest is preserved when already in dependencies."""
        response_content = json.dumps({
            "code": {
                "tests/test_calculator.py": "def test_add():\n    assert 1 + 1 == 2"
            },
            "dependencies": ["pytest", "pytest-cov"]
        })
        
        testwriter_agent.llm_service.call_llm.return_value = LLMResponse(
            content=response_content,
            prompt_tokens=100,
            completion_tokens=50,
            cost=0.01
        )
        
        context = {
            "waypoint": sample_waypoint,
            "source_code": "def add(a, b): return a + b",
            "project_context": "Calculator project"
        }
        
        result = testwriter_agent.execute(context)
        
        assert result["success"] is True
        assert result["dependencies"] == ["pytest", "pytest-cov"]
        assert result["dependencies"].count("pytest") == 1  # Not duplicated
    
    def test_markdown_stripping_json_block(self, testwriter_agent, sample_waypoint):
        """Test stripping of markdown code blocks from response."""
        # Response wrapped in markdown
        response_content = '''```json
{
    "code": {
        "tests/test_main.py": "import pytest\\n\\ndef test_main():\\n    assert True"
    },
    "dependencies": ["pytest"]
}
```'''
        
        testwriter_agent.llm_service.call_llm.return_value = LLMResponse(
            content=response_content,
            prompt_tokens=120,
            completion_tokens=60,
            cost=0.012
        )
        
        context = {
            "waypoint": sample_waypoint,
            "source_code": "def main(): pass",
            "project_context": "Main module"
        }
        
        result = testwriter_agent.execute(context)
        
        assert result["success"] is True
        assert "tests/test_main.py" in result["code"]
        assert "import pytest" in result["code"]["tests/test_main.py"]
    
    def test_raw_json_without_markdown(self, testwriter_agent, sample_waypoint):
        """Test handling of raw JSON without markdown wrapping."""
        response_content = json.dumps({
            "code": {
                "tests/test_utils.py": "def test_helper():\n    from src.utils import helper\n    assert helper() == 42"
            },
            "dependencies": ["pytest"]
        })
        
        testwriter_agent.llm_service.call_llm.return_value = LLMResponse(
            content=response_content,
            prompt_tokens=100,
            completion_tokens=50,
            cost=0.01
        )
        
        context = {
            "waypoint": sample_waypoint,
            "source_code": "def helper(): return 42",
            "project_context": "Utility functions"
        }
        
        result = testwriter_agent.execute(context)
        
        assert result["success"] is True
        assert "tests/test_utils.py" in result["code"]
    
    def test_malformed_json_handling(self, testwriter_agent, sample_waypoint):
        """Test handling of malformed JSON responses."""
        response_content = "This is not valid JSON"
        
        testwriter_agent.llm_service.call_llm.return_value = LLMResponse(
            content=response_content,
            prompt_tokens=50,
            completion_tokens=20,
            cost=0.005
        )
        
        context = {
            "waypoint": sample_waypoint,
            "source_code": "def test(): pass",
            "project_context": "Test"
        }
        
        result = testwriter_agent.execute(context)
        
        assert result["success"] is False
        assert "Failed to parse generated tests" in result["error"]
        assert "raw_content" in result


class TestTestWriterDecisionTracking:
    """Test decision point tracking in TestWriterAgent."""
    
    @pytest.fixture
    def testwriter_agent(self):
        """Create a TestWriterAgent instance."""
        return TestWriterAgent(Mock())
    
    def test_test_strategy_decisions(self, testwriter_agent, sample_waypoint):
        """Test decision points for test generation strategy."""
        # Small source code
        small_code = "def add(a, b): return a + b"
        
        response_content = json.dumps({
            "code": {"tests/test_add.py": "def test_add(): pass"},
            "dependencies": ["pytest"]
        })
        
        testwriter_agent.llm_service.call_llm.return_value = LLMResponse(
            content=response_content,
            prompt_tokens=100,
            completion_tokens=50,
            cost=0.01
        )
        
        # Capture decision points
        decision_points = []
        original_log = testwriter_agent.log_agent_telemetry
        
        def capture_telemetry(*args, **kwargs):
            if "decision_points" in kwargs:
                decision_points.extend(kwargs["decision_points"])
            return original_log(*args, **kwargs)
        
        testwriter_agent.log_agent_telemetry = capture_telemetry
        
        context = {
            "waypoint": sample_waypoint,
            "source_code": small_code,
            "project_context": "Simple math functions"
        }
        
        result = testwriter_agent.execute(context)
        
        # Check strategy decision
        strategy_decision = next(dp for dp in decision_points if dp["description"] == "Test coverage strategy")
        assert strategy_decision["chosen"] == "Focused"  # Small code = focused strategy
        
        # Check framework decision
        framework_decision = next(dp for dp in decision_points if dp["description"] == "Test framework choice")
        assert framework_decision["chosen"] == "pytest"
    
    def test_revision_feedback_decisions(self, testwriter_agent, sample_waypoint):
        """Test decision tracking with revision feedback."""
        revision_feedback = RevisionFeedback(
            pytest_output="tests/test_calc.py::test_calc FAILED - AssertionError",
            flake8_output=None,
            syntax_error=None
        )
        
        response_content = json.dumps({
            "code": {"tests/test_calc.py": "def test_calc(): assert True"},
            "dependencies": ["pytest"]
        })
        
        testwriter_agent.llm_service.call_llm.return_value = LLMResponse(
            content=response_content,
            prompt_tokens=150,
            completion_tokens=75,
            cost=0.015
        )
        
        # Capture decision points
        decision_points = []
        original_log = testwriter_agent.log_agent_telemetry
        
        def capture_telemetry(*args, **kwargs):
            if "decision_points" in kwargs:
                decision_points.extend(kwargs["decision_points"])
            return original_log(*args, **kwargs)
        
        testwriter_agent.log_agent_telemetry = capture_telemetry
        
        context = {
            "waypoint": sample_waypoint,
            "source_code": "def calc(): pass",
            "project_context": "Calculator",
            "revision_feedback": revision_feedback
        }
        
        result = testwriter_agent.execute(context)
        
        # Check revision decision
        revision_decision = next(dp for dp in decision_points if dp["description"] == "Revision approach")
        assert revision_decision["chosen"] == "Fix failing tests"
        assert "specific feedback" in revision_decision["reasoning"]


class TestTestWriterTelemetryIntegration:
    """Test full telemetry integration for TestWriterAgent."""
    
    @pytest.fixture
    def testwriter_agent(self, tmp_path):
        """Create a TestWriterAgent with project path set."""
        agent = TestWriterAgent(Mock())
        agent.set_project_path(tmp_path)
        return agent
    
    def test_comprehensive_test_generation(self, testwriter_agent, sample_waypoint, tmp_path):
        """Test generation of comprehensive test suite with telemetry."""
        source_code = '''
class Calculator:
    """A simple calculator class."""
    
    def add(self, a, b):
        """Add two numbers."""
        return a + b
    
    def divide(self, a, b):
        """Divide two numbers."""
        if b == 0:
            raise ValueError("Cannot divide by zero")
        return a / b
'''
        
        response_content = json.dumps({
            "code": {
                "tests/test_calculator.py": '''import pytest
from src.calculator import Calculator

class TestCalculator:
    def test_add(self):
        calc = Calculator()
        assert calc.add(2, 3) == 5
        assert calc.add(-1, 1) == 0
    
    def test_divide(self):
        calc = Calculator()
        assert calc.divide(10, 2) == 5
    
    def test_divide_by_zero(self):
        calc = Calculator()
        with pytest.raises(ValueError, match="Cannot divide by zero"):
            calc.divide(10, 0)
'''
            },
            "dependencies": ["pytest"]
        })
        
        testwriter_agent.llm_service.call_llm.return_value = LLMResponse(
            content=response_content,
            prompt_tokens=300,
            completion_tokens=200,
            cost=0.04
        )
        
        context = {
            "waypoint": sample_waypoint,
            "source_code": source_code,
            "project_context": "Calculator application with error handling",
            "model": "gpt-4"
        }
        
        result = testwriter_agent.execute(context)
        
        assert result["success"] is True
        assert "tests/test_calculator.py" in result["code"]
        
        # Check telemetry
        telemetry_file = tmp_path / "logs" / "agent_telemetry.jsonl"
        assert telemetry_file.exists()
        
        with open(telemetry_file, 'r') as f:
            telemetry_data = json.loads(f.readline())
            assert telemetry_data["agent_name"] == "TestWriter"
            assert telemetry_data["confidence_level"] == 0.9
            assert len(telemetry_data["decision_points"]) >= 3
        
        # Check debrief
        debrief_dir = tmp_path / "logs" / "debriefs"
        assert debrief_dir.exists()
        debrief_files = list(debrief_dir.glob("TestWriter_*.json"))
        assert len(debrief_files) > 0
    
    def test_confidence_levels_based_on_outcome(self, testwriter_agent, sample_waypoint):
        """Test different confidence levels for different outcomes."""
        # Successful test generation
        success_response = json.dumps({
            "code": {"tests/test_main.py": "def test_main(): pass"},
            "dependencies": ["pytest"]
        })
        
        testwriter_agent.llm_service.call_llm.return_value = LLMResponse(
            content=success_response,
            prompt_tokens=100,
            completion_tokens=50,
            cost=0.01
        )
        
        confidence_levels = []
        original_log = testwriter_agent.log_agent_telemetry
        
        def capture_confidence(*args, **kwargs):
            if "confidence_level" in kwargs:
                confidence_levels.append(kwargs["confidence_level"])
            return original_log(*args, **kwargs)
        
        testwriter_agent.log_agent_telemetry = capture_confidence
        
        context = {
            "waypoint": sample_waypoint,
            "source_code": "def main(): pass",
            "project_context": "Test"
        }
        
        # Successful generation
        result = testwriter_agent.execute(context)
        assert confidence_levels[-1] == 0.9  # High confidence
        
        # Failed parsing
        testwriter_agent.llm_service.call_llm.return_value = LLMResponse(
            content="Invalid JSON",
            prompt_tokens=50,
            completion_tokens=25,
            cost=0.005
        )
        
        result = testwriter_agent.execute(context)
        assert confidence_levels[-1] == 0.2  # Low confidence due to failure


@pytest.fixture
def sample_waypoint():
    """Shared fixture for sample waypoint."""
    return Waypoint(
        id="wp_002",
        description="Test waypoint",
        agent_type="TestWriter",
        status="PENDING"
    ) 