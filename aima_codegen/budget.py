"""Budget and token tracking functionality.
Implements spec_v5.1.md Section 4 - Budget and Token Management
"""
import logging
from typing import Dict, Optional, Tuple
from rich.prompt import Confirm
from rich.console import Console

from .config import config
from .exceptions import BudgetExceededError

logger = logging.getLogger(__name__)
console = Console()

class BudgetTracker:
    """Manages budget tracking and token counting."""
    
    def __init__(self, total_budget: float):
        self.total_budget = total_budget
        self.current_spent = 0.0
        self.model_costs = config.get_model_costs()
    
    def pre_call_check(self, model: str, prompt_tokens: int, max_completion_tokens: int) -> bool:
        """Check if API call would exceed budget. Returns True if OK to proceed.
        Implements spec_v5.1.md Section 4.2 - Pre-API Call Check
        """
        if model not in self.model_costs:
            raise ValueError(f"ERROR: Model '{model}' not found in 'model_costs.json'. "
                           "Suggestion: Please add cost data for this model.")
        
        costs = self.model_costs[model]
        prompt_cost = (prompt_tokens / 1000) * costs["prompt_cost_per_1k_tokens"]
        max_completion_cost = (max_completion_tokens / 1000) * costs["completion_cost_per_1k_tokens"]
        total_call_cost = prompt_cost + max_completion_cost
        
        estimated_future_spent = self.current_spent + total_call_cost
        
        if estimated_future_spent > self.total_budget:
            # Display warning exactly as specified
            remaining = self.total_budget - self.current_spent
            warning = (
                f"WARNING: This action's prompt costs ${prompt_cost:.4f}. "
                f"It may generate up to {max_completion_tokens} tokens, potentially costing "
                f"an additional ${max_completion_cost:.4f}. The maximum total cost could be "
                f"${total_call_cost:.4f}. This may exceed your project budget of "
                f"${self.total_budget:.2f}. Current spent: ${self.current_spent:.2f}. "
                f"Remaining: ${remaining:.2f}. Proceed? (yes/no)"
            )
            console.print(warning, style="yellow")
            return Confirm.ask("Proceed?", default=False)
        
        return True
    
    def update_spent(self, model: str, prompt_tokens: int, completion_tokens: int):
        """Update spent amount after API call.
        Implements spec_v5.1.md Section 4.2 - Post-API Call Update
        """
        costs = self.model_costs[model]
        prompt_cost = (prompt_tokens / 1000) * costs["prompt_cost_per_1k_tokens"]
        completion_cost = (completion_tokens / 1000) * costs["completion_cost_per_1k_tokens"]
        total_cost = prompt_cost + completion_cost
        
        self.current_spent += total_cost
        logger.debug(f"Updated budget: spent ${self.current_spent:.4f} of ${self.total_budget:.2f}")
        
        return total_cost

class TokenCounter:
    """Handles token counting for different providers.
    Implements spec_v5.1.md Section 4.1 - Token Counting Strategy
    """
    
    @staticmethod
    def count_openai_tokens(text: str, model: str) -> int:
        """Count tokens for OpenAI models using tiktoken."""
        try:
            import tiktoken
            # Get the encoding for the model
            try:
                encoding = tiktoken.encoding_for_model(model)
            except KeyError:
                # Fall back to cl100k_base for newer models
                encoding = tiktoken.get_encoding("cl100k_base")
            
            tokens = encoding.encode(text)
            return len(tokens)
        except ImportError:
            logger.error("tiktoken not installed for OpenAI token counting")
            raise
    
    @staticmethod
    def estimate_anthropic_tokens(text: str) -> int:
        """Estimate tokens for Anthropic models.
        Implements spec_v5.1.md Section 4.1 - Anthropic estimation formula
        """
        estimated_tokens = int((len(text) / 3.2) * 1.25)
        logger.warning(f"Using Anthropic token estimation formula: {estimated_tokens} tokens")
        return estimated_tokens
    
    @staticmethod
    def count_google_tokens(text: str, model: str) -> int:
        """Count tokens for Google models."""
        try:
            import google.generativeai as genai
            # Use the SDK's token counting if available
            model_obj = genai.GenerativeModel(model)
            return model_obj.count_tokens(text).total_tokens
        except Exception as e:
            logger.warning(f"Google token counting failed: {e}, using estimation")
            # Fallback estimation
            return len(text) // 4