"""Base agent class.
Implements spec_v5.1.md Section 2.2 - Agent Architecture
"""
import logging
from typing import Dict, List, Optional
from abc import ABC, abstractmethod

from ..models import LLMRequest, LLMResponse, Waypoint
from ..llm import LLMServiceInterface

logger = logging.getLogger(__name__)

class BaseAgent(ABC):
    """Base class for all agents."""
    
    def __init__(self, name: str, llm_service: LLMServiceInterface):
        self.name = name
        self.llm_service = llm_service
        self.logger = logging.getLogger(f"{__name__}.{name}")
    
    @abstractmethod
    def execute(self, context: Dict, **kwargs) -> Dict:
        """Execute the agent's task with given context."""
        pass
    
    def call_llm(self, messages: List[Dict[str, str]], 
                 temperature: float = 0.7, 
                 max_tokens: int = 1000,
                 model: str = None) -> LLMResponse:
        """Make an LLM call through the service interface."""
        request = LLMRequest(
            model=model or "gpt-4.1-2025-04-14",  # Default from config
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens
        )
        
        return self.llm_service.call_llm(request)
    
    def format_prompt(self, template: str, **kwargs) -> str:
        """Format a prompt template with variables."""
        return template.format(**kwargs)