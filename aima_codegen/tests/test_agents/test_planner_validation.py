"""Tests for PlannerAgent validation and JSON extraction."""
import pytest
from unittest.mock import Mock
import json

from aima_codegen.agents.planner import PlannerAgent
from aima_codegen.models import LLMResponse


class TestPlannerValidation:
    """Test agent type validation and waypoint creation."""
    
    @pytest.fixture
    def mock_llm_service(self):
        """Create a mock LLM service."""
        return Mock()
    
    @pytest.fixture
    def planner_agent(self, mock_llm_service):
        """Create a PlannerAgent instance."""
        return PlannerAgent(mock_llm_service)
    
    def test_valid_agent_types(self, planner_agent):
        """Test that valid agent types are accepted."""
        response_content = json.dumps([
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
        ])
        
        planner_agent.llm_service.call_llm.return_value = LLMResponse(
            content=response_content,
            prompt_tokens=100,
            completion_tokens=50,
            cost=0.01
        )
        
        context = {"user_prompt": "Build a calculator app"}
        result = planner_agent.execute(context)
        
        assert result["success"] is True
        assert len(result["waypoints"]) == 2
        assert result["waypoints"][0].agent_type == "CodeGen"
        assert result["waypoints"][1].agent_type == "TestWriter"
    
    def test_invalid_agent_type_defaults_to_codegen(self, planner_agent, caplog):
        """Test that invalid agent types default to CodeGen with warning."""
        response_content = json.dumps([
            {
                "id": "wp_001",
                "description": "Invalid agent type waypoint",
                "agent_type": "InvalidType",
                "dependencies": []
            },
            {
                "id": "wp_002",
                "description": "Missing agent type",
                "agent_type": "",
                "dependencies": []
            }
        ])
        
        planner_agent.llm_service.call_llm.return_value = LLMResponse(
            content=response_content,
            prompt_tokens=100,
            completion_tokens=50,
            cost=0.01
        )
        
        context = {"user_prompt": "Build something"}
        result = planner_agent.execute(context)
        
        assert result["success"] is True
        assert len(result["waypoints"]) == 2
        # Both should default to CodeGen
        assert all(wp.agent_type == "CodeGen" for wp in result["waypoints"])
        # Check warnings were logged
        assert "Invalid agent_type 'InvalidType'" in caplog.text
        assert "defaulting to CodeGen" in caplog.text
    
    def test_json_extraction_from_markdown(self, planner_agent):
        """Test extraction of JSON from markdown code blocks."""
        response_content = '''Here's the waypoint plan for your calculator:

```json
[
    {
        "id": "wp_001",
        "description": "Create calculator class",
        "agent_type": "CodeGen",
        "dependencies": []
    },
    {
        "id": "wp_002",
        "description": "Add arithmetic operations",
        "agent_type": "CodeGen",
        "dependencies": ["wp_001"]
    }
]
```

This plan creates a basic calculator structure first...'''
        
        planner_agent.llm_service.call_llm.return_value = LLMResponse(
            content=response_content,
            prompt_tokens=150,
            completion_tokens=100,
            cost=0.02
        )
        
        context = {"user_prompt": "Build a calculator"}
        result = planner_agent.execute(context)
        
        assert result["success"] is True
        assert len(result["waypoints"]) == 2
        assert result["waypoints"][0].id == "wp_001"
        # Don't check dependencies as Waypoint model doesn't have that attribute
    
    def test_raw_json_response(self, planner_agent):
        """Test handling of raw JSON response without markdown."""
        response_content = json.dumps([
            {
                "id": "wp_001",
                "description": "Direct JSON response",
                "agent_type": "CodeGen",
                "dependencies": []
            }
        ])
        
        planner_agent.llm_service.call_llm.return_value = LLMResponse(
            content=response_content,
            prompt_tokens=80,
            completion_tokens=40,
            cost=0.008
        )
        
        context = {"user_prompt": "Simple task"}
        result = planner_agent.execute(context)
        
        assert result["success"] is True
        assert len(result["waypoints"]) == 1
        assert result["waypoints"][0].description == "Direct JSON response"
    
    def test_malformed_json_handling(self, planner_agent):
        """Test handling of malformed JSON responses."""
        response_content = "This is not valid JSON at all"
        
        planner_agent.llm_service.call_llm.return_value = LLMResponse(
            content=response_content,
            prompt_tokens=50,
            completion_tokens=20,
            cost=0.005
        )
        
        context = {"user_prompt": "Build something"}
        result = planner_agent.execute(context)
        
        assert result["success"] is False
        assert "Failed to parse waypoints" in result["error"]
        assert result["tokens_used"] == 70
        assert result["cost"] == 0.005


