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
        decision_points = []
        
        # Track decision point: Planning approach
        decision_points.append(self.track_decision_point(
            description="Planning decomposition strategy",
            options=["Sequential build", "Feature-first", "Test-driven"],
            chosen="Sequential build",
            reasoning="Ensures logical dependency order and stable foundation"
        ))
        
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
            max_tokens=20000,
            model=context.get("model")
        )
        
        # Add this debug line:
        logger.info(f"Planner LLM response: {response.content[:500] if response.content else 'EMPTY'}")

        # Extract JSON from markdown code blocks if present
        content = response.content
        if "```json" in content:
            # Find the JSON content between code blocks
            lines = content.split('\n')
            json_lines = []
            in_json_block = False
            for line in lines:
                if line.strip().startswith("```json"):
                    in_json_block = True
                    continue
                elif line.strip() == "```" and in_json_block:
                    break
                elif in_json_block:
                    json_lines.append(line)
            content = '\n'.join(json_lines)

        # Parse waypoints from response
        confidence_level = 0.8  # High confidence for structured planning
        result = None
        
        try:
            waypoints_data = json.loads(content)
            waypoints = []
            
            # Track decision point: Waypoint validation
            decision_points.append(self.track_decision_point(
                description="Waypoint structure validation",
                options=["Accept all waypoints", "Filter invalid", "Request regeneration"],
                chosen="Accept all waypoints" if len(waypoints_data) > 0 else "Request regeneration",
                reasoning=f"Found {len(waypoints_data)} waypoints with valid structure"
            ))
            
            for wp_data in waypoints_data:
                # Validate agent_type
                agent_type = wp_data.get("agent_type", "")
                if agent_type not in ["CodeGen", "TestWriter"]:
                    logger.warning(f"Invalid agent_type '{agent_type}' for waypoint {wp_data.get('id', 'unknown')}, defaulting to CodeGen")
                    agent_type = "CodeGen"
                
                waypoint = Waypoint(
                    id=wp_data["id"],
                    description=wp_data["description"],
                    agent_type=agent_type,
                    status="PENDING"
                )
                waypoints.append(waypoint)
            
            result = {
                "success": True,
                "waypoints": waypoints,
                "tokens_used": response.prompt_tokens + response.completion_tokens,
                "cost": response.cost
            }
            
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse planner response: {e}")
            confidence_level = 0.0  # No confidence due to parsing failure
            result = {
                "success": False,
                "error": "Failed to parse waypoints",
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