# AIMA CodeGen - AI Multi-Agent Coding Assistant

A sophisticated AI-powered coding assistant that uses multiple specialized agents to generate, test, and explain Python projects. Built with a multi-agent architecture for robust, production-ready code generation.

## 🚀 New Features

- **🎨 Professional GUI**: Full-featured graphical interface with project management, real-time logs, and visual waypoint tracking
- **🤖 Multi-Model Support**: Configure different LLM models for each agent - optimize for cost and quality
- **🔗 GitHub Integration**: Automated code review, pull request creation, and branch management
- **👁️ AI Code Review**: Intelligent code analysis with the Reviewer agent before merging
- **🧠 Self-Improvement System**: The system can now enhance its own capabilities autonomously using the `improve` command

## Features

### Core Capabilities
- **Multi-Agent Architecture**: Specialized agents for planning, code generation, test writing, code review, and explanation
- **Multiple LLM Providers**: Support for OpenAI, Anthropic, and Google AI models
- **Budget Management**: Built-in cost tracking and budget enforcement
- **Virtual Environment Management**: Automatic Python environment setup and dependency management
- **Comprehensive Testing**: Automated test generation and validation
- **Rich CLI Interface**: Beautiful command-line interface with progress tracking
- **Project State Management**: Persistent project state with waypoint tracking

### Advanced Features
- **GUI Application**: Professional desktop interface for all operations
- **Per-Agent Model Configuration**: Use GPT-3.5 for planning, GPT-4 for code, Claude for reviews
- **GitHub Workflow Integration**: Create PRs, manage branches, automated merging
- **Model Presets**: Fast, Quality, and Balanced configurations
- **Real-time Progress Monitoring**: Visual feedback for all operations
- **Multi-Project Management**: Handle multiple projects simultaneously

## Installation

### Prerequisites

- Python 3.10 or higher
- pip package manager
- Git (for GitHub integration features)

### Install from Source

1. Clone or download the project
2. Navigate to the project directory
3. Install in development mode:

```bash
pip install -e .
```

### Install Dependencies

All dependencies are automatically installed with the package:

- `typer` - CLI framework
- `rich` - Rich text and beautiful formatting
- `openai` - OpenAI API client
- `anthropic` - Anthropic API client
- `google-generativeai` - Google AI API client
- `tiktoken` - Token counting for OpenAI models
- `keyring` - Secure API key storage
- `pydantic` - Data validation and settings management
- `psutil` - System and process utilities
- `packaging` - Version handling
- `requests` - HTTP library for GitHub integration
- `tkinter` - GUI framework (usually pre-installed with Python)

## Quick Start

### 1. Set Up API Keys

Configure your preferred LLM provider's API key:

```bash
# For OpenAI
aima-codegen config --set API_Keys.openai_api_key --value YOUR_OPENAI_KEY

# For Anthropic
aima-codegen config --set API_Keys.anthropic_api_key --value YOUR_ANTHROPIC_KEY

# For Google AI
aima-codegen config --set API_Keys.google_api_key --value YOUR_GOOGLE_KEY
```

### 2. Launch the GUI (Recommended)

The easiest way to use AIMA CodeGen is through the graphical interface:

```bash
aima-codegen gui
```

This opens a comprehensive interface where you can:
- Create and manage projects visually
- Configure different models for each agent
- Monitor progress in real-time
- Review code before committing
- Create GitHub pull requests automatically

### 3. CLI Usage

For command-line usage:

#### Initialize a Project

```bash
aima-codegen init "My Calculator Project" --budget 10.0
```

#### Start Development

```bash
aima-codegen develop --prompt "Create a scientific calculator with GUI using tkinter. Include basic arithmetic operations, trigonometric functions, and logarithms."
```

#### Check Project Status

```bash
aima-codegen status
```

#### Load Existing Projects

```bash
aima-codegen load "My Calculator Project"
```

## GUI Overview

The GUI provides three main panels:

1. **Project Panel** (Left)
   - Project information and budget tracking
   - Waypoint tree with visual status indicators
   - Project management buttons

2. **Development Panel** (Center)
   - Requirements input area
   - Development controls
   - Model strategy selection (Single/Multi-Model)
   - Per-agent model configuration
   - Code review options

