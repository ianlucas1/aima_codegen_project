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
        decision_points = []
        
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