"""Custom exception classes for the AIMA CodeGen application.
Implements spec_v5.1.md Section 6.1 - Custom Exceptions
"""

class AIMACodeGenError(Exception):
    """Base exception for all AIMA CodeGen errors."""
    pass

class InvalidAPIKeyError(AIMACodeGenError):
    """Raised when API key validation fails."""
    pass

class RateLimitError(AIMACodeGenError):
    """Raised when API rate limit is exceeded."""
    pass

class ServerError(AIMACodeGenError):
    """Raised for API server errors (5xx)."""
    pass

class NetworkError(AIMACodeGenError):
    """Raised for network connectivity issues."""
    pass

class ToolingError(AIMACodeGenError):
    """Raised when external tools (pytest, flake8) fail."""
    pass

class BudgetExceededError(AIMACodeGenError):
    """Raised when operation would exceed budget."""
    pass

class LLMOutputError(AIMACodeGenError):
    """Raised when LLM fails to produce valid output."""
    pass

class LLMAPIError(AIMACodeGenError):
    """General catch-all for other LLM API errors."""
    pass 