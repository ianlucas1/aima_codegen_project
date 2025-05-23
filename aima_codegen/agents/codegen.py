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
        try:
            result = json.loads(response.content)
            
            return {
                "success": True,
                "code": result.get("code", {}),
                "dependencies": result.get("dependencies", []),
                "tokens_used": response.prompt_tokens + response.completion_tokens,
                "cost": response.cost
            }
            
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse CodeGen response: {e}")
            return {
                "success": False,
                "error": "Failed to parse generated code",
                "raw_content": response.content,
                "tokens_used": response.prompt_tokens + response.completion_tokens,
                "cost": response.cost
            }
    
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