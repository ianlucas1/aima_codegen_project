"""Explainer agent implementation.
Implements spec_v5.1.md Section 2.2 - Explainer Agent
"""
import logging
import re
from typing import Dict, Optional

from .base import BaseAgent

logger = logging.getLogger(__name__)

# Security patterns to redact
SECRET_PATTERNS = [
    (r'[0-9a-f]{32,}', 'REDACTED_HEX'),  # Hex encoded secrets/hashes (check first)
    (r'[a-zA-Z0-9+/]{40,}={0,2}', 'REDACTED_BASE64'),  # Base64 encoded secrets
    (r'api[_-]?key\s*=\s*["\'][^"\']+["\']', 'api_key="REDACTED"'),
    (r'password\s*=\s*["\'][^"\']+["\']', 'password="REDACTED"'),
    (r'secret\s*=\s*["\'][^"\']+["\']', 'secret="REDACTED"'),
    (r'token\s*=\s*["\'][^"\']+["\']', 'token="REDACTED"'),
]

class ExplainerAgent(BaseAgent):
    """Generates plain English explanations of code."""
    
    def __init__(self, llm_service):
        super().__init__("Explainer", llm_service)
    
    def _redact_secrets(self, content: str) -> str:
        """Redact potential secrets from content."""
        redacted = content
        redacted_count = 0
        
        for pattern, replacement in SECRET_PATTERNS:
            matches = re.finditer(pattern, redacted, re.IGNORECASE)
            for match in matches:
                redacted_count += 1
                redacted = redacted[:match.start()] + replacement + redacted[match.end():]
        
        if redacted_count > 0:
            logger.info(f"Redacted {redacted_count} potential secrets from content")
        
        return redacted
    
    def execute(self, context: Dict) -> Dict:
        """Generate explanation for code.
        Note: For MVP, only invoked via 'explain' CLI command
        """
        file_path = context.get("file_path", "")
        code_content = context.get("code_content", "")
        target = context.get("target", None)  # function/class name
        structured_format = context.get("structured_format", False)
        decision_points = []
        
        # Redact secrets from code before processing
        safe_code_content = self._redact_secrets(code_content)
        
        # Track decision point: Explanation scope
        scope = "Targeted" if target else "Comprehensive"
        decision_points.append(self.track_decision_point(
            description="Explanation scope selection",
            options=["Targeted", "Comprehensive", "High-level overview"],
            chosen=scope,
            reasoning=f"{'Specific target requested' if target else 'No specific target, explaining entire file'}"
        ))
        
        # Track decision point: Explanation depth
        code_complexity = "Complex" if len(code_content) > 1000 else "Simple"
        decision_points.append(self.track_decision_point(
            description="Explanation depth strategy",
            options=["Beginner-friendly", "Technical", "Balanced"],
            chosen="Beginner-friendly",
            reasoning=f"Code complexity: {code_complexity}, targeting accessible explanation"
        ))
        
        # Track decision point: Output format
        output_format = "Structured" if structured_format else "Natural language"
        decision_points.append(self.track_decision_point(
            description="Output format selection",
            options=["Natural language", "Structured", "Markdown"],
            chosen=output_format,
            reasoning=f"User requested {'structured' if structured_format else 'natural'} format"
        ))
        
        # Build prompt
        if structured_format:
            prompt = self._build_structured_prompt(safe_code_content, target)
        else:
            prompt = self._build_natural_prompt(safe_code_content, target)
        
        messages = [
            {"role": "system", "content": "You are an expert programming instructor."},
            {"role": "user", "content": prompt}
        ]
        
        # Get response from LLM
        response = self.call_llm(
            messages=messages,
            temperature=0.7,
            max_tokens=1000,
            model=context.get("model")
        )
        
        # Track decision point: Explanation quality assessment
        explanation_length = len(response.content)
        decision_points.append(self.track_decision_point(
            description="Explanation quality validation",
            options=["Accept explanation", "Request more detail", "Request simplification"],
            chosen="Accept explanation",
            reasoning=f"Generated {explanation_length} chars of explanation content"
        ))
        
        # High confidence for explanation tasks (simple text generation)
        confidence_level = 0.95
        
        result = {
            "success": True,
            "explanation": response.content,
            "redacted_secrets": code_content != safe_code_content,
            "tokens_used": response.prompt_tokens + response.completion_tokens,
            "cost": response.cost
        }
        
        # Log comprehensive telemetry
        self.log_agent_telemetry(
            context=context,
            llm_response=response,
            result=result,
            decision_points=decision_points,
            confidence_level=confidence_level
        )
        
        # Generate post-task debrief
        debrief = self.generate_debrief(
            context=context,
            result=result,
            decision_points=decision_points,
            confidence_level=confidence_level
        )
        
        return result
    
    def _build_natural_prompt(self, code_content: str, target: Optional[str]) -> str:
        """Build natural language explanation prompt."""
        if target:
            return f"""Please explain the following Python code, specifically focusing on the {target} function/class:

```python
{code_content}
```

Provide a clear, detailed explanation suitable for someone learning Python."""
        else:
            return f"""Please explain the following Python code:

```python
{code_content}
```

Provide a clear, comprehensive explanation of what this code does, suitable for someone learning Python."""
    
    def _build_structured_prompt(self, code_content: str, target: Optional[str]) -> str:
        """Build structured explanation prompt."""
        focus = f"focusing on the {target} function/class" if target else ""
        
        return f"""Please explain the following Python code {focus} in a structured format:

```python
{code_content}
```

Provide your explanation using this structure:

## Overview
[Brief summary of what the code does]

## Key Components
[List and explain main functions/classes]

## How It Works
[Step-by-step explanation of the logic]

## Important Details
[Any special considerations, edge cases, or notable patterns]

## Usage Example
[How to use this code]

Make the explanation suitable for someone learning Python."""