class TestPlannerTelemetry:
    """Test telemetry and decision tracking for PlannerAgent."""
    
    @pytest.fixture
    def planner_agent(self, tmp_path):
        """Create a PlannerAgent with project path set."""
        agent = PlannerAgent(Mock())
        agent.set_project_path(tmp_path)
        return agent
    
    def test_decision_point_tracking(self, planner_agent):
        """Test that decision points are properly tracked."""
        response_content = json.dumps([
            {
                "id": "wp_001",
                "description": "Test waypoint",
                "agent_type": "CodeGen",
                "dependencies": []
            }
        ])
        
        planner_agent.llm_service.call_llm.return_value = LLMResponse(
            content=response_content,
            prompt_tokens=100,
            completion_tokens=50,
            cost=0.01
        )
        
        # Capture decision points
        decision_points = []
        original_log = planner_agent.log_agent_telemetry
        
        def capture_telemetry(*args, **kwargs):
            if "decision_points" in kwargs:
                decision_points.extend(kwargs["decision_points"])
            return original_log(*args, **kwargs)
        
        planner_agent.log_agent_telemetry = capture_telemetry
        
        context = {"user_prompt": "Build a web app"}
        result = planner_agent.execute(context)
        
        # Verify decision points
        assert len(decision_points) > 0
        assert any(dp["description"] == "Planning decomposition strategy" for dp in decision_points)
        assert any(dp["description"] == "Waypoint structure validation" for dp in decision_points)
        assert all("chosen" in dp and "reasoning" in dp for dp in decision_points)
    
    def test_telemetry_with_failed_parsing(self, planner_agent, tmp_path):
        """Test telemetry logging when JSON parsing fails."""
        planner_agent.llm_service.call_llm.return_value = LLMResponse(
            content="Invalid JSON",
            prompt_tokens=50,
            completion_tokens=20,
            cost=0.005
        )
        
        context = {"user_prompt": "Build something"}
        result = planner_agent.execute(context)
        
        # Check telemetry was logged despite failure
        telemetry_file = tmp_path / "logs" / "agent_telemetry.jsonl"
        assert telemetry_file.exists()
        
        with open(telemetry_file, 'r') as f:
            telemetry_data = json.loads(f.readline())
            assert telemetry_data["agent_name"] == "Planner"
            assert telemetry_data["confidence_level"] == 0.0  # No confidence due to failure
            assert telemetry_data["outcome"]["success"] is False


class TestPlannerIntegration:
    """Test full planning workflow integration."""
    
    @pytest.fixture
    def planner_agent(self, tmp_path):
        """Create a PlannerAgent with full setup."""
        agent = PlannerAgent(Mock())
        agent.set_project_path(tmp_path)
        return agent
    
    def test_complex_project_planning(self, planner_agent):
        """Test planning for a complex project with multiple waypoints."""
        response_content = json.dumps([
            {
                "id": "wp_001",
                "description": "Set up project structure and main entry point",
                "agent_type": "CodeGen",
                "dependencies": []
            },
            {
                "id": "wp_002",
                "description": "Create data models",
                "agent_type": "CodeGen",
                "dependencies": ["wp_001"]
            },
            {
                "id": "wp_003",
                "description": "Write tests for data models",
                "agent_type": "TestWriter",
                "dependencies": ["wp_002"]
            },
            {
                "id": "wp_004",
                "description": "Implement business logic",
                "agent_type": "CodeGen",
                "dependencies": ["wp_002"]
            },
            {
                "id": "wp_005",
                "description": "Write tests for business logic",
                "agent_type": "TestWriter",
                "dependencies": ["wp_004"]
            }
        ])
        
        planner_agent.llm_service.call_llm.return_value = LLMResponse(
            content=response_content,
            prompt_tokens=300,
            completion_tokens=200,
            cost=0.05
        )
        
        context = {
            "user_prompt": "Build a task management system with user authentication",
            "model": "gpt-4"
        }
        
        result = planner_agent.execute(context)
        
        assert result["success"] is True
        assert len(result["waypoints"]) == 5
        
        # Verify waypoint structure
        waypoints = result["waypoints"]
        # Just verify the waypoints exist and have the right types
        assert waypoints[0].id == "wp_001"
        assert waypoints[0].agent_type == "CodeGen"
        assert waypoints[2].agent_type == "TestWriter"
        assert waypoints[2].id == "wp_003"  # Tests come after code
        
        # Verify proper agent type distribution
        codegen_count = sum(1 for wp in waypoints if wp.agent_type == "CodeGen")
        testwriter_count = sum(1 for wp in waypoints if wp.agent_type == "TestWriter")
        assert codegen_count == 3
        assert testwriter_count == 2
    
    def test_markdown_with_multiple_code_blocks(self, planner_agent):
        """Test handling response with multiple code blocks."""
        response_content = '''Let me plan this project:

First, here's some example code:
```python
# This is not the waypoints
def example():
    pass
```

Now here are the actual waypoints:

```json
[
    {
        "id": "wp_001",
        "description": "Create main module",
        "agent_type": "CodeGen",
        "dependencies": []
    }
]
```

That should work well.'''
        
        planner_agent.llm_service.call_llm.return_value = LLMResponse(
            content=response_content,
            prompt_tokens=150,
            completion_tokens=100,
            cost=0.025
        )
        
        context = {"user_prompt": "Build something"}
        result = planner_agent.execute(context)
        
        # Should extract the JSON block, not the Python block
        assert result["success"] is True
        assert len(result["waypoints"]) == 1
        assert result["waypoints"][0].id == "wp_001" 