"""Tests for budget tracking functionality."""
import pytest
from unittest.mock import Mock, patch
from rich.prompt import Confirm

from aima_codegen.budget import BudgetTracker, TokenCounter
from aima_codegen.config import config


class TestBudgetTracker:
    """Test suite for budget tracking."""
    
    @pytest.fixture
    def model_costs(self):
        """Mock model costs data."""
        return {
            "gpt-4": {
                "prompt_cost_per_1k_tokens": 0.03,
                "completion_cost_per_1k_tokens": 0.06
            },
            "gpt-3.5-turbo": {
                "prompt_cost_per_1k_tokens": 0.0015,
                "completion_cost_per_1k_tokens": 0.002
            }
        }
    
    def test_pre_call_check_within_budget(self, model_costs):
        """Test pre-call check when within budget."""
        with patch.object(config, 'get_model_costs', return_value=model_costs):
            tracker = BudgetTracker(total_budget=10.0)
            
            # Check with small call that fits in budget
            result = tracker.pre_call_check(
                model="gpt-4",
                prompt_tokens=1000,
                max_completion_tokens=1000
            )
            
            assert result is True
    
    def test_pre_call_check_exceeds_budget(self, model_costs):
        """Test pre-call check when exceeding budget."""
        with patch.object(config, 'get_model_costs', return_value=model_costs):
            tracker = BudgetTracker(total_budget=0.1)
            tracker.current_spent = 0.08
            
            # Mock user response to "no"
            with patch('rich.prompt.Confirm.ask', return_value=False):
                result = tracker.pre_call_check(
                    model="gpt-4",
                    prompt_tokens=1000,
                    max_completion_tokens=1000
                )
                
                assert result is False
    
    def test_pre_call_check_user_confirms(self, model_costs):
        """Test pre-call check when user confirms to proceed."""
        with patch.object(config, 'get_model_costs', return_value=model_costs):
            tracker = BudgetTracker(total_budget=0.1)
            tracker.current_spent = 0.08
            
            # Mock user response to "yes"
            with patch('rich.prompt.Confirm.ask', return_value=True):
                result = tracker.pre_call_check(
                    model="gpt-4",
                    prompt_tokens=1000,
                    max_completion_tokens=1000
                )
                
                assert result is True
    
    def test_pre_call_check_missing_model(self, model_costs):
        """Test pre-call check with missing model in costs."""
        with patch.object(config, 'get_model_costs', return_value=model_costs):
            tracker = BudgetTracker(total_budget=10.0)
            
            with pytest.raises(ValueError) as exc_info:
                tracker.pre_call_check(
                    model="unknown-model",
                    prompt_tokens=1000,
                    max_completion_tokens=1000
                )
            
            assert "Model 'unknown-model' not found" in str(exc_info.value)
    
    def test_update_spent(self, model_costs):
        """Test updating spent amount after API call."""
        with patch.object(config, 'get_model_costs', return_value=model_costs):
            tracker = BudgetTracker(total_budget=10.0)
            
            initial_spent = tracker.current_spent
            cost = tracker.update_spent(
                model="gpt-4",
                prompt_tokens=1000,
                completion_tokens=500
            )
            
            expected_cost = (1.0 * 0.03) + (0.5 * 0.06)  # 0.03 + 0.03 = 0.06
            assert cost == pytest.approx(expected_cost)
            assert tracker.current_spent == pytest.approx(initial_spent + expected_cost)


class TestTokenCounter:
    """Test suite for token counting."""
    
    def test_count_openai_tokens(self):
        """Test OpenAI token counting with tiktoken."""
        with patch('tiktoken.encoding_for_model') as mock_encoding:
            # Mock the encoding
            mock_enc = Mock()
            mock_enc.encode.return_value = [1, 2, 3, 4, 5]  # 5 tokens
            mock_encoding.return_value = mock_enc
            
            count = TokenCounter.count_openai_tokens("Hello world", "gpt-4")
            assert count == 5
    
    def test_count_openai_tokens_fallback(self):
        """Test OpenAI token counting with fallback encoding."""
        with patch('tiktoken.encoding_for_model', side_effect=KeyError):
            with patch('tiktoken.get_encoding') as mock_get_encoding:
                mock_enc = Mock()
                mock_enc.encode.return_value = [1, 2, 3, 4]  # 4 tokens
                mock_get_encoding.return_value = mock_enc
                
                count = TokenCounter.count_openai_tokens("Hello world", "new-model")
                assert count == 4
                mock_get_encoding.assert_called_once_with("cl100k_base")
    
    def test_estimate_anthropic_tokens(self):
        """Test Anthropic token estimation formula."""
        # Test the formula: (len(text) / 3.2) * 1.25
        text = "a" * 320  # 320 characters
        
        with patch('logging.Logger.warning') as mock_warning:
            count = TokenCounter.estimate_anthropic_tokens(text)
            
            expected = int((320 / 3.2) * 1.25)  # 125
            assert count == expected
            mock_warning.assert_called_once()
    
    def test_count_google_tokens_success(self):
        """Test Google token counting with SDK."""
        with patch('google.generativeai.GenerativeModel') as mock_model_class:
            mock_model = Mock()
            mock_count_result = Mock()
            mock_count_result.total_tokens = 42
            mock_model.count_tokens.return_value = mock_count_result
            mock_model_class.return_value = mock_model
            
            count = TokenCounter.count_google_tokens("Hello world", "gemini-pro")
            assert count == 42
    
    def test_count_google_tokens_fallback(self):
        """Test Google token counting fallback."""
        with patch('google.generativeai.GenerativeModel', side_effect=Exception("API Error")):
            with patch('logging.Logger.warning') as mock_warning:
                count = TokenCounter.count_google_tokens("Hello world test", "gemini-pro")
                
                # Fallback formula: len(text) // 4
                assert count == len("Hello world test") // 4
                mock_warning.assert_called_once()