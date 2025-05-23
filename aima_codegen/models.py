"""Pydantic models for the AIMA CodeGen application.
Implements spec_v5.1.md Appendix B - Core Pydantic Models
"""
from typing import List, Optional, Any, Dict, Literal
from pydantic import BaseModel, Field
import datetime
from abc import ABC, abstractmethod

# --- LLM Interaction ---

class LLMRequest(BaseModel):
    model: str
    messages: List[Dict[str, str]]
    temperature: float = 0.7
    max_tokens: int = 1000

class LLMResponse(BaseModel):
    content: Optional[str] = None
    error_message: Optional[str] = None
    prompt_tokens: int
    completion_tokens: int
    cost: float
    raw_response: Optional[Any] = Field(None, exclude=True)

# --- Revision & Waypoints ---

class RevisionFeedback(BaseModel):
    pytest_output: Optional[str] = None
    flake8_output: Optional[str] = None
    syntax_error: Optional[str] = None

class Waypoint(BaseModel):
    id: str = Field(..., description="Unique ID for the waypoint (e.g., 'wp_001')")
    description: str = Field(..., description="Human-readable task description from Planner")
    agent_type: Literal["CodeGen", "TestWriter", "Explainer", "Planner"]
    status: Literal[
        "PENDING", "RUNNING", "SUCCESS", "FAILED_CODE", "FAILED_TESTS",
        "FAILED_LINT", "FAILED_TOOLING", "FAILED_REVISIONS", "FAILED_LLM_OUTPUT", "ABORTED"
    ] = "PENDING"
    input_files: List[str] = []
    output_files: List[str] = []
    generated_code: Optional[str] = None
    generated_tests: Optional[str] = None
    explanation: Optional[str] = None
    logs: List[str] = []
    revision_attempts: int = 0
    feedback_history: List[RevisionFeedback] = []
    cost: float = 0.0

# --- Project State ---

class ProjectState(BaseModel):
    project_name: str
    project_slug: str
    creation_date: datetime.datetime = Field(default_factory=datetime.datetime.now)
    last_modified: datetime.datetime = Field(default_factory=datetime.datetime.now)
    total_budget_usd: float
    current_spent_usd: float = 0.0
    initial_prompt: str
    waypoints: List[Waypoint] = []
    current_waypoint_index: int = 0
    venv_path: str
    python_path: str  # Path used to *create* the VEnv
    requirements_hash: Optional[str] = None
    api_provider: Optional[str] = None
    model_name: Optional[str] = None

# --- LLM Abstraction Interface ---

class LLMServiceInterface(ABC):
    @abstractmethod
    def call_llm(self, request: LLMRequest) -> LLMResponse:
        pass

    @abstractmethod
    def count_tokens(self, text: str, model: str) -> int:
        pass

    @abstractmethod
    def validate_api_key(self) -> bool:
        pass 