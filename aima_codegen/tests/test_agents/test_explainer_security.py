"""Tests for ExplainerAgent security filtering and output formats."""
import pytest
from unittest.mock import Mock
import json
import logging

from aima_codegen.agents.explainer import ExplainerAgent, SECRET_PATTERNS
from aima_codegen.models import LLMResponse


class TestExplainerSecurity:
    """Test secret redaction and security filtering."""
    
    @pytest.fixture
    def mock_llm_service(self):
        """Create a mock LLM service."""
        return Mock()
    
    @pytest.fixture
    def explainer_agent(self, mock_llm_service):
        """Create an ExplainerAgent instance."""
        return ExplainerAgent(mock_llm_service)
    
    def test_api_key_redaction(self, explainer_agent):
        """Test redaction of API keys."""
        code_with_secrets = '''
API_KEY = "sk-1234567890abcdef"
api_key = "test-api-key-12345"
OPENAI_API_KEY = "sk-proj-abcdef123456"
'''
        
        redacted = explainer_agent._redact_secrets(code_with_secrets)
        
        assert "sk-1234567890abcdef" not in redacted
        assert "test-api-key-12345" not in redacted
        assert "sk-proj-abcdef123456" not in redacted
        assert 'api_key="REDACTED"' in redacted
    
    def test_password_redaction(self, explainer_agent):
        """Test redaction of passwords."""
        code_with_passwords = '''
password = "super_secret_123"
db_password = "mysql_pass_456"
user_password = "admin123"
'''
        
        redacted = explainer_agent._redact_secrets(code_with_passwords)
        
        assert "super_secret_123" not in redacted
        assert "mysql_pass_456" not in redacted
        assert "admin123" not in redacted
        assert redacted.count('password="REDACTED"') == 3
    
    def test_token_and_secret_redaction(self, explainer_agent):
        """Test redaction of tokens and secrets."""
        code_with_tokens = '''
secret = "my_secret_value"
auth_token = "Bearer xyz789abc"
jwt_token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9"
'''
        
        redacted = explainer_agent._redact_secrets(code_with_tokens)
        
        assert "my_secret_value" not in redacted
        assert "Bearer xyz789abc" not in redacted
        assert 'secret="REDACTED"' in redacted
        assert 'token="REDACTED"' in redacted
    
    def test_base64_and_hex_redaction(self, explainer_agent):
        """Test redaction of base64 and hex encoded secrets."""
        code_with_encoded = '''
# Base64 encoded secret (40+ chars)
encoded_secret = "dGhpc2lzYXZlcnlsb25nc2VjcmV0c3RyaW5ndGhhdHNob3VsZGJlcmVkYWN0ZWQ="

# Hex encoded hash (32+ chars)
sha256_hash = "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"
'''
        
        redacted = explainer_agent._redact_secrets(code_with_encoded)
        
        assert "dGhpc2lzYXZlcnlsb25nc2VjcmV0c3RyaW5ndGhhdHNob3VsZGJlcmVkYWN0ZWQ=" not in redacted
        assert "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855" not in redacted
        assert "REDACTED" in redacted
        assert "REDACTED_HEX" in redacted
    
    def test_no_redaction_for_safe_code(self, explainer_agent):
        """Test that safe code is not modified."""
        safe_code = '''
def calculate_sum(a, b):
    """Add two numbers."""
    result = a + b
    return result

class Calculator:
    def __init__(self):
        self.history = []
'''
        
        redacted = explainer_agent._redact_secrets(safe_code)
        
        assert redacted == safe_code  # No changes
    
    def test_redaction_logging(self, explainer_agent, caplog):
        """Test that redaction is logged."""
        code_with_secrets = 'api_key = "secret123"'
        
        # Capture INFO level logs
        with caplog.at_level(logging.INFO):
            redacted = explainer_agent._redact_secrets(code_with_secrets)
        
        assert "Redacted 1 potential secrets from content" in caplog.text


