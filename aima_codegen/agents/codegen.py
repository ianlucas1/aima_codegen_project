"""Code generation agent implementation.
Implements spec_v5.1.md Section 2.2 - CodeGen Agent
"""
import json
import logging
from typing import Dict, List, Optional

from .base import BaseAgent
from ..models import RevisionFeedback

logger = logging.getLogger(__name__)

class CodeGenAgent(BaseAgent):
    """Generates Python code and identifies dependencies."""
    
    def __init__(self, llm_service):
        super().__init__("CodeGen", llm_service)
    
    def execute(self, context: Dict) -> Dict:
        """Generate code for a waypoint.
        Implements spec_v5.1.md Appendix C.2 - CodeGen Agent Prompt
        """
        waypoint = context.get("waypoint")
        project_context = context.get("project_context", "")
        revision_feedback = context.get("revision_feedback", None)
        decision_points = []
        
        # Track decision point: Code generation approach
        approach = "Revision" if revision_feedback else "Initial generation"
        decision_points.append(self.track_decision_point(
            description="Code generation mode",
            options=["Initial generation", "Revision", "Enhancement"],
            chosen=approach,
            reasoning=f"{'Addressing feedback' if revision_feedback else 'Fresh implementation'}"
        ))
        
        # Track decision point: Template selection
        has_context = len(project_context) > 100
        decision_points.append(self.track_decision_point(
            description="Context utilization strategy",
            options=["Full context", "Minimal context", "No context"],
            chosen="Full context" if has_context else "Minimal context",
            reasoning=f"Context size: {len(project_context)} chars"
        ))
        
        # Build structured prompt
        prompt = self._build_prompt(waypoint, project_context, revision_feedback)
        
        messages = [
            {"role": "system", "content": "You are an expert Python developer."},
            {"role": "user", "content": prompt}
        ]
        
        # Get response from LLM
        response = self.call_llm(
            messages=messages,
            temperature=0.2,  # Lower temperature for code generation
            max_tokens=4000,
            model=context.get("model")
        )
        
        # Parse code and dependencies from response
        confidence_level = 0.7  # Moderate confidence for code generation
        result = None
        
        try:
            parsed_result = json.loads(response.content)
            
            # Track decision point: Output validation
            num_files = len(parsed_result.get("code", {}))
            num_deps = len(parsed_result.get("dependencies", []))
            decision_points.append(self.track_decision_point(
                description="Output structure validation",
                options=["Accept output", "Request corrections", "Manual intervention"],
                chosen="Accept output",
                reasoning=f"Generated {num_files} files and {num_deps} dependencies"
            ))
            
            confidence_level = 0.9  # High confidence for successful parsing
            result = {
                "success": True,
                "code": parsed_result.get("code", {}),
                "dependencies": parsed_result.get("dependencies", []),
                "tokens_used": response.prompt_tokens + response.completion_tokens,
                "cost": response.cost
            }
            
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse CodeGen response: {e}")
            confidence_level = 0.1  # Very low confidence due to parsing failure
            decision_points.append(self.track_decision_point(
                description="JSON parsing failure",
                options=["Retry with clarification", "Manual parsing", "Request regeneration"],
                chosen="Request regeneration",
                reasoning=f"JSON parsing failed: {str(e)}"
            ))
            
            result = {
                "success": False,
                "error": "Failed to parse generated code",
                "raw_content": response.content,
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
    
    def _build_prompt(self, waypoint, project_context: str, 
                     revision_feedback: Optional[RevisionFeedback]) -> str:
        """Build the structured prompt for code generation."""
        prompt = """### ROLE ###
You are an expert Python developer. Your task is to write clean, efficient, PEP 8 compliant code based on the provided task, context, and requirements. You MUST also identify any new Python package dependencies required and list them. **You MUST output your response in the specified JSON format.**

### CONTEXT ###
{context}

### TASK ###
{task}

### REQUIREMENTS / CONSTRAINTS ###
- MUST use Python 3.10+.
- Adhere strictly to PEP 8.
- If new libraries are needed, list them (e.g., "requests", "pandas>=1.3.0").
- **Output MUST be a single, valid JSON object as specified.**
"""
        
        if revision_feedback:
            # Add revision feedback section
            feedback_json = revision_feedback.model_dump_json(exclude_none=True)
            prompt += f"""
### REVISION FEEDBACK (Optional) ###
{feedback_json}
"The previous attempt failed. Analyze the feedback above and regenerate the code for the affected files, fixing *all* identified issues. Ensure your output is valid JSON."
"""
        
        prompt += """
### OUTPUT FORMAT ###
Provide *only* a JSON object with two keys: `code` and `dependencies`.
- `code`: A dictionary where keys are file paths (e.g., `"src/app.py"`) and values are the full file content to write.
- `dependencies`: A list of required packages (strings, e.g., `["requests", "pandas==1.3.0"]`).

Example:
```json
{
  "code": {
    "src/app.py": "def add(a, b):\\n    return a + b\\n"
  },
  "dependencies": []
}
```"""
        
        return prompt.format(
            context=project_context,
            task=waypoint.description
        )