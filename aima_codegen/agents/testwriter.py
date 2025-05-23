"""Test writer agent implementation.
Implements spec_v5.1.md Section 2.2 - TestWriter Agent
"""
import json
import logging
from typing import Dict, Optional

from .base import BaseAgent
from ..models import RevisionFeedback

logger = logging.getLogger(__name__)

class TestWriterAgent(BaseAgent):
    """Generates pytest unit tests."""
    
    def __init__(self, llm_service):
        super().__init__("TestWriter", llm_service)
    
    def execute(self, context: Dict) -> Dict:
        """Generate tests for a waypoint."""
        waypoint = context.get("waypoint")
        source_code = context.get("source_code", "")
        project_context = context.get("project_context", "")
        revision_feedback = context.get("revision_feedback", None)
        
        # Build structured prompt
        prompt = self._build_prompt(waypoint, source_code, project_context, revision_feedback)
        
        messages = [
            {"role": "system", "content": "You are an expert Python test engineer."},
            {"role": "user", "content": prompt}
        ]
        
        # Get response from LLM
        response = self.call_llm(
            messages=messages,
            temperature=0.2,
            max_tokens=4000,
            model=context.get("model")
        )
        
        # Parse test code from response
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
            logger.error(f"Failed to parse TestWriter response: {e}")
            return {
                "success": False,
                "error": "Failed to parse generated tests",
                "raw_content": response.content,
                "tokens_used": response.prompt_tokens + response.completion_tokens,
                "cost": response.cost
            }
    
    def _build_prompt(self, waypoint, source_code: str, project_context: str,
                     revision_feedback: Optional[RevisionFeedback]) -> str:
        """Build the structured prompt for test generation."""
        prompt = """### ROLE ###
You are an expert Python test engineer. Your task is to write comprehensive pytest unit tests for the provided code.

### SOURCE CODE TO TEST ###
{source_code}

### CONTEXT ###
{context}

### TASK ###
{task}

### REQUIREMENTS ###
- Write pytest tests that thoroughly test the functionality
- Include edge cases and error scenarios
- Use appropriate pytest fixtures and markers
- Follow pytest best practices
- Output MUST be valid JSON as specified

"""
        
        if revision_feedback:
            feedback_json = revision_feedback.model_dump_json(exclude_none=True)
            prompt += f"""
### REVISION FEEDBACK ###
{feedback_json}
"The previous tests failed. Fix all identified issues and ensure tests pass."
"""
        
        prompt += """
### OUTPUT FORMAT ###
Provide *only* a JSON object with two keys: `code` and `dependencies`.
- `code`: Dictionary with test file paths and content
- `dependencies`: List of required packages (should include "pytest")

Example:
```json
{
  "code": {
    "src/tests/test_app.py": "import pytest\\nfrom src.app import add\\n\\ndef test_add():\\n    assert add(2, 3) == 5\\n"
  },
  "dependencies": ["pytest"]
}
```"""
        
        return prompt.format(
            source_code=source_code,
            context=project_context,
            task=waypoint.description
        )