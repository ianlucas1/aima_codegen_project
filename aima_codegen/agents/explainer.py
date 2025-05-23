"""Explainer agent implementation.
Implements spec_v5.1.md Section 2.2 - Explainer Agent
"""
import logging
from typing import Dict, Optional

from .base import BaseAgent

logger = logging.getLogger(__name__)

class ExplainerAgent(BaseAgent):
    """Generates plain English explanations of code."""
    
    def __init__(self, llm_service):
        super().__init__("Explainer", llm_service)
    
    def execute(self, context: Dict) -> Dict:
        """Generate explanation for code.
        Note: For MVP, only invoked via 'explain' CLI command
        """
        file_path = context.get("file_path", "")
        code_content = context.get("code_content", "")
        target = context.get("target", None)  # function/class name
        
        # Build prompt
        if target:
            prompt = f"""Please explain the following Python code, specifically focusing on the {target} function/class:

```python
{code_content}
```

Provide a clear, detailed explanation suitable for someone learning Python."""
        else:
            prompt = f"""Please explain the following Python code:

```python
{code_content}
```

Provide a clear, comprehensive explanation of what this code does, suitable for someone learning Python."""
        
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
        
        return {
            "success": True,
            "explanation": response.content,
            "tokens_used": response.prompt_tokens + response.completion_tokens,
            "cost": response.cost
        }