"""GUI implementation for AIMA CodeGen.
Provides a comprehensive graphical interface for all application functionality.
"""
import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox, filedialog
import threading
import queue
import json
from pathlib import Path
from typing import Optional, Dict, List
import logging

from ..orchestrator import Orchestrator
from ..config import config
from ..models import ProjectState

logger = logging.getLogger(__name__)

class AIMACodeGenGUI:
    """Main GUI application for AIMA CodeGen."""
    
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("AIMA CodeGen - AI Multi-Agent Coding Assistant")
        self.root.geometry("1200x800")
        
        # Initialize orchestrator
        self.orchestrator = Orchestrator()
        self.current_project = None
        
        # Queue for thread communication
        self.message_queue = queue.Queue()
        
        # Setup UI
        self._setup_ui()
        self._setup_styles()
        
        # Start message processor
        self.root.after(100, self._process_messages)
    
    def _setup_styles(self):
        """Configure ttk styles."""
        style = ttk.Style()
        style.theme_use('clam')
        
        # Configure colors
        style.configure('Success.TLabel', foreground='green')
        style.configure('Error.TLabel', foreground='red')
        style.configure('Info.TLabel', foreground='blue')

    def _setup_ui(self):
        """Build the main UI."""
        # Menu bar
        self._create_menu()
        
        # Main container
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Configure grid weights
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(1, weight=1)
        main_frame.rowconfigure(1, weight=1)
        
        # Left panel - Project management
        self._create_project_panel(main_frame)
        
        # Center panel - Development area
        self._create_development_panel(main_frame)
        
        # Right panel - Status and logs
        self._create_status_panel(main_frame)
        
        # Bottom status bar
        self._create_status_bar()
    
    def _create_menu(self):
        """Create menu bar."""
        menubar = tk.Menu(self.root)
        self.root.config(menu=menubar)
        
        # File menu
        file_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="File", menu=file_menu)
        file_menu.add_command(label="New Project", command=self._new_project)
        file_menu.add_command(label="Load Project", command=self._load_project)
        file_menu.add_separator()
        file_menu.add_command(label="Exit", command=self.root.quit)
        
        # Tools menu
        tools_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Tools", menu=tools_menu)
        tools_menu.add_command(label="Configure API Keys", command=self._configure_api_keys)
        tools_menu.add_command(label="Model Settings", command=self._model_settings)
        tools_menu.add_command(label="GitHub Settings", command=self._github_settings)
        
        # Help menu
        help_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Help", menu=help_menu)
        help_menu.add_command(label="About", command=self._show_about)

    def _create_project_panel(self, parent):
        """Create project management panel."""
        panel = ttk.LabelFrame(parent, text="Project", padding="10")
        panel.grid(row=0, column=0, rowspan=2, sticky=(tk.W, tk.E, tk.N, tk.S), padx=(0, 5))
        
        # Project info
        ttk.Label(panel, text="Name:").grid(row=0, column=0, sticky=tk.W, pady=2)
        self.project_name_var = tk.StringVar(value="No project loaded")
        ttk.Label(panel, textvariable=self.project_name_var).grid(row=0, column=1, sticky=tk.W, pady=2)
        
        ttk.Label(panel, text="Budget:").grid(row=1, column=0, sticky=tk.W, pady=2)
        self.budget_var = tk.StringVar(value="$0.00 / $0.00")
        ttk.Label(panel, textvariable=self.budget_var).grid(row=1, column=1, sticky=tk.W, pady=2)
        
        # Buttons
        ttk.Button(panel, text="New Project", command=self._new_project).grid(
            row=2, column=0, columnspan=2, pady=5, sticky=(tk.W, tk.E))
        ttk.Button(panel, text="Load Project", command=self._load_project).grid(
            row=3, column=0, columnspan=2, pady=5, sticky=(tk.W, tk.E))
        
        # Waypoints list
        ttk.Label(panel, text="Waypoints:").grid(row=4, column=0, columnspan=2, sticky=tk.W, pady=(10, 2))
        
        # Treeview for waypoints
        self.waypoints_tree = ttk.Treeview(panel, columns=('Status', 'Type'), height=10)
        self.waypoints_tree.grid(row=5, column=0, columnspan=2, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Configure columns
        self.waypoints_tree.heading('#0', text='Description')
        self.waypoints_tree.heading('Status', text='Status')
        self.waypoints_tree.heading('Type', text='Type')
        
        self.waypoints_tree.column('#0', width=200)
        self.waypoints_tree.column('Status', width=80)
        self.waypoints_tree.column('Type', width=80)
        
        # Scrollbar
        scrollbar = ttk.Scrollbar(panel, orient=tk.VERTICAL, command=self.waypoints_tree.yview)
        scrollbar.grid(row=5, column=2, sticky=(tk.N, tk.S))
        self.waypoints_tree.configure(yscrollcommand=scrollbar.set)

    def _create_development_panel(self, parent):
        """Create main development panel."""
        panel = ttk.LabelFrame(parent, text="Development", padding="10")
        panel.grid(row=0, column=1, sticky=(tk.W, tk.E, tk.N, tk.S), padx=5)
        
        # Requirements input
        ttk.Label(panel, text="Requirements:").pack(anchor=tk.W)
        
        self.requirements_text = scrolledtext.ScrolledText(panel, height=10, width=60)
        self.requirements_text.pack(fill=tk.BOTH, expand=True, pady=(5, 10))
        
        # Control buttons
        button_frame = ttk.Frame(panel)
        button_frame.pack(fill=tk.X)
        
        self.develop_button = ttk.Button(button_frame, text="Start Development", 
                                       command=self._start_development)
        self.develop_button.pack(side=tk.LEFT, padx=5)
        
        self.stop_button = ttk.Button(button_frame, text="Stop", state=tk.DISABLED,
                                    command=self._stop_development)
        self.stop_button.pack(side=tk.LEFT, padx=5)
        
        # Model selection
        model_frame = ttk.Frame(panel)
        model_frame.pack(fill=tk.X, pady=10)
        
        ttk.Label(model_frame, text="Model Strategy:").pack(side=tk.LEFT, padx=5)
        self.model_strategy_var = tk.StringVar(value="single")
        ttk.Radiobutton(model_frame, text="Single Model", variable=self.model_strategy_var, 
                       value="single").pack(side=tk.LEFT, padx=5)
        ttk.Radiobutton(model_frame, text="Multi-Model", variable=self.model_strategy_var, 
                       value="multi").pack(side=tk.LEFT, padx=5)
        
        # Code review options
        review_frame = ttk.LabelFrame(panel, text="Code Review", padding="5")
        review_frame.pack(fill=tk.X, pady=10)
        
        self.auto_review_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(review_frame, text="Enable automatic code review", 
                       variable=self.auto_review_var).pack(anchor=tk.W)
        
        self.github_integration_var = tk.BooleanVar(value=False)
        ttk.Checkbutton(review_frame, text="GitHub integration (create PRs)", 
                       variable=self.github_integration_var).pack(anchor=tk.W)
        
        ttk.Button(review_frame, text="Manual Review", 
                  command=self._manual_review).pack(anchor=tk.W, pady=5)

    # Agent-specific model selection
        agent_models_frame = ttk.LabelFrame(panel, text="Agent Model Configuration", padding="5")
        agent_models_frame.pack(fill=tk.X, pady=10)
        
        # Create dropdowns for each agent
        agents = ["Planner", "CodeGen", "TestWriter", "Reviewer"]
        self.agent_model_vars = {}
        
        for i, agent in enumerate(agents):
            ttk.Label(agent_models_frame, text=f"{agent} Agent:").grid(row=i, column=0, sticky=tk.W, padx=5, pady=3)
            
            model_var = tk.StringVar(value="Default")
            self.agent_model_vars[agent] = model_var
            
            # Model dropdown
            model_combo = ttk.Combobox(
                agent_models_frame, 
                textvariable=model_var,
                values=["Default", "gpt-4-turbo", "gpt-3.5-turbo", "claude-3-opus", "claude-3-sonnet", "gemini-pro"],
                width=25,
                state="readonly"
            )
            model_combo.grid(row=i, column=1, padx=5, pady=3)

    def _create_status_panel(self, parent):
        """Create status and logging panel."""
        panel = ttk.LabelFrame(parent, text="Status & Logs", padding="10")
        panel.grid(row=0, column=2, rowspan=2, sticky=(tk.W, tk.E, tk.N, tk.S), padx=(5, 0))
        
        # Progress
        ttk.Label(panel, text="Progress:").pack(anchor=tk.W)
        self.progress_var = tk.DoubleVar()
        self.progress_bar = ttk.Progressbar(panel, variable=self.progress_var, maximum=100)
        self.progress_bar.pack(fill=tk.X, pady=(5, 10))
        
        # Current task
        ttk.Label(panel, text="Current Task:").pack(anchor=tk.W)
        self.current_task_var = tk.StringVar(value="Idle")
        ttk.Label(panel, textvariable=self.current_task_var, style='Info.TLabel').pack(anchor=tk.W, pady=(0, 10))
        
        # Log output
        ttk.Label(panel, text="Logs:").pack(anchor=tk.W)
        self.log_text = scrolledtext.ScrolledText(panel, height=20, width=40)
        self.log_text.pack(fill=tk.BOTH, expand=True)
        
        # Configure tags for colored output
        self.log_text.tag_config('info', foreground='blue')
        self.log_text.tag_config('success', foreground='green')
        self.log_text.tag_config('error', foreground='red')
        self.log_text.tag_config('warning', foreground='orange')
    
    def _create_status_bar(self):
        """Create bottom status bar."""
        status_bar = ttk.Frame(self.root)
        status_bar.grid(row=1, column=0, sticky=(tk.W, tk.E))
        
        self.status_var = tk.StringVar(value="Ready")
        ttk.Label(status_bar, textvariable=self.status_var).pack(side=tk.LEFT, padx=10)
        
        # Provider and model info
        self.provider_var = tk.StringVar(value="Provider: Not configured")
        ttk.Label(status_bar, textvariable=self.provider_var).pack(side=tk.RIGHT, padx=10)

    def _new_project(self):
        """Create new project dialog."""
        dialog = NewProjectDialog(self.root)
        self.root.wait_window(dialog.dialog)
        
        if dialog.result:
            name, budget = dialog.result
            self._run_async(self._create_project_async, name, budget)
    
    def _load_project(self):
        """Load existing project dialog."""
        # Get list of projects
        projects_dir = Path.home() / ".AIMA_CodeGen" / "projects"
        if not projects_dir.exists():
            messagebox.showinfo("No Projects", "No projects found.")
            return
        
        projects = [p.name for p in projects_dir.iterdir() if p.is_dir()]
        if not projects:
            messagebox.showinfo("No Projects", "No projects found.")
            return
        
        dialog = LoadProjectDialog(self.root, projects)
        self.root.wait_window(dialog.dialog)
        
        if dialog.result:
            self._run_async(self._load_project_async, dialog.result)
    
    def _start_development(self):
        """Start development process."""
        if not self.current_project:
            messagebox.showerror("Error", "Please load a project first.")
            return
        
        requirements = self.requirements_text.get("1.0", tk.END).strip()
        if not requirements:
            messagebox.showerror("Error", "Please enter requirements.")
            return
        
        # Disable buttons
        self.develop_button.config(state=tk.DISABLED)
        self.stop_button.config(state=tk.NORMAL)
        
        # Get settings
        use_multi_model = self.model_strategy_var.get() == "multi"
        auto_review = self.auto_review_var.get()
        github_integration = self.github_integration_var.get()
        
        self._run_async(
            self._develop_async, 
            requirements, 
            use_multi_model, 
            auto_review, 
            github_integration
        )
    
    def _run_async(self, func, *args):
        """Run function in separate thread."""
        thread = threading.Thread(target=func, args=args, daemon=True)
        thread.start()

    def _create_project_async(self, name: str, budget: float):
        """Create project in background."""
        try:
            self._log("info", f"Creating project '{name}'...")
            success = self.orchestrator.init_project(name, budget)
            
            if success:
                self._log("success", f"Project '{name}' created successfully!")
                self.current_project = name
                self._update_project_info()
            else:
                self._log("error", "Failed to create project.")
                
        except Exception as e:
            self._log("error", f"Error: {str(e)}")
    
    def _load_project_async(self, name: str):
        """Load project in background."""
        try:
            self._log("info", f"Loading project '{name}'...")
            success = self.orchestrator.load_project(name)
            
            if success:
                self._log("success", f"Project '{name}' loaded successfully!")
                self.current_project = name
                self._update_project_info()
                self._update_waypoints()
            else:
                self._log("error", "Failed to load project.")
                
        except Exception as e:
            self._log("error", f"Error: {str(e)}")
    
    def _develop_async(self, requirements: str, use_multi_model: bool, 
                      auto_review: bool, github_integration: bool):
        """Run development process in background."""
        try:
            self._log("info", "Starting development process...")
            
            # Configure multi-model if requested
            if use_multi_model:
                self._configure_multi_model()
            
            # Start development
            success = self.orchestrator.develop(requirements, 0.0)
            
            if success:
                self._log("success", "Development completed successfully!")
                
                if auto_review:
                    self._log("info", "Starting code review...")
                    self._run_code_review(github_integration)
            else:
                self._log("error", "Development failed.")
                
        except Exception as e:
            self._log("error", f"Error: {str(e)}")
        finally:
            # Re-enable buttons
            self.message_queue.put(('enable_buttons', None))

    def _configure_multi_model(self):
        """Configure multi-model strategy."""
        if not self.orchestrator.multi_model_enabled:
            self.orchestrator.enable_multi_model()
        
        # Apply agent model configurations from dropdowns
        for agent, model_var in self.agent_model_vars.items():
            model = model_var.get()
            if model != "Default":
                # Map model names to actual model identifiers
                model_map = {
                    "gpt-4-turbo": "gpt-4-turbo-preview",
                    "gpt-3.5-turbo": "gpt-3.5-turbo",
                    "claude-3-opus": "claude-3-opus-20240229",
                    "claude-3-sonnet": "claude-3-sonnet-20240229",
                    "gemini-pro": "gemini-pro"
                }
                
                # Determine provider from model
                if model.startswith("gpt"):
                    provider = "OpenAI"
                elif model.startswith("claude"):
                    provider = "Anthropic"
                elif model.startswith("gemini"):
                    provider = "Google"
                else:
                    provider = "OpenAI"  # Default
                
                # Update agent configuration
                self.orchestrator.multi_model_manager.update_agent_config(
                    agent, 
                    provider=provider,
                    model=model_map.get(model, model)
                )
    
    def _run_code_review(self, github_integration: bool):
        """Run code review process."""
        # This will use the ReviewerAgent
        pass
    
    def _manual_review(self):
        """Open manual code review dialog."""
        if not self.current_project:
            messagebox.showinfo("No Project", "Please load a project first.")
            return
        
        # TODO: Implement manual review dialog
        messagebox.showinfo("Coming Soon", "Manual review dialog coming soon!")
    
    def _configure_api_keys(self):
        """Open API key configuration dialog."""
        dialog = APIKeyDialog(self.root)
        self.root.wait_window(dialog.dialog)
    
    def _model_settings(self):
        """Open model settings dialog."""
        dialog = ModelSettingsDialog(self.root)
        self.root.wait_window(dialog.dialog)
    
    def _github_settings(self):
        """Open GitHub settings dialog."""
        dialog = GitHubSettingsDialog(self.root)
        self.root.wait_window(dialog.dialog)
    
    def _show_about(self):
        """Show about dialog."""
        messagebox.showinfo(
            "About AIMA CodeGen",
            "AIMA CodeGen v1.0.0\n\n"
            "AI Multi-Agent Coding Assistant\n\n"
            "Generate Python projects with specialized AI agents."
        )
    
    def _log(self, level: str, message: str):
        """Add log message to queue."""
        self.message_queue.put(('log', (level, message)))

    def _process_messages(self):
        """Process messages from background threads."""
        try:
            while True:
                msg_type, data = self.message_queue.get_nowait()
                
                if msg_type == 'log':
                    level, message = data
                    self.log_text.insert(tk.END, f"{message}\n", level)
                    self.log_text.see(tk.END)
                    
                elif msg_type == 'progress':
                    self.progress_var.set(data)
                    
                elif msg_type == 'task':
                    self.current_task_var.set(data)
                    
                elif msg_type == 'enable_buttons':
                    self.develop_button.config(state=tk.NORMAL)
                    self.stop_button.config(state=tk.DISABLED)
                    
        except queue.Empty:
            pass
        
        # Schedule next check
        self.root.after(100, self._process_messages)
    
    def _update_project_info(self):
        """Update project information display."""
        if self.orchestrator.project_state:
            state = self.orchestrator.project_state
            self.project_name_var.set(state.project_name)
            self.budget_var.set(f"${state.current_spent_usd:.2f} / ${state.total_budget_usd:.2f}")
            
            # Update provider info
            provider = state.api_provider or "Not configured"
            model = state.model_name or "Not set"
            self.provider_var.set(f"Provider: {provider} | Model: {model}")
    
    def _update_waypoints(self):
        """Update waypoints display."""
        # Clear existing
        for item in self.waypoints_tree.get_children():
            self.waypoints_tree.delete(item)
        
        # Add waypoints
        if self.orchestrator.project_state and self.orchestrator.project_state.waypoints:
            for wp in self.orchestrator.project_state.waypoints:
                status_symbol = {
                    "SUCCESS": "✓",
                    "FAILED": "✗",
                    "RUNNING": "▶",
                    "PENDING": "◯"
                }.get(wp.status.split('_')[0], "?")
                
                self.waypoints_tree.insert(
                    '', 'end',
                    text=wp.description,
                    values=(f"{status_symbol} {wp.status}", wp.agent_type)
                )
    
    def _stop_development(self):
        """Stop development process."""
        # TODO: Implement stop functionality
        messagebox.showinfo("Stop", "Stopping development...")
    
    def run(self):
        """Start the GUI application."""
        self.root.mainloop()
    
    # Dialog classes
class NewProjectDialog:
    """Dialog for creating new project."""
    
    def __init__(self, parent):
        self.result = None
        
        self.dialog = tk.Toplevel(parent)
        self.dialog.title("New Project")
        self.dialog.geometry("400x200")
        self.dialog.transient(parent)
        self.dialog.grab_set()
        
        # Center the dialog
        self.dialog.update_idletasks()
        x = (self.dialog.winfo_screenwidth() // 2) - (self.dialog.winfo_width() // 2)
        y = (self.dialog.winfo_screenheight() // 2) - (self.dialog.winfo_height() // 2)
        self.dialog.geometry(f"+{x}+{y}")
        
        # Create form
        frame = ttk.Frame(self.dialog, padding="20")
        frame.pack(fill=tk.BOTH, expand=True)
        
        ttk.Label(frame, text="Project Name:").grid(row=0, column=0, sticky=tk.W, pady=10)
        self.name_entry = ttk.Entry(frame, width=30)
        self.name_entry.grid(row=0, column=1, pady=10)
        self.name_entry.focus()
        
        ttk.Label(frame, text="Budget (USD):").grid(row=1, column=0, sticky=tk.W, pady=10)
        self.budget_entry = ttk.Entry(frame, width=30)
        self.budget_entry.grid(row=1, column=1, pady=10)
        self.budget_entry.insert(0, "10.0")
        
        # Buttons
        button_frame = ttk.Frame(frame)
        button_frame.grid(row=2, column=0, columnspan=2, pady=20)
        
        ttk.Button(button_frame, text="Create", command=self._create).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Cancel", command=self.dialog.destroy).pack(side=tk.LEFT, padx=5)
        
        # Bind Enter key
        self.dialog.bind('<Return>', lambda e: self._create())
    
    def _create(self):
        """Validate and create project."""
        name = self.name_entry.get().strip()
        if not name:
            messagebox.showerror("Error", "Please enter a project name.")
            return
        
        try:
            budget = float(self.budget_entry.get())
            if budget <= 0:
                raise ValueError("Budget must be positive")
        except ValueError:
            messagebox.showerror("Error", "Please enter a valid budget amount.")
            return
        
        self.result = (name, budget)
        self.dialog.destroy()

class LoadProjectDialog:
    """Dialog for loading existing project."""
    
    def __init__(self, parent, projects: List[str]):
        self.result = None
        
        self.dialog = tk.Toplevel(parent)
        self.dialog.title("Load Project")
        self.dialog.geometry("400x300")
        self.dialog.transient(parent)
        self.dialog.grab_set()
        
        # Center the dialog
        self.dialog.update_idletasks()
        x = (self.dialog.winfo_screenwidth() // 2) - (self.dialog.winfo_width() // 2)
        y = (self.dialog.winfo_screenheight() // 2) - (self.dialog.winfo_height() // 2)
        self.dialog.geometry(f"+{x}+{y}")
        
        # Create list
        frame = ttk.Frame(self.dialog, padding="20")
        frame.pack(fill=tk.BOTH, expand=True)
        
        ttk.Label(frame, text="Select a project:").pack(anchor=tk.W, pady=(0, 10))
        
        # Listbox with scrollbar
        list_frame = ttk.Frame(frame)
        list_frame.pack(fill=tk.BOTH, expand=True)
        
        scrollbar = ttk.Scrollbar(list_frame)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        self.listbox = tk.Listbox(list_frame, yscrollcommand=scrollbar.set)
        self.listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.config(command=self.listbox.yview)
        
        # Add projects
        for project in sorted(projects):
            self.listbox.insert(tk.END, project)
        
        # Buttons
        button_frame = ttk.Frame(frame)
        button_frame.pack(pady=10)
        
        ttk.Button(button_frame, text="Load", command=self._load).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Cancel", command=self.dialog.destroy).pack(side=tk.LEFT, padx=5)
        
        # Bind double-click
        self.listbox.bind('<Double-Button-1>', lambda e: self._load())
    
    def _load(self):
        """Load selected project."""
        selection = self.listbox.curselection()
        if not selection:
            messagebox.showerror("Error", "Please select a project.")
            return
        
        self.result = self.listbox.get(selection[0])
        self.dialog.destroy()

class APIKeyDialog:
    """Dialog for configuring API keys."""
    
    def __init__(self, parent):
        self.dialog = tk.Toplevel(parent)
        self.dialog.title("API Key Configuration")
        self.dialog.geometry("500x400")
        self.dialog.transient(parent)
        self.dialog.grab_set()
        
        # Create notebook for tabs
        notebook = ttk.Notebook(self.dialog, padding="10")
        notebook.pack(fill=tk.BOTH, expand=True)
        
        # OpenAI tab
        openai_frame = ttk.Frame(notebook)
        notebook.add(openai_frame, text="OpenAI")
        self._create_api_tab(openai_frame, "OpenAI", "openai_api_key")
        
        # Anthropic tab
        anthropic_frame = ttk.Frame(notebook)
        notebook.add(anthropic_frame, text="Anthropic")
        self._create_api_tab(anthropic_frame, "Anthropic", "anthropic_api_key")
        
        # Google tab
        google_frame = ttk.Frame(notebook)
        notebook.add(google_frame, text="Google AI")
        self._create_api_tab(google_frame, "Google AI", "google_api_key")
        
        # Buttons
        button_frame = ttk.Frame(self.dialog)
        button_frame.pack(pady=10)
        
        ttk.Button(button_frame, text="Save", command=self._save).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Close", command=self.dialog.destroy).pack(side=tk.LEFT, padx=5)
    
    def _create_api_tab(self, parent, provider: str, config_key: str):
        """Create API key configuration tab."""
        frame = ttk.Frame(parent, padding="20")
        frame.pack(fill=tk.BOTH, expand=True)
        
        ttk.Label(frame, text=f"{provider} API Key:").pack(anchor=tk.W, pady=(0, 5))
        
        # Entry with show/hide
        entry_frame = ttk.Frame(frame)
        entry_frame.pack(fill=tk.X, pady=(0, 10))
        
        entry = ttk.Entry(entry_frame, show="*")
        entry.pack(side=tk.LEFT, fill=tk.X, expand=True)
        
        # Load existing key
        existing_key = config.get("API_Keys", config_key, "")
        if existing_key:
            entry.insert(0, existing_key)
        
        show_var = tk.BooleanVar()
        show_check = ttk.Checkbutton(
            entry_frame, 
            text="Show", 
            variable=show_var,
            command=lambda: entry.config(show="" if show_var.get() else "*")
        )
        show_check.pack(side=tk.LEFT, padx=(5, 0))
        
        # Store reference
        setattr(self, f"{config_key}_entry", entry)
        
        # Instructions
        instructions = {
            "OpenAI": "Get your API key from https://platform.openai.com/api-keys",
            "Anthropic": "Get your API key from https://console.anthropic.com/",
            "Google AI": "Get your API key from https://makersuite.google.com/app/apikey"
        }
        
        ttk.Label(frame, text=instructions[provider], foreground="gray").pack(anchor=tk.W)
        
        # Test button
        ttk.Button(
            frame, 
            text=f"Test {provider} Connection",
            command=lambda: self._test_api_key(provider, config_key)
        ).pack(anchor=tk.W, pady=(20, 0))
    
    def _save(self):
        """Save API keys to config."""
        # Save each key
        for provider, config_key in [
            ("OpenAI", "openai_api_key"),
            ("Anthropic", "anthropic_api_key"),
            ("Google AI", "google_api_key")
        ]:
            entry = getattr(self, f"{config_key}_entry")
            key = entry.get().strip()
            
            if key:
                config.set("API_Keys", config_key, key)
        
        messagebox.showinfo("Success", "API keys saved successfully!")
    
    def _test_api_key(self, provider: str, config_key: str):
        """Test API key validity."""
        entry = getattr(self, f"{config_key}_entry")
        key = entry.get().strip()
        
        if not key:
            messagebox.showerror("Error", "Please enter an API key.")
            return
        
        # TODO: Implement actual API key testing
        messagebox.showinfo("Test Result", f"{provider} API key test not yet implemented.")
class ModelSettingsDialog:
    """Dialog for model settings."""
    
    def __init__(self, parent):
        self.dialog = tk.Toplevel(parent)
        self.dialog.title("Model Settings")
        self.dialog.geometry("600x500")
        self.dialog.transient(parent)
        self.dialog.grab_set()
        
        # Main frame
        main_frame = ttk.Frame(self.dialog, padding="20")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Default model settings
        ttk.Label(main_frame, text="Default Settings", font=('', 12, 'bold')).pack(anchor=tk.W, pady=(0, 10))
        
        default_frame = ttk.Frame(main_frame)
        default_frame.pack(fill=tk.X, pady=(0, 20))
        
        ttk.Label(default_frame, text="Default Provider:").grid(row=0, column=0, sticky=tk.W, pady=5)
        self.default_provider = ttk.Combobox(default_frame, values=["OpenAI", "Anthropic", "Google"], width=20)
        self.default_provider.grid(row=0, column=1, pady=5)
        self.default_provider.set(config.get("General", "default_provider", "OpenAI"))
        
        ttk.Label(default_frame, text="Default Model:").grid(row=1, column=0, sticky=tk.W, pady=5)
        self.default_model = ttk.Entry(default_frame, width=30)
        self.default_model.grid(row=1, column=1, pady=5)
        self.default_model.insert(0, config.get("General", "default_model", ""))
        
        # Multi-model configuration
        ttk.Label(main_frame, text="Multi-Model Configuration", font=('', 12, 'bold')).pack(anchor=tk.W, pady=(0, 10))
        
        # Create notebook for agent-specific settings
        notebook = ttk.Notebook(main_frame)
        notebook.pack(fill=tk.BOTH, expand=True)
        
        # Add tabs for each agent
        for agent in ["Planner", "CodeGen", "TestWriter", "Reviewer", "Explainer"]:
            frame = ttk.Frame(notebook)
            notebook.add(frame, text=agent)
            self._create_agent_config(frame, agent)
        
        # Buttons
        button_frame = ttk.Frame(self.dialog)
        button_frame.pack(pady=10)
        
        ttk.Button(button_frame, text="Save", command=self._save).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Cancel", command=self.dialog.destroy).pack(side=tk.LEFT, padx=5)
    
    def _create_agent_config(self, parent, agent: str):
        """Create configuration for specific agent."""
        frame = ttk.Frame(parent, padding="20")
        frame.pack(fill=tk.BOTH, expand=True)
        
        ttk.Label(frame, text=f"{agent} Agent Configuration").pack(anchor=tk.W, pady=(0, 10))
        
        # Provider selection
        ttk.Label(frame, text="Provider:").pack(anchor=tk.W, pady=(5, 0))
        provider_var = ttk.Combobox(frame, values=["Default", "OpenAI", "Anthropic", "Google"], width=20)
        provider_var.pack(anchor=tk.W, pady=(0, 10))
        provider_var.set("Default")
        
        # Model selection
        ttk.Label(frame, text="Model:").pack(anchor=tk.W, pady=(5, 0))
        model_var = ttk.Entry(frame, width=40)
        model_var.pack(anchor=tk.W, pady=(0, 10))
        model_var.insert(0, "Use default")
        
        # Temperature
        ttk.Label(frame, text="Temperature:").pack(anchor=tk.W, pady=(5, 0))
        temp_frame = ttk.Frame(frame)
        temp_frame.pack(anchor=tk.W, pady=(0, 10))
        
        temp_var = tk.DoubleVar(value=0.7)
        temp_scale = ttk.Scale(temp_frame, from_=0.0, to=2.0, variable=temp_var, orient=tk.HORIZONTAL, length=200)
        temp_scale.pack(side=tk.LEFT)
        ttk.Label(temp_frame, textvariable=temp_var).pack(side=tk.LEFT, padx=(10, 0))
        
        # Store references
        setattr(self, f"{agent.lower()}_provider", provider_var)
        setattr(self, f"{agent.lower()}_model", model_var)
        setattr(self, f"{agent.lower()}_temp", temp_var)
    
    def _save(self):
        """Save model settings."""
        # Save default settings
        config.set("General", "default_provider", self.default_provider.get())
        config.set("General", "default_model", self.default_model.get())
        
        # TODO: Save agent-specific settings
        messagebox.showinfo("Success", "Model settings saved!")
        self.dialog.destroy()


class GitHubSettingsDialog:
    """Dialog for GitHub settings."""
    
    def __init__(self, parent):
        self.dialog = tk.Toplevel(parent)
        self.dialog.title("GitHub Settings")
        self.dialog.geometry("500x300")
        self.dialog.transient(parent)
        self.dialog.grab_set()
        
        # Main frame
        frame = ttk.Frame(self.dialog, padding="20")
        frame.pack(fill=tk.BOTH, expand=True)
        
        # GitHub token
        ttk.Label(frame, text="GitHub Personal Access Token:").pack(anchor=tk.W, pady=(0, 5))
        
        token_frame = ttk.Frame(frame)
        token_frame.pack(fill=tk.X, pady=(0, 10))
        
        self.token_entry = ttk.Entry(token_frame, show="*")
        self.token_entry.pack(side=tk.LEFT, fill=tk.X, expand=True)
        
        # Load existing token
        existing_token = config.get("GitHub", "token", "")
        if existing_token:
            self.token_entry.insert(0, existing_token)
        
        show_var = tk.BooleanVar()
        ttk.Checkbutton(
            token_frame,
            text="Show",
            variable=show_var,
            command=lambda: self.token_entry.config(show="" if show_var.get() else "*")
        ).pack(side=tk.LEFT, padx=(5, 0))
        
        # Instructions
        ttk.Label(
            frame, 
            text="Get a token from: https://github.com/settings/tokens\n"
                 "Required scopes: repo, workflow",
            foreground="gray"
        ).pack(anchor=tk.W, pady=(0, 20))
        
        # Auto-create PR checkbox
        self.auto_pr_var = tk.BooleanVar()
        ttk.Checkbutton(
            frame,
            text="Automatically create pull requests after development",
            variable=self.auto_pr_var
        ).pack(anchor=tk.W, pady=5)
        
        # Auto-merge checkbox
        self.auto_merge_var = tk.BooleanVar()
        ttk.Checkbutton(
            frame,
            text="Automatically merge approved pull requests",
            variable=self.auto_merge_var
        ).pack(anchor=tk.W, pady=5)
        
        # Buttons
        button_frame = ttk.Frame(self.dialog)
        button_frame.pack(pady=10)
        
        ttk.Button(button_frame, text="Save", command=self._save).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Test Connection", command=self._test).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Cancel", command=self.dialog.destroy).pack(side=tk.LEFT, padx=5)
    
    def _save(self):
        """Save GitHub settings."""
        token = self.token_entry.get().strip()
        if token:
            config.set("GitHub", "token", token)
        
        config.set("GitHub", "auto_pr", str(self.auto_pr_var.get()))
        config.set("GitHub", "auto_merge", str(self.auto_merge_var.get()))
        
        messagebox.showinfo("Success", "GitHub settings saved!")
        self.dialog.destroy()
    
    def _test(self):
        """Test GitHub connection."""
        token = self.token_entry.get().strip()
        if not token:
            messagebox.showerror("Error", "Please enter a GitHub token.")
            return
        
        # TODO: Implement actual connection test
        messagebox.showinfo("Test", "GitHub connection test not yet implemented.")


def launch_gui():
    """Launch the GUI application."""
    app = AIMACodeGenGUI()
    app.run()


if __name__ == "__main__":
    launch_gui()