class TestExplainerOutputFormats:
    """Test different output format options."""
    
    @pytest.fixture
    def explainer_agent(self):
        """Create an ExplainerAgent instance."""
        return ExplainerAgent(Mock())
    
    def test_natural_language_format(self, explainer_agent):
        """Test natural language explanation format."""
        code = "def add(a, b): return a + b"
        explanation = "This function adds two numbers together."
        
        explainer_agent.llm_service.call_llm.return_value = LLMResponse(
            content=explanation,
            prompt_tokens=100,
            completion_tokens=50,
            cost=0.01
        )
        
        context = {
            "file_path": "math.py",
            "code_content": code,
            "structured_format": False
        }
        
        result = explainer_agent.execute(context)
        
        assert result["success"] is True
        assert result["explanation"] == explanation
        
        # Check the prompt was built correctly
        call_args = explainer_agent.llm_service.call_llm.call_args
        request = call_args[0][0]  # First positional argument is the LLMRequest
        messages = request.messages
        prompt = messages[1]["content"]
        assert "Please explain the following Python code:" in prompt
        assert code in prompt
    
    def test_structured_format(self, explainer_agent):
        """Test structured explanation format."""
        code = "def multiply(x, y): return x * y"
        structured_explanation = """## Overview
This function performs multiplication of two numbers.

## Key Components
- multiply: A function that takes two parameters

## How It Works
1. Takes two input parameters x and y
2. Returns their product using the * operator

## Important Details
Simple arithmetic operation with no error handling

## Usage Example
result = multiply(5, 3)  # Returns 15"""
        
        explainer_agent.llm_service.call_llm.return_value = LLMResponse(
            content=structured_explanation,
            prompt_tokens=150,
            completion_tokens=100,
            cost=0.02
        )
        
        context = {
            "file_path": "math.py",
            "code_content": code,
            "structured_format": True
        }
        
        result = explainer_agent.execute(context)
        
        assert result["success"] is True
        assert "## Overview" in result["explanation"]
        assert "## Key Components" in result["explanation"]
        
        # Check structured prompt was used
        call_args = explainer_agent.llm_service.call_llm.call_args
        request = call_args[0][0]  # First positional argument is the LLMRequest
        messages = request.messages
        prompt = messages[1]["content"]
        assert "in a structured format:" in prompt
        assert "## Overview" in prompt
    
    def test_targeted_explanation(self, explainer_agent):
        """Test explanation targeting specific function/class."""
        code = '''
def helper():
    return 42

def main():
    """Main function."""
    result = helper()
    print(f"The answer is {result}")
'''
        
        explanation = "The main function calls helper() to get the value 42 and prints it."
        
        explainer_agent.llm_service.call_llm.return_value = LLMResponse(
            content=explanation,
            prompt_tokens=120,
            completion_tokens=60,
            cost=0.015
        )
        
        context = {
            "file_path": "app.py",
            "code_content": code,
            "target": "main",
            "structured_format": False
        }
        
        result = explainer_agent.execute(context)
        
        assert result["success"] is True
        
        # Check target was included in prompt
        call_args = explainer_agent.llm_service.call_llm.call_args
        request = call_args[0][0]  # First positional argument is the LLMRequest
        messages = request.messages
        prompt = messages[1]["content"]
        assert "focusing on the main function/class" in prompt


class TestExplainerDecisionTracking:
    """Test decision point tracking in ExplainerAgent."""
    
    @pytest.fixture
    def explainer_agent(self):
        """Create an ExplainerAgent instance."""
        return ExplainerAgent(Mock())
    
    def test_decision_points_tracked(self, explainer_agent):
        """Test that all decision points are properly tracked."""
        code = "def test(): pass"
        
        explainer_agent.llm_service.call_llm.return_value = LLMResponse(
            content="This is a test function.",
            prompt_tokens=50,
            completion_tokens=25,
            cost=0.005
        )
        
        # Capture decision points
        decision_points = []
        original_log = explainer_agent.log_agent_telemetry
        
        def capture_telemetry(*args, **kwargs):
            if "decision_points" in kwargs:
                decision_points.extend(kwargs["decision_points"])
            return original_log(*args, **kwargs)
        
        explainer_agent.log_agent_telemetry = capture_telemetry
        
        context = {
            "file_path": "test.py",
            "code_content": code,
            "structured_format": True
        }
        
        result = explainer_agent.execute(context)
        
        # Verify all expected decision points
        assert len(decision_points) >= 4
        
        descriptions = [dp["description"] for dp in decision_points]
        assert "Explanation scope selection" in descriptions
        assert "Explanation depth strategy" in descriptions
        assert "Output format selection" in descriptions
        assert "Explanation quality validation" in descriptions
        
        # Check specific decision
        format_decision = next(dp for dp in decision_points if dp["description"] == "Output format selection")
        assert format_decision["chosen"] == "Structured"
        assert "structured" in format_decision["reasoning"]


