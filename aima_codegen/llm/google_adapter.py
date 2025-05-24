"""Google adapter implementation.
Implements spec_v5.1.md Section 3.6.1 - Google support
"""
import os
import time
import logging
from typing import Optional

import google.generativeai as genai
from google.api_core import exceptions as google_exceptions

from ..models import LLMRequest, LLMResponse
from ..exceptions import (
    InvalidAPIKeyError, RateLimitError, ServerError, 
    NetworkError, LLMAPIError
)
from ..budget import TokenCounter
from .interface import LLMServiceInterface

logger = logging.getLogger(__name__)

class GoogleAdapter(LLMServiceInterface):
    """Google Generative AI adapter."""
    
    def __init__(self, api_key: str):
        self.api_key = api_key
        genai.configure(api_key=api_key)
    
    def call_llm(self, request: LLMRequest) -> LLMResponse:
        """Make a Google AI API call with error handling and retries."""
        max_attempts = 3
        
        for attempt in range(1, max_attempts + 1):
            try:
                # Create model instance
                model = genai.GenerativeModel(request.model)
                
                # Convert messages to Google format
                # Google uses a different format - combine into single prompt
                prompt = ""
                for msg in request.messages:
                    role = msg["role"]
                    content = msg["content"]
                    if role == "system":
                        prompt += f"System: {content}\n\n"
                    elif role == "user":
                        prompt += f"User: {content}\n\n"
                    elif role == "assistant":
                        prompt += f"Assistant: {content}\n\n"
                
                # Generate response
                response = model.generate_content(
                    prompt,
                    generation_config=genai.GenerationConfig(
                        temperature=request.temperature,
                        max_output_tokens=request.max_tokens
                    )
                )
                
                # Count tokens - use metadata when available
                prompt_tokens = model.count_tokens(prompt).total_tokens

                # Handle MAX_TOKENS case where response.text is not available
                try:
                    response_text = response.text
                    completion_tokens = model.count_tokens(response_text).total_tokens
                except ValueError as e:
                    # Response hit token limit, return empty string
                    response_text = ""
                    # Use total tokens from metadata minus prompt tokens
                    if hasattr(response, 'usage_metadata'):
                        total_tokens = response.usage_metadata.total_token_count
                        completion_tokens = total_tokens - prompt_tokens
                    else:
                        completion_tokens = 0
                    logger.warning(f"Gemini hit token limit, response truncated")

                return LLMResponse(
                    content=response_text,
                    prompt_tokens=prompt_tokens,
                    completion_tokens=completion_tokens,
                    cost=0.0,  # Will be calculated by BudgetTracker
                    raw_response=response
                )
                
            except google_exceptions.Unauthenticated as e:
                raise InvalidAPIKeyError(f"Google authentication failed: {e}")
            
            except google_exceptions.ResourceExhausted as e:
                if attempt < max_attempts:
                    delay = min(60, 2 ** attempt)
                    logger.warning(f"Rate limit hit, retrying in {delay}s...")
                    time.sleep(delay)
                    continue
                raise RateLimitError(f"Google rate limit exceeded: {e}")
            
            except google_exceptions.InternalServerError as e:
                if attempt < max_attempts:
                    delay = min(60, 2 ** attempt)
                    logger.warning(f"Server error, retrying in {delay}s...")
                    time.sleep(delay)
                    continue
                raise ServerError(f"Google server error: {e}")
            
            except google_exceptions.DeadlineExceeded as e:
                if attempt < max_attempts:
                    delay = min(60, 2 ** attempt)
                    logger.warning(f"Timeout, retrying in {delay}s...")
                    time.sleep(delay)
                    continue
                raise NetworkError(f"Google timeout: {e}")
            
            except Exception as e:
                raise LLMAPIError(f"Unexpected Google error: {e}")
    
    def count_tokens(self, text: str, model: str) -> int:
        """Count tokens for Google models.
        Implements spec_v5.1.md Section 4.1 - Google token counting
        """
        return TokenCounter.count_google_tokens(text, model)
    
    def validate_api_key(self) -> bool:
        """Validate API key with minimal test call."""
        try:
            # List available models as validation
            list(genai.list_models())
            return True
        except Exception as e:
            logger.error(f"Google API key validation failed: {e}")
            return False