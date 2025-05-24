"""Tests for LLM adapters."""
import pytest
from unittest.mock import Mock, patch, MagicMock

from aima_codegen.llm import OpenAIAdapter, AnthropicAdapter, GoogleAdapter
from aima_codegen.models import LLMRequest, LLMResponse
from aima_codegen.exceptions import (
    InvalidAPIKeyError, RateLimitError, ServerError, NetworkError
)


class TestOpenAIAdapter:
    """Test suite for OpenAI adapter."""
    
    def test_call_llm_success(self):
        """Test successful LLM call."""
        with patch('aima_codegen.llm.openai_adapter.OpenAI') as mock_openai_class:
            mock_client = Mock()
            mock_openai_class.return_value = mock_client
            
            # Mock response
            mock_response = Mock()
            mock_response.choices = [Mock(message=Mock(content="Hello, world!"))]
            mock_response.usage = Mock(prompt_tokens=10, completion_tokens=5)
            mock_client.chat.completions.create.return_value = mock_response
            
            adapter = OpenAIAdapter("test-key")
            request = LLMRequest(
                model="gpt-4",
                messages=[{"role": "user", "content": "Hello"}],
                temperature=0.7,
                max_tokens=100
            )
            
            response = adapter.call_llm(request)
            
            assert response.content == "Hello, world!"
            assert response.prompt_tokens == 10
            assert response.completion_tokens == 5
    
    def test_call_llm_auth_error(self):
        """Test authentication error handling."""
        with patch('aima_codegen.llm.openai_adapter.OpenAI') as mock_openai_class:
            mock_client = Mock()
            mock_openai_class.return_value = mock_client
            
            # Mock auth error
            import openai
            mock_client.chat.completions.create.side_effect = openai.AuthenticationError(
                "Invalid API key",
                response=Mock(),
                body={}
            )
            
            adapter = OpenAIAdapter("bad-key")
            request = LLMRequest(
                model="gpt-4",
                messages=[{"role": "user", "content": "Hello"}]
            )
            
            with pytest.raises(InvalidAPIKeyError):
                adapter.call_llm(request)
    
    def test_call_llm_rate_limit_with_retry(self):
        """Test rate limit error with retry."""
        with patch('aima_codegen.llm.openai_adapter.OpenAI') as mock_openai_class:
            mock_client = Mock()
            mock_openai_class.return_value = mock_client
            
            # First call fails with rate limit, second succeeds
            import openai
            mock_response = Mock()
            mock_response.choices = [Mock(message=Mock(content="Success!"))]
            mock_response.usage = Mock(prompt_tokens=10, completion_tokens=5)
            
            mock_client.chat.completions.create.side_effect = [
                openai.RateLimitError("Rate limit", response=Mock(), body={}),
                mock_response
            ]
            
            adapter = OpenAIAdapter("test-key")
            request = LLMRequest(
                model="gpt-4",
                messages=[{"role": "user", "content": "Hello"}]
            )
            
            with patch('time.sleep'):  # Speed up test
                response = adapter.call_llm(request)
            
            assert response.content == "Success!"
            assert mock_client.chat.completions.create.call_count == 2
    
    def test_validate_api_key_success(self):
        """Test successful API key validation."""
        with patch('aima_codegen.llm.openai_adapter.OpenAI') as mock_openai_class:
            mock_client = Mock()
            mock_openai_class.return_value = mock_client
            mock_client.models.list.return_value = ["gpt-4", "gpt-3.5"]
            
            adapter = OpenAIAdapter("test-key")
            assert adapter.validate_api_key() is True
    
    def test_validate_api_key_failure(self):
        """Test failed API key validation."""
        with patch('aima_codegen.llm.openai_adapter.OpenAI') as mock_openai_class:
            mock_client = Mock()
            mock_openai_class.return_value = mock_client
            mock_client.models.list.side_effect = Exception("Invalid key")
            
            adapter = OpenAIAdapter("bad-key")
            assert adapter.validate_api_key() is False