3. **Status Panel** (Right)
   - Real-time progress bar
   - Current task display
   - Color-coded log output
   - Live updates from all agents

## Multi-Model Configuration

AIMA CodeGen supports using different models for different tasks:

### Example Configuration
- **Planner Agent**: GPT-3.5-Turbo (fast, economical planning)
- **CodeGen Agent**: GPT-4 (high-quality code generation)
- **TestWriter Agent**: GPT-4 (comprehensive test coverage)
- **Reviewer Agent**: Claude-3-Opus (excellent at finding bugs)

### Model Presets

1. **Fast Development**: Uses economical models for rapid prototyping
2. **High Quality**: Premium models for production-ready code
3. **Balanced**: Optimal mix of performance and cost

## GitHub Integration

### Setup

1. Configure your GitHub token:
```bash
aima-codegen config --set GitHub.token --value YOUR_GITHUB_TOKEN
```

2. Enable auto-PR in the GUI or config:
```bash
aima-codegen config --set GitHub.auto_pr --value true
```

### Features

- **Automated PR Creation**: Each waypoint can create its own PR
- **AI Code Review**: Review code before creating PRs
- **Branch Management**: Automatic branch creation and switching
- **PR Descriptions**: AI-generated PR descriptions with changes summary

## CLI Commands

### `init`
Initialize a new project with specified budget.

```bash
aima-codegen init PROJECT_NAME --budget AMOUNT
```

### `develop`
Start development based on requirements.

```bash
aima-codegen develop --prompt "Your requirements" [--budget AMOUNT] [--provider PROVIDER] [--model MODEL]
```

### `load`
Load an existing project.

```bash
aima-codegen load PROJECT_NAME
```

### `status`
Show current project status, progress, and budget usage.

```bash
aima-codegen status
```

### `explain`
Get plain English explanations of code.

```bash
aima-codegen explain path/to/file.py [function_or_class_name]
```

### `gui`
Launch the graphical user interface.

```bash
aima-codegen gui
```

### `config`
Manage configuration settings.

```bash
# Get a configuration value
aima-codegen config --get Section.key

# Set a configuration value
aima-codegen config --set Section.key --value "new_value"
```

## Self-Improvement System

AIMA CodeGen can now improve its own capabilities autonomously:

### `improve`
Enable the system to implement enhancements to itself.

```bash
aima-codegen improve FEATURE --budget AMOUNT
```

Available improvements:
- `agent-guides`: Create comprehensive documentation for each agent
- `basic-telemetry`: Add execution logging and decision tracking
- `debrief-system`: Implement post-task self-assessment

### Features
- **Autonomous Enhancement**: System modifies its own code safely
- **Agent Guidelines**: Self-generated best practices documentation
- **Telemetry Logging**: Complete execution tracking with decision reasoning
- **Self-Assessment**: Post-task debriefs with confidence metrics
- **Safe Modification**: Symlink-based approach prevents breaking changes

### Example
```bash
# Have the system improve its own documentation
aima-codegen improve agent-guides --budget 5.0
```

The system will analyze its own architecture and implement the requested improvements autonomously.

## Configuration

The application stores configuration in `~/.AIMA_CodeGen/config.ini`. Key settings include:

### General Settings
- `default_provider`: Default LLM provider (OpenAI, Anthropic, Google)
- `default_model`: Default model to use
- `redact_llm_logs`: Whether to redact sensitive information in logs

### LLM Settings
- `codegen_temperature`: Temperature for code generation (default: 0.2)
- `other_temperature`: Temperature for other tasks (default: 0.7)
- `codegen_max_tokens`: Max tokens for code generation (default: 4000)
- `network_timeout`: API call timeout in seconds (default: 60)

### Virtual Environment Settings
- `python_path`: Preferred Python interpreter path
- `pip_timeout`: Timeout for pip operations (default: 300s)
- `flake8_args`: Arguments for code linting
- `pytest_args`: Arguments for test execution

### GitHub Settings
- `token`: GitHub personal access token
- `auto_pr`: Automatically create pull requests (true/false)
- `auto_merge`: Automatically merge approved PRs (true/false)

## Project Structure

