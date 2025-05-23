"""Main CLI entry point for AIMA CodeGen.
Implements spec_v5.1.md Section 3.1 - User Interaction (CLI)
"""
import sys
import logging
import logging.handlers
from typing import Optional
from pathlib import Path

import typer
from rich.console import Console
from rich.logging import RichHandler
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

from aima_codegen.orchestrator import Orchestrator
from aima_codegen.config import config
from aima_codegen.utils import setup_signal_handler

# Setup logging
logging.basicConfig(
    level=config.get("Logging", "console_level", "INFO"),
    format="%(message)s",
    datefmt="[%H:%M:%S]",
    handlers=[
        RichHandler(rich_tracebacks=True, markup=True, console=Console(stderr=True))
    ]
)

# Setup file logging
log_dir = Path.home() / ".AIMA_CodeGen" / "logs"
log_dir.mkdir(exist_ok=True)
file_handler = logging.handlers.RotatingFileHandler(
    log_dir / "app.log",
    maxBytes=config.get("Logging", "log_max_bytes", 5242880),
    backupCount=config.get("Logging", "log_backup_count", 3)
)
file_handler.setLevel(config.get("Logging", "file_level", "DEBUG"))
file_handler.setFormatter(logging.Formatter(
    "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
))
logging.getLogger().addHandler(file_handler)

logger = logging.getLogger(__name__)

# Create Typer app
app = typer.Typer(
    name="aima-codegen",
    help="AI Multi-Agent Coding Assistant - Generate Python projects with AI agents",
    add_completion=False
)

# Global orchestrator instance
orchestrator = Orchestrator()

# Setup graceful shutdown
setup_signal_handler(orchestrator.cleanup)

@app.command()
def init(
    project_name: str = typer.Argument(..., help="Name of the project to create"),
    budget: float = typer.Option(..., "--budget", "-b", help="Budget in USD for LLM API calls")
):
    """Initialize a new project with the specified budget."""
    if budget <= 0:
        typer.echo("ERROR: Budget must be a positive number.", err=True)
        raise typer.Exit(1)
    
    success = orchestrator.init_project(project_name, budget)
    if not success:
        raise typer.Exit(1)

@app.command()
def develop(
    prompt: str = typer.Option(..., "--prompt", "-p", help="Initial requirements for the project"),
    budget: float = typer.Option(0.0, "--budget", "-b", help="Budget in USD (updates project budget)"),
    provider: Optional[str] = typer.Option(None, "--provider", help="LLM provider (OpenAI, Anthropic, Google)"),
    model: Optional[str] = typer.Option(None, "--model", help="Model name to use")
):
    """Start development based on the provided requirements."""
    if not prompt:
        typer.echo("ERROR: --prompt is required for develop command.", err=True)
        raise typer.Exit(1)
    
    success = orchestrator.develop(prompt, budget, provider, model)
    if not success:
        raise typer.Exit(1)

@app.command()
def load(
    project_name: str = typer.Argument(..., help="Name of the project to load")
):
    """Load an existing project."""
    success = orchestrator.load_project(project_name)
    if not success:
        raise typer.Exit(1)

@app.command()
def status():
    """Show the current project status."""
    orchestrator.show_status()

@app.command()
def explain(
    file_path: str = typer.Argument(..., help="Path to the Python file to explain"),
    target: Optional[str] = typer.Argument(None, help="Specific function or class to explain")
):
    """Explain code in plain English."""
    orchestrator.explain_code(file_path, target)

@app.command(name="config")
def config_cmd(
    set_key: Optional[str] = typer.Option(None, "--set", help="Configuration key to set"),
    value: Optional[str] = typer.Option(None, "--value", "-v", help="Value to set"),
    get_key: Optional[str] = typer.Option(None, "--get", help="Configuration key to get")
):
    """Get or set configuration values."""
    console = Console()
    
    if set_key and value is not None:
        # Parse section and key
        if "." in set_key:
            section, key = set_key.split(".", 1)
        else:
            console.print(f"[red]ERROR: Invalid key format. Use 'Section.key'[/red]")
            raise typer.Exit(1)
        
        try:
            config.set(section, key, value)
            console.print(f"[green]✓ Set {set_key} = {value}[/green]")
        except Exception as e:
            console.print(f"[red]ERROR: Failed to set configuration: {e}[/red]")
            raise typer.Exit(1)
    
    elif get_key:
        # Parse section and key
        if "." in get_key:
            section, key = get_key.split(".", 1)
        else:
            console.print(f"[red]ERROR: Invalid key format. Use 'Section.key'[/red]")
            raise typer.Exit(1)
        
        value = config.get(section, key)
        if value is not None:
            console.print(f"{get_key} = {value}")
        else:
            console.print(f"[red]ERROR: Key '{get_key}' not found[/red]")
            raise typer.Exit(1)
    
    else:
        console.print("[yellow]Usage: config --set Section.key --value value OR config --get Section.key[/yellow]")

@app.callback()
def main():
    """AI Multi-Agent Coding Assistant - Generate Python projects with AI agents."""
    pass

if __name__ == "__main__":
    try:
        app()
    finally:
        # Ensure cleanup on exit
        orchestrator.cleanup()