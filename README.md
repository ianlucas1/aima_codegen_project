# AIMA CodeGen - AI Multi-Agent Coding Assistant

A sophisticated AI-powered coding assistant that uses multiple specialized agents to generate, test, and explain Python projects. Built with a multi-agent architecture for robust, production-ready code generation.

## Features

- **Multi-Agent Architecture**: Specialized agents for planning, code generation, test writing, and code explanation
- **Multiple LLM Providers**: Support for OpenAI, Anthropic, and Google AI models
- **Budget Management**: Built-in cost tracking and budget enforcement
- **Virtual Environment Management**: Automatic Python environment setup and dependency management
- **Comprehensive Testing**: Automated test generation and validation
- **Rich CLI Interface**: Beautiful command-line interface with progress tracking
- **Project State Management**: Persistent project state with waypoint tracking

## Installation

### Prerequisites

- Python 3.10 or higher
- pip package manager

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

### 2. Initialize a Project

Create a new project with a budget:

```bash
aima-codegen init "My Calculator Project" --budget 10.0
```

### 3. Start Development

Begin development with your requirements:

```bash
aima-codegen develop --prompt "Create a scientific calculator with GUI using tkinter. Include basic arithmetic operations, trigonometric functions, and logarithms."
```

### 4. Check Project Status

Monitor progress and costs:

```bash
aima-codegen status
```

### 5. Load Existing Projects

Resume work on existing projects:

```bash
aima-codegen load "My Calculator Project"
```

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

### `config`
Manage configuration settings.

```bash
# Get a configuration value
aima-codegen config --get Section.key

# Set a configuration value
aima-codegen config --set Section.key --value "new_value"
```

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

## Project Structure

```
~/.AIMA_CodeGen/
├── config.ini              # Configuration file
├── model_costs.json         # Model pricing information
├── logs/                    # Application logs
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
4. **Validation**: Syntax checking, linting, and test execution
5. **Revision Loops**: Automatic error correction and improvement
6. **Documentation**: Code explanation and documentation generation

## Supported Models

### OpenAI
- GPT-4 (latest)
- GPT-4 Turbo
- GPT-3.5 Turbo

### Anthropic
- Claude 3 Opus
- Claude 3 Sonnet
- Claude 3 Haiku

### Google AI
- Gemini Pro
- Gemini Pro Vision

## Security

- **API Key Storage**: Secure storage using system keyring
- **File Permissions**: Restricted access to configuration files
- **Log Redaction**: Optional redaction of sensitive information
- **Project Isolation**: Each project runs in isolated environment

## Troubleshooting

### Common Issues

1. **Import Errors**: Ensure package is installed with `pip install -e .`
2. **API Key Issues**: Verify keys are set correctly with `aima-codegen config --get API_Keys.provider_api_key`
3. **Budget Exceeded**: Check spending with `aima-codegen status`
4. **Python Version**: Ensure Python 3.10+ is being used

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