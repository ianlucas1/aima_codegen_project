"""Central orchestrator for AIMA CodeGen.
Implements spec_v5.1.md Section 2.2 - Orchestrator Agent
"""
import os
import shutil
import json
import hashlib
import logging
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional, Tuple
from packaging.requirements import Requirement
import tempfile

from rich.console import Console
from rich.prompt import Confirm
from rich.progress import Progress, SpinnerColumn, TextColumn

from .models import ProjectState, Waypoint, RevisionFeedback, LLMRequest
from .config import config
from .state import StateManager
from .venv_manager import VEnvManager
from .budget import BudgetTracker
from .utils import slugify, check_lock_file, create_lock_file, remove_lock_file
from .exceptions import (
    ToolingError, BudgetExceededError, LLMOutputError,
    InvalidAPIKeyError, RateLimitError, ServerError, NetworkError
)
from .agents import PlannerAgent, CodeGenAgent, TestWriterAgent, ExplainerAgent
from .llm import OpenAIAdapter, AnthropicAdapter, GoogleAdapter

logger = logging.getLogger(__name__)
console = Console()

class Orchestrator:
    """Central controller managing the entire application flow."""
    
    def __init__(self):
        self.config = config
        self.console = console
        self.llm_service = None
        self.project_state = None
        self.state_manager = None
        self.venv_manager = None
        self.budget_tracker = None
        self.project_path = None
        self.lock_path = None
        
        # Initialize agents (will set LLM service later)
        self.planner = None
        self.codegen = None
        self.testwriter = None
        self.explainer = None
        self.reviewer = None

        # Multi-model support
        self.multi_model_enabled = False
        self.multi_model_manager = None
        self.multi_model_orchestrator = None
    
    def _initialize_reviewer(self):
        """Initialize the Reviewer agent."""
        if self.llm_service:
            from .agents import ReviewerAgent
            github_token = config.get("GitHub", "token")
            self.reviewer = ReviewerAgent(self.llm_service, github_token)

    def enable_multi_model(self):
        """Enable multi-model configuration."""
        from .multi_model import MultiModelManager, MultiModelOrchestrator
        self.multi_model_manager = MultiModelManager()
        self.multi_model_orchestrator = MultiModelOrchestrator(self)
        self.multi_model_orchestrator.configure_agents_with_multi_model()
        self.multi_model_enabled = True
        logger.info("Multi-model configuration enabled")

    def init_project(self, project_name: str, budget: float) -> bool:
        """Initialize a new project.
        Implements spec_v5.1.md Section 3.2 - Project Initialization
        """
        project_slug = slugify(project_name)
        self.project_path = Path.home() / ".AIMA_CodeGen" / "projects" / project_slug
        
        # Check if project already exists
        if self.project_path.exists():
            self.console.print(f"[red]ERROR: Project '{project_name}' already exists.[/red]")
            return False
        
        # Create project structure
        try:
            self.project_path.mkdir(parents=True)
            (self.project_path / "src").mkdir()
            (self.project_path / "src" / "tests").mkdir()
            (self.project_path / "waypoints").mkdir()
            (self.project_path / "logs").mkdir()
            
            # Create empty requirements.txt
            (self.project_path / "src" / "requirements.txt").write_text("")
            
            # Initialize VEnv
            self.venv_manager = VEnvManager(self.project_path)
            python_path = self.venv_manager.find_python()
            self.venv_manager.create_venv(python_path)
            
            # Create project state
            self.project_state = ProjectState(
                project_name=project_name,
                project_slug=project_slug,
                total_budget_usd=budget,
                initial_prompt="",
                venv_path=str(self.project_path / ".venv"),
                python_path=python_path
            )
            
            # Save state
            self.state_manager = StateManager(self.project_path)
            self.state_manager.save(self.project_state)
            
            # Create lock file
            self.lock_path = self.project_path / ".lock"
            create_lock_file(self.lock_path)
            
            self.console.print(f"[green]✓ Project '{project_name}' initialized successfully![/green]")
            return True
            
        except Exception as e:
            logger.error(f"Failed to initialize project: {e}")
            self.console.print(f"[red]ERROR: Failed to initialize project: {e}[/red]")
            # Clean up on failure
            if self.project_path.exists():
                shutil.rmtree(self.project_path)
            return False
    
    def load_project(self, project_name: str) -> bool:
        """Load an existing project.
        Implements spec_v5.1.md Section 3.1 - Load command
        """
        project_slug = slugify(project_name)
        self.project_path = Path.home() / ".AIMA_CodeGen" / "projects" / project_slug
        
        if not self.project_path.exists():
            self.console.print(f"[red]ERROR: Project '{project_name}' not found.[/red]")
            return False
        
        # Check lock file
        self.lock_path = self.project_path / ".lock"
        if not check_lock_file(self.lock_path, project_name):
            return False
        
        # Create lock file
        create_lock_file(self.lock_path)
        
        # Load state
        self.state_manager = StateManager(self.project_path)
        self.project_state = self.state_manager.load()
        
        if not self.project_state:
            self.console.print(f"[red]ERROR: Failed to load project state.[/red]")
            remove_lock_file(self.lock_path)
            return False
        
        # Initialize managers
        self.venv_manager = VEnvManager(self.project_path)
        self.budget_tracker = BudgetTracker(self.project_state.total_budget_usd)
        self.budget_tracker.current_spent = self.project_state.current_spent_usd
        
        self.console.print(f"[green]✓ Project '{project_name}' loaded successfully![/green]")
        return True
    
    def develop(self, prompt: str, budget: float, provider: str = None, model: str = None) -> bool:
        """Start development process.
        Implements spec_v5.1.md Section 3.3 - Waypoint Definition and Execution
        """
        if not self.project_state:
            self.console.print("[red]ERROR: No project loaded.[/red]")
            return False
        
        # Update initial prompt and budget if provided
        self.project_state.initial_prompt = prompt
        if budget > 0:
            self.project_state.total_budget_usd = budget
            self.budget_tracker = BudgetTracker(budget)
        
        # Setup LLM service
        if not self._setup_llm_service(provider, model):
            return False
        
        # Save updated state
        self.state_manager.save(self.project_state)
        
        # Plan waypoints
        self.console.print("\n[cyan]Planning project waypoints...[/cyan]")
        waypoints = self._plan_waypoints(prompt)
        
        if not waypoints:
            self.console.print("[red]Failed to create project plan.[/red]")
            return False
        
        # Display plan and get confirmation
        self.console.print("\n[bold]Project Plan:[/bold]")
        for i, wp in enumerate(waypoints, 1):
            self.console.print(f"{i}. [{wp.agent_type}] {wp.description}")
        
        if not Confirm.ask("\nProceed with this plan?"):
            self.console.print("[yellow]Development aborted by user.[/yellow]")
            return False
        
        # Execute waypoints
        self.project_state.waypoints = waypoints
        self.state_manager.save(self.project_state)
        
        return self._execute_waypoints()
    
    def show_status(self):
        """Show project status.
        Implements spec_v5.1.md Section 3.1 - Status command
        """
        if not self.project_state:
            self.console.print("[red]ERROR: No project loaded.[/red]")
            return
        
        self.console.print(f"\n[bold]Project: {self.project_state.project_name}[/bold]")
        self.console.print(f"Created: {self.project_state.creation_date}")
        self.console.print(f"Budget: ${self.project_state.current_spent_usd:.2f} / ${self.project_state.total_budget_usd:.2f}")
        
        if self.project_state.waypoints:
            self.console.print("\n[bold]Waypoints:[/bold]")
            for wp in self.project_state.waypoints:
                status_color = {
                    "SUCCESS": "green",
                    "RUNNING": "yellow",
                    "PENDING": "cyan",
                    "FAILED_CODE": "red",
                    "FAILED_TESTS": "red",
                    "FAILED_LINT": "red",
                    "FAILED_TOOLING": "red",
                    "FAILED_REVISIONS": "red",
                    "FAILED_LLM_OUTPUT": "red",
                    "ABORTED": "red"
                }.get(wp.status, "white")
                
                self.console.print(f"  [{status_color}]{wp.id}[/{status_color}]: {wp.description} [{wp.status}]")
    
    def explain_code(self, file_path: str, target: Optional[str] = None):
        """Explain code using the Explainer agent.
        Implements spec_v5.1.md Section 3.1 - Explain command
        """
        path = Path(file_path)
        if not path.exists():
            self.console.print(f"[red]ERROR: File '{file_path}' not found.[/red]")
            return
        
        # Setup LLM service if needed
        if not self.llm_service:
            if not self._setup_llm_service():
                return
        
        # Read file content
        code_content = path.read_text()
        
        # Get explanation
        self.console.print(f"\n[cyan]Analyzing {file_path}...[/cyan]")
        
        context = {
            "file_path": str(path),
            "code_content": code_content,
            "target": target,
            "model": self.project_state.model_name if self.project_state else None
        }
        
        result = self.explainer.execute(context)
        
        if result["success"]:
            self.console.print("\n[bold]Explanation:[/bold]")
            self.console.print(result["explanation"])
            
            if self.project_state and self.budget_tracker:
                # Update budget
                cost = self.budget_tracker.update_spent(
                    self.project_state.model_name,
                    result.get("tokens_used", 0),
                    0  # No completion tokens for explanation
                )
                self.project_state.current_spent_usd += cost
                self.state_manager.save(self.project_state)
        else:
            self.console.print("[red]Failed to generate explanation.[/red]")
    
    def cleanup(self):
        """Clean up resources on exit."""
        if self.lock_path:
            remove_lock_file(self.lock_path)
        if self.state_manager and self.project_state:
            self.state_manager.save(self.project_state)
    
    def review_code(self, waypoint: Waypoint, create_pr: bool = False) -> Dict:
        """Review code using the Reviewer agent."""
        if not self.reviewer:
            logger.error("Reviewer agent not initialized")
            return {"success": False, "error": "Reviewer not available"}
        
        # Get code changes for the waypoint
        code_changes = {}
        for file_path in waypoint.output_files:
            full_path = self.project_path / file_path
            if full_path.exists():
                code_changes[file_path] = full_path.read_text()
        
        context = {
            "action": "review",
            "waypoint": waypoint,
            "code_changes": code_changes,
            "project_context": self.project_state.initial_prompt,
            "model": self.project_state.model_name
        }
        
        result = self.reviewer.execute(context)
        
        if result["success"] and result["approved"] and create_pr:
            # Create pull request
            pr_context = {
                "action": "create_pr",
                "project_path": str(self.project_path),
                "branch_name": f"feature/{waypoint.id}",
                "pr_title": f"Implementation: {waypoint.description}",
                "pr_body": self._format_pr_body(waypoint, result["review"])
            }
            
            pr_result = self.reviewer.execute(pr_context)
            return {**result, "pr": pr_result}
        
        return result

    def _format_pr_body(self, waypoint: Waypoint, review: Dict) -> str:
        """Format pull request body."""
        body = f"## Waypoint: {waypoint.id}\n\n"
        body += f"**Description:** {waypoint.description}\n\n"
        
        if review.get("comments"):
            body += "### Review Comments\n"
            for comment in review["comments"]:
                body += f"- {comment}\n"
        
        if review.get("suggestions"):
            body += "\n### Suggestions\n"
            for suggestion in review["suggestions"]:
                body += f"- {suggestion}\n"
        
        body += "\n---\n*Generated by AIMA CodeGen*"
        return body
    
    def _setup_llm_service(self, provider: str = None, model: str = None) -> bool:
        """Setup LLM service with API key management.
        Implements spec_v5.1.md Section 7.2 - API Key Management
        """
        # Get provider and model from config if not specified
        if not provider:
            provider = self.config.get("General", "default_provider", "OpenAI")
        if not model:
            model = self.config.get("General", "default_model", "gpt-4.1-2025-04-14")
        
        # Get API key following priority order
        api_key = self._get_api_key(provider)
        if not api_key:
            return False
        
        # Create adapter based on provider
        try:
            if provider.lower() == "openai":
                self.llm_service = OpenAIAdapter(api_key)
            elif provider.lower() == "anthropic":
                self.llm_service = AnthropicAdapter(api_key)
            elif provider.lower() == "google":
                self.llm_service = GoogleAdapter(api_key)
            else:
                self.console.print(f"[red]ERROR: Unknown provider '{provider}'[/red]")
                return False
            
            # Validate API key
            self.console.print(f"[cyan]Validating {provider} API key...[/cyan]")
            if not self.llm_service.validate_api_key():
                self.console.print(
                    f"[red]ERROR: The API key for {provider} failed validation. "
                    f"Suggestion: Verify the key and permissions.[/red]"
                )
                return False
            
            # Initialize agents
            self.planner = PlannerAgent(self.llm_service)
            self.codegen = CodeGenAgent(self.llm_service)
            self.testwriter = TestWriterAgent(self.llm_service)
            self.explainer = ExplainerAgent(self.llm_service)
            self._initialize_reviewer()
            
            # Update project state
            if self.project_state:
                self.project_state.api_provider = provider
                self.project_state.model_name = model
            
            self.console.print(f"[green]✓ {provider} API configured successfully![/green]")
            return True
            
        except Exception as e:
            self.console.print(f"[red]ERROR: Failed to setup LLM service: {e}[/red]")
            return False
    
    def _get_api_key(self, provider: str) -> Optional[str]:
        """Get API key following priority order.
        Implements spec_v5.1.md Section 7.2 - Priority Order
        """
        # 1. Check environment variables
        env_var_map = {
            "openai": "OPENAI_API_KEY",
            "anthropic": "ANTHROPIC_API_KEY",
            "google": "GOOGLE_API_KEY"
        }
        env_var = env_var_map.get(provider.lower())
        if env_var:
            api_key = os.environ.get(env_var)
            if api_key:
                logger.info(f"Using {provider} API key from environment variable")
                return api_key
        
        # 2. Check keychain
        try:
            import keyring
            service_name = self.config.get("Security", "keychain_service_name", "AIMA_CodeGen_Keys")
            api_key = keyring.get_password(service_name, provider.lower())
            if api_key:
                logger.info(f"Using {provider} API key from keychain")
                return api_key
        except Exception as e:
            logger.warning(f"WARNING: keyring access failed: {e}")
        
        # 3. Check config.ini
        config_key = f"{provider.lower()}_api_key"
        api_key = self.config.get("API_Keys", config_key)
        if api_key:
            logger.info(f"Using {provider} API key from config.ini")
            return api_key
        
        # 4. Prompt user
        from rich.prompt import Prompt
        self.console.print(f"\n[yellow]No {provider} API key found.[/yellow]")
        api_key = Prompt.ask(f"Please enter your {provider} API key", password=True)
        
        if api_key:
            # Offer to save
            if Confirm.ask(f"Save API key to config.ini?"):
                self.config.set("API_Keys", config_key, api_key)
                os.chmod(self.config.config_path, 0o600)
                self.console.print("[green]API key saved to config.ini[/green]")
        
        return api_key
    
    def _plan_waypoints(self, prompt: str) -> List[Waypoint]:
        """Plan waypoints using the Planner agent."""
        context = {
            "user_prompt": prompt,
            "model": self.project_state.model_name
        }
        
        # Check budget before calling
        estimated_tokens = self.llm_service.count_tokens(prompt, self.project_state.model_name)
        if not self.budget_tracker.pre_call_check(
            self.project_state.model_name,
            estimated_tokens,
            2000  # Max tokens for planner
        ):
            return []
        
        result = self.planner.execute(context)
        
        if result["success"]:
            # Update budget
            self.budget_tracker.update_spent(
                self.project_state.model_name,
                result.get("tokens_used", 0) // 2,  # Rough estimate
                result.get("tokens_used", 0) // 2
            )
            return result["waypoints"]
        else:
            self.console.print(f"[red]Planning failed: {result.get('error', 'Unknown error')}[/red]")
            return []
    
    def _execute_waypoints(self) -> bool:
        """Execute all waypoints sequentially.
        Implements spec_v5.1.md Section 3.3 - Sequential Execution
        """
        success_count = 0
        
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=self.console
        ) as progress:
            
            for i, waypoint in enumerate(self.project_state.waypoints):
                if waypoint.status == "SUCCESS":
                    success_count += 1
                    continue
                
                task = progress.add_task(f"Executing {waypoint.id}: {waypoint.description}", total=1)
                
                # Update current waypoint index
                self.project_state.current_waypoint_index = i
                self.state_manager.save(self.project_state)
                
                # Execute waypoint
                waypoint.status = "RUNNING"
                success = self._execute_single_waypoint(waypoint)
                
                if success:
                    waypoint.status = "SUCCESS"
                    success_count += 1
                    progress.update(task, completed=1)
                else:
                    # Waypoint failed - status already set by execute method
                    progress.stop()
                    self.console.print(f"\n[red]Waypoint {waypoint.id} failed with status: {waypoint.status}[/red]")
                    break
                
                # Save state after each waypoint
                self.state_manager.save(self.project_state)
        
        # Final summary
        total = len(self.project_state.waypoints)
        self.console.print(f"\n[bold]Development Complete:[/bold] {success_count}/{total} waypoints succeeded")
        self.console.print(f"Total cost: ${self.project_state.current_spent_usd:.4f}")
        
        return success_count == total
    
    def _execute_single_waypoint(self, waypoint: Waypoint) -> bool:
        """Execute a single waypoint with revision loop.
        Implements spec_v5.1.md Section 3.6 - Iterative Revision Process
        """
        max_revisions = 3
        
        # Create waypoint working directory
        waypoint_dir = self.project_path / "waypoints" / waypoint.id
        if waypoint_dir.exists():
            shutil.rmtree(waypoint_dir)
        waypoint_dir.mkdir(parents=True)
        
        # Copy current src to waypoint directory
        shutil.copytree(self.project_path / "src", waypoint_dir / "src")
        
        for revision in range(max_revisions + 1):
            waypoint.revision_attempts = revision
            
            # Get context for agent
            context = self._build_agent_context(waypoint, waypoint_dir)
            
            # Add revision feedback if this is a revision
            if revision > 0 and waypoint.feedback_history:
                context["revision_feedback"] = waypoint.feedback_history[-1]
            
            # Execute appropriate agent
            if waypoint.agent_type == "CodeGen":
                result = self._execute_codegen(waypoint, context, waypoint_dir)
            elif waypoint.agent_type == "TestWriter":
                result = self._execute_testwriter(waypoint, context, waypoint_dir)
            else:
                logger.error(f"Unknown agent type: {waypoint.agent_type}")
                waypoint.status = "FAILED_TOOLING_ERROR"
                return False
            
            if not result["success"]:
                # Check if it's an LLM output error
                if result.get("llm_output_error"):
                    waypoint.status = "FAILED_LLM_OUTPUT"
                    return False
                
                # Try revision if not at max
                if revision < max_revisions:
                    self.console.print(f"[yellow]Revision {revision + 1}/{max_revisions} for {waypoint.id}[/yellow]")
                    continue
                else:
                    waypoint.status = "FAILED_REVISIONS"
                    return False
            
            # Run tests and linting
            verification_result = self._verify_waypoint(waypoint, waypoint_dir)
            
            if verification_result["success"]:
                # Copy successful results back to src
                self._copy_waypoint_results(waypoint_dir, self.project_path / "src")
                
                # Update requirements hash if changed
                new_hash = self.venv_manager._compute_requirements_hash()
                if new_hash != self.project_state.requirements_hash:
                    self.project_state.requirements_hash = new_hash
                
                # Clean up waypoint directory
                if not self.config.get("General", "keep_failed_waypoints", False):
                    shutil.rmtree(waypoint_dir)
                
                return True
            else:
                # Add feedback for revision
                feedback = RevisionFeedback(
                    pytest_output=verification_result.get("pytest_output"),
                    flake8_output=verification_result.get("flake8_output"),
                    syntax_error=verification_result.get("syntax_error")
                )
                waypoint.feedback_history.append(feedback)
                
                # Set appropriate status
                if verification_result.get("error_type") == "lint":
                    waypoint.status = "FAILED_LINT"
                elif verification_result.get("error_type") == "test":
                    waypoint.status = "FAILED_TESTS"
                elif verification_result.get("error_type") == "syntax":
                    waypoint.status = "FAILED_CODE"
                else:
                    waypoint.status = "FAILED_TOOLING_ERROR"
                
                # Try revision if not at max
                if revision < max_revisions:
                    self.console.print(f"[yellow]Revision {revision + 1}/{max_revisions} for {waypoint.id}[/yellow]")
                    continue
                else:
                    waypoint.status = "FAILED_REVISIONS"
                    return False
        
        return False
    
    def _build_agent_context(self, waypoint: Waypoint, waypoint_dir: Path) -> Dict:
        """Build context for agent execution.
        Implements spec_v5.1.md Section 2.4 - Context Management Strategy
        """
        context = {
            "waypoint": waypoint,
            "model": self.project_state.model_name,
            "project_context": ""
        }
        
        # Build project context
        context_parts = []
        
        # 1. Include requirements.txt
        req_path = waypoint_dir / "src" / "requirements.txt"
        if req_path.exists():
            context_parts.append(f"=== requirements.txt ===\n{req_path.read_text()}")
        
        # 2. Include files mentioned in waypoint description
        # Simple heuristic: look for .py filenames in description
        import re
        mentioned_files = re.findall(r'(\w+\.py)', waypoint.description)
        for filename in mentioned_files:
            file_path = waypoint_dir / "src" / filename
            if file_path.exists():
                context_parts.append(f"=== {filename} ===\n{file_path.read_text()}")
        
        # 3. For TestWriter, include source files being tested
        if waypoint.agent_type == "TestWriter":
            # Look for source files that might be tested
            src_dir = waypoint_dir / "src"
            for py_file in src_dir.glob("*.py"):
                if py_file.name != "__init__.py" and not py_file.name.startswith("test_"):
                    content = py_file.read_text()
                    if len(content.encode()) <= 8192:  # 8KB limit
                        context_parts.append(f"=== {py_file.name} ===\n{content}")
        
        # 4. Fallback: include all Python files under 8KB
        if waypoint.agent_type == "CodeGen" and len(context_parts) < 2:
            logger.warning("WARNING: Using 8KB fallback context strategy. Including all *.py files under 8KB.")
            src_dir = waypoint_dir / "src"
            for py_file in src_dir.glob("**/*.py"):
                if py_file.stat().st_size <= 8192:
                    content = py_file.read_text()
                    context_parts.append(f"=== {py_file.relative_to(src_dir)} ===\n{content}")
                else:
                    # File too large - abort
                    logger.error(f"ERROR: File '{py_file}' exceeds 8 KB fallback limit. "
                               "Suggestion: Refactor the file or increase the limit in config.ini.")
                    waypoint.status = "FAILED_TOOLING_ERROR"
                    raise ToolingError(f"File '{py_file}' exceeds 8 KB fallback limit")
        
        # 5. Include user's original prompt
        context_parts.append(f"=== Original Requirements ===\n{self.project_state.initial_prompt}")
        
        # 6. Include current waypoint task
        context_parts.append(f"=== Current Task ===\n{waypoint.description}")
        
        context["project_context"] = "\n\n".join(context_parts)
        
        return context
    
    def _execute_codegen(self, waypoint: Waypoint, context: Dict, waypoint_dir: Path) -> Dict:
        """Execute CodeGen agent with JSON retry logic.
        Implements spec_v5.1.md Section 3.6.3 - LLM JSON Output Parsing
        """
        # Check budget
        prompt_text = context.get("project_context", "")
        prompt_tokens = self.llm_service.count_tokens(prompt_text, self.project_state.model_name)
        
        if not self.budget_tracker.pre_call_check(
            self.project_state.model_name,
            prompt_tokens,
            4000  # Max tokens for code generation
        ):
            waypoint.status = "ABORTED"
            return {"success": False, "error": "Budget check failed"}
        
        # Execute agent
        result = self.codegen.execute(context)
        
        # Handle JSON parsing failure with retry
        if not result["success"] and "raw_content" in result:
            logger.warning("WARNING: CodeGen returned invalid JSON, attempting retry")
            
            # Build retry prompt
            retry_prompt = f"""### FAILED JSON OUTPUT ###
The previous response was not valid JSON. Please fix it. Here is the invalid response:
{result['raw_content']}
### TASK ###
Regenerate the *entire* response in the correct JSON format, ensuring all structure and escaping rules are followed."""
            
            retry_context = {
                "waypoint": waypoint,
                "model": self.project_state.model_name,
                "project_context": retry_prompt
            }
            
            # One retry attempt
            retry_result = self.codegen.execute(retry_context)
            
            if not retry_result["success"]:
                logger.error(f"ERROR: LLM failed to produce valid JSON output after 1 retry. "
                           f"Waypoint '{waypoint.id}' marked as FAILED_LLM_OUTPUT.")
                return {"success": False, "llm_output_error": True}
            
            result = retry_result
        
        if result["success"]:
            # Update budget
            cost = self.budget_tracker.update_spent(
                self.project_state.model_name,
                result.get("tokens_used", 0) // 2,
                result.get("tokens_used", 0) // 2
            )
            waypoint.cost += cost
            self.project_state.current_spent_usd = self.budget_tracker.current_spent
            
            # Write generated code
            for file_path, content in result["code"].items():
                full_path = waypoint_dir / file_path
                full_path.parent.mkdir(parents=True, exist_ok=True)
                full_path.write_text(content)
                waypoint.output_files.append(file_path)
            
            # Update requirements
            if result.get("dependencies"):
                self._update_requirements(waypoint_dir, result["dependencies"])
            
            return {"success": True}
        
        return result
    
    def _execute_testwriter(self, waypoint: Waypoint, context: Dict, waypoint_dir: Path) -> Dict:
        """Execute TestWriter agent with JSON retry logic."""
        # Similar to _execute_codegen but for test generation
        # Get source code to test
        source_files = []
        src_dir = waypoint_dir / "src"
        for py_file in src_dir.glob("*.py"):
            if not py_file.name.startswith("test_"):
                source_files.append(py_file.read_text())
        
        context["source_code"] = "\n\n".join(source_files)
        
        # Check budget
        prompt_text = context.get("project_context", "") + context.get("source_code", "")
        prompt_tokens = self.llm_service.count_tokens(prompt_text, self.project_state.model_name)
        
        if not self.budget_tracker.pre_call_check(
            self.project_state.model_name,
            prompt_tokens,
            4000
        ):
            waypoint.status = "ABORTED"
            return {"success": False, "error": "Budget check failed"}
        
        # Execute agent
        result = self.testwriter.execute(context)
        
        # Handle JSON parsing failure with retry (same as codegen)
        if not result["success"] and "raw_content" in result:
            logger.warning("WARNING: TestWriter returned invalid JSON, attempting retry")
            
            retry_prompt = f"""### FAILED JSON OUTPUT ###
The previous response was not valid JSON. Please fix it. Here is the invalid response:
{result['raw_content']}
### TASK ###
Regenerate the *entire* response in the correct JSON format, ensuring all structure and escaping rules are followed."""
            
            retry_context = {
                "waypoint": waypoint,
                "model": self.project_state.model_name,
                "project_context": retry_prompt,
                "source_code": context["source_code"]
            }
            
            retry_result = self.testwriter.execute(retry_context)
            
            if not retry_result["success"]:
                logger.error(f"ERROR: LLM failed to produce valid JSON output after 1 retry. "
                           f"Waypoint '{waypoint.id}' marked as FAILED_LLM_OUTPUT.")
                return {"success": False, "llm_output_error": True}
            
            result = retry_result
        
        if result["success"]:
            # Update budget
            cost = self.budget_tracker.update_spent(
                self.project_state.model_name,
                result.get("tokens_used", 0) // 2,
                result.get("tokens_used", 0) // 2
            )
            waypoint.cost += cost
            self.project_state.current_spent_usd = self.budget_tracker.current_spent
            
            # Write test files
            for file_path, content in result["code"].items():
                full_path = waypoint_dir / file_path
                full_path.parent.mkdir(parents=True, exist_ok=True)
                full_path.write_text(content)
                waypoint.output_files.append(file_path)
            
            # Update requirements (should include pytest)
            if result.get("dependencies"):
                self._update_requirements(waypoint_dir, result["dependencies"])
            
            return {"success": True}
        
        return result
    
    def _update_requirements(self, waypoint_dir: Path, new_deps: List[str]):
        """Update requirements.txt using packaging library.
        Implements spec_v5.1.md Section 3.4 and Appendix D
        """
        req_path = waypoint_dir / "src" / "requirements.txt"
        
        # Parse existing requirements
        reqs_dict = {}
        if req_path.exists():
            for line in req_path.read_text().splitlines():
                line = line.strip()
                if line and not line.startswith("#"):
                    try:
                        req = Requirement(line)
                        reqs_dict[req.name.lower()] = req
                    except Exception as e:
                        logger.warning(f"Failed to parse requirement '{line}': {e}")
        
        # Add/update new dependencies
        for dep in new_deps:
            try:
                req = Requirement(dep)
                reqs_dict[req.name.lower()] = req
            except Exception as e:
                logger.warning(f"Failed to parse new dependency '{dep}': {e}")
        
        # Sort and write back
        sorted_reqs = sorted(reqs_dict.values(), key=lambda r: r.name.lower())
        req_content = "\n".join(str(req) for req in sorted_reqs)
        req_path.write_text(req_content + "\n")
        
        # Install new requirements
        try:
            self.venv_manager.install_requirements()
        except ToolingError as e:
            logger.error(f"Failed to install requirements: {e}")
            raise
    
    def _verify_waypoint(self, waypoint: Waypoint, waypoint_dir: Path) -> Dict:
        """Run tests and linting on waypoint code.
        Implements spec_v5.1.md Section 3.5 - Testing & Verification
        """
        venv_python = str(self.venv_manager.get_venv_python())
        tool_timeout = self.config.get("VEnv", "tool_timeout", 60)
        
        # First check syntax by trying to compile all Python files
        src_dir = waypoint_dir / "src"
        for py_file in src_dir.glob("**/*.py"):
            try:
                compile(py_file.read_text(), str(py_file), 'exec')
            except SyntaxError as e:
                return {
                    "success": False,
                    "error_type": "syntax",
                    "syntax_error": f"Syntax error in {py_file}: {e}"
                }
        
        # Run flake8
        flake8_args = self.config.get("VEnv", "flake8_args", "").split()
        flake8_cmd = [venv_python, "-m", "flake8"] + flake8_args + [str(src_dir)]
        
        try:
            flake8_result = self.venv_manager.run_subprocess(flake8_cmd, timeout=tool_timeout)
            if flake8_result.returncode != 0:
                return {
                    "success": False,
                    "error_type": "lint",
                    "flake8_output": flake8_result.stdout + flake8_result.stderr
                }
        except ToolingError as e:
            waypoint.status = "FAILED_TOOLING_ERROR"
            return {
                "success": False,
                "error_type": "tooling",
                "error": str(e)
            }
        
        # Run pytest
        pytest_args = self.config.get("VEnv", "pytest_args", "").split()
        pytest_cmd = [venv_python, "-m", "pytest"] + pytest_args + [str(src_dir / "tests")]
        
        try:
            pytest_result = self.venv_manager.run_subprocess(pytest_cmd, timeout=tool_timeout)
            if pytest_result.returncode != 0:
                return {
                    "success": False,
                    "error_type": "test",
                    "pytest_output": pytest_result.stdout + pytest_result.stderr
                }
        except ToolingError as e:
            waypoint.status = "FAILED_TOOLING_ERROR"
            return {
                "success": False,
                "error_type": "tooling",
                "error": str(e)
            }
        
        return {"success": True}
    
    def _copy_waypoint_results(self, waypoint_dir: Path, src_dir: Path):
        """Copy successful waypoint results back to main src directory."""
        waypoint_src = waypoint_dir / "src"
        
        # Copy all files from waypoint src to main src
        for item in waypoint_src.rglob("*"):
            if item.is_file():
                relative_path = item.relative_to(waypoint_src)
                target_path = src_dir / relative_path
                target_path.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(item, target_path)