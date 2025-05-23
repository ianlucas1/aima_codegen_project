"""LLM Service Interface.
Implements spec_v5.1.md Section 3.6.1 - Multi-Model Support & API Abstraction
"""
from abc import ABC, abstractmethod
from ..models import LLMRequest, LLMResponse

class LLMServiceInterface(ABC):
    """Abstract interface for LLM service providers."""
    
    @abstractmethod
    def call_llm(self, request: LLMRequest) -> LLMResponse:
        """Make an LLM API call."""
        pass
    
    @abstractmethod
    def count_tokens(self, text: str, model: str) -> int:
        """Count tokens for the given text and model."""
        pass
    
    @abstractmethod
    def validate_api_key(self) -> bool:
        """Validate the API key with a minimal test call."""
        pass