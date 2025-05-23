"""Planner agent implementation.
Implements spec_v5.1.md Section 2.2 - Planner Agent
"""
import json
import logging
from typing import Dict, List

from .base import BaseAgent
from ..models import Waypoint

logger = logging.getLogger(__name__)

class PlannerAgent(BaseAgent):
    """Decomposes requirements into waypoints."""
    
    def __init__(self, llm_service):
        super().__init__("Planner", llm_service)
    
    def execute(self, context: Dict) -> Dict:
        """Create waypoints from user requirements.
        Implements spec_v5.1.md Appendix C - Structured Prompts
        """
        user_prompt = context.get("user_prompt", "")
        
        # Build structured prompt
        prompt = """### ROLE ###
You are an expert software architect and project planner. Your task is to break down a user's requirements into small, logical, testable waypoints.

### TASK ###
Analyze the following requirements and create a detailed plan of waypoints. Each waypoint should:
- Represent a single, logical, testable change
- Be small enough to implement and test independently
- Build upon previous waypoints
- Include clear success criteria

### REQUIREMENTS ###
{requirements}

### OUTPUT FORMAT ###
Provide a JSON array of waypoint objects, each with:
- "id": Unique identifier (e.g., "wp_001", "wp_002")
- "description": Clear description of what needs to be done
- "agent_type": Either "CodeGen" or "TestWriter"
- "dependencies": Array of waypoint IDs this depends on

Example:
[
  {{
    "id": "wp_001",
    "description": "Create the main application entry point with basic structure",
    "agent_type": "CodeGen",
    "dependencies": []
  }},
  {{
    "id": "wp_002",
    "description": "Write unit tests for the main application entry point",
    "agent_type": "TestWriter",
    "dependencies": ["wp_001"]
  }}
]

### REQUIREMENTS TO ANALYZE ###
{requirements}"""
        
        messages = [
            {"role": "system", "content": "You are an expert software architect."},
            {"role": "user", "content": prompt.format(requirements=user_prompt)}
        ]
        
        # Get response from LLM
        response = self.call_llm(
            messages=messages,
            temperature=0.7,
            max_tokens=2000,
            model=context.get("model")
        )
        
        # Parse waypoints from response
        try:
            waypoints_data = json.loads(response.content)
            waypoints = []
            
            for wp_data in waypoints_data:
                waypoint = Waypoint(
                    id=wp_data["id"],
                    description=wp_data["description"],
                    agent_type=wp_data["agent_type"],
                    status="PENDING"
                )
                waypoints.append(waypoint)
            
            return {
                "success": True,
                "waypoints": waypoints,
                "tokens_used": response.prompt_tokens + response.completion_tokens,
                "cost": response.cost
            }
            
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse planner response: {e}")
            return {
                "success": False,
                "error": "Failed to parse waypoints",
                "tokens_used": response.prompt_tokens + response.completion_tokens,
                "cost": response.cost
            }