class TestExplainerTelemetryIntegration:
    """Test full telemetry integration for ExplainerAgent."""
    
    @pytest.fixture
    def explainer_agent(self, tmp_path):
        """Create an ExplainerAgent with project path set."""
        agent = ExplainerAgent(Mock())
        agent.set_project_path(tmp_path)
        return agent
    
    def test_full_explanation_with_redaction(self, explainer_agent, tmp_path):
        """Test full explanation flow with secret redaction."""
        code_with_secrets = '''
class DatabaseConnection:
    """Handles database connections."""
    
    def __init__(self):
        self.host = "localhost"
        self.password = "super_secret_db_pass"
        self.api_key = "sk-1234567890abcdef"
    
    def connect(self):
        """Connect to the database."""
        # Connection logic here
        pass
'''
        
        explanation = """## Overview
This class manages database connections with configuration for host and authentication.

## Key Components
- DatabaseConnection: Main class for database operations
- connect(): Method to establish database connection

## How It Works
1. Initialize with host and credentials
2. Call connect() to establish connection

## Important Details
Credentials are stored as instance variables (security consideration)

## Usage Example
db = DatabaseConnection()
db.connect()"""
        
        explainer_agent.llm_service.call_llm.return_value = LLMResponse(
            content=explanation,
            prompt_tokens=200,
            completion_tokens=150,
            cost=0.03
        )
        
        context = {
            "file_path": "db.py",
            "code_content": code_with_secrets,
            "structured_format": True,
            "model": "gpt-4"
        }
        
        result = explainer_agent.execute(context)
        
        assert result["success"] is True
        assert result["redacted_secrets"] is True  # Secrets were redacted
        
        # Verify secrets were not sent to LLM
        call_args = explainer_agent.llm_service.call_llm.call_args
        request = call_args[0][0]  # First positional argument is the LLMRequest
        messages = request.messages
        prompt = messages[1]["content"]
        assert "super_secret_db_pass" not in prompt
        assert "sk-1234567890abcdef" not in prompt
        assert "REDACTED" in prompt
        
        # Check telemetry
        telemetry_file = tmp_path / "logs" / "agent_telemetry.jsonl"
        assert telemetry_file.exists()
        
        with open(telemetry_file, 'r') as f:
            telemetry_data = json.loads(f.readline())
            assert telemetry_data["agent_name"] == "Explainer"
            assert telemetry_data["confidence_level"] == 0.95  # High confidence for explanations
            assert telemetry_data["outcome"]["success"] is True
        
        # Check debrief
        debrief_dir = tmp_path / "logs" / "debriefs"
        assert debrief_dir.exists()
        debrief_files = list(debrief_dir.glob("Explainer_*.json"))
        assert len(debrief_files) > 0
    
    def test_confidence_level_consistency(self, explainer_agent):
        """Test that confidence level is consistently high for explanations."""
        explainer_agent.llm_service.call_llm.return_value = LLMResponse(
            content="Simple explanation.",
            prompt_tokens=50,
            completion_tokens=25,
            cost=0.005
        )
        
        confidence_levels = []
        original_log = explainer_agent.log_agent_telemetry
        
        def capture_confidence(*args, **kwargs):
            if "confidence_level" in kwargs:
                confidence_levels.append(kwargs["confidence_level"])
            return original_log(*args, **kwargs)
        
        explainer_agent.log_agent_telemetry = capture_confidence
        
        # Test multiple explanations
        for i in range(3):
            context = {
                "file_path": f"file{i}.py",
                "code_content": f"def func{i}(): pass",
                "structured_format": i % 2 == 0
            }
            result = explainer_agent.execute(context)
        
        # All should have high confidence
        assert all(cl == 0.95 for cl in confidence_levels) 