class TestAnthropicAdapter:
    """Test suite for Anthropic adapter."""
    
    def test_call_llm_success(self):
        """Test successful Anthropic API call."""
        with patch('aima_codegen.llm.anthropic_adapter.Anthropic') as mock_anthropic_class:
            mock_client = Mock()
            mock_anthropic_class.return_value = mock_client
            
            # Mock response
            mock_response = Mock()
            mock_response.content = [Mock(text="Claude response")]
            mock_response.usage = Mock(input_tokens=15, output_tokens=8)
            mock_client.messages.create.return_value = mock_response
            
            adapter = AnthropicAdapter("test-key")
            request = LLMRequest(
                model="claude-3-opus",
                messages=[
                    {"role": "system", "content": "You are helpful"},
                    {"role": "user", "content": "Hello"}
                ]
            )
            
            response = adapter.call_llm(request)
            
            assert response.content == "Claude response"
            assert response.prompt_tokens == 15
            assert response.completion_tokens == 8
            
            # Verify system message handling
            create_call = mock_client.messages.create.call_args
            assert create_call.kwargs["system"] == "You are helpful"
            assert len(create_call.kwargs["messages"]) == 1
    
    def test_count_tokens_estimation(self):
        """Test Anthropic token estimation."""
        adapter = AnthropicAdapter("test-key")
        
        with patch('aima_codegen.budget.TokenCounter.estimate_anthropic_tokens', return_value=100):
            count = adapter.count_tokens("Test text", "claude-3")
            assert count == 100


class TestGoogleAdapter:
    """Test suite for Google adapter."""
    
    def test_call_llm_success(self):
        """Test successful Google AI API call."""
        with patch('google.generativeai.configure'):
            with patch('google.generativeai.GenerativeModel') as mock_model_class:
                mock_model = Mock()
                mock_model_class.return_value = mock_model
                
                # Mock response
                mock_response = Mock()
                mock_response.text = "Gemini response"
                mock_model.generate_content.return_value = mock_response
                
                # Mock token counting
                mock_model.count_tokens.side_effect = [
                    Mock(total_tokens=20),  # prompt
                    Mock(total_tokens=10)   # completion
                ]
                
                adapter = GoogleAdapter("test-key")
                request = LLMRequest(
                    model="gemini-pro",
                    messages=[
                        {"role": "system", "content": "Be helpful"},
                        {"role": "user", "content": "Hello"},
                        {"role": "assistant", "content": "Hi there"},
                        {"role": "user", "content": "How are you?"}
                    ]
                )
                
                response = adapter.call_llm(request)
                
                assert response.content == "Gemini response"
                assert response.prompt_tokens == 20
                assert response.completion_tokens == 10
                
                # Verify prompt formatting
                generate_call = mock_model.generate_content.call_args
                prompt = generate_call[0][0]
                assert "System: Be helpful" in prompt
                assert "User: Hello" in prompt
                assert "Assistant: Hi there" in prompt
                assert "User: How are you?" in prompt
    
    def test_validate_api_key_success(self):
        """Test successful Google API key validation."""
        with patch('google.generativeai.configure'):
            with patch('google.generativeai.list_models', return_value=["gemini-pro"]):
                adapter = GoogleAdapter("test-key")
                assert adapter.validate_api_key() is True
    
    def test_call_llm_auth_error(self):
        """Test Google authentication error."""
        with patch('google.generativeai.configure'):
            with patch('google.generativeai.GenerativeModel') as mock_model_class:
                mock_model = Mock()
                mock_model_class.return_value = mock_model
                
                # Mock auth error
                from google.api_core import exceptions as google_exceptions
                mock_model.generate_content.side_effect = google_exceptions.Unauthenticated("Bad key")
                
                adapter = GoogleAdapter("bad-key")
                request = LLMRequest(
                    model="gemini-pro",
                    messages=[{"role": "user", "content": "Hello"}]
                )
                
                with pytest.raises(InvalidAPIKeyError):
                    adapter.call_llm(request)