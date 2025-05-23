"""Configuration management for AIMA CodeGen.
Implements spec_v5.1.md Section 7.1 - Configuration Management
"""
import os
import configparser
from pathlib import Path
from typing import Optional, Dict, Any
import json
import logging

logger = logging.getLogger(__name__)

DEFAULT_CONFIG = """# ~/.AIMA_CodeGen/config.ini
# AI Multi-Agent Coding Assistant Configuration

[General]
# Default LLM provider (OpenAI, Anthropic, or Google)
default_provider = OpenAI
# Default model (must exist in model_costs.json)
default_model = gpt-4.1-2025-04-14
# Redact LLM prompts/responses in project logs (true/false)
redact_llm_logs = true
# Application name (for paths, etc.)
app_name = AIMA_CodeGen
# Keep failed waypoint directories (for debugging)
keep_failed_waypoints = false

[LLM]
# Temperature settings
codegen_temperature = 0.2
other_temperature = 0.7
# Max tokens settings
codegen_max_tokens = 4000
other_max_tokens = 1000
# Network timeout for API calls (seconds)
network_timeout = 60
# Path to model costs file
model_costs_path = ~/.AIMA_CodeGen/model_costs.json

[VEnv]
# Preferred Python interpreter path (leave blank to auto-discover)
python_path =
# Timeout for pip install (seconds)
pip_timeout = 300
# Timeout for test/lint subprocess calls (seconds)
tool_timeout = 60
# flake8 command-line arguments
flake8_args = --ignore E501,W503 --max-line-length=88 --count --show-source --statistics
# pytest command-line arguments
pytest_args = -q

[Security]
# Config file path (for permission check)
config_path = ~/.AIMA_CodeGen/config.ini
# macOS Keychain service name for API keys
keychain_service_name = AIMA_CodeGen_Keys

[Logging]
# Console log level: DEBUG, INFO, WARNING, ERROR
console_level = INFO
# File log level (app.log)
file_level = DEBUG
# Project log level (project_activity.jsonl)
project_level = DEBUG
# Max app.log size in bytes before rotation (5MB)
log_max_bytes = 5242880
# Number of backup log files to keep
log_backup_count = 3

[API_Keys]
# (If stored here, these will be filled after user confirmation, with 0o600 perms)
# openai_api_key =
# anthropic_api_key =
# google_api_key =

[GitHub]
# GitHub integration settings
token = 
auto_pr = false
auto_merge = false
webhook_url =
"""

DEFAULT_MODEL_COSTS = {
    "gpt-4.1-2025-04-14": {
        "prompt_cost_per_1k_tokens": 0.00200,  # $2.00 per 1M tokens
        "completion_cost_per_1k_tokens": 0.00800,  # $8.00 per 1M tokens
    },
    "o4-mini-2025-04-16": {
        "prompt_cost_per_1k_tokens": 0.00110,  # $1.10 per 1M tokens
        "completion_cost_per_1k_tokens": 0.00440,  # $4.40 per 1M tokens
    },
    "o3-2025-04-16": {
        "prompt_cost_per_1k_tokens": 0.01000,  # $10.00 per 1M tokens
        "completion_cost_per_1k_tokens": 0.04000,  # $40.00 per 1M tokens
    },
    "gemini-2.5-pro-preview-05-06": {
        "prompt_cost_per_1k_tokens": 0.00125,  # $1.25 per 1M tokens
        "completion_cost_per_1k_tokens": 0.01000,  # $10.00 per 1M tokens
    },
    "gemini-2.5-flash-preview-05-20": {
        "prompt_cost_per_1k_tokens": 0.00015,  # $0.15 per 1M tokens
        "completion_cost_per_1k_tokens": 0.00060,  # $0.60 per 1M tokens
    },
    "claude-opus-4-20250514": {
        "prompt_cost_per_1k_tokens": 0.01500,  # $15.00 per 1M tokens
        "completion_cost_per_1k_tokens": 0.07500,  # $75.00 per 1M tokens
    },
    "claude-sonnet-4-20250514": {
        "prompt_cost_per_1k_tokens": 0.00300,  # $3.00 per 1M tokens
        "completion_cost_per_1k_tokens": 0.01500,  # $15.00 per 1M tokens
    }
}

class ConfigManager:
    """Manages application configuration."""
    
    def __init__(self):
        self.base_path = Path.home() / ".AIMA_CodeGen"
        self.config_path = self.base_path / "config.ini"
        self.model_costs_path = self.base_path / "model_costs.json"
        self.config = configparser.ConfigParser()
        self._ensure_config_exists()
        self._load_config()
        self._ensure_model_costs_exists()
        
    def _ensure_config_exists(self):
        """Create default config if it doesn't exist."""
        # Implements spec_v5.1.md Section 7.1
        self.base_path.mkdir(exist_ok=True)
        if not self.config_path.exists():
            self.config_path.write_text(DEFAULT_CONFIG)
            # Set permissions to 0o600 as per spec
            os.chmod(self.config_path, 0o600)
            logger.info(f"Created default config at {self.config_path}")
    
    def _ensure_model_costs_exists(self):
        """Create default model costs file if it doesn't exist."""
        # Implements spec_v5.1.md Appendix A
        if not self.model_costs_path.exists():
            with open(self.model_costs_path, 'w') as f:
                json.dump(DEFAULT_MODEL_COSTS, f, indent=2)
            logger.info(f"Created default model costs at {self.model_costs_path}")
    
    def _load_config(self):
        """Load configuration from file."""
        self.config.read(self.config_path)
    
    def get(self, section: str, key: str, fallback: Any = None) -> Any:
        """Get configuration value."""
        try:
            value = self.config.get(section, key)
            # Handle boolean values
            if value.lower() in ('true', 'false'):
                return value.lower() == 'true'
            # Handle numeric values
            try:
                if '.' in value:
                    return float(value)
                return int(value)
            except ValueError:
                return value
        except (configparser.NoSectionError, configparser.NoOptionError):
            return fallback
    
    def set(self, section: str, key: str, value: str):
        """Set configuration value and save."""
        if not self.config.has_section(section):
            self.config.add_section(section)
        self.config.set(section, key, str(value))
        with open(self.config_path, 'w') as f:
            self.config.write(f)
        # Maintain permissions
        os.chmod(self.config_path, 0o600)
    
    def get_model_costs(self) -> Dict[str, Dict[str, float]]:
        """Load model costs from JSON file."""
        # Implements spec_v5.1.md Section 4.2
        try:
            with open(self.model_costs_path, 'r') as f:
                return json.load(f)
        except (json.JSONDecodeError, FileNotFoundError) as e:
            raise RuntimeError(
                f"ERROR: 'model_costs.json' is missing or contains invalid data at '{self.model_costs_path}'. "
                "Suggestion: Please check the file's format or delete it to regenerate defaults."
            )
    
    def expand_path(self, path: str) -> Path:
        """Expand ~ in paths."""
        return Path(path).expanduser()

# Global config instance
config = ConfigManager()