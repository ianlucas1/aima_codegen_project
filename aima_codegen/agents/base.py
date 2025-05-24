"""Base agent class.
Implements spec_v5.1.md Section 2.2 - Agent Architecture
"""
import logging
import json
import time
from typing import Dict, List, Optional, Any
from abc import ABC, abstractmethod
from pathlib import Path
from datetime import datetime, timezone

from ..models import LLMRequest, LLMResponse, Waypoint
from ..llm import LLMServiceInterface

logger = logging.getLogger(__name__)

class BaseAgent(ABC):
    """Base class for all agents."""
    
    def __init__(self, name: str, llm_service: LLMServiceInterface):
        self.name = name
        self.llm_service = llm_service
        self.logger = logging.getLogger(f"{__name__}.{name}")
        self.telemetry_enabled = True
        self.project_path = None  # Set by orchestrator
    
    @abstractmethod
    def execute(self, context: Dict, **kwargs) -> Dict:
        """Execute the agent's task with given context."""
        pass
    
    def log_agent_telemetry(self, 
                           context: Dict, 
                           llm_response: Optional[LLMResponse] = None,
                           result: Optional[Dict] = None,
                           decision_points: Optional[List[Dict]] = None,
                           confidence_level: Optional[float] = None) -> None:
        """Log comprehensive agent telemetry data."""
        if not self.telemetry_enabled or not self.project_path:
            return
        
        telemetry_data = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "agent_name": self.name,
            "context": {
                "waypoint_id": context.get("waypoint", {}).get("id") if isinstance(context.get("waypoint"), dict) else getattr(context.get("waypoint"), "id", None),
                "waypoint_description": context.get("waypoint", {}).get("description") if isinstance(context.get("waypoint"), dict) else getattr(context.get("waypoint"), "description", None),
                "model": context.get("model"),
                "context_size": len(str(context))
            },
            "llm_interaction": {
                "raw_response": llm_response.content if llm_response else None,
                "prompt_tokens": llm_response.prompt_tokens if llm_response else None,
                "completion_tokens": llm_response.completion_tokens if llm_response else None,
                "cost": llm_response.cost if llm_response else None
            } if llm_response else None,
            "decision_points": decision_points or [],
            "confidence_level": confidence_level,
            "outcome": {
                "success": result.get("success") if result else None,
                "error": result.get("error") if result else None,
                "output_files": list(result.get("code", {}).keys()) if result and result.get("code") else None,
                "dependencies": result.get("dependencies") if result else None
            } if result else None
        }
        
        # Write to telemetry log file
        try:
            telemetry_dir = Path(self.project_path) / "logs"
            telemetry_dir.mkdir(exist_ok=True)
            telemetry_file = telemetry_dir / "agent_telemetry.jsonl"
            
            with open(telemetry_file, "a", encoding="utf-8") as f:
                f.write(json.dumps(telemetry_data) + "\n")
                
        except Exception as e:
            self.logger.warning(f"Failed to write telemetry data: {e}")
    
    def track_decision_point(self, description: str, options: List[str], chosen: str, reasoning: str) -> Dict:
        """Track a decision point during agent execution."""
        return {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "description": description,
            "options": options,
            "chosen": chosen,
            "reasoning": reasoning
        }
    
    def call_llm(self, messages: List[Dict[str, str]], 
                 temperature: float = 0.7, 
                 max_tokens: int = 1000,
                 model: str = None) -> LLMResponse:
        """Make an LLM call through the service interface."""
        start_time = time.time()
        
        request = LLMRequest(
            model=model or "gpt-4.1-2025-04-14",  # Default from config
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens
        )
        
        response = self.llm_service.call_llm(request)
        
        # Log LLM call details
        call_duration = time.time() - start_time
        self.logger.debug(f"LLM call completed in {call_duration:.2f}s - "
                         f"Model: {request.model}, "
                         f"Tokens: {response.prompt_tokens}+{response.completion_tokens}, "
                         f"Cost: ${response.cost:.4f}")
        
        return response
    
    def format_prompt(self, template: str, **kwargs) -> str:
        """Format a prompt template with variables."""
        return template.format(**kwargs)
    
    def set_project_path(self, project_path: Path) -> None:
        """Set the project path for telemetry logging."""
        self.project_path = project_path
        
    def enable_telemetry(self, enabled: bool = True) -> None:
        """Enable or disable telemetry logging."""
        self.telemetry_enabled = enabled
    
    def generate_debrief(self, 
                        context: Dict, 
                        result: Dict, 
                        decision_points: List[Dict],
                        confidence_level: float) -> Dict:
        """Generate structured post-task debrief and self-assessment."""
        debrief = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "agent_name": self.name,
            "task_summary": {
                "waypoint_id": getattr(context.get("waypoint"), "id", None),
                "success": result.get("success", False),
                "duration_estimate": "unknown",  # Could be tracked if needed
                "complexity": self._assess_task_complexity(context)
            },
            "confidence_assessment": {
                "overall_confidence": confidence_level,
                "confidence_factors": self._analyze_confidence_factors(context, result),
                "risk_areas": self._identify_risk_areas(decision_points, result)
            },
            "decision_analysis": {
                "key_decisions": decision_points,
                "decision_quality": self._assess_decision_quality(decision_points),
                "alternative_approaches": self._suggest_alternatives(context, decision_points)
            },
            "lessons_learned": {
                "what_worked_well": self._identify_successes(result, decision_points),
                "challenges_faced": self._identify_challenges(result, decision_points),
                "improvement_opportunities": self._suggest_improvements(context, result)
            },
            "future_recommendations": {
                "for_similar_tasks": self._recommend_for_similar_tasks(context, result),
                "for_follow_up_tasks": self._recommend_follow_ups(context, result),
                "process_improvements": self._suggest_process_improvements(result)
            }
        }
        
        # Save debrief to file
        self._save_debrief(debrief)
        
        return debrief
    
    def _assess_task_complexity(self, context: Dict) -> str:
        """Assess the complexity of the given task."""
        # Basic heuristics for complexity assessment
        context_size = len(str(context))
        if context_size > 5000:
            return "high"
        elif context_size > 2000:
            return "medium"
        else:
            return "low"
    
    def _analyze_confidence_factors(self, context: Dict, result: Dict) -> List[str]:
        """Analyze factors that contributed to confidence level."""
        factors = []
        
        if result.get("success"):
            factors.append("Task completed successfully")
        
        if "raw_content" not in result:
            factors.append("Clean LLM response parsing")
        
        waypoint = context.get("waypoint")
        if waypoint and hasattr(waypoint, "description"):
            if len(waypoint.description) > 50:
                factors.append("Detailed task specification")
            else:
                factors.append("Brief task specification may increase uncertainty")
        
        return factors
    
    def _identify_risk_areas(self, decision_points: List[Dict], result: Dict) -> List[str]:
        """Identify areas of risk or uncertainty."""
        risks = []
        
        if not result.get("success"):
            risks.append("Task execution failed")
        
        # Check for complex decision points
        complex_decisions = [dp for dp in decision_points if len(dp.get("options", [])) > 3]
        if complex_decisions:
            risks.append(f"Complex decisions with {len(complex_decisions)} multi-option choices")
        
        # Check for parsing issues
        if "raw_content" in result:
            risks.append("LLM response required manual parsing")
        
        return risks
    
    def _assess_decision_quality(self, decision_points: List[Dict]) -> str:
        """Assess the quality of decisions made during execution."""
        if not decision_points:
            return "minimal_decisions"
        
        # Simple heuristic: more reasoning = better decisions
        avg_reasoning_length = sum(len(dp.get("reasoning", "")) for dp in decision_points) / len(decision_points)
        
        if avg_reasoning_length > 50:
            return "well_reasoned"
        elif avg_reasoning_length > 20:
            return "adequately_reasoned"
        else:
            return "briefly_reasoned"
    
    def _suggest_alternatives(self, context: Dict, decision_points: List[Dict]) -> List[str]:
        """Suggest alternative approaches that could have been taken."""
        alternatives = []
        
        # Generic alternatives based on agent type
        if self.name == "CodeGen":
            alternatives.extend([
                "Could have generated code incrementally",
                "Could have focused on core functionality first",
                "Could have included more error handling"
            ])
        elif self.name == "TestWriter":
            alternatives.extend([
                "Could have written integration tests",
                "Could have focused on edge cases first",
                "Could have used property-based testing"
            ])
        elif self.name == "Planner":
            alternatives.extend([
                "Could have created more granular waypoints",
                "Could have prioritized core features",
                "Could have considered different architectural approaches"
            ])
        
        return alternatives[:2]  # Limit to most relevant
    
    def _identify_successes(self, result: Dict, decision_points: List[Dict]) -> List[str]:
        """Identify what worked well in the execution."""
        successes = []
        
        if result.get("success"):
            successes.append("Task completed successfully")
        
        if decision_points:
            successes.append("Made informed decisions throughout execution")
        
        if result.get("dependencies"):
            successes.append("Identified necessary dependencies")
        
        return successes
    
    def _identify_challenges(self, result: Dict, decision_points: List[Dict]) -> List[str]:
        """Identify challenges faced during execution."""
        challenges = []
        
        if not result.get("success"):
            challenges.append(f"Task failed: {result.get('error', 'Unknown error')}")
        
        if "raw_content" in result:
            challenges.append("LLM response parsing difficulties")
        
        # Check for decision complexity
        complex_decisions = [dp for dp in decision_points if len(dp.get("options", [])) > 3]
        if complex_decisions:
            challenges.append("Complex decision-making required")
        
        return challenges
    
    def _suggest_improvements(self, context: Dict, result: Dict) -> List[str]:
        """Suggest improvements for future similar tasks."""
        improvements = []
        
        if not result.get("success"):
            improvements.append("Improve error handling and recovery mechanisms")
        
        if "raw_content" in result:
            improvements.append("Enhance LLM prompt structure for better JSON compliance")
        
        # Context-specific improvements
        context_size = len(str(context))
        if context_size > 8000:
            improvements.append("Consider breaking large contexts into smaller chunks")
        
        return improvements
    
    def _recommend_for_similar_tasks(self, context: Dict, result: Dict) -> List[str]:
        """Provide recommendations for similar future tasks."""
        recommendations = []
        
        if result.get("success"):
            recommendations.append("Current approach is effective for similar tasks")
        
        # Agent-specific recommendations
        if self.name == "CodeGen" and result.get("code"):
            recommendations.append("Maintain similar code structure patterns")
        elif self.name == "TestWriter" and result.get("code"):
            recommendations.append("Continue comprehensive test coverage approach")
        
        return recommendations
    
    def _recommend_follow_ups(self, context: Dict, result: Dict) -> List[str]:
        """Recommend follow-up actions."""
        follow_ups = []
        
        if result.get("success") and self.name == "CodeGen":
            follow_ups.append("Consider adding integration tests")
            follow_ups.append("Review code for optimization opportunities")
        
        if not result.get("success"):
            follow_ups.append("Investigate root cause of failure")
            follow_ups.append("Consider alternative implementation approach")
        
        return follow_ups
    
    def _suggest_process_improvements(self, result: Dict) -> List[str]:
        """Suggest improvements to the overall process."""
        improvements = []
        
        if "raw_content" in result:
            improvements.append("Improve LLM response format validation")
        
        improvements.append("Consider confidence-based task routing")
        improvements.append("Implement incremental feedback loops")
        
        return improvements
    
    def _save_debrief(self, debrief: Dict) -> None:
        """Save debrief to structured file."""
        if not self.project_path:
            return
        
        try:
            debrief_dir = Path(self.project_path) / "logs" / "debriefs"
            debrief_dir.mkdir(parents=True, exist_ok=True)
            
            # Save as both individual file and append to master log
            timestamp = debrief["timestamp"].replace(":", "-")
            individual_file = debrief_dir / f"{self.name}_{timestamp}.json"
            
            with open(individual_file, "w", encoding="utf-8") as f:
                json.dump(debrief, f, indent=2)
            
            # Append to master debrief log
            master_log = debrief_dir / "all_debriefs.jsonl"
            with open(master_log, "a", encoding="utf-8") as f:
                f.write(json.dumps(debrief) + "\n")
                
        except Exception as e:
            self.logger.warning(f"Failed to save debrief: {e}")