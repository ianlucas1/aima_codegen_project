"""Anthropic adapter implementation.
Implements spec_v5.1.md Section 3.6.1 - Anthropic support
"""
import os
import time
import logging
from typing import Optional

import anthropic
from anthropic import Anthropic

from ..models import LLMRequest, LLMResponse
from ..exceptions import (
    InvalidAPIKeyError, RateLimitError, ServerError, 
    NetworkError, LLMAPIError
)
from ..budget import TokenCounter
from .interface import LLMServiceInterface

logger = logging.getLogger(__name__)

class AnthropicAdapter(LLMServiceInterface):
    """Anthropic API adapter."""
    
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.client = Anthropic(api_key=api_key)
    
    def call_llm(self, request: LLMRequest) -> LLMResponse:
        """Make an Anthropic API call with error handling and retries."""
        max_attempts = 3
        
        for attempt in range(1, max_attempts + 1):
            try:
                # Convert messages to Anthropic format
                system_msg = None
                messages = []
                for msg in request.messages:
                    if msg["role"] == "system":
                        system_msg = msg["content"]
                    else:
                        messages.append(msg)
                
                response = self.client.messages.create(
                    model=request.model,
                    messages=messages,
                    system=system_msg,
                    temperature=request.temperature,
                    max_tokens=request.max_tokens,
                    timeout=60
                )
                
                # Get actual token counts from response
                prompt_tokens = response.usage.input_tokens
                completion_tokens = response.usage.output_tokens
                
                return LLMResponse(
                    content=response.content[0].text,
                    prompt_tokens=prompt_tokens,
                    completion_tokens=completion_tokens,
                    cost=0.0,  # Will be calculated by BudgetTracker
                    raw_response=response
                )
                
            except anthropic.AuthenticationError as e:
                raise InvalidAPIKeyError(f"Anthropic authentication failed: {e}")
            
            except anthropic.RateLimitError as e:
                if attempt < max_attempts:
                    delay = min(60, 2 ** attempt)
                    logger.warning(f"Rate limit hit, retrying in {delay}s...")
                    time.sleep(delay)
                    continue
                raise RateLimitError(f"Anthropic rate limit exceeded: {e}")
            
            except anthropic.InternalServerError as e:
                if attempt < max_attempts:
                    delay = min(60, 2 ** attempt)
                    logger.warning(f"Server error, retrying in {delay}s...")
                    time.sleep(delay)
                    continue
                raise ServerError(f"Anthropic server error: {e}")
            
            except anthropic.APITimeoutError as e:
                if attempt < max_attempts:
                    delay = min(60, 2 ** attempt)
                    logger.warning(f"Timeout, retrying in {delay}s...")
                    time.sleep(delay)
                    continue
                raise NetworkError(f"Anthropic timeout: {e}")
            
            except anthropic.APIConnectionError as e:
                if attempt < max_attempts:
                    delay = min(60, 2 ** attempt)
                    logger.warning(f"Connection error, retrying in {delay}s...")
                    time.sleep(delay)
                    continue
                raise NetworkError(f"Anthropic connection error: {e}")
            
            except Exception as e:
                raise LLMAPIError(f"Unexpected Anthropic error: {e}")
    
    def count_tokens(self, text: str, model: str) -> int:
        """Count tokens for Anthropic models.
        Implements spec_v5.1.md Section 4.1 - Anthropic token counting
        """
        # Try to use official method if available
        try:
            if hasattr(self.client, 'count_tokens'):
                return self.client.count_tokens(text=text)
        except Exception:
            pass
        
        # Fall back to estimation formula
        return TokenCounter.estimate_anthropic_tokens(text)
    
    def validate_api_key(self) -> bool:
        """Validate API key with minimal test call."""
        try:
            # Make a minimal API call
            self.client.messages.create(
                model="claude-3-haiku-20240307",
                messages=[{"role": "user", "content": "Hi"}],
                max_tokens=10
            )
            return True
        except Exception as e:
            logger.error(f"Anthropic API key validation failed: {e}")
            return False