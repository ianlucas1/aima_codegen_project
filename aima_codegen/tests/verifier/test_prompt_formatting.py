"""Test prompt formatting with and without feedback_json."""
import pytest
from unittest.mock import MagicMock, patch
from aima_codegen.agents.codegen import CodeGenAgent
from aima_codegen.agents.testwriter import TestWriterAgent


class TestPromptFormatting:
    """Test prompt formatting in agents."""

    def test_codegen_prompt_without_feedback(self):
        """Test CodeGenAgent prompt formatting without feedback_json."""
        # Mock LLM service
        mock_llm = MagicMock()
        agent = CodeGenAgent(mock_llm)
        
        # Test that agent can handle missing feedback_json
        context = {
            'waypoint': MagicMock(description='Test function', id='test_func'),
            'requirements': 'Should work',
            'model': 'test-model'
        }
        
        # Should not raise KeyError when feedback_json is missing
        with patch.object(agent, 'call_llm') as mock_call:
            mock_call.return_value = MagicMock(content='{"code": {"test.py": "def test(): pass"}, "dependencies": []}')
            result = agent.execute(context)
            assert 'error' not in result or 'KeyError' not in str(result.get('error', ''))

    def test_codegen_prompt_with_feedback(self):
        """Test CodeGenAgent prompt formatting with feedback_json."""
        mock_llm = MagicMock()
        agent = CodeGenAgent(mock_llm)
        
        context = {
            'waypoint': MagicMock(description='Test function', id='test_func'),
            'requirements': 'Should work',
            'model': 'test-model',
            'feedback_json': {'error': 'Test error', 'suggestion': 'Fix it'}
        }
        
        with patch.object(agent, 'call_llm') as mock_call:
            mock_call.return_value = MagicMock(content='{"code": {"test.py": "def test(): pass"}, "dependencies": []}')
            result = agent.execute(context)
            # Should execute without errors
            assert 'error' not in result or 'KeyError' not in str(result.get('error', ''))

    def test_testwriter_prompt_without_feedback(self):
        """Test TestWriterAgent prompt formatting without feedback_json."""
        mock_llm = MagicMock()
        agent = TestWriterAgent(mock_llm)
        
        context = {
            'waypoint': MagicMock(description='Write tests', id='test_task'),
            'code': {'module.py': 'def test_func(): pass'},
            'model': 'test-model'
        }
        
        # Should not raise KeyError
        with patch.object(agent, 'call_llm') as mock_call:
            mock_call.return_value = MagicMock(content='{"test_code": {"test_module.py": "def test_func(): assert True"}, "dependencies": ["pytest"]}')
            result = agent.execute(context)
            assert 'error' not in result or 'KeyError' not in str(result.get('error', ''))

    def test_testwriter_prompt_with_feedback(self):
        """Test TestWriterAgent prompt formatting with feedback_json."""
        mock_llm = MagicMock()
        agent = TestWriterAgent(mock_llm)
        
        context = {
            'waypoint': MagicMock(description='Write tests', id='test_task'),
            'code': {'module.py': 'def test_func(): pass'},
            'model': 'test-model',
            'feedback_json': {'test_failures': ['Test 1 failed'], 'coverage': 80}
        }
        
        with patch.object(agent, 'call_llm') as mock_call:
            mock_call.return_value = MagicMock(content='{"test_code": {"test_module.py": "def test_func(): assert True"}, "dependencies": ["pytest"]}')
            result = agent.execute(context)
            assert 'error' not in result or 'KeyError' not in str(result.get('error', ''))

    def test_prompt_template_formatting(self):
        """Test direct prompt template formatting."""
        mock_llm = MagicMock()
        agent = CodeGenAgent(mock_llm)
        
        # Test the format_prompt method directly if it exists
        if hasattr(agent, 'format_prompt'):
            prompt = agent.format_prompt(
                "Generate {function_name} with {requirements}",
                function_name="test_func",
                requirements="Should work"
            )
            assert 'test_func' in prompt
            assert 'Should work' in prompt 