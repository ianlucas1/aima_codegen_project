"""OpenAI adapter implementation.
Implements spec_v5.1.md Section 3.6.1 - OpenAI support
"""
import os
import time
import logging
from typing import Optional

import openai
from openai import OpenAI

from ..models import LLMRequest, LLMResponse
from ..exceptions import (
    InvalidAPIKeyError, RateLimitError, ServerError, 
    NetworkError, LLMAPIError
)
from ..budget import TokenCounter
from .interface import LLMServiceInterface

logger = logging.getLogger(__name__)

class OpenAIAdapter(LLMServiceInterface):
    """OpenAI API adapter."""
    
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.client = OpenAI(api_key=api_key)
    
    def call_llm(self, request: LLMRequest) -> LLMResponse:
        """Make an OpenAI API call with error handling and retries.
        Implements spec_v5.1.md Section 6.1 - LLM Retries
        """
        max_attempts = 3
        
        for attempt in range(1, max_attempts + 1):
            try:
                response = self.client.chat.completions.create(
                    model=request.model,
                    messages=request.messages,
                    temperature=request.temperature,
                    max_tokens=request.max_tokens,
                    timeout=60  # Network timeout from config
                )
                
                # Calculate cost
                prompt_tokens = response.usage.prompt_tokens
                completion_tokens = response.usage.completion_tokens
                
                # Cost calculation will be done by BudgetTracker
                return LLMResponse(
                    content=response.choices[0].message.content,
                    prompt_tokens=prompt_tokens,
                    completion_tokens=completion_tokens,
                    cost=0.0,  # Will be calculated by BudgetTracker
                    raw_response=response
                )
                
            except openai.AuthenticationError as e:
                raise InvalidAPIKeyError(f"OpenAI authentication failed: {e}")
            
            except openai.RateLimitError as e:
                if attempt < max_attempts:
                    delay = min(60, 2 ** attempt)
                    logger.warning(f"Rate limit hit, retrying in {delay}s...")
                    time.sleep(delay)
                    continue
                raise RateLimitError(f"OpenAI rate limit exceeded: {e}")
            
            except openai.APIStatusError as e:
                if e.status_code >= 500:
                    if attempt < max_attempts:
                        delay = min(60, 2 ** attempt)
                        logger.warning(f"Server error, retrying in {delay}s...")
                        time.sleep(delay)
                        continue
                    raise ServerError(f"OpenAI server error: {e}")
                else:
                    raise LLMAPIError(f"OpenAI API error: {e}")
            
            except openai.APITimeoutError as e:
                if attempt < max_attempts:
                    delay = min(60, 2 ** attempt)
                    logger.warning(f"Timeout, retrying in {delay}s...")
                    time.sleep(delay)
                    continue
                raise NetworkError(f"OpenAI timeout: {e}")
            
            except openai.APIConnectionError as e:
                if attempt < max_attempts:
                    delay = min(60, 2 ** attempt)
                    logger.warning(f"Connection error, retrying in {delay}s...")
                    time.sleep(delay)
                    continue
                raise NetworkError(f"OpenAI connection error: {e}")
            
            except Exception as e:
                raise LLMAPIError(f"Unexpected OpenAI error: {e}")
    
    def count_tokens(self, text: str, model: str) -> int:
        """Count tokens using tiktoken.
        Implements spec_v5.1.md Section 4.1 - OpenAI token counting
        """
        return TokenCounter.count_openai_tokens(text, model)
    
    def validate_api_key(self) -> bool:
        """Validate API key with minimal test call.
        Implements spec_v5.1.md Section 7.2 - API Key Validation
        """
        try:
            # Make a minimal API call to validate key
            self.client.models.list()
            return True
        except Exception as e:
            logger.error(f"OpenAI API key validation failed: {e}")
            return False