```
~/.AIMA_CodeGen/
├── config.ini              # Configuration file
├── model_costs.json        # Model pricing information
├── multi_model_config.json # Multi-model configurations
├── logs/                   # Application logs
└── projects/               # Project directories
    └── project-name/
        ├── src/            # Generated source code
        ├── tests/          # Generated tests
        ├── waypoints/      # Development waypoints
        ├── logs/           # Project-specific logs
        └── project_state.json  # Project state
```

## Multi-Agent Architecture

### Planner Agent
- Analyzes requirements and creates development waypoints
- Breaks down complex tasks into manageable steps
- Determines optimal agent sequence

### CodeGen Agent
- Generates Python code based on specifications
- Handles dependency management
- Implements error handling and best practices

### TestWriter Agent
- Creates comprehensive test suites
- Generates unit tests, integration tests, and edge cases
- Ensures code coverage and quality

### Reviewer Agent
- Performs AI-powered code review
- Identifies bugs, security issues, and performance problems
- Suggests improvements and best practices
- Integrates with GitHub for PR reviews

### Explainer Agent
- Provides plain English explanations of code
- Documents complex algorithms and design patterns
- Helps with code understanding and maintenance

## Budget Management

The system tracks costs across all LLM API calls:

- **Pre-call Budget Checks**: Prevents operations that would exceed budget
- **Real-time Cost Tracking**: Updates spending after each API call
- **Model-specific Pricing**: Accurate cost calculation per model
- **Budget Warnings**: Alerts when approaching budget limits
- **Per-Agent Cost Tracking**: See which agents use the most budget

## Error Handling

Robust error handling includes:

- **API Rate Limiting**: Automatic retry with exponential backoff
- **Network Failures**: Graceful handling of connectivity issues
- **Invalid Responses**: JSON parsing error recovery
- **Budget Enforcement**: Hard stops when budget is exceeded
- **Validation Errors**: Clear error messages for invalid inputs

## Development Workflow

1. **Planning Phase**: Requirements analysis and waypoint creation
2. **Code Generation**: Iterative code development with validation
3. **Testing Phase**: Comprehensive test suite generation
4. **Review Phase**: AI-powered code review and suggestions
5. **GitHub Integration**: Automated PR creation and management
6. **Validation**: Syntax checking, linting, and test execution
7. **Revision Loops**: Automatic error correction and improvement
8. **Documentation**: Code explanation and documentation generation

## Supported Models

### OpenAI
- GPT-4 (latest)
- GPT-4 Turbo
- GPT-3.5 Turbo
- o3-mini
- o4-mini

### Anthropic
- Claude 3 Opus
- Claude 3 Sonnet
- Claude 3 Haiku

### Google AI
- Gemini 2.5 Pro
- Gemini 2.5 Flash

## Security

- **API Key Storage**: Secure storage using system keyring
- **File Permissions**: Restricted access to configuration files
- **Log Redaction**: Optional redaction of sensitive information
- **Project Isolation**: Each project runs in isolated environment
- **GitHub Token Security**: Tokens never logged or exposed

## Troubleshooting

### Common Issues

1. **Import Errors**: Ensure package is installed with `pip install -e .`
2. **API Key Issues**: Verify keys are set correctly with `aima-codegen config --get API_Keys.provider_api_key`
3. **Budget Exceeded**: Check spending with `aima-codegen status`
4. **Python Version**: Ensure Python 3.10+ is being used
5. **GUI Not Opening**: Check tkinter is installed: `python -m tkinter`
6. **GitHub Integration**: Ensure token has `repo` and `workflow` scopes

### Logs

Check logs for detailed error information:
- Application logs: `~/.AIMA_CodeGen/logs/app.log`
- Project logs: `~/.AIMA_CodeGen/projects/PROJECT_NAME/logs/`

## Contributing

This project follows the AIMA (Artificial Intelligence: A Modern Approach) principles for multi-agent systems. Contributions should maintain the modular architecture and comprehensive error handling.

## License

This project is provided as-is for educational and development purposes.

## Support

For issues and questions:
1. Check the logs for detailed error information
2. Verify configuration settings
3. Ensure API keys are valid and have sufficient credits
4. Check that all dependencies are properly installed
5. Visit the [GitHub Issues](https://github.com/ianlucas1/aima_codegen_project/issues) page
