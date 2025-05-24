# API Reference

This document provides a comprehensive API reference for the new features in AIMA CodeGen: GitHub Integration, GUI Application, and Multi-Model Configuration.

## Table of Contents
- [GitHub Integration API](#github-integration-api)
  - [ReviewerAgent](#revieweragent)
  - [GitHubIntegration](#githubintegration)
  - [GitOperations](#gitoperations)
- [GUI Application API](#gui-application-api)
  - [AIMACodeGenGUI](#aimacodegengui)
  - [Dialog Classes](#dialog-classes)
- [Multi-Model API](#multi-model-api)
  - [MultiModelManager](#multimodelmanager)
  - [AgentModelConfig](#agentmodelconfig)
  - [ModelPresets](#modelpresets)
  - [MultiModelOrchestrator](#multimodelorchestrator)
- [Extension Points](#extension-points)

## GitHub Integration API

### ReviewerAgent

**Location**: `aima_codegen/agents/reviewer.py`

The ReviewerAgent performs AI-powered code review and manages GitHub integration.

```python
class ReviewerAgent(BaseAgent):
    def __init__(self, llm_service: LLMServiceInterface, github_token: Optional[str] = None)
```

#### Methods

##### execute(context: Dict) -> Dict
Executes the reviewer agent action based on context.

**Parameters:**
- `context`: Dictionary containing:
  - `action`: One of "review", "create_pr", "merge_pr"
  - `waypoint`: Waypoint object (for review)
  - `code_changes`: Dict of file paths to content
  - `project_path`: Path to project (for PR actions)
  - `branch_name`: Branch name (for PR creation)
  - `pr_title`: PR title
  - `pr_body`: PR description

**Returns:** Dictionary with results based on action

**Example:**
```python
reviewer = ReviewerAgent(llm_service, github_token)
result = reviewer.execute({
    "action": "review",
    "waypoint": waypoint,
    "code_changes": {"src/app.py": "def main():..."},
    "project_context": "Calculator app"
})
```

### GitHubIntegration

**Location**: `aima_codegen/github/integration.py`

Manages GitHub API interactions.

```python
class GitHubIntegration:
    def __init__(self, token: Optional[str] = None)
```

#### Methods

##### create_pull_request(repo: str, title: str, body: str, head: str, base: str = "main") -> Dict
Creates a pull request via GitHub API.

**Parameters:**
- `repo`: Repository in "owner/name" format
- `title`: PR title
- `body`: PR description
- `head`: Source branch
- `base`: Target branch (default: "main")

**Returns:** Dict with `success`, `number`, `url`, `id`

##### get_pull_request(repo: str, pr_number: int) -> Dict
Retrieves pull request details.

**Returns:** GitHub PR object

##### merge_pull_request(repo: str, pr_number: int, merge_method: str = "merge") -> Dict
Merges a pull request.

**Parameters:**
- `merge_method`: One of "merge", "squash", "rebase"

**Returns:** Dict with `success`, `sha`, `message`

##### create_issue_comment(repo: str, issue_number: int, body: str) -> Dict
Adds a comment to a PR or issue.

##### get_pr_files(repo: str, pr_number: int) -> List[Dict]
Gets list of files changed in a PR.

##### setup_webhook(repo: str, url: str, events: List[str]) -> Dict
Sets up webhook for repository events.

### GitOperations

**Location**: `aima_codegen/github/integration.py`

Static methods for local git operations.

```python
class GitOperations:
    # All methods are static
```

#### Static Methods

##### init_repo(project_path: Path) -> bool
Initializes git repository if not exists.

##### create_branch(project_path: Path, branch_name: str) -> bool
Creates and checks out a new branch.

##### commit_changes(project_path: Path, message: str, files: List[str] = None) -> bool
Stages and commits changes.

**Parameters:**
- `files`: Specific files to stage (None = all)

##### push_branch(project_path: Path, branch_name: str, remote: str = "origin") -> bool
Pushes branch to remote.

##### get_current_branch(project_path: Path) -> Optional[str]
Returns current branch name.

##### get_remote_url(project_path: Path, remote: str = "origin") -> Optional[str]
Returns remote repository URL.

## GUI Application API

### AIMACodeGenGUI

**Location**: `aima_codegen/gui/main_window.py`

Main GUI application class.

```python
class AIMACodeGenGUI:
    def __init__(self)
```

#### Key Attributes

- `orchestrator`: Orchestrator instance
- `current_project`: Current project name
- `message_queue`: Thread communication queue
- `project_name_var`: Tkinter variable for project name
- `budget_var`: Tkinter variable for budget display
- `requirements_text`: Text widget for requirements
- `waypoints_tree`: Treeview for waypoints
- `log_text`: ScrolledText for logs

#### Methods

##### run()
Starts the GUI event loop.

##### _new_project()
Opens new project dialog.

##### _load_project()
Opens load project dialog.

##### _start_development()
Begins development process with current requirements.

##### _configure_multi_model()
Configures multi-model settings based on GUI selections.

##### _log(level: str, message: str)
Adds log message to queue for thread-safe logging.

**Parameters:**
- `level`: One of "info", "success", "error", "warning"
- `message`: Log message

### Dialog Classes

#### NewProjectDialog

**Location**: `aima_codegen/gui/main_window.py`

Dialog for creating new projects.

```python
class NewProjectDialog:
    def __init__(self, parent)
```

**Attributes:**
- `result`: Tuple of (name, budget) or None

#### LoadProjectDialog

Dialog for loading existing projects.

```python
class LoadProjectDialog:
    def __init__(self, parent, projects: List[str])
```

**Parameters:**
- `projects`: List of available project names

#### APIKeyDialog

Dialog for configuring API keys.

```python
class APIKeyDialog:
    def __init__(self, parent)
```

Creates tabbed interface for OpenAI, Anthropic, and Google API keys.

#### ModelSettingsDialog

Dialog for model configuration.

```python
class ModelSettingsDialog:
    def __init__(self, parent)
```

#### GitHubSettingsDialog

Dialog for GitHub settings.

```python
class GitHubSettingsDialog:
    def __init__(self, parent)
```

## Multi-Model API

### MultiModelManager

**Location**: `aima_codegen/multi_model/config.py`

Manages multiple LLM configurations for different agents.

```python
class MultiModelManager:
    def __init__(self)
```

#### Attributes

- `default_provider`: Default LLM provider
- `default_model`: Default model name
- `agent_configs`: Dict[str, AgentModelConfig]
- `llm_services`: Cache of LLM service instances

#### Methods

##### get_llm_service(agent_type: str) -> LLMServiceInterface
Gets or creates LLM service for specific agent.

**Returns:** LLM service instance configured for agent

##### get_agent_config(agent_type: str) -> AgentModelConfig
Gets configuration for specific agent.

##### set_agent_config(agent_type: str, config: AgentModelConfig)
Sets configuration for specific agent.

##### update_agent_config(agent_type: str, **kwargs)
Updates specific fields of agent configuration.

**Example:**
```python
manager.update_agent_config(
    "CodeGen",
    provider="Google",
    model="gemini-2.5-flash-preview-05-20"
)
```

##### save_configurations()
Saves current configurations to file.

##### get_model_options(provider: str) -> List[str]
Returns available models for a provider.

##### validate_all_services() -> Dict[str, bool]
Validates all configured LLM services.

### AgentModelConfig

**Location**: `aima_codegen/multi_model/config.py`

Configuration dataclass for agent models.

```python
@dataclass
class AgentModelConfig:
    provider: str
    model: str
    temperature: float
    max_tokens: int
```

#### Methods

##### to_dict() -> Dict[str, Any]
Converts to dictionary.

##### from_dict(data: Dict[str, Any]) -> AgentModelConfig
Creates instance from dictionary.

### ModelPresets

**Location**: `aima_codegen/multi_model/config.py`

Predefined model configurations.

```python
class ModelPresets:
    FAST_DEVELOPMENT: Dict[str, AgentModelConfig]
    HIGH_QUALITY: Dict[str, AgentModelConfig]
    BALANCED: Dict[str, AgentModelConfig]
```

#### Class Methods

##### apply_preset(preset_name: str, manager: MultiModelManager)
Applies a preset configuration to manager.

**Parameters:**
- `preset_name`: One of "fast", "quality", "balanced"

**Example:**
```python
ModelPresets.apply_preset("balanced", manager)
```

### MultiModelOrchestrator

**Location**: `aima_codegen/multi_model/config.py`

Extension of Orchestrator for multi-model support.

```python
class MultiModelOrchestrator:
    def __init__(self, orchestrator: Orchestrator)
```

#### Methods

##### configure_agents_with_multi_model()
Configures all agents to use their specific models.

##### execute_with_multi_model(agent_type: str, context: Dict) -> Dict
Executes agent with its specific model configuration.

##### update_agent_model(agent_type: str, provider: str = None, model: str = None, temperature: float = None)
Updates model configuration for specific agent.

##### get_cost_breakdown_by_agent() -> Dict[str, Dict[str, float]]
Returns cost breakdown per agent (not yet implemented).

## Extension Points

### Adding New Agents

To add a new agent type:

1. Create agent class inheriting from `BaseAgent`
2. Add to agent type literals in models
3. Update MultiModelManager default configs
4. Add GUI dropdown in main_window.py

### Adding New LLM Providers

To add a new provider:

1. Create adapter implementing `LLMServiceInterface`
2. Update `MultiModelManager._create_llm_service()`
3. Add to GUI model options
4. Add model costs to config

### Custom Presets

Create custom presets:

```python
MY_CUSTOM_PRESET = {
    "Planner": AgentModelConfig("Anthropic", "claude-opus-4-20250514", 0.5, 3000),
    "CodeGen": AgentModelConfig("Google", "gemini-2.5-flash-preview-05-20", 0.2, 8000),
    # ... etc
}

# Apply custom preset
for agent, config in MY_CUSTOM_PRESET.items():
    manager.set_agent_config(agent, config)
```

### GUI Extensions

Add new menu items or dialogs:

```python
# In AIMACodeGenGUI._create_menu()
custom_menu = tk.Menu(menubar, tearoff=0)
menubar.add_cascade(label="Custom", menu=custom_menu)
custom_menu.add_command(label="My Feature", command=self._my_feature)
```

### GitHub Webhook Handling

Implement webhook endpoint:

```python
@app.post("/webhook")
async def handle_webhook(request: Request):
    event = request.headers.get("X-GitHub-Event")
    if event == "pull_request":
        # Handle PR events
        pass
```

## Error Handling

All API methods follow consistent error handling:

1. **Return Format**: Methods return dictionaries with `success` field
2. **Exceptions**: Critical errors raise specific exceptions
3. **Logging**: All errors are logged with context
4. **User Feedback**: GUI methods use message queue for user updates

Example error handling:

```python
try:
    result = github.create_pull_request(...)
    if result["success"]:
        # Handle success
    else:
        # Handle API error
        logger.error(f"PR creation failed: {result['error']}")
except ToolingError as e:
    # Handle tooling error
    logger.error(f"Git operation failed: {e}")
```

## Core Orchestration & Resilience API

### ResilientOrchestrator

**Location**: `aima_codegen/orchestrator.py`

Fault-tolerant orchestrator that extends the base Orchestrator with error isolation and recovery features.

```python
class ResilientOrchestrator(Orchestrator):
    def execute_waypoint(self, waypoint_id: str, agent_func, critical: bool = False) -> Any
```

#### Methods

##### execute_waypoint(waypoint_id: str, agent_func: Callable, critical: bool = False) -> Any
Executes a given agent function as a waypoint with fault isolation.

**Parameters:**
- `waypoint_id`: Identifier for the waypoint (for tracking and logging)
- `agent_func`: Function or lambda that executes the agent's task (e.g., `planner.plan_next`)
- `critical`: If True, a failure triggers special recovery or abort logic

**Returns:** Result of the agent function, or a recovery result on failure.

This method handles:
- Timeout and retries (circuit breaker with exponential backoff)
- Graceful shutdown checks (stopping if a shutdown event is set)
- Error catching: marking waypoint as failed and attempting recovery if `critical`

##### _execute_with_circuit_breaker(func: Callable, checkpoint: Any, timeout: int) -> Any
*(internal)* Executes a function in an isolated subprocess with a timeout and multiple retries.

##### _shutdown_handler(signum, frame) -> None
*(internal)* Handles SIGINT/SIGTERM by setting a stop event and saving progress (checkpoint).

##### _handle_critical_failure(waypoint_id, error: Exception) -> Any
*(internal)* Attempts to recover from a critical waypoint failure (e.g., roll back or skip future waypoints).

### TelemetryAwareErrorHandler

**Location**: `aima_codegen/error_handler.py`

Centralized error logging and telemetry integration.

```python
class TelemetryAwareErrorHandler:
    def __init__(self, state: Optional[ProjectState] = None)
```

#### Methods

##### handle_error(error: Exception, context: Dict[str, Any], agent: str) -> None
Logs the error with context and updates internal telemetry (error history, patterns). May modify `context` to inject safe defaults (e.g., for missing keys).

##### get_recovery_strategy(error: Exception) -> Dict[str, str]
Returns a suggested recovery action (e.g., retry with extended timeout, inject default values) based on error type.

##### get_telemetry_summary() -> Dict[str, Any]
Provides a summary of collected error telemetry (counts by agent and error type).

##### should_circuit_break(agent: str) -> bool
Indicates if the error frequency for a given agent exceeds a threshold, suggesting the orchestrator should halt or change strategy for that agent.

This error handler works in conjunction with the orchestrator to prevent repeated failures from propagating and to assist in automated recovery.

### SymlinkAwarePathResolver

**Location**: `aima_codegen/path_resolver.py`

Utility to correctly handle file paths in a symlinked environment (used during self-improvement where `aima_codegen` is linked into a project).

```python
class SymlinkAwarePathResolver:
    def __init__(self, base_path: str)
```

#### Methods

##### resolve_path(path: str) -> Path
Resolves a given path string to an absolute Path, following symlinks if present.

##### get_canonical_path(path: str) -> Path
Returns the fully resolved canonical Path for a given path (resolving any symlinks).

##### resolve_module_path(module: str) -> Optional[Path]
Converts a module import string to a file system path, if that module exists in the base path or its subpackages.

##### resolve_relative(path: str, from_path: str) -> Path
Resolves a relative path against a reference path within the base project.

##### validate_safe_path(path: str) -> None
Raises ValueError if the given path would escape the base project directory (preventing directory traversal attacks).

##### setup_python_path() -> None
Adds both the logical project path and the physical path (if different due to symlinks) to `sys.path` to ensure imports work correctly in a self-improvement setup.

In normal operation, these classes work behind the scenes, but understanding their interface can help in extending or debugging the system's core behavior.