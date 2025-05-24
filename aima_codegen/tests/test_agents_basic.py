"""Tests for agent implementations."""
import pytest
import json
from unittest.mock import Mock, patch

from aima_codegen.agents import PlannerAgent, CodeGenAgent, TestWriterAgent, ExplainerAgent
from aima_codegen.models import LLMResponse, Waypoint, RevisionFeedback


class TestPlannerAgent:
    """Test suite for Planner agent."""
    
    def test_execute_success(self):
        """Test successful waypoint planning."""
        # Mock LLM service
        llm_service = Mock()
        llm_response = LLMResponse(
            content=json.dumps([
                {
                    "id": "wp_001",
                    "description": "Create main application",
                    "agent_type": "CodeGen",
                    "dependencies": []
                },
                {
                    "id": "wp_002",
                    "description": "Write tests",
                    "agent_type": "TestWriter",
                    "dependencies": ["wp_001"]
                }
            ]),
            prompt_tokens=100,
            completion_tokens=200,
            cost=0.01
        )
        llm_service.call_llm.return_value = llm_response
        
        # Create agent and execute
        agent = PlannerAgent(llm_service)
        result = agent.execute({
            "user_prompt": "Create a simple calculator",
            "model": "gpt-4"
        })
        
        assert result["success"] is True
        assert len(result["waypoints"]) == 2
        assert result["waypoints"][0].id == "wp_001"
        assert result["waypoints"][0].agent_type == "CodeGen"
        assert result["waypoints"][1].id == "wp_002"
        assert result["waypoints"][1].agent_type == "TestWriter"
    
    def test_execute_invalid_json(self):
        """Test handling of invalid JSON response."""
        llm_service = Mock()
        llm_response = LLMResponse(
            content="This is not valid JSON",
            prompt_tokens=100,
            completion_tokens=50,
            cost=0.01
        )
        llm_service.call_llm.return_value = llm_response
        
        agent = PlannerAgent(llm_service)
        result = agent.execute({"user_prompt": "Test", "model": "gpt-4"})
        
        assert result["success"] is False
        assert "error" in result
        assert result["tokens_used"] == 150


class TestCodeGenAgent:
    """Test suite for CodeGen agent."""
    
    def test_execute_success(self):
        """Test successful code generation."""
        llm_service = Mock()
        llm_response = LLMResponse(
            content=json.dumps({
                "code": {
                    "src/calculator.py": "def add(a, b):\n    return a + b\n"
                },
                "dependencies": ["pytest"]
            }),
            prompt_tokens=200,
            completion_tokens=100,
            cost=0.02
        )
        llm_service.call_llm.return_value = llm_response
        
        waypoint = Waypoint(
            id="wp_001",
            description="Create calculator add function",
            agent_type="CodeGen"
        )
        
        agent = CodeGenAgent(llm_service)
        result = agent.execute({
            "waypoint": waypoint,
            "project_context": "# Calculator project",
            "model": "gpt-4"
        })
        
        assert result["success"] is True
        assert "src/calculator.py" in result["code"]
        assert result["dependencies"] == ["pytest"]
        assert result["tokens_used"] == 300
    
    def test_execute_with_revision_feedback(self):
        """Test code generation with revision feedback."""
        llm_service = Mock()
        llm_response = LLMResponse(
            content=json.dumps({
                "code": {
                    "src/calculator.py": "def add(a, b):\n    return a + b\n"
                },
                "dependencies": []
            }),
            prompt_tokens=300,
            completion_tokens=150,
            cost=0.03
        )
        llm_service.call_llm.return_value = llm_response
        
        waypoint = Waypoint(
            id="wp_001",
            description="Fix calculator add function",
            agent_type="CodeGen"
        )
        
        feedback = RevisionFeedback(
            pytest_output="test_add failed: assert add(2, 2) == 4",
            flake8_output=None
        )
        
        agent = CodeGenAgent(llm_service)
        result = agent.execute({
            "waypoint": waypoint,
            "project_context": "# Calculator project",
            "revision_feedback": feedback,
            "model": "gpt-4"
        })
        
        assert result["success"] is True
        # Verify that the prompt included revision feedback
        call_args = llm_service.call_llm.call_args
        request = call_args[0][0]  # First positional argument is the LLMRequest
        messages = request.messages
        assert "REVISION FEEDBACK" in messages[1]["content"]


class TestTestWriterAgent:
    """Test suite for TestWriter agent."""
    
    def test_execute_success(self):
        """Test successful test generation."""
        llm_service = Mock()
        llm_response = LLMResponse(
            content=json.dumps({
                "code": {
                    "src/tests/test_calculator.py": "import pytest\nfrom src.calculator import add\n\ndef test_add():\n    assert add(2, 3) == 5\n"
                },
                "dependencies": ["pytest"]
            }),
            prompt_tokens=250,
            completion_tokens=120,
            cost=0.025
        )
        llm_service.call_llm.return_value = llm_response
        
        waypoint = Waypoint(
            id="wp_002",
            description="Write tests for calculator",
            agent_type="TestWriter"
        )
        
        agent = TestWriterAgent(llm_service)
        result = agent.execute({
            "waypoint": waypoint,
            "source_code": "def add(a, b):\n    return a + b\n",
            "project_context": "# Calculator project",
            "model": "gpt-4"
        })
        
        assert result["success"] is True
        assert "src/tests/test_calculator.py" in result["code"]
        assert "pytest" in result["dependencies"]
        assert "test_add" in result["code"]["src/tests/test_calculator.py"]


class TestExplainerAgent:
    """Test suite for Explainer agent."""
    
    def test_execute_success(self):
        """Test successful code explanation."""
        llm_service = Mock()
        llm_response = LLMResponse(
            content="This function adds two numbers together and returns the result.",
            prompt_tokens=150,
            completion_tokens=50,
            cost=0.015
        )
        llm_service.call_llm.return_value = llm_response
        
        agent = ExplainerAgent(llm_service)
        result = agent.execute({
            "file_path": "calculator.py",
            "code_content": "def add(a, b):\n    return a + b\n",
            "target": None,
            "model": "gpt-4"
        })
        
        assert result["success"] is True
        assert "adds two numbers" in result["explanation"]
        assert result["tokens_used"] == 200
    
    def test_execute_with_target(self):
        """Test explanation with specific target."""
        llm_service = Mock()
        llm_response = LLMResponse(
            content="The add function takes two parameters and returns their sum.",
            prompt_tokens=180,
            completion_tokens=60,
            cost=0.018
        )
        llm_service.call_llm.return_value = llm_response
        
        agent = ExplainerAgent(llm_service)
        result = agent.execute({
            "file_path": "calculator.py",
            "code_content": "def add(a, b):\n    return a + b\n\ndef subtract(a, b):\n    return a - b\n",
            "target": "add",
            "model": "gpt-4"
        })
        
        assert result["success"] is True
        # Verify that the prompt focuses on the target
        call_args = llm_service.call_llm.call_args
        request = call_args[0][0]  # First positional argument is the LLMRequest
        messages = request.messages
        assert "add function" in messages[1]